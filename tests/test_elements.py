#!/usr/bin/env python

import six
from io import StringIO
from mock import patch
from unittest import TestCase
from xmltool.testbase import BaseTest
from lxml import etree, html as lxml_html
import os.path
from xmltool import utils, dtd_parser, dtd
from xmltool.elements import (
    Element,
    ContainerElement,
    ListElement,
    TextElement,
    ChoiceElement,
    ChoiceListElement,
    update_eol,
    InListMixin,
    InChoiceMixin,
    EmptyElement,
    escape_attr,
)
from xmltool import render, factory
import xmltool.elements as elements
from .test_dtd_parser import (
    BOOK_XML,
    BOOK_DTD,
    EXERCISE_XML_2,
    EXERCISE_DTD_2,
    EXERCISE_DTD,
    MOVIE_DTD,
    MOVIE_XML_TITANIC,
    MOVIE_XML_TITANIC_COMMENTS,
)

_marker = object()


class FakeClass(object):
    root = None

    def __init__(self, *args, **kw):
        self.xml_elements = {}


class TestElement(BaseTest):

    def setUp(self):
        self.sub_cls = type(
            'SubCls', (ContainerElement,),
            {
                'tagname': 'subtag',
                'children_classes': []
            }
        )
        self.cls = type(
            'Cls', (ContainerElement, ),
            {
                'tagname': 'tag',
                'children_classes': [self.sub_cls]
            }
        )
        self.root_cls = type(
            'Cls', (ContainerElement, ),
            {
                'tagname': 'root_tag',
                'children_classes': [self.cls]
            }
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls._parent_cls = self.cls

    def test_prefixes_no_cache(self):
        obj = self.cls()
        sub_obj = self.sub_cls(obj)
        self.assertEqual(obj.prefixes_no_cache, ['tag'])
        self.assertEqual(sub_obj.prefixes_no_cache, ['tag', 'subtag'])

    def test_prefixes(self):
        obj = self.cls()
        sub_obj = self.sub_cls(obj)
        self.assertEqual(obj.prefixes, ['tag'])
        self.assertEqual(sub_obj.prefixes, ['tag', 'subtag'])

        # The prefixes are in the cache
        sub_obj._parent_obj = None
        self.assertEqual(sub_obj.prefixes, ['tag', 'subtag'])
        self.assertEqual(sub_obj._cache_prefixes, ['tag', 'subtag'])

        sub_obj._cache_prefixes = None
        self.assertEqual(sub_obj.prefixes, ['subtag'])

    def test_position(self):
        obj = self.cls()
        self.assertEqual(obj.position, None)

    def test__get_creatable_class_by_tagnames(self):
        self.assertEqual(self.cls._get_creatable_class_by_tagnames(),
                         {'tag': self.cls})

    def test__get_creatable_subclass_by_tagnames(self):
        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {'subtag': self.sub_cls}
        self.assertEqual(res, expected)

        sub_cls1 = type(
            'SubCls1', (ContainerElement,),
            {
                'tagname': 'subtag1',
                'children_classes': [],
                '_parent_cls': self.cls,
            }
        )
        self.cls.children_classes += [sub_cls1]

        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {
            'subtag': self.sub_cls,
            'subtag1': sub_cls1,
        }
        self.assertEqual(res, expected)

    def test_get_child_class(self):
        self.assertEqual(self.cls.get_child_class('subtag'), self.sub_cls)
        self.assertEqual(self.cls.get_child_class('unexisting'), None)

    def test__get_value_from_parent(self):
        obj = self.cls(self.root_obj)
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), obj)
        self.root_obj['tag'] = None
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)

    def test__get_sub_value(self):
        result = self.cls._get_sub_value(self.root_obj)
        self.assertFalse(result)
        self.cls._required = True
        obj = self.cls(self.root_obj)
        self.assertEqual(self.cls._get_sub_value(self.root_obj), obj)

        self.root_obj['tag'] = None
        result = self.cls._get_sub_value(self.root_obj)
        self.assertTrue(result)
        self.assertTrue(result != obj)

    def test__has_value(self):
        obj = self.cls()
        self.assertFalse(obj._has_value())
        obj['subtag'] = self.sub_cls()
        self.assertTrue(obj._has_value())

    def test_children(self):
        obj = self.cls()
        children = list(obj.children)
        self.assertEqual(children, [])

        sub = obj.add('subtag')
        children = list(obj.children)
        self.assertEqual(children, [sub])

    def test__children_with_required(self):
        obj = self.cls()
        children = list(obj._children_with_required)
        self.assertEqual(children, [])

        self.sub_cls._required = True
        children = list(obj._children_with_required)
        self.assertEqual(len(children), 1)
        self.assertTrue(isinstance(children[0], self.sub_cls))

    def test__full_children(self):
        obj = self.cls()
        children = list(obj._full_children)
        self.assertEqual(len(children), 1)
        self.assertTrue(isinstance(children[0], self.sub_cls))

    def test_root(self):
        self.assertEqual(self.root_obj.root, self.root_obj)
        obj = self.cls._create('subtag', self.root_obj)
        self.assertEqual(obj.root, self.root_obj)

    def test__add(self):
        try:
            obj = self.cls._create('tag', self.root_obj, 'my value')
            assert(False)
        except Exception as e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj = self.cls._create('tag', self.root_obj)
        self.assertEqual(obj._parent_obj, self.root_obj)
        self.assertEqual(obj.root, self.root_obj)
        self.assertTrue(isinstance(obj, ContainerElement))
        self.assertEqual(self.root_obj['tag'], obj)

    def test_is_addable(self):
        obj = self.cls()
        res = obj.is_addable('test')
        self.assertEqual(res, False)

        res = obj.is_addable('subtag')
        self.assertEqual(res, True)

        obj['subtag'] = 'somthing'
        res = obj.is_addable('subtag')
        self.assertEqual(res, False)

    def test_add(self):
        root_cls = type(
            'RootElement', (ContainerElement,),
            {
                'tagname': 'root_element',
                'children_classes': [],
            }
        )
        root_obj = root_cls()
        obj = self.cls(root_obj)
        newobj = obj.add('subtag')
        self.assertTrue(newobj)
        try:
            obj.add('unexisting')
        except Exception as e:
            self.assertEqual(str(e), 'Invalid child unexisting')

        root_obj = root_cls()
        obj = self.cls(root_obj)
        try:
            newobj = obj.add('subtag', 'my value')
            assert 0
        except Exception as e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

    def test_delete(self):
        try:
            self.root_obj.delete()
            assert(False)
        except Exception as e:
            self.assertEqual(str(e), 'Can\'t delete the root Element')

        obj = self.cls(self.root_obj)
        self.assertEqual(self.root_obj[self.cls.tagname], obj)
        obj.delete()
        self.assertEqual(self.root_obj.get(self.cls.tagname), None)

    def test_add_attribute(self):
        obj = self.cls()
        obj._attribute_names = ['attr1', 'attr2']
        obj.add_attribute('attr1', 'value1')
        self.assertEqual(obj.attributes, {'attr1': 'value1'})
        obj.add_attribute('attr2', 'value2')
        self.assertEqual(obj.attributes, {'attr1': 'value1',
                                           'attr2': 'value2'})
        obj.add_attribute('attr2', 'newvalue2')
        self.assertEqual(obj.attributes, {'attr1': 'value1',
                                           'attr2': 'newvalue2'})

        try:
            obj.add_attribute('unexisting', 'newvalue2')
        except Exception as e:
            self.assertEqual(str(e), 'Invalid attribute name: unexisting')

    def test__load_attributes_from_xml(self):
        obj = self.cls()
        obj._attribute_names = ['attr']
        xml = etree.Element('test')
        xml.attrib['attr'] = 'value'
        obj._load_attributes_from_xml(xml)
        self.assertEqual(obj.attributes, {'attr': 'value'})

    def test__load_attributes_from_dict(self):
        obj = self.cls()
        obj._attribute_names = ['attr']
        obj._load_attributes_from_dict({})
        self.assertEqual(obj.attributes, None)
        obj._load_attributes_from_dict({'key': 'value'})
        self.assertEqual(obj.attributes, None)

        dic = {'_attrs': {'attr': 'value'}}
        obj._load_attributes_from_dict(dic)
        self.assertEqual(obj.attributes, {'attr': 'value'})
        self.assertEqual(dic, {})

        dic = {'_attrs': {'unexisting': 'value'}}
        try:
            obj._load_attributes_from_dict(dic)
        except Exception as e:
            self.assertEqual(str(e), 'Invalid attribute name: unexisting')

    def test__attributes_to_xml(self):
        xml = etree.Element('test')
        obj = self.cls()
        obj._attribute_names = ['attr']
        obj._attributes_to_xml(xml)
        self.assertEqual(xml.attrib, {})
        dic = {'attr': 'value'}
        obj.attributes = dic
        obj._attributes_to_xml(xml)
        self.assertEqual(xml.attrib, dic)

    def test__attributes_to_html(self):
        obj = self.cls(self.root_obj)
        obj._attribute_names = ['attr']
        dic = {'attr': 'value'}
        html = obj._attributes_to_html()
        self.assertEqual(html, '')

        cls = type(
            'Cls', (InListMixin, TextElement, ),
            {
                'tagname': 'tag',
                'children_classes': [self.sub_cls],
                '_attribute_names': ['attr'],
            }
        )

        list_cls = type(
            'ListCls', (ListElement,),
            {
                'tagname': 'list_tag',
                '_children_class': cls,
                '_parent_cls': self.root_cls
            }
        )

        cls._parent_cls = list_cls
        root_obj = self.root_cls()
        self.root_cls.children_classes = [list_cls]
        list_obj = root_obj.add(list_cls.tagname)
        obj = list_obj.add(cls.tagname)
        obj.attributes = dic
        list_obj.insert(0, EmptyElement(parent_obj=list_obj))
        html = obj._attributes_to_html()
        expected = (
            '<a name="attr=value"></a>'
            '<input value="value" name="root_tag:list_tag:1:tag:_attrs:attr" '
            'id="root_tag:list_tag:1:tag:_attrs:attr" class="_attrs" />')
        self.assertEqual(html, expected)

    def test__load_comment_from_xml(self):
        obj = self.cls()
        xml = etree.Element('test')
        self.assertEqual(obj.comment, None)
        obj._load_comment_from_xml(xml)
        self.assertEqual(obj.comment, None)

        for i in range(5):
            if i == 2:
                elt = etree.Element('sub')
            else:
                elt = etree.Comment('comment %i' % i)
            xml.append(elt)
        obj._load_comment_from_xml(xml.getchildren()[2])
        expected = 'comment 0\ncomment 1\ncomment 3\ncomment 4'
        self.assertEqual(obj.comment, expected)

        obj = self.cls()
        xml = etree.Element('test')
        for i in range(3):
            elt = etree.Element('sub')
            xml.append(elt)
        obj._load_comment_from_xml(xml.getchildren()[2])
        self.assertEqual(obj.comment, None)

        obj = self.cls()
        xml = etree.Element('test')
        for i in range(5):
            if i in [0, 2, 4]:
                elt = etree.Element('sub')
            else:
                elt = etree.Comment('comment %i' % i)
            xml.append(elt)
        obj._load_comment_from_xml(xml.getchildren()[2])
        expected = 'comment 1'
        self.assertEqual(obj.comment, expected)

    def test__load_comment_from_dict(self):
        obj = self.cls()
        obj._load_comment_from_dict({})
        self.assertEqual(obj.comment, None)
        dic = {'_comment': 'my comment'}
        obj._load_comment_from_dict(dic)
        self.assertEqual(obj.comment, 'my comment')

    def test__comment_to_xml(self):
        xml = etree.Element('test')
        obj = self.cls()
        obj._comment_to_xml(xml)
        self.assertEqual(xml.getprevious(), None)

        obj.comment = 'my comment'
        obj._comment_to_xml(xml)
        elt = xml.getprevious()
        self.assertEqual(elt.getprevious(), None)
        self.assertEqual(elt.text, 'my comment')

    def test__comment_to_html(self):
        obj = self.cls(self.root_obj)
        html = obj._comment_to_html()
        expected = ('<a data-comment-name="root_tag:tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>')
        self.assertEqual(html, expected)

        obj.comment = 'my comment'
        html = obj._comment_to_html()
        expected = ('<a data-comment-name="root_tag:tag:_comment" '
                    'class="btn-comment has-comment" title="my comment"></a>'
                    '<textarea class="_comment" name="root_tag:tag:_comment">'
                    'my comment</textarea>')
        self.assertEqual(html, expected)

    def test__load_extra_from_xml(self):
        xml = etree.Element('test')
        xml.append(etree.Element('prev'))
        elt = etree.Element('element')
        elt.attrib['attr'] = 'value'
        xml.append(elt)
        xml.append(etree.Comment('comment'))
        obj = self.cls()
        obj._attribute_names = ['attr']
        obj._load_extra_from_xml(xml.getchildren()[1])
        self.assertEqual(obj.comment, 'comment')
        self.assertEqual(obj.attributes, {'attr': 'value'})

    def test_load_from_xml(self):
        xml = etree.Element('test')
        xml.append(etree.Element('prev'))
        elt = etree.Element('element')
        elt.attrib['attr'] = 'value'
        xml.append(elt)
        xml.append(etree.Comment('comment'))

        sub_cls1 = type('SubClsPrev', (ContainerElement,), {'tagname': 'prev',
                                                   'children_classes': []})
        sub_cls2 = type('SubClsElement', (ContainerElement,),
                        {'tagname': 'element',
                         'children_classes': [],
                         '_attribute_names': ['attr']})
        cls = type('Cls', (ContainerElement, ),
                   {'tagname': 'tag',
                    'children_classes': [sub_cls1, sub_cls2]})
        obj = cls()
        obj.load_from_xml(xml)
        self.assertTrue(obj)
        self.assertFalse(obj.comment)
        self.assertFalse(obj.attributes)
        self.assertTrue(obj['prev'])
        self.assertFalse(obj['prev'].comment)
        self.assertFalse(obj['prev'].attributes)
        self.assertTrue(obj['element'])
        self.assertEqual(obj['element'].comment, 'comment')
        self.assertEqual(obj['element'].attributes, {'attr': 'value'})

    def test__load_extra_from_dict(self):
        obj = self.cls()
        obj._attribute_names = ['attr']
        dic = {'_comment': 'comment', '_attrs': {'attr': 'value'}}
        obj._load_extra_from_dict(dic)
        self.assertEqual(obj.comment, 'comment')
        self.assertEqual(obj.attributes, {'attr': 'value'})

    def test_load_from_dict(self):
        sub_cls1 = type('SubClsPrev', (ContainerElement,), {'tagname': 'prev',
                                                   'children_classes': []})
        sub_cls2 = type('SubClsElement', (ContainerElement,),
                        {'tagname': 'element',
                         'children_classes': [],
                         '_attribute_names': ['attr']})
        cls = type('Cls', (ContainerElement, ),
                   {'tagname': 'tag',
                    'children_classes': [sub_cls1, sub_cls2]})
        obj = cls()
        dic = {}
        obj.load_from_dict(dic)
        self.assertEqual(obj.comment, None)
        self.assertEqual(obj.attributes, None)
        dic = {
            'tag': {
                '_comment': 'comment',
                'element': {'_attrs': {'attr': 'value'},
                            '_comment': 'element comment'
                           }
            }
        }
        obj.load_from_dict(dic)
        self.assertTrue(obj)
        self.assertEqual(obj.comment, 'comment')
        self.assertFalse(obj.attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj['element'])
        self.assertEqual(obj['element'].comment, 'element comment')
        self.assertEqual(obj['element'].attributes, {'attr': 'value'})

        # skip_extra = True
        obj = cls()
        # We need a new dict since we remove _attrs and _comment when we
        # load_from_dict
        dic = {
            'tag': {
                '_comment': 'comment',
                'element': {
                    '_attrs': {'attr': 'value'},
                    '_comment': 'element comment'
                }
            }
        }
        obj.load_from_dict(dic, skip_extra=True)
        self.assertTrue(obj)
        self.assertEqual(obj.comment, None)
        self.assertFalse(obj.attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj['element'])
        self.assertEqual(obj['element'].comment, None)
        self.assertEqual(obj['element'].attributes, None)

    def test_load_from_dict_sub_list(self):
        sub_cls = type('Element', (InListMixin, ContainerElement,),
                       {'tagname': 'sub',
                        'children_classes': [],
                        '_attribute_names': ['attr']})
        list_cls = type('ListElement', (ListElement,),
                        {'tagname': 'element',
                         'children_classes': [],
                         '_children_class': sub_cls})
        cls = type('Cls', (ContainerElement, ),
                   {'tagname': 'tag',
                    'children_classes': [list_cls]})
        list_cls._parent_cls = cls
        sub_cls._parent_cls = list_cls
        dic = {}
        obj = cls()
        obj.load_from_dict(dic)
        self.assertEqual(obj.comment, None)
        self.assertEqual(obj.attributes, None)
        dic = {
            'tag': {
                '_comment': 'comment',
                'element': [
                    {'sub': {
                        '_attrs': {'attr': 'value'},
                        '_comment': 'element comment'
                    }}]
            }
        }
        obj = cls()
        obj.load_from_dict(dic)
        self.assertEqual(obj.comment, 'comment')
        self.assertFalse(obj.attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj['sub'])
        self.assertEqual(len(obj['sub']), 1)
        self.assertEqual(obj['sub'][0].comment, 'element comment')
        self.assertEqual(obj['sub'][0].attributes, {'attr': 'value'})

        # Test with empty element to keep the index position
        dic = {
            'tag': {
                '_comment': 'comment',
                'element': [
                    None,
                    {'sub': {
                        '_attrs': {'attr': 'value'},
                        '_comment': 'element comment'
                    }}]
            }
        }
        obj = cls()
        obj.load_from_dict(dic)
        self.assertEqual(obj.comment, 'comment')
        self.assertFalse(obj.attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj['sub'])
        self.assertEqual(len(obj['sub']), 2)
        self.assertTrue(isinstance(obj['sub'][0], elements.EmptyElement))
        self.assertEqual(obj['sub'][1].comment, 'element comment')
        self.assertEqual(obj['sub'][1].attributes, {'attr': 'value'})

    def test_to_xml(self):
        sub_cls = type('SubClsElement', (ContainerElement,),
                            {'tagname': 'element',
                             'children_classes': [],
                             '_attribute_names': ['attr']})
        cls = type('Cls', (ContainerElement, ),
                   {'tagname': 'tag',
                   'children_classes': [sub_cls]})
        obj = cls()
        obj['element'] = sub_cls()
        obj['element'].comment = 'comment'
        obj['element'].attributes = {'attr': 'value'}
        xml = obj.to_xml()
        self.assertEqual(xml.tag, 'tag')
        self.assertEqual(xml.attrib, {})
        self.assertEqual(len(xml.getchildren()), 2)
        comment = xml.getchildren()[0]
        self.assertEqual(comment.text, 'comment')
        element = xml.getchildren()[1]
        self.assertEqual(element.tag, 'element')
        self.assertEqual(element.attrib, {'attr': 'value'})

    def test_to_xml_sub_list(self):
        sub_cls = type('Element', (InListMixin, ContainerElement,),
                       {'tagname': 'sub',
                        'children_classes': [],
                        '_attribute_names': ['attr']})
        list_cls = type('ListElement', (ListElement,),
                        {'tagname': 'element',
                         '_children_class': sub_cls})
        cls = type('Cls', (ContainerElement, ),
                   {'tagname': 'tag',
                    'children_classes': [list_cls]})
        list_cls._parent_cls = cls
        sub_cls._parent_cls = list_cls
        obj = cls()
        lis = list_cls(obj)
        obj1 = lis.add(sub_cls.tagname)
        obj1.comment = 'comment1'
        obj1.attributes = {'attr': 'value'}
        obj2 = lis.add(sub_cls.tagname)
        obj2.comment = 'comment2'
        xml = obj.to_xml()
        self.assertEqual(xml.tag, 'tag')
        self.assertEqual(len(xml.getchildren()), 4)
        (comment1,
         element1,
         comment2,
         element2) = xml.getchildren()
        self.assertEqual(comment1.text, 'comment1')
        self.assertEqual(element1.tag, 'sub')
        self.assertEqual(element1.attrib, {'attr': 'value'})
        self.assertEqual(comment2.text, 'comment2')
        self.assertEqual(element2.tag, 'sub')
        self.assertEqual(element2.attrib, {})

    def test__get_html_add_button(self):
        obj = self.cls(self.root_obj)
        html = obj._get_html_add_button()
        expected = ('<a class="btn-add btn-add-tag" data-elt-id="root_tag:tag">'
                    'Add tag</a>')
        self.assertEqual(html, expected)

        cls = type(
            'Cls', (InListMixin, TextElement, ),
            {
                'tagname': 'tag',
                'children_classes': [self.sub_cls],
                '_attribute_names': ['attr'],
            }
        )

        list_cls = type(
            'ListCls', (ListElement,),
            {
                'tagname': 'list_tag',
                '_children_class': cls,
                '_parent_cls': self.root_cls
            }
        )

        cls._parent_cls = list_cls
        self.root_cls.children_classes = [list_cls]

        list_obj = self.root_obj.add(list_cls.tagname)
        obj = list_obj.add(cls.tagname)
        list_obj.insert(0, EmptyElement(parent_obj=list_obj))

        html = obj._get_html_add_button('css_class')
        expected = ('<a class="btn-add btn-add-tag css_class" '
                    'data-elt-id="root_tag:list_tag:1:tag">'
                    'Add tag</a>')
        self.assertEqual(html, expected)

        sub_cls = type('SubCls', (InChoiceMixin, ContainerElement,), {
            'tagname': 'tag'
        })
        cls = type('MultipleCls', (ChoiceElement,), {
            '_choice_classes': [sub_cls],
            'tagname': 'choice_tagname',
            '_parent_cls': self.root_cls,
        })
        sub_cls._parent_cls = cls
        self.root_cls.children_classes = [cls]
        obj = cls(self.root_cls())
        html = obj._get_html_add_button()
        expected = ('<select class="btn-add">'
                    '<option>New tag</option>'
                    '<option class="xt-option-tag" '
                    'value="root_tag:tag">tag</option>'
                    '</select>')
        self.assertEqual(html, expected)

        # Test element in a choice
        obj = obj.add('tag')
        html = obj._get_html_add_button()
        self.assertEqual(html, expected)

    def test_to_jstree_dict(self):
        obj = self.cls()
        result = obj.to_jstree_dict()
        expected = {
            'text': 'tag',
            'li_attr': {
                'class': 'tree_tag tag'
            },
            'a_attr': {
                'id': 'tree_tag',
            },
            'children': [],
            'state': {'opened': True},
        }
        self.assertEqual(result, expected)

        cls = type(
            'Cls', (InListMixin, TextElement, ),
            {
                'tagname': 'tag',
                'children_classes': [self.sub_cls],
                '_attribute_names': ['attr'],
            }
        )

        list_cls = type(
            'ListCls', (ListElement,),
            {
                'tagname': 'list_tag',
                '_children_class': cls,
                '_parent_cls': self.root_cls
            }
        )

        cls._parent_cls = list_cls
        self.root_cls.children_classes = [list_cls]

        list_obj = self.root_obj.add(list_cls.tagname)
        obj = list_obj.add(cls.tagname)
        obj.text = 'my value'
        for i in range(10):
            list_obj.insert(0, EmptyElement(parent_obj=list_obj))

        result = obj.to_jstree_dict()
        expected = {
            'text': u'tag <span class="_tree_text">(my value)</span>',
            'li_attr': {
                'class': 'tree_root_tag:list_tag tag'
            },
            'a_attr': {
                'id': 'tree_root_tag:list_tag:10:tag',
            },
            'children': [],
            'state': {'opened': True},
        }
        self.assertEqual(result, expected)

        obj.add(self.sub_cls.tagname)
        result = obj.to_jstree_dict()
        expected = {
            'text': u'tag <span class="_tree_text">(my value)</span>',
            'li_attr': {
                'class': 'tree_root_tag:list_tag tag'},
            'a_attr': {
                'id': 'tree_root_tag:list_tag:10:tag',
            },
            'children': [
                {
                    'li_attr': {
                        'class': 'tree_root_tag:list_tag:10:tag:subtag subtag',
                    },
                    'a_attr': {
                        'id': 'tree_root_tag:list_tag:10:tag:subtag'
                    },
                    'children': [],
                    'text': 'subtag',
                    'state': {'opened': True},
                }
            ],
            'state': {'opened': True},
        }
        self.assertEqual(result, expected)

    def test_to_jstree_dict_with_ListElement(self):
        sub_cls = type('Element', (InListMixin, ContainerElement,),
                       {'tagname': 'sub',
                        'children_classes': [],
                        '_attribute_names': ['attr']})
        list_cls = type('ListElement', (ListElement,),
                        {'tagname': 'element',
                         '_children_class': sub_cls})
        cls = type('Cls', (ContainerElement, ),
                   {'tagname': 'tag',
                    'children_classes': [list_cls]})

        list_cls._parent_cls = cls
        sub_cls._parent_cls = list_cls
        obj = cls()
        result = obj.to_jstree_dict()
        expected = {
            'text': 'tag',
            'li_attr': {
                'class': 'tree_tag tag'
            },
            'a_attr': {
                'id': 'tree_tag',
            },
            'children': [],
            'state': {'opened': True},
        }
        self.assertEqual(result, expected)

        list_cls._required = True
        result = obj.to_jstree_dict()
        expected = {
            'text': 'tag',
            'li_attr': {
                'class': 'tree_tag tag'
            },
            'a_attr': {
                'id': 'tree_tag',
            },
            'children': [
                {
                    'text': 'sub',
                    'li_attr': {
                        'class': 'tree_tag:element sub'
                    },
                    'a_attr': {
                        'id': 'tree_tag:element:0:sub',
                    },
                    'children': [],
                    'state': {'opened': True},
                }
            ],
            'state': {'opened': True},
        }
        self.assertEqual(result, expected)

    def test___getitem__(self):
        obj = self.cls()
        obj['subtag'] = 'Hello world'
        self.assertEqual(obj['subtag'], 'Hello world')
        try:
            self.assertEqual(obj['unexisting'], 'Hello world')
            assert 0
        except KeyError as e:
            self.assertEqual(str(e), "'unexisting'")

    def test___contains__(self):
        obj = self.cls()
        obj['subtag'] = 'Hello world'
        self.assertTrue('subtag' in obj)
        self.assertFalse('unexisting' in obj)

    def test_get_or_add(self):
        obj = self.cls()
        try:
            obj.get_or_add('unexisting')
            assert 0
        except Exception as e:
            self.assertEqual(str(e), 'Invalid child unexisting')
        subtag = obj.get_or_add('subtag')
        self.assertTrue(subtag)
        self.assertEqual(subtag._parent_obj, obj)
        self.assertEqual(subtag.root, obj)

        subtag1 = obj.get_or_add('subtag')
        self.assertEqual(subtag1, subtag)

    def test_walk(self):
        parent_obj = self.cls()
        obj = self.sub_cls(parent_obj)

        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj])

        parent_obj['subtag'] = None
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [])

        sub_sub_cls = type(
            'SubSubCls', (TextElement, ),
            {
                'tagname': 'subsub',
                'children_classes': [],
                '_parent_cls': self.sub_cls,
            }
        )
        self.sub_cls.children_classes = [sub_sub_cls]

        obj = self.sub_cls(parent_obj)
        subsub1 = sub_sub_cls(obj)
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj, subsub1])

    def test_findall(self):
        parent_obj = self.cls()
        obj = self.sub_cls(parent_obj)
        lis = parent_obj.findall('subtag')
        self.assertEqual(lis, [obj])

        lis = parent_obj.findall('unexisting')
        self.assertEqual(lis, [])

    def test_write(self):
        filename = 'tests/test.xml'
        self.assertFalse(os.path.isfile(filename))
        try:
            obj = self.cls()
            try:
                obj.write()
                assert 0
            except Exception as e:
                self.assertEqual(str(e), 'No filename given')

            obj.dtd_url = None
            try:
                obj.write(filename)
                assert 0
            except Exception as e:
                self.assertEqual(str(e), 'No dtd given')

            with patch('xmltool.dtd.DTD.validate_xml', return_value=True):
                obj.write(filename, dtd_url='http://dtd.url')

            obj.write(filename, dtd_url='http://dtd.url', validate=False)
            result = open(filename, 'r').read()
            expected = ("<?xml version='1.0' encoding='UTF-8'?>\n"
                        '<!DOCTYPE tag SYSTEM "http://dtd.url">\n'
                        "<tag/>\n")
            self.assertEqual(result, expected)

            obj.filename = filename
            obj.write(dtd_url='http://dtd.url', validate=False)

            obj.dtd_url = 'http://dtd.url'
            obj.encoding = 'iso-8859-1'
            obj.write(validate=False)
            result = open(filename, 'r').read()
            expected = ("<?xml version='1.0' encoding='iso-8859-1'?>\n"
                        '<!DOCTYPE tag SYSTEM "http://dtd.url">\n'
                        "<tag/>\n")
            self.assertEqual(result, expected)

            transform = lambda s: s.replace('tag', 'replaced-tag')
            obj.write(validate=False, transform=transform)
            result = open(filename, 'r').read()
            expected = ("<?xml version='1.0' encoding='iso-8859-1'?>\n"
                        '<!DOCTYPE replaced-tag SYSTEM "http://dtd.url">\n'
                        "<replaced-tag/>\n")
            self.assertEqual(result, expected)
        finally:
            if os.path.isfile(filename):
                os.remove(filename)


class TestContainerElement(BaseTest):

    def setUp(self):
        self.sub_cls = type(
            'SubCls', (ContainerElement,),
            {
                'tagname': 'subtag',
                'children_classes': []
            }
        )
        self.cls = type(
            'Cls', (ContainerElement, ),
            {
                'tagname': 'tag',
                'children_classes': [self.sub_cls]
            }
        )
        self.root_cls = type(
            'Cls', (ContainerElement, ),
            {
                'tagname': 'root_tag',
                'children_classes': [self.cls]
            }
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls._parent_cls = self.cls

    def test_to_html(self):
        obj = self.cls()
        # Root element
        html = obj._to_html()
        expected1 = (
            '<div class="panel panel-default tag" id="tag">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" href="#collapse-tag">tag'
            '<a data-comment-name="tag:_comment" class="btn-comment" '
            'title="Add comment"></a>'
            '</span>'
            '</div>'
            '<div class="panel-body panel-collapse collapse in" id="collapse-tag">'
            '<a class="btn-add btn-add-subtag" data-elt-id="tag:subtag">Add subtag</a>'
            '</div></div>')
        self.assertEqual_(html, expected1)

        html = obj.to_html()
        self.assertEqual_(html, expected1)

        # Container with parent
        obj = self.cls()
        obj._parent_obj = self.root_obj
        html = obj._to_html()
        expected_button = ('<a class="btn-add btn-add-tag" '
                           'data-elt-id="root_tag:tag">'
                           'Add tag</a>')
        self.assertEqual_(html, expected_button)

        # HTML with root prefix and button
        expected2 = (
            '<div class="panel panel-default tag" id="root_tag:tag">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" href="#collapse-root_tag\:tag">'
            'tag<a class="btn-add btn-add-tag hidden" '
            'data-elt-id="root_tag:tag">Add tag</a>'
            '<a class="btn-delete" data-target="#root_tag:tag" title="Delete"></a>'
            '<a data-comment-name="root_tag:tag:_comment" class="btn-comment" '
            'title="Add comment"></a></span></div>'
            '<div class="panel-body panel-collapse collapse in" '
            'id="collapse-root_tag:tag">'
            '<a class="btn-add btn-add-subtag" '
            'data-elt-id="root_tag:tag:subtag">Add subtag</a>'
            '</div></div>'
        )

        html = obj.to_html()
        self.assertEqual_(html, expected2)

        # HTML without buttons
        expected3 = (
            '<div class="panel panel-default tag" id="root_tag:tag">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" href="#collapse-root_tag\:tag">tag'
            '<a data-comment-name="root_tag:tag:_comment" class="btn-comment" '
            'title="Add comment"></a>'
            '</span>'
            '</div>'
            '<div class="panel-body panel-collapse collapse in" '
            'id="collapse-root_tag:tag">'
            '<a class="btn-add btn-add-subtag" '
            'data-elt-id="root_tag:tag:subtag">Add '
            'subtag</a></div></div>')

        # Required Container
        obj = self.cls()
        obj._parent_obj = self.root_obj
        obj._required = True
        html = obj._to_html()
        self.assertEqual_(html, expected3)

        html = obj.to_html()
        self.assertEqual_(html, expected3)

        # Not required container with a sub object
        obj = self.cls()
        obj._parent_obj = self.root_obj
        obj._required = False
        obj['subtag'] = self.sub_cls(obj)
        html = obj._to_html()
        self.assertEqual_(html, expected2)

        html = obj.to_html()
        self.assertEqual_(html, expected2)

    def test_to_html_readonly(self):
        obj = self.cls()
        obj.root.html_renderer = render.ReadonlyRender()
        html = obj._to_html()
        expected1 = (
            '<div class="panel panel-default tag" id="tag">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" href="#collapse-tag">tag</span>'
            '</div>'
            '<div class="panel-body panel-collapse collapse in" '
            'id="collapse-tag">'
            '</div></div>')
        self.assertEqual(html, expected1)

        obj = self.cls()
        obj.root.html_renderer = render.ReadonlyRender()
        obj._parent_obj = 'my fake parent'
        html = obj._to_html()
        self.assertEqual(html, '')

        obj = self.cls()
        obj.root.html_renderer = render.ReadonlyRender()
        html = obj._to_html()
        expected2 = (
            '<div class="panel panel-default tag" id="tag">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" href="#collapse-tag">'
            'tag</span></div>'
            '<div class="panel-body panel-collapse collapse in" '
            'id="collapse-tag">'
            '</div></div>'
        )
        self.assertEqual(html, expected2)

        obj._required = True
        html = obj._to_html()
        self.assertEqual(html, expected1)

        obj._required = False
        obj['subtag'] = self.sub_cls(obj)
        html = obj._to_html()
        self.assertEqual(html, expected2)


class TestTextElement(BaseTest):

    def setUp(self):
        self.sub_cls = type(
            'SubCls', (ContainerElement,),
            {
                'tagname': 'subtag',
                'children_classes': []
            }
        )
        self.cls = type(
            'Cls', (TextElement, ),
            {
                'tagname': 'tag',
                'children_classes': [self.sub_cls],
                '_attribute_names': ['attr']
            }
        )
        self.root_cls = type(
            'Cls', (ContainerElement, ),
            {
                'tagname': 'parent_tag',
                'children_classes': [self.cls]
            }
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls._parent_cls = self.cls

    def test___repr__(self):
        self.assertTrue(repr(self.cls()))

    def test_position(self):
        obj = self.cls()
        self.assertEqual(obj.position, None)

    def test__get_creatable_class_by_tagnames(self):
        res = self.cls._get_creatable_class_by_tagnames()
        expected = {
            'tag': self.cls
        }
        self.assertEqual(res, expected)

    def test__get_creatable_subclass_by_tagnames(self):
        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {
            'subtag': self.sub_cls
        }
        self.assertEqual(res, expected)

    def test__add(self):
        obj = self.cls._create('tagname', self.root_obj, 'my value')
        self.assertEqual(obj.text, 'my value')
        self.assertEqual(obj._parent_obj, self.root_obj)

    def test_load_from_xml(self):
        root = etree.Element('root')
        text = etree.Element('text')
        text.text = 'text'
        empty = etree.Element('empty')
        comment = etree.Comment('comment')
        root.append(comment)
        root.append(text)
        root.append(empty)
        text.attrib['attr'] = 'value'
        obj = self.cls()
        obj.load_from_xml(text)
        self.assertEqual(obj.text, 'text')
        self.assertEqual(obj.comment, 'comment')
        self.assertEqual(obj.attributes, {'attr': 'value'})

        text.text = 'Hello world'
        comment1 = etree.Comment('comment inside a tag')
        text.append(comment1)

        obj = self.cls()
        obj.load_from_xml(text)
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj.comment, 'comment\ncomment inside a tag')
        self.assertEqual(obj.attributes, {'attr': 'value'})

        obj = self.cls()
        obj.load_from_xml(empty)
        self.assertEqual(obj.text, '')
        self.assertEqual(obj.comment, None)

    def test_load_from_dict(self):
        dic = {'tag': {'_value': 'text',
                       '_comment': 'comment',
                       '_attrs':{
                            'attr': 'value'
                       }}
              }
        obj = self.cls()
        obj.load_from_dict(dic)
        self.assertEqual(obj.text, 'text')
        self.assertEqual(obj.cdata, False)
        self.assertEqual(obj.comment, 'comment')
        self.assertEqual(obj.attributes, {'attr': 'value'})

        obj = self.cls()
        obj.load_from_dict(dic, skip_extra=True)
        self.assertEqual(obj.text, 'text')
        self.assertEqual(obj.comment, None)
        self.assertEqual(obj.attributes, None)

        dic = {'tag': {'_value': 'text',
                       '_cdata': '',
                       '_comment': 'comment',
                       '_attrs':{
                            'attr': 'value'
                       }}
              }
        obj = self.cls()
        obj.load_from_dict(dic)
        self.assertEqual(obj.text, 'text')
        self.assertEqual(obj.cdata, True)
        self.assertEqual(obj.comment, 'comment')
        self.assertEqual(obj.attributes, {'attr': 'value'})

    def test_to_xml(self):
        obj = self.cls()
        obj.text = 'text'
        obj.comment = 'comment'
        obj.attributes = {'attr': 'value'}
        xml = obj.to_xml()
        self.assertTrue(xml.tag, 'tag')
        self.assertTrue(xml.text, 'text')
        self.assertTrue(xml.attrib, {'attr': 'value'})

        obj = self.cls()
        obj.text = etree.CDATA('<div>HTML</div>')
        xml = obj.to_xml()
        self.assertEqual(etree.tostring(xml),
                         b'<tag><![CDATA[<div>HTML</div>]]></tag>')

        obj = self.cls()
        obj.text = '<div>HTML</div>'
        xml = obj.to_xml()
        self.assertEqual(etree.tostring(xml),
                         b'<tag>&lt;div&gt;HTML&lt;/div&gt;</tag>')

        obj = self.cls()
        obj._is_empty = True
        obj.text = 'text'
        try:
            xml = obj.to_xml()
            assert 0
        except Exception as e:
            self.assertEqual(str(e),
                             'It\'s forbidden to have a value to an EMPTY tag')
        obj.text = None
        xml = obj.to_xml()
        self.assertEqual(xml.tag, 'tag')
        self.assertEqual(xml.text, None)
        self.assertEqual(xml.attrib, {})

    def test__get_html_attrs(self):
        obj = self.cls(self.root_obj)
        result = obj._get_html_attrs(rows=1)
        expected = [('name', "parent_tag:tag:_value"), ('rows', 1), ('class', 'tag')]
        self.assertEqual(result, expected)

        cls = type(
            'Cls', (InListMixin, TextElement, ),
            {
                'tagname': 'tag',
                'children_classes': [self.sub_cls],
                '_attribute_names': ['attr'],
            }
        )

        list_cls = type(
            'ListCls', (ListElement,),
            {
                'tagname': 'list_tag',
                '_children_class': cls,
                '_parent_cls': self.root_cls
            }
        )

        cls._parent_cls = list_cls

        root_obj = self.root_cls()
        self.root_cls.children_classes = [list_cls]
        list_obj = root_obj.add(list_cls.tagname)
        obj = list_obj.add(cls.tagname)
        for i in range(10):
            list_obj.insert(0, EmptyElement(parent_obj=list_obj))
        result = obj._get_html_attrs(rows=3)
        expected = [('name', "parent_tag:list_tag:10:tag:_value"),
                    ('rows', 3),
                    ('class', 'tag')]
        self.assertEqual(result, expected)

    def test_to_html(self):
        # No value
        obj = self.cls()
        html = obj._to_html()
        expected = (
            '<a class="btn-add btn-add-tag" data-elt-id="tag">Add tag</a>')
        self.assertEqual_(html, expected)

        expected = ('<div id="tag" class="xt-container-tag">'
                    '<label>tag</label>'
                    '<span class="btn-external-editor" '
                    'ng-click="externalEditor(this)"></span>'
                    '<a class="btn-add btn-add-tag hidden" '
                    'data-elt-id="tag">Add tag</a>'
                    '<a class="btn-delete" data-target="#tag" '
                    'title="Delete"></a>'
                    '<a data-comment-name="tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="1"></textarea>'
                    '</div>')

        html = obj.to_html()
        self.assertEqual_(html, expected)

        # With value
        obj.set_text('')
        html = obj._to_html()
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

        # Required
        obj._required = True
        html = obj._to_html()
        expected = ('<div id="tag" class="xt-container-tag">'
                    '<label>tag</label>'
                    '<span class="btn-external-editor" '
                    'ng-click="externalEditor(this)"></span>'
                    '<a data-comment-name="tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '<textarea class="form-control tag" name="tag:_value" rows="1">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

        # Multiline
        obj.text = 'line1\nline2'
        html = obj._to_html()
        expected = ('<div id="tag" class="xt-container-tag">'
                    '<label>tag</label>'
                    '<span class="btn-external-editor" '
                    'ng-click="externalEditor(this)"></span>'
                    '<a data-comment-name="tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '<textarea class="form-control tag" name="tag:_value" rows="2">'
                    'line1\nline2'
                    '</textarea>'
                    '</div>')
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

        # In list without value but required
        cls = type(
            'Cls', (InListMixin, TextElement, ),
            {
                'tagname': 'tag',
                'children_classes': [self.sub_cls],
                '_attribute_names': ['attr']
            }
        )
        parent_cls = type(
            'MyListElement', (ListElement, ),
            {
                'tagname': 'mytag',
                '_attribute_names': [],
                '_children_class': cls,
                '_parent_cls': self.root_cls
            }
        )
        self.root_cls.children_classes = [parent_cls]
        cls._parent_cls = parent_cls

        parent_obj = parent_cls(self.root_cls())
        obj = parent_obj.add(cls.tagname)
        obj.text = None
        obj._required = True

        html = obj._to_html()
        expected = (
            '<a class="btn-add btn-add-tag btn-list" '
            'data-elt-id="parent_tag:mytag:0:tag">New tag</a>'
            '<div id="parent_tag:mytag:0:tag" class="xt-container-tag">'
            '<label>tag</label>'
            '<span class="btn-external-editor" '
            'ng-click="externalEditor(this)"></span>'
            '<a class="btn-delete btn-list" '
            'data-target="#parent_tag:mytag:0:tag" title="Delete"></a>'
            '<a data-comment-name="parent_tag:mytag:0:tag:_comment" class="btn-comment"'
            ' title="Add comment"></a>'
            '<textarea class="form-control tag" name="parent_tag:mytag:0:tag:_value" rows="1">'
            '</textarea>'
            '</div>'
        )
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

        # Not required in a list
        obj._required = False
        html = obj.to_html()
        expected = (
            '<a class="btn-add btn-add-tag btn-list" '
            'data-elt-id="parent_tag:mytag:0:tag">New tag</a>'
            '<div id="parent_tag:mytag:0:tag" class="xt-container-tag">'
            '<label>tag</label>'
            '<span class="btn-external-editor" '
            'ng-click="externalEditor(this)"></span>'
            '<a class="btn-delete btn-list" '
            'data-target="#parent_tag:mytag:0:tag" title="Delete"></a>'
            '<a data-comment-name="parent_tag:mytag:0:tag:_comment" class="btn-comment"'
            ' title="Add comment"></a>'
            '<textarea class="form-control tag" name="parent_tag:mytag:0:tag:_value" rows="1">'
            '</textarea>'
            '</div>'
        )
        self.assertEqual_(html, expected)

        expected = (
            '<a class="btn-add btn-add-tag" '
            'data-elt-id="parent_tag:mytag:0:tag">'
            'Add tag</a>')
        html = obj._to_html()
        self.assertEqual_(html, expected)

    def test_to_html_readonly(self):
        obj = self.cls()
        obj.root.html_renderer = render.ReadonlyRender()
        html = obj._to_html()
        self.assertEqual(html, '')

        obj.set_text('')
        html = obj._to_html()
        expected = ('<div id="tag" class="xt-container-tag">'
                    '<label>tag</label>'
                    '<span class="btn-external-editor" '
                    'ng-click="externalEditor(this)"></span>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="1" readonly="readonly"></textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj._required = True
        html = obj._to_html()
        expected = ('<div id="tag" class="xt-container-tag">'
                    '<label>tag</label>'
                    '<span class="btn-external-editor" '
                    'ng-click="externalEditor(this)"></span>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="1" readonly="readonly">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj.text = 'line1\nline2'
        html = obj._to_html()
        expected = ('<div id="tag" class="xt-container-tag">'
                    '<label>tag</label>'
                    '<span class="btn-external-editor" '
                    'ng-click="externalEditor(this)"></span>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="2" readonly="readonly">'
                    'line1\nline2'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj.text = None
        obj._parent_obj = type(
            'MyListElement', (ListElement, ),
            {
                'tagname': 'mytag',
                '_attribute_names': [],
                '_choice_classes': [],
                '_children_class': self.cls
            }
        )(self.root_obj)
        html = obj._to_html()
        expected = ('<div id="tag" class="xt-container-tag">'
                    '<label>tag</label>'
                    '<span class="btn-external-editor" '
                    'ng-click="externalEditor(this)"></span>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="1" readonly="readonly">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)


class TestListElement(BaseTest):

    def setUp(self):
        self.sub_cls = type(
            'SubCls', (InListMixin, ContainerElement, ),
            {
                'tagname': 'subtag',
                '_attribute_names': ['attr'],
                'children_classes': []
            }
        )
        self.cls = type(
            'Cls', (ListElement,),
            {
                'tagname': 'tag',
                '_children_class': self.sub_cls
            }
        )
        self.root_cls = type(
            'Cls', (ContainerElement,),
            {
                'tagname': 'parent_tag',
                'children_classes': [self.cls]
            }
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls._parent_cls = self.cls

    def test_position(self):
        self.assertEqual(self.root_obj.position, None)

        obj = self.root_cls()
        sub1 = obj.add('subtag')
        sub2 = obj.add('subtag')
        self.assertEqual(sub1.position, 0)
        self.assertEqual(sub2.position, 1)

    def test__get_creatable_class_by_tagnames(self):
        res = self.cls._get_creatable_class_by_tagnames()
        expected = {
            'subtag': self.sub_cls,
            'tag': self.cls,
        }
        self.assertEqual(res, expected)

    def test__get_creatable_subclass_by_tagnames(self):
        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {
            'subtag': self.sub_cls,
        }
        self.assertEqual(res, expected)

    def test_get_child_class(self):
        self.assertEqual(self.cls.get_child_class('subtag'), self.sub_cls)
        self.assertEqual(self.cls.get_child_class('tag'), None)

    def test__get_value_from_parent(self):
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)
        list_obj = self.cls(self.root_obj)
        obj = list_obj.add(self.sub_cls.tagname)
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), [obj])

    def test_children(self):
        obj = self.root_cls()
        sub1 = obj.add('subtag')
        sub2 = obj.add('subtag')
        children = list(obj.children)
        self.assertEqual(children, [sub1, sub2])

    def test_is_addable(self):
        obj = self.root_obj.add(self.cls.tagname)
        # Can't add same object as child
        self.assertEqual(obj.is_addable(self.cls.tagname), False)
        self.assertEqual(obj.is_addable('subtag'), True)
        self.assertEqual(obj.is_addable('test'), False)
        # Addable even we already have element defined
        obj.add('subtag')
        self.assertEqual(obj.is_addable('subtag'), True)

    def test__add(self):
        try:
            obj1 = self.cls._create('tag', self.root_obj, 'my value')
            assert(False)
        except Exception as e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj1 = self.cls._create('tag', self.root_obj)
        self.assertTrue(obj1.tagname, 'tag')
        self.assertEqual(obj1._parent_obj, self.root_obj)
        self.assertEqual(obj1.root, self.root_obj)
        self.assertTrue(isinstance(obj1, ListElement))
        self.assertEqual(self.root_obj['tag'].root, self.root_obj)

        # Since the object already exists it just return it!
        obj2 = self.cls._create('tag', self.root_obj)
        self.assertEqual(obj1, obj2)

        try:
            self.cls._create('unexisting', self.root_obj)
            assert(False)
        except Exception as e:
            self.assertEqual(str(e), 'Unsupported tagname unexisting')

    def test_add_list_of_list(self):
        dtd_str = u'''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (subtext+)>
        <!ELEMENT subtext (#PCDATA)>
        '''
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic['texts']()
        text = obj.add('text')
        subtext = text.add('subtext', 'value')
        self.assertEqual(subtext.text, 'value')

        # We can add another text
        obj.add('text')

        # List already exists, it just returns it
        list_obj = obj.add(text._parent_cls.tagname)
        self.assertEqual(text._parent_obj, list_obj)

        l = list_obj.add(text._parent_cls.tagname)
        self.assertEqual(list_obj, l)

    def test_delete(self):
        list_obj = self.root_obj.add(self.cls.tagname)
        obj = list_obj.add('subtag')
        self.assertEqual(len(list_obj), 1)

        obj.delete()
        self.assertEqual(len(list_obj), 0)

        self.assertEqual(self.root_obj['tag'], list_obj)
        self.assertEqual(self.root_obj['subtag'], list_obj)
        list_obj.delete()
        self.assertEqual(self.root_obj.get('tag'), None)
        self.assertEqual(self.root_obj.get('subtag'), None)

    def test_to_xml(self):
        obj = self.root_cls().add(self.cls.tagname)
        lis = obj.to_xml()
        self.assertEqual(lis, [])

        subobj = self.sub_cls()
        subobj.comment = 'comment'
        subobj.attributes = {'attr': 'value'}

        obj.append(subobj)
        lis = obj.to_xml()
        self.assertEqual(len(lis), 2)
        self.assertEqual(lis[0].text, 'comment')
        self.assertEqual(lis[1].tag, 'subtag')

        obj = self.root_cls().add(self.cls.tagname)
        obj._required = True
        lis = obj.to_xml()
        # Empty required with only one element, xml is created!
        self.assertEqual(len(lis), 1)
        self.assertEqual(lis[0].tag, 'subtag')

    def test__get_html_add_button(self):
        obj = self.cls(self.root_obj)
        html = obj._get_html_add_button(0)
        expected = ('<a class="btn-add btn-add-subtag btn-list" '
                    'data-elt-id="parent_tag:tag:0:subtag">New subtag</a>')
        self.assertEqual(html, expected)

        html = obj._get_html_add_button(10)
        expected = ('<a class="btn-add btn-add-subtag btn-list" '
                    'data-elt-id="parent_tag:tag:10:subtag">New subtag</a>')
        self.assertEqual(html, expected)

    def test_to_html(self):
        obj = self.root_obj.add(self.cls.tagname)
        html = obj._to_html()
        expected = ('<div class="list-container">'
                    '<a class="btn-add btn-add-subtag btn-list" '
                    'data-elt-id="parent_tag:tag:0:subtag">New subtag</a>'
                    '</div>')
        self.assertEqual_(html, expected)

        obj._required = True
        html = obj._to_html()
        expected = ('<div class="list-container">'
                    '<a class="btn-add btn-add-subtag btn-list" '
                    'data-elt-id="parent_tag:tag:0:subtag">New subtag</a>'
                    '<div class="panel panel-default subtag" '
                    'id="parent_tag:tag:0:subtag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-parent_tag\:tag\:0\:subtag">subtag'
                    '<a class="btn-delete btn-list" '
                    'data-target="#parent_tag:tag:0:subtag" title="Delete"></a>'
                    '<a data-comment-name="parent_tag:tag:0:subtag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-parent_tag:tag:0:subtag">'
                    '</div></div>'
                    '<a class="btn-add btn-add-subtag btn-list" '
                    'data-elt-id="parent_tag:tag:1:subtag">New subtag</a>'
                    '</div>')
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

        obj.add('subtag')
        for i in range(10):
            obj.insert(0, EmptyElement(parent_obj=obj))
        html = obj._to_html()
        expected = ('<div class="list-container">'
                    '<a class="btn-add btn-add-subtag btn-list" '
                    'data-elt-id="parent_tag:tag:10:subtag">New subtag</a>'
                    '<div class="panel panel-default subtag" id="parent_tag:tag:10:subtag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-parent_tag\:tag\:10\:subtag">subtag'
                    '<a class="btn-delete btn-list" '
                    'data-target="#parent_tag:tag:10:subtag" title="Delete"></a>'
                    '<a data-comment-name="parent_tag:tag:10:subtag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-parent_tag:tag:10:subtag">'
                    '</div></div>'
                    '<a class="btn-add btn-add-subtag btn-list" '
                    'data-elt-id="parent_tag:tag:11:subtag">New subtag</a>'
                    '</div>')
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

    def test_to_html_readonly(self):
        obj = self.root_obj.add(self.cls.tagname)
        obj.root.html_renderer = render.ReadonlyRender()
        html = obj._to_html()
        expected = '<div class="list-container"></div>'
        self.assertEqual(html, expected)

        obj._required = True
        html = obj._to_html()
        expected = ('<div class="list-container">'
                    '<div class="panel panel-default subtag" '
                    'id="parent_tag:tag:0:subtag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-parent_tag\:tag\:0\:subtag">subtag'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-parent_tag:tag:0:subtag">'
                    '</div></div>'
                    '</div>')
        self.assertEqual_(html, expected)

        obj.add('subtag')
        for i in range(10):
            obj.insert(0, EmptyElement(parent_obj=obj))

        html = obj._to_html()
        expected = ('<div class="list-container">'
                    '<div class="panel panel-default subtag" id="parent_tag:tag:10:subtag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-parent_tag\:tag\:10\:subtag">subtag'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-parent_tag:tag:10:subtag">'
                    '</div></div>'
                    '</div>')
        self.assertEqual_(html, expected)

    def test_to_jstree_dict(self):
        obj = self.root_obj.add(self.cls.tagname)
        result = obj.to_jstree_dict()
        self.assertEqual(result, [])

        obj._required = True
        result = obj.to_jstree_dict()
        expected = [{
            'li_attr': {
                'class': 'tree_parent_tag:tag subtag',
            },
            'a_attr': {
                'id': 'tree_parent_tag:tag:0:subtag'},
            'children': [],
            'text': 'subtag',
            'state': {'opened': True},
        }]
        self.assertEqual(result, expected)

    def test_walk_list(self):
        sub_sub_cls = type(
            'SubSubCls', (TextElement, ),
            {
                'tagname': 'subsubtag',
                'children_classes': []
            }
        )
        self.sub_cls.children_classes = [sub_sub_cls]
        obj = self.cls(self.root_obj)
        self.root_obj['subtag'] = obj
        sub1 = self.sub_cls()
        sub2 = self.sub_cls()
        subsub1 = sub_sub_cls()
        sub1['subsubtag'] = subsub1
        obj.append(sub1)
        obj.append(sub2)

        lis = [e for e in self.root_obj.walk()]
        self.assertEqual(lis, [sub1, subsub1, sub2])

    def test_get_or_add(self):
        obj = self.cls(self.root_obj)
        try:
            obj.get_or_add('unexisting')
            assert(False)
        except Exception as e:
            self.assertEqual(str(e), 'Parameter index is required')

        subobj = obj.get_or_add('subtag', index=1)
        self.assertEqual(len(obj), 2)

        subobj1 = obj.get_or_add('subtag', index=1)
        self.assertEqual(subobj, subobj1)

        obj = self.cls(self.root_obj)
        subobj = obj.get_or_add('subtag', index=0)
        self.assertEqual(len(obj), 1)

        subobj1 = obj.get_or_add('subtag', index=0)
        self.assertEqual(subobj, subobj1)


class TestChoiceListElement(BaseTest):

    def setUp(self):
        self.sub_cls1 = type(
            'SubCls1', (InListMixin, ContainerElement, ),
            {
                'tagname': 'subtag1',
                '_attribute_names': ['attr'],
                'children_classes': []
            }
        )
        self.sub_cls2 = type(
            'SubCls2', (InListMixin, ContainerElement, ),
            {
                'tagname': 'subtag2',
                '_attribute_names': ['attr'],
                'children_classes': []
            }
        )
        self.cls = type(
            'Cls', (ChoiceListElement,),
            {
                'tagname': 'tag',
                '_choice_classes': [self.sub_cls1, self.sub_cls2]
            }
        )
        self.root_cls = type(
            'Cls', (ContainerElement,),
            {
                'tagname': 'parent_tag',
                'children_classes': [self.cls]
            }
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls1._parent_cls = self.cls
        self.sub_cls2._parent_cls = self.cls

    def test_children(self):
        obj = self.root_cls()
        children = list(obj.children)
        self.assertEqual(children, [])
        sub1 = obj.add('subtag1')
        sub2 = obj.add('subtag2')
        children = list(obj.children)
        self.assertEqual(children, [sub1, sub2])

    def test_delete(self):
        root_obj = self.root_cls()
        list_obj = self.cls(root_obj)
        obj = self.sub_cls1(list_obj, parent=root_obj)
        list_obj.append(obj)

        self.assertEqual(len(list_obj), 1)
        self.assertEqual(root_obj['tag'], list_obj)

        obj.delete()
        self.assertEqual(len(list_obj), 0)
        self.assertEqual(root_obj['tag'], list_obj)

        list_obj.delete()
        self.assertEqual(root_obj.get('tag'), None)

    def test__get_value_from_parent_multiple(self):
        root_obj = self.root_cls()
        list_obj = self.cls(root_obj)
        obj = self.sub_cls1(list_obj, parent=root_obj)
        list_obj.append(obj)
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)
        self.root_obj['subtag'] = list_obj
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)
        self.root_obj['tag'] = list_obj
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), [obj])

    def test_to_xml(self):
        obj = self.root_cls().add(self.cls.tagname)
        obj._required = True
        lis = obj.to_xml()
        self.assertEqual(lis, [])

    def test__get_html_add_button_multiple(self):
        obj = self.cls()
        html = obj._get_html_add_button(0)
        expected = ('<select class="btn-add btn-list">'
                    '<option>New subtag1/subtag2</option>'
                    '<option class="xt-option-subtag1" '
                    'value="tag:0:subtag1">subtag1</option>'
                    '<option class="xt-option-subtag2" '
                    'value="tag:0:subtag2">subtag2</option>'
                    '</select>')
        self.assertEqual(html, expected)

    def test_walk(self):
        root_obj = self.root_cls()
        parent_obj = self.cls()
        obj1 = self.sub_cls1(parent_obj=parent_obj, parent=root_obj)
        obj2 = self.sub_cls2(parent_obj=parent_obj, parent=root_obj)

        parent_obj.extend([obj1, obj2])
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj1, obj2])

        sub_sub_cls = type('SubSubCls', (TextElement, ),
                       {'tagname': 'subsub',
                        'children_classes': []})
        self.sub_cls1.children_classes = [sub_sub_cls]
        subsub1 = sub_sub_cls()
        obj1['subsub'] = subsub1
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj1, subsub1, obj2])

    def test_to_html(self):
        obj = self.root_obj.add(self.cls.tagname)
        html = obj._to_html()
        expected = (
            '<div class="list-container">'
            '<select class="btn-add btn-list">'
            '<option>New subtag1/subtag2</option>'
            '<option class="xt-option-subtag1" '
            'value="parent_tag:tag:0:subtag1">subtag1</option>'
            '<option class="xt-option-subtag2" '
            'value="parent_tag:tag:0:subtag2">subtag2</option>'
            '</select>'
            '</div>'
        )
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

        # Required will not change anything since we don't know which subtag
        # should be added
        obj._required = True
        html = obj._to_html()
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

        obj.add('subtag1')
        html = obj._to_html()
        expected = (
            '<div class="list-container">'
            '<select class="btn-add btn-list">'
            '<option>New subtag1/subtag2</option>'
            '<option class="xt-option-subtag1" '
            'value="parent_tag:tag:0:subtag1">subtag1</option>'
            '<option class="xt-option-subtag2" '
            'value="parent_tag:tag:0:subtag2">subtag2</option>'
            '</select>'
            '<div class="panel panel-default subtag1" '
            'id="parent_tag:tag:0:subtag1">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" '
            'href="#collapse-parent_tag\:tag\:0\:subtag1">subtag1'
            '<a class="btn-delete btn-list" '
            'data-target="#parent_tag:tag:0:subtag1" title="Delete"/>'
            '<a data-comment-name="parent_tag:tag:0:subtag1:_comment" '
            'class="btn-comment" title="Add comment"/></span>'
            '</div>'
            '<div class="panel-body panel-collapse collapse in" '
            'id="collapse-parent_tag:tag:0:subtag1"/>'
            '</div>'
            '<select class="btn-add btn-list">'
            '<option>New subtag1/subtag2</option>'
            '<option class="xt-option-subtag1" '
            'value="parent_tag:tag:1:subtag1">subtag1</option>'
            '<option class="xt-option-subtag2" '
            'value="parent_tag:tag:1:subtag2">subtag2</option>'
            '</select>'
            '</div>'

        )
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)

        for i in range(10):
            obj.insert(0, EmptyElement(parent_obj=obj))
        html = obj._to_html()
        expected = (
            '<div class="list-container">'
            '<select class="btn-add btn-list">'
            '<option>New subtag1/subtag2</option>'
            '<option class="xt-option-subtag1" '
            'value="parent_tag:tag:10:subtag1">subtag1</option>'
            '<option class="xt-option-subtag2" '
            'value="parent_tag:tag:10:subtag2">subtag2</option>'
            '</select>'
            '<div class="panel panel-default subtag1" '
            'id="parent_tag:tag:10:subtag1">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" '
            'href="#collapse-parent_tag\:tag\:10\:subtag1">subtag1'
            '<a class="btn-delete btn-list" '
            'data-target="#parent_tag:tag:10:subtag1" title="Delete"/>'
            '<a data-comment-name="parent_tag:tag:10:subtag1:_comment" '
            'class="btn-comment" title="Add comment"/></span>'
            '</div>'
            '<div class="panel-body panel-collapse collapse in" '
            'id="collapse-parent_tag:tag:10:subtag1"/>'
            '</div>'
            '<select class="btn-add btn-list">'
            '<option>New subtag1/subtag2</option>'
            '<option class="xt-option-subtag1" '
            'value="parent_tag:tag:11:subtag1">subtag1</option>'
            '<option class="xt-option-subtag2" '
            'value="parent_tag:tag:11:subtag2">subtag2</option>'
            '</select>'
            '</div>'
        )
        self.assertEqual_(html, expected)

        html = obj.to_html()
        self.assertEqual_(html, expected)


class TestChoiceElement(BaseTest):

    def setUp(self):
        self.sub_cls1 = type(
            'SubCls', (InChoiceMixin, ContainerElement, ),
            {
                'tagname': 'subtag1',
                'children_classes': []
            }
        )
        self.sub_cls2 = type(
            'SubCls', (InChoiceMixin, ContainerElement, ),
            {
                'tagname': 'subtag2',
                'children_classes': []
            }
        )
        self.cls = type(
            'Cls', (ChoiceElement,),
            {
                'tagname': 'tag',
                'children_classes': [],
                '_choice_classes': [self.sub_cls1, self.sub_cls2]
            }
        )
        self.root_cls = type(
            'ParentCls', (ContainerElement, ),
            {
                'tagname': 'root_tag',
                'children_classes': [self.cls]
            }
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls1._parent_cls = self.cls
        self.sub_cls2._parent_cls = self.cls

    def test_position(self):
        self.assertEqual(self.root_obj.position, None)
        obj1 = self.sub_cls1()
        obj2 = self.sub_cls2()

        self.assertEqual(obj1.position, None)
        self.assertEqual(obj2.position, None)

    def test__get_creatable_class_by_tagnames(self):
        res = self.cls._get_creatable_class_by_tagnames()
        expected = {
            'subtag1': self.sub_cls1,
            'subtag2': self.sub_cls2,
            'tag': self.cls,
        }
        self.assertEqual(res, expected)

    def test__get_creatable_subclass_by_tagnames(self):
        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {
            'subtag1': self.sub_cls1,
            'subtag2': self.sub_cls2,
        }
        self.assertEqual(res, expected)

    def test_get_child_class(self):
        self.assertEqual(self.cls.get_child_class('subtag1'), self.sub_cls1)
        self.assertEqual(self.cls.get_child_class('subtag2'), self.sub_cls2)

    def test__get_value_from_parent(self):
        obj1 = self.sub_cls1()
        obj2 = self.sub_cls2()
        self.assertTrue(obj1 != obj2)
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)
        obj1 = self.root_obj.add('subtag1')
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), obj1)

    def test__get_sub_value(self):
        obj = self.sub_cls1()
        result = self.cls._get_sub_value(self.root_obj)
        self.assertFalse(result)
        self.cls._required = True
        result = self.cls._get_sub_value(self.root_obj)
        self.assertTrue(result)
        # The created object is a ChoiceElement
        self.assertTrue(isinstance(result, self.cls))
        obj = self.root_obj.add('subtag1')
        self.assertEqual(self.cls._get_sub_value(self.root_obj), obj)

    def test_children(self):
        obj = self.root_cls()
        children = list(obj.children)
        self.assertEqual(children, [])
        sub1 = obj.add('subtag1')
        children = list(obj.children)
        self.assertEqual(children, [sub1])

    def test_is_addable(self):
        obj = self.cls()
        self.assertEqual(obj.is_addable('test'), False)

    def test_add(self):
        root_cls = type('ParentCls', (ContainerElement, ),
                          {'tagname': 'parent',
                           'children_classes': [self.cls]})
        root_obj = root_cls()
        obj = self.cls(root_obj)

        try:
            obj.add('test')
        except Exception as e:
            self.assertEqual(str(e), 'Invalid child test')

        obj1 = obj.add('subtag1')
        self.assertEqual(obj1._parent_obj, obj)
        self.assertEqual(obj1.parent, root_obj)
        self.assertEqual(root_obj['subtag1'], obj1)
        self.assertEqual(root_obj['tag'], obj)

        root_obj = root_cls()
        choice_obj = root_obj.add('tag')
        choice_obj.add('subtag1')

        choice_obj1 = root_obj.add('tag')
        # It's the same object when we add we just get it if defined
        self.assertEqual(choice_obj, choice_obj1)

        try:
            choice_obj.add('subtag1')
            assert(False)
        except Exception as e:
            self.assertEqual(str(e),
                             'subtag1 is already defined')

        try:
            choice_obj.add('subtag2')
            assert(False)
        except Exception as e:
            self.assertEqual(str(e),
                             'subtag1 is defined so you can\'t add subtag2')

        self.cls._choice_classes = [
            type('Cls', (InChoiceMixin, TextElement, ),
                 {
                     'tagname': 'subtag',
                     'children_classes': [],
                     '_parent_cls': self.cls
                 })]

        root_obj = root_cls()
        choice_obj2 = root_obj.add('tag')
        obj2 = choice_obj2.add('subtag', 'my value')
        self.assertEqual(obj2.text, 'my value')
        self.assertEqual(obj2._parent_obj, choice_obj2)
        self.assertEqual(obj2.parent, root_obj)

    def test__add(self):
        try:
            obj1 = self.cls._create('tag', self.root_obj, 'my value')
            assert(False)
        except Exception as e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj1 = self.cls._create('tag', self.root_obj)
        self.assertEqual(obj1.tagname, 'tag')
        self.assertEqual(obj1._parent_obj, self.root_obj)
        self.assertTrue(isinstance(obj1, ChoiceElement))
        self.assertEqual(self.root_obj['tag'], obj1)

    def test_delete(self):
        obj = self.cls(self.root_obj)
        obj1 = obj.add('subtag1')
        self.assertEqual(self.root_obj[self.cls.tagname], obj)
        self.assertEqual(self.root_obj.get(self.sub_cls1.tagname), obj1)
        self.assertEqual(obj._value, obj1)

        obj1.delete()
        self.assertEqual(self.root_obj.get(self.cls.tagname), None)
        self.assertEqual(self.root_obj.get(self.sub_cls1.tagname), None)

        obj = self.cls(self.root_obj)
        obj1 = obj.add('subtag1')
        self.assertEqual(self.root_obj[self.cls.tagname], obj)
        self.assertEqual(self.root_obj.get(self.sub_cls1.tagname), obj1)
        self.assertEqual(obj._value, obj1)

        obj.delete()
        self.assertFalse(self.cls.tagname in self.root_obj)
        self.assertFalse('subtag1' in self.root_obj)

    def test__get_html_add_button(self):
        obj = self.cls(self.root_obj)
        html = obj._get_html_add_button()
        expected = ('<select class="btn-add">'
                    '<option>New subtag1/subtag2</option>'
                    '<option class="xt-option-subtag1" '
                    'value="root_tag:subtag1">subtag1</option>'
                    '<option class="xt-option-subtag2" '
                    'value="root_tag:subtag2">subtag2</option>'
                    '</select>')
        self.assertEqual(html, expected)

    def test_to_jstree_dict(self):
        obj = self.cls(self.root_obj)
        res = obj.to_jstree_dict()
        self.assertEqual(res, None)

        obj.add('subtag1')
        res = obj.to_jstree_dict()
        expected = {
            'text': 'subtag1',
            'state': {'opened': True},
            'a_attr': {'id': 'tree_root_tag:subtag1'},
            'children': [],
            'li_attr': {'class': 'tree_root_tag:subtag1 subtag1'}
        }
        self.assertEqual(res, expected)

    def test_to_html(self):
        obj = self.cls(self.root_obj)
        expected = (
            '<select class="btn-add">'
            '<option>New subtag1/subtag2</option>'
            '<option class="xt-option-subtag1" '
            'value="root_tag:subtag1">subtag1</option>'
            '<option class="xt-option-subtag2" '
            'value="root_tag:subtag2">subtag2</option>'
            '</select>'
        )
        html = obj._to_html()
        self.assertEqual_(html, expected)

        try:
            obj.to_html()
            assert(False)
        except NotImplementedError:
            pass

        obj._required = True
        html = obj._to_html()
        self.assertEqual_(html, expected)

        obj.add('subtag1')
        expected = (
            '<div class="panel panel-default subtag1" id="root_tag:subtag1">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" '
            'href="#collapse-root_tag\:subtag1">subtag1'
            '<select class="btn-add hidden">'
            '<option>New subtag1/subtag2</option>'
            '<option class="xt-option-subtag1" '
            'value="root_tag:subtag1">subtag1</option>'
            '<option class="xt-option-subtag2" '
            'value="root_tag:subtag2">subtag2</option>'
            '</select>'
            '<a class="btn-delete" data-target="#root_tag:subtag1" '
            'title="Delete"/>'
            '<a data-comment-name="root_tag:subtag1:_comment" '
            'class="btn-comment" title="Add comment"/></span>'
            '</div>'
            '<div class="panel-body panel-collapse collapse in" '
            'id="collapse-root_tag:subtag1"/>'
            '</div>'
        )
        html = obj._to_html()
        self.assertEqual_(html, expected)


class TestFunctions(BaseTest):

    def test_update_eol(self):
        res = update_eol('Hello\r\n')
        self.assertEqual(res, 'Hello\n')

        res = update_eol('Hello\n')
        self.assertEqual(res, 'Hello\n')

        elements.EOL = '\r\n'
        res = update_eol('Hello\r\n')
        self.assertEqual(res, 'Hello\r\n')

        res = update_eol('Hello\n')
        self.assertEqual(res, 'Hello\r\n')

        res = update_eol('Hello\r')
        self.assertEqual(res, 'Hello\r\n')

    def test_get_previous_js_selectors(self):
        dtd_str = u'''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts'
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str)
        lis = obj.get_previous_js_selectors()
        self.assertEqual(lis, [])

        lis = obj.get_previous_js_selectors()
        self.assertEqual(lis, [])

        str_id = 'texts:list__list:0:list:text'
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str)
        lis = obj.get_previous_js_selectors()
        expected = [('inside', escape_attr('#tree_texts:list__list:0:list'))]
        self.assertEqual(lis, expected)

        str_id = 'texts:list__list:0:list'
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str)
        lis = obj.get_previous_js_selectors()
        expected = [
            ('after', escape_attr('.tree_texts:tag1') + ':last'),
            ('inside', escape_attr('#tree_texts'))]
        self.assertEqual(lis, expected)

        str_id = 'texts:list__list:1:list'
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str)
        lis = obj.get_previous_js_selectors()
        expected = [('after', escape_attr('#tree_texts:list__list:0:list'))]
        self.assertEqual(lis, expected)

        str_id = 'texts:tag2'
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str)
        lis = obj.get_previous_js_selectors()
        expected = [('after', escape_attr('.tree_texts:list__list') + ':last'),
                    ('after', escape_attr('.tree_texts:tag1') + ':last'),
                    ('inside', escape_attr('#tree_texts'))]
        self.assertEqual(lis, expected)
