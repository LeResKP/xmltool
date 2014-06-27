#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import os.path
from xmltool import utils, dtd_parser
from xmltool.elements import (
    Element,
    ListElement,
    TextElement,
    ChoiceElement,
    get_obj_from_str_id,
)
from xmltool import render
import xmltool.elements as elements
from test_dtd_parser import (
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


class TestElement(TestCase):

    def setUp(self):
        self.sub_cls = type('SubCls', (Element,),
                            {'tagname': 'subtag',
                             'children_classes': []})
        self.cls = type('Cls', (Element, ), {'tagname': 'tag',
                                             'children_classes': [self.sub_cls]})

    def test_prefixes_no_cache(self):
        obj = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': []})()
        parent_obj = type('Cls', (Element, ),
                          {'tagname': 'ptag',
                           'children_classes': [obj.__class__]})()
        self.assertEqual(obj.prefixes_no_cache, ['tag'])
        self.assertEqual(parent_obj.prefixes_no_cache, ['ptag'])

        obj.parent = parent_obj
        self.assertEqual(obj.prefixes_no_cache, ['ptag', 'tag'])

    def test_prefixes(self):
        obj = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': []})()
        parent_obj = type('Cls', (Element, ),
                          {'tagname': 'ptag',
                           'children_classes': [obj.__class__]})()
        self.assertEqual(obj.prefixes, ['tag'])
        self.assertEqual(parent_obj.prefixes, ['ptag'])

        # The prefixes are in the cache
        obj.parent = parent_obj
        self.assertEqual(obj.prefixes, ['tag'])
        self.assertEqual(obj._cache_prefixes, ['tag'])

        obj._cache_prefixes = None
        self.assertEqual(obj.prefixes, ['ptag', 'tag'])

    def test__get_allowed_tagnames(self):
        self.assertEqual(self.cls._get_allowed_tagnames(), ['tag'])

    def test_get_child_class(self):
        self.assertEqual(self.cls.get_child_class('subtag'), self.sub_cls)
        self.assertEqual(self.cls.get_child_class('unexisting'), None)

    def test__get_value_from_parent(self):
        obj = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': []})()
        parent_obj = type('Cls', (Element, ),
                          {'tagname': 'tag',
                           'children_classes': [obj.__class__]})()
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), None)
        parent_obj['tag'] = obj
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj)

    def test__get_sub_value(self):
        obj = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': []})()
        parent_obj = type('Cls', (Element, ),
                          {'tagname': 'tag',
                           'children_classes': [obj.__class__]})()
        result = self.cls._get_sub_value(parent_obj)
        self.assertFalse(result)
        self.cls._required = True
        result = self.cls._get_sub_value(parent_obj)
        self.assertTrue(result)
        self.assertTrue(result != obj)
        parent_obj['tag'] = obj
        self.assertEqual(self.cls._get_sub_value(parent_obj), obj)

    def test__has_value(self):
        obj = self.cls()
        self.assertFalse(obj._has_value())
        cls = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': []})
        obj['subtag'] = cls()
        self.assertTrue(obj._has_value())

    def test__get_prefixes(self):
        result = self.cls._get_prefixes([], None)
        self.assertEqual(result, ['tag'])
        result = self.cls._get_prefixes(['prefix'], None)
        self.assertEqual(result, ['prefix', 'tag'])
        result = self.cls._get_prefixes(['prefix'], 1)
        self.assertEqual(result, ['prefix', '1', 'tag'])
        result = self.cls._get_prefixes(['prefix'], 1, 'name')
        self.assertEqual(result, ['prefix', '1', 'tag', 'name'])

    def test__get_str_prefix(self):
        result = self.cls._get_str_prefix([], None)
        self.assertEqual(result, 'tag')
        result = self.cls._get_str_prefix(['prefix'], None)
        self.assertEqual(result, 'prefix:tag')
        result = self.cls._get_str_prefix(['prefix'], 1)
        self.assertEqual(result, 'prefix:1:tag')
        result = self.cls._get_str_prefix(['prefix'], 1, 'name')
        self.assertEqual(result, 'prefix:1:tag:name')

    def test_root(self):
        parent_obj = type('Cls', (Element, ),
                          {'tagname': 'tag',
                           'children_classes': []})()
        self.assertEqual(parent_obj.root, parent_obj)
        obj = self.cls._create('tagname', parent_obj)
        self.assertEqual(obj.root, parent_obj)

    def test__add(self):
        parent_obj = type('Cls', (Element, ),
                          {'tagname': 'tag',
                           'children_classes': []})()
        try:
            obj = self.cls._create('tagname', parent_obj, 'my value')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj = self.cls._create('tagname', parent_obj)
        self.assertEqual(obj.parent, parent_obj)
        self.assertEqual(obj.root, parent_obj)
        self.assertTrue(isinstance(obj, Element))
        self.assertEqual(parent_obj['tagname'], obj)

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
        parent_obj = FakeClass()
        obj = self.cls(parent_obj)
        newobj = obj.add('subtag')
        self.assertTrue(newobj)
        try:
            obj.add('unexisting')
        except Exception, e:
            self.assertEqual(str(e), 'Invalid child unexisting')

        parent_obj = FakeClass()
        obj = self.cls(parent_obj)
        try:
            newobj = obj.add('subtag', 'my value')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

    def test_add_attribute(self):
        obj = self.cls()
        obj._attribute_names = ['attr1', 'attr2']
        obj.add_attribute('attr1', 'value1')
        self.assertEqual(obj._attributes, {'attr1': 'value1'})
        obj.add_attribute('attr2', 'value2')
        self.assertEqual(obj._attributes, {'attr1': 'value1',
                                           'attr2': 'value2'})
        obj.add_attribute('attr2', 'newvalue2')
        self.assertEqual(obj._attributes, {'attr1': 'value1',
                                           'attr2': 'newvalue2'})

        try:
            obj.add_attribute('unexisting', 'newvalue2')
        except Exception, e:
            self.assertEqual(str(e), 'Invalid attribute name: unexisting')

    def test__load_attributes_from_xml(self):
        obj = self.cls()
        obj._attribute_names = ['attr']
        xml = etree.Element('test')
        xml.attrib['attr'] = 'value'
        obj._load_attributes_from_xml(xml)
        self.assertEqual(obj._attributes, {'attr': 'value'})

    def test__load_attributes_from_dict(self):
        obj = self.cls()
        obj._attribute_names = ['attr']
        obj._load_attributes_from_dict({})
        self.assertEqual(obj._attributes, None)
        obj._load_attributes_from_dict({'key': 'value'})
        self.assertEqual(obj._attributes, None)

        dic = {'_attrs': {'attr': 'value'}}
        obj._load_attributes_from_dict(dic)
        self.assertEqual(obj._attributes, {'attr': 'value'})
        self.assertEqual(dic, {})

        dic = {'_attrs': {'unexisting': 'value'}}
        try:
            obj._load_attributes_from_dict(dic)
        except Exception, e:
            self.assertEqual(str(e), 'Invalid attribute name: unexisting')

    def test__attributes_to_xml(self):
        xml = etree.Element('test')
        obj = self.cls()
        obj._attribute_names = ['attr']
        obj._attributes_to_xml(xml)
        self.assertEqual(xml.attrib, {})
        dic = {'attr': 'value'}
        obj._attributes = dic
        obj._attributes_to_xml(xml)
        self.assertEqual(xml.attrib, dic)

    def test__attributes_to_html(self):
        obj = self.cls()
        obj._attribute_names = ['attr']
        dic = {'attr': 'value'}
        html = obj._attributes_to_html(['prefix'], 1)
        self.assertEqual(html, '')
        obj._attributes = dic
        html = obj._attributes_to_html(['prefix'], 1)
        expected = ('<input value="value" name="prefix:1:tag:_attrs:attr" '
                    'id="prefix:1:tag:_attrs:attr" class="_attrs" />')
        self.assertEqual(html, expected)

    def test__load_comment_from_xml(self):
        obj = self.cls()
        xml = etree.Element('test')
        self.assertEqual(obj._comment, None)
        obj._load_comment_from_xml(xml)
        self.assertEqual(obj._comment, None)

        for i in range(5):
            if i == 2:
                elt = etree.Element('sub')
            else:
                elt = etree.Comment('comment %i' % i)
            xml.append(elt)
        obj._load_comment_from_xml(xml.getchildren()[2])
        expected = 'comment 0\ncomment 1\ncomment 3\ncomment 4'
        self.assertEqual(obj._comment, expected)

        obj = self.cls()
        xml = etree.Element('test')
        for i in range(3):
            elt = etree.Element('sub')
            xml.append(elt)
        obj._load_comment_from_xml(xml.getchildren()[2])
        self.assertEqual(obj._comment, None)

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
        self.assertEqual(obj._comment, expected)

    def test__load_comment_from_dict(self):
        obj = self.cls()
        obj._load_comment_from_dict({})
        self.assertEqual(obj._comment, None)
        dic = {'_comment': 'my comment'}
        obj._load_comment_from_dict(dic)
        self.assertEqual(obj._comment, 'my comment')

    def test__comment_to_xml(self):
        xml = etree.Element('test')
        obj = self.cls()
        obj._comment_to_xml(xml)
        self.assertEqual(xml.getprevious(), None)

        obj._comment = 'my comment'
        obj._comment_to_xml(xml)
        elt = xml.getprevious()
        self.assertEqual(elt.getprevious(), None)
        self.assertEqual(elt.text, 'my comment')

    def test__comment_to_html(self):
        obj = self.cls()
        html = obj._comment_to_html(['prefix'], None)
        expected = ('<a data-comment-name="prefix:tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>')
        self.assertEqual(html, expected)

        obj._comment = 'my comment'
        html = obj._comment_to_html(['prefix'], None)
        expected = ('<a data-comment-name="prefix:tag:_comment" '
                    'class="btn-comment has-comment" title="my comment"></a>'
                    '<textarea class="_comment" name="prefix:tag:_comment">'
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
        self.assertEqual(obj._comment, 'comment')
        self.assertEqual(obj._attributes, {'attr': 'value'})

    def test_load_from_xml(self):
        xml = etree.Element('test')
        xml.append(etree.Element('prev'))
        elt = etree.Element('element')
        elt.attrib['attr'] = 'value'
        xml.append(elt)
        xml.append(etree.Comment('comment'))

        sub_cls1 = type('SubClsPrev', (Element,), {'tagname': 'prev',
                                                   'children_classes': []})
        sub_cls2 = type('SubClsElement', (Element,),
                        {'tagname': 'element',
                         'children_classes': [],
                         '_attribute_names': ['attr']})
        cls = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': [sub_cls1, sub_cls2]})
        obj = cls()
        obj.load_from_xml(xml)
        self.assertTrue(obj)
        self.assertFalse(obj._comment)
        self.assertFalse(obj._attributes)
        self.assertTrue(obj['prev'])
        self.assertFalse(obj['prev']._comment)
        self.assertFalse(obj['prev']._attributes)
        self.assertTrue(obj['element'])
        self.assertEqual(obj['element']._comment, 'comment')
        self.assertEqual(obj['element']._attributes, {'attr': 'value'})

    def test__load_extra_from_dict(self):
        obj = self.cls()
        obj._attribute_names = ['attr']
        dic = {'_comment': 'comment', '_attrs': {'attr': 'value'}}
        obj._load_extra_from_dict(dic)
        self.assertEqual(obj._comment, 'comment')
        self.assertEqual(obj._attributes, {'attr': 'value'})

    def test_load_from_dict(self):
        sub_cls1 = type('SubClsPrev', (Element,), {'tagname': 'prev',
                                                   'children_classes': []})
        sub_cls2 = type('SubClsElement', (Element,),
                        {'tagname': 'element',
                         'children_classes': [],
                         '_attribute_names': ['attr']})
        cls = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': [sub_cls1, sub_cls2]})
        obj = cls()
        dic = {}
        obj.load_from_dict(dic)
        self.assertEqual(obj._comment, None)
        self.assertEqual(obj._attributes, None)
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
        self.assertEqual(obj._comment, 'comment')
        self.assertFalse(obj._attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj['element'])
        self.assertEqual(obj['element']._comment, 'element comment')
        self.assertEqual(obj['element']._attributes, {'attr': 'value'})

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
        self.assertEqual(obj._comment, None)
        self.assertFalse(obj._attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj['element'])
        self.assertEqual(obj['element']._comment, None)
        self.assertEqual(obj['element']._attributes, None)

    def test_load_from_dict_sub_list(self):
        sub_cls = type('Element', (Element,),
                       {'tagname': 'sub',
                        'children_classes': [],
                        '_attribute_names': ['attr']})
        list_cls = type('ListElement', (ListElement,),
                        {'tagname': 'element',
                         'children_classes': [],
                         '_elts': [sub_cls]})
        cls = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': [list_cls]})
        dic = {}
        obj = cls()
        obj.load_from_dict(dic)
        self.assertEqual(obj._comment, None)
        self.assertEqual(obj._attributes, None)
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
        self.assertEqual(obj._comment, 'comment')
        self.assertFalse(obj._attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj['sub'])
        self.assertEqual(len(obj['sub']), 1)
        self.assertEqual(obj['sub'][0]._comment, 'element comment')
        self.assertEqual(obj['sub'][0]._attributes, {'attr': 'value'})

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
        self.assertEqual(obj._comment, 'comment')
        self.assertFalse(obj._attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj['sub'])
        self.assertEqual(len(obj['sub']), 2)
        self.assertTrue(isinstance(obj['sub'][0], elements.EmptyElement))
        self.assertEqual(obj['sub'][1]._comment, 'element comment')
        self.assertEqual(obj['sub'][1]._attributes, {'attr': 'value'})

    def test_to_xml(self):
        sub_cls = type('SubClsElement', (Element,),
                            {'tagname': 'element',
                             'children_classes': [],
                             '_attribute_names': ['attr']})
        cls = type('Cls', (Element, ),
                   {'tagname': 'tag',
                   'children_classes': [sub_cls]})
        obj = cls()
        obj['element'] = sub_cls()
        obj['element']._comment = 'comment'
        obj['element']._attributes = {'attr': 'value'}
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
        sub_cls = type('Element', (Element,),
                       {'tagname': 'sub',
                        'children_classes': [],
                        '_attribute_names': ['attr']})
        list_cls = type('ListElement', (ListElement,),
                            {'tagname': 'element',
                             '_elts': [sub_cls]
                            })
        cls = type('Cls', (Element, ),
                   {'tagname': 'tag',
                   'children_classes': [list_cls]})
        obj = cls()
        obj1 = sub_cls()
        obj1._comment = 'comment1'
        obj1._attributes = {'attr': 'value'}
        obj2 = sub_cls()
        obj2._comment = 'comment2'
        lis = list_cls()
        lis.append(obj1)
        lis.append(obj2)
        obj['sub'] = lis
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
        html = self.cls._get_html_add_button(['prefix'])
        expected = ('<a class="btn-add" data-elt-id="prefix:tag">'
                    'Add tag</a>')
        self.assertEqual(html, expected)

        html = self.cls._get_html_add_button(['prefix'], 1, 'css_class')
        expected = ('<a class="btn-add css_class" '
                    'data-elt-id="prefix:1:tag">'
                    'Add tag</a>')
        self.assertEqual(html, expected)

        sub_cls = type('SubCls', (Element,), {'tagname': 'tag'})
        cls = type('MultipleCls', (ChoiceElement,), {'_elts': [sub_cls]})
        self.cls.parent = cls
        self.cls._is_choice = True
        html = self.cls._get_html_add_button(['prefix'])
        expected = ('<select class="btn-add">'
                    '<option>New tag</option>'
                    '<option value="prefix:tag">tag</option>'
                    '</select>')
        self.assertEqual(html, expected)

    def test__to_html(self):
        expected = ('<a class="btn-add" '
                    'data-elt-id="subtag">Add subtag</a>')
        parent_obj = self.cls()
        html = self.sub_cls._to_html(parent_obj)
        self.assertTrue(html, expected)

        parent_obj['subtag'] = self.sub_cls(parent_obj)
        html = self.sub_cls._to_html(parent_obj)
        self.assertTrue(html, expected)

    def test_to_html(self):
        obj = self.cls()
        html = obj.to_html()
        expected1 = ('<div class="panel panel-default tag" id="tag"><div class="panel-heading"><span data-toggle="collapse" href="#collapse-tag">tag'
                    '<a data-comment-name="tag:_comment" class="btn-comment" '
                    'title="Add comment"></a>'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-tag">'
                    '<a class="btn-add" data-elt-id="tag:subtag">Add '
                     'subtag</a></div></div>')
        self.assertEqual(html, expected1)

        obj.parent = 'my fake parent'
        html = obj.to_html()
        expected_button = ('<a class="btn-add" data-elt-id="tag">'
                           'Add tag</a>')
        self.assertEqual(html, expected_button)

        html = obj.to_html(partial=True)
        expected2 = (
            '<div class="panel panel-default tag" id="tag">'
            '<div class="panel-heading">'
            '<span data-toggle="collapse" href="#collapse-tag">'
            'tag<a class="btn-add hidden" data-elt-id="tag">Add tag</a>'
            '<a class="btn-delete" data-target="#tag" title="Delete"></a>'
            '<a data-comment-name="tag:_comment" class="btn-comment" '
            'title="Add comment"></a></span></div>'
            '<div class="panel-body panel-collapse collapse in" '
            'id="collapse-tag">'
            '<a class="btn-add" data-elt-id="tag:subtag">Add subtag</a>'
            '</div></div>'
        )
        self.assertEqual(html, expected2)

        obj._required = True
        html = obj.to_html()
        self.assertEqual(html, expected1)

        obj._required = False
        obj['subtag'] = self.sub_cls(obj)
        html = obj.to_html()
        self.assertEqual(html, expected2)

    def test_to_html_readonly(self):
        obj = self.cls()
        obj.root.html_render = render.ReadonlyRender()
        html = obj.to_html()
        expected1 = ('<div class="panel panel-default tag" id="tag"><div class="panel-heading"><span data-toggle="collapse" href="#collapse-tag">tag'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-tag">'
                     '</div></div>')
        self.assertEqual(html, expected1)

        obj.parent = 'my fake parent'
        html = obj.to_html()
        self.assertEqual(html, '')

        html = obj.to_html(partial=True)
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
        html = obj.to_html()
        self.assertEqual(html, expected1)

        obj._required = False
        obj['subtag'] = self.sub_cls(obj)
        html = obj.to_html()
        self.assertEqual(html, expected2)

    def test__to_jstree_dict(self):
        parent_obj = self.cls()
        result = self.sub_cls._to_jstree_dict(parent_obj)
        self.assertEqual(result, None)

        self.sub_cls._required = True
        result = self.sub_cls._to_jstree_dict(parent_obj)
        expected = {
            'data': 'subtag',
            'attr': {
                'id': 'tree_subtag',
                'class': 'tree_subtag subtag'},
            'children': []}
        self.assertEqual(result, expected)

        self.sub_cls._required = False
        parent_obj['subtag'] = self.sub_cls(parent_obj)
        expected = {
            'data': 'subtag',
            'attr': {
                'id': 'tree_subtag',
                'class': 'tree_subtag subtag'},
            'children': []}
        self.assertEqual(result, expected)

    def test_to_jstree_dict(self):
        obj = self.cls()
        result = obj.to_jstree_dict([])
        expected = {
            'data': 'tag',
            'attr': {
                'id': 'tree_tag',
                'class': 'tree_tag tag'},
            'children': []}
        self.assertEqual(result, expected)

        obj.text = 'my value'
        result = obj.to_jstree_dict([], index=10)
        expected = {
            'data': u'tag <span class="_tree_text">(my value)</span>',
            'attr': {
                'id': 'tree_10:tag',
                'class': 'tree_ tree_10 tag'},
            'children': []}
        self.assertEqual(result, expected)

        obj['subtag'] = self.sub_cls(obj)
        result = obj.to_jstree_dict([], index=10)
        expected = {
            'data': u'tag <span class="_tree_text">(my value)</span>',
            'attr': {
                'id': 'tree_10:tag',
                'class': 'tree_ tree_10 tag'},
            'children': [
                {'attr': {
                    'class': 'tree_10:tag:subtag subtag',
                    'id': 'tree_10:tag:subtag'},
                 'children': [],
                 'data': 'subtag'}]}
        self.assertEqual(result, expected)

    def test_to_jstree_dict_with_ListElement(self):
        sub_cls = type('Element', (Element,),
                       {'tagname': 'sub',
                        'children_classes': [],
                        '_attribute_names': ['attr']})
        list_cls = type('ListElement', (ListElement,),
                        {'tagname': 'element',
                         '_elts': [sub_cls]})
        cls = type('Cls', (Element, ),
                   {'tagname': 'tag',
                    'children_classes': [list_cls]})
        obj = cls()
        result = obj.to_jstree_dict([])
        expected = {
            'data': 'tag',
            'attr': {
                'id': 'tree_tag',
                'class': 'tree_tag tag'},
            'children': []}
        self.assertEqual(result, expected)

        list_cls._required = True
        result = obj.to_jstree_dict([])
        expected = {
            'data': 'tag',
            'attr': {
                'id': 'tree_tag',
                'class': 'tree_tag tag'
            },
            'children': [
                {
                    'data': 'sub',
                    'attr': {
                        'id': 'tree_tag:element:0:sub',
                        'class': 'tree_tag:element tree_tag:element:0 sub'
                    },
                    'children': []
                }
            ]
        }
        self.assertEqual(result, expected)

    def test___getitem__(self):
        obj = self.cls()
        obj['subtag'] = 'Hello world'
        self.assertEqual(obj['subtag'], 'Hello world')
        try:
            self.assertEqual(obj['unexisting'], 'Hello world')
            assert 0
        except KeyError, e:
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
        except Exception, e:
            self.assertEqual(str(e), 'Invalid child unexisting')
        subtag = obj.get_or_add('subtag')
        self.assertTrue(subtag)
        self.assertEqual(subtag.parent, obj)
        self.assertEqual(subtag.root, obj)

        subtag1 = obj.get_or_add('subtag')
        self.assertEqual(subtag1, subtag)

    def test_walk(self):
        parent_obj = self.cls()
        obj = self.sub_cls(parent_obj)

        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [])

        parent_obj['subtag'] = obj
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj])

        sub_sub_cls = type('SubSubCls', (TextElement, ),
                       {'tagname': 'subsub',
                        'children_classes': []})
        self.sub_cls.children_classes = [sub_sub_cls]
        subsub1 = sub_sub_cls()
        obj['subsub'] = subsub1
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj, subsub1])

    def test_findall(self):
        parent_obj = self.cls()
        obj = self.sub_cls(parent_obj)
        lis = parent_obj.findall('subtag')
        self.assertEqual(lis, [])

        lis = parent_obj.findall('unexisting')
        self.assertEqual(lis, [])

        parent_obj['subtag'] = obj
        lis = parent_obj.findall('subtag')
        self.assertEqual(lis, [obj])

    def test_write(self):
        filename = 'tests/test.xml'
        self.assertFalse(os.path.isfile(filename))
        try:
            obj = self.cls()
            try:
                obj.write()
                assert 0
            except Exception, e:
                self.assertEqual(str(e), 'No filename given')

            try:
                obj.write(filename)
                assert 0
            except Exception, e:
                self.assertEqual(str(e), 'No dtd url given')

            old_get_content = utils.get_dtd_content
            old_validate_xml = utils.validate_xml
            try:
                utils.get_dtd_content = lambda url, path: 'dtd content'
                utils.validate_xml = lambda xml, dtd_str: True
                obj.write(filename, dtd_url='http://dtd.url')
            finally:
                utils.get_dtd_content = old_get_content
                utils.validate_xml = old_validate_xml

            obj.write(filename, dtd_url='http://dtd.url', validate=False)
            result = open(filename, 'r').read()
            expected = ("<?xml version='1.0' encoding='UTF-8'?>\n"
                        '<!DOCTYPE tag SYSTEM "http://dtd.url">\n'
                        "<tag/>\n")
            self.assertEqual(result, expected)

            obj._xml_filename = filename
            obj.write(dtd_url='http://dtd.url', validate=False)

            obj._xml_dtd_url = 'http://dtd.url'
            obj._xml_encoding = 'iso-8859-1'
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


class TestTextElement(TestCase):

    def setUp(self):
        self.sub_cls = type('SubCls', (Element,),
                            {'tagname': 'subtag',
                             'children_classes': []})
        self.cls = type('Cls', (TextElement, ),
                        {'tagname': 'tag',
                         'children_classes': [self.sub_cls],
                         '_attribute_names': ['attr']})

    def test___repr__(self):
        self.assertTrue(repr(self.cls()))

    def test__get_allowed_tagnames(self):
        self.assertEqual(self.cls._get_allowed_tagnames(), ['tag'])

    def test__add(self):
        parent = type('Cls', (Element, ),
                      {'tagname': 'tag',
                       'children_classes': []})()
        obj = self.cls._create('tagname', parent, 'my value')
        self.assertEqual(obj.text, 'my value')
        self.assertEqual(obj.parent, parent)

    def test_load_from_xml(self):
        root = etree.Element('root')
        text = etree.Element('text')
        text.text = 'text'
        empty = etree.Element('empty')
        empty.text = ''
        comment = etree.Comment('comment')
        root.append(comment)
        root.append(text)
        root.append(empty)
        text.attrib['attr'] = 'value'
        obj = self.cls()
        obj.load_from_xml(text)
        self.assertEqual(obj.text, 'text')
        self.assertEqual(obj._exists, True)
        self.assertEqual(obj._comment, 'comment')
        self.assertEqual(obj._attributes, {'attr': 'value'})

        text.text = 'Hello world'
        comment1 = etree.Comment('comment inside a tag')
        text.append(comment1)

        obj = self.cls()
        obj.load_from_xml(text)
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj._exists, True)
        self.assertEqual(obj._comment, 'comment\ncomment inside a tag')
        self.assertEqual(obj._attributes, {'attr': 'value'})

        obj = self.cls()
        obj.load_from_xml(empty)
        self.assertEqual(obj.text, '')
        self.assertEqual(obj._exists, True)
        self.assertEqual(obj._comment, None)

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
        self.assertEqual(obj._comment, 'comment')
        self.assertEqual(obj._attributes, {'attr': 'value'})

        obj = self.cls()
        obj.load_from_dict(dic, skip_extra=True)
        self.assertEqual(obj.text, 'text')
        self.assertEqual(obj._comment, None)
        self.assertEqual(obj._attributes, None)

    def test_to_xml(self):
        obj = self.cls()
        obj.text = 'text'
        obj._comment = 'comment'
        obj._attributes = {'attr': 'value'}
        xml = obj.to_xml()
        self.assertTrue(xml.tag, 'tag')
        self.assertTrue(xml.text, 'text')
        self.assertTrue(xml.attrib, {'attr': 'value'})

        obj = self.cls()
        obj._is_empty = True
        obj.text = 'text'
        try:
            xml = obj.to_xml()
            assert 0
        except Exception, e:
            self.assertEqual(str(e),
                             'It\'s forbidden to have a value to an EMPTY tag')
        obj.text = None
        self.assertTrue(xml.tag, 'tag')
        self.assertTrue(xml.text, None)
        self.assertTrue(xml.attrib, {})

    def test__get_html_attrs(self):
        obj = self.cls()
        result = obj._get_html_attrs(None, 1)
        expected = [('name', "tag:_value"), ('rows', 1), ('class', 'tag')]
        self.assertEqual(result, expected)

        result = obj._get_html_attrs(['prefix'], 1)
        expected = [('name', "prefix:tag:_value"),
                    ('rows', 1),
                    ('class', 'tag')]
        self.assertEqual(result, expected)

        result = obj._get_html_attrs(['prefix'], 1, 10)
        expected = [('name', "prefix:10:tag:_value"),
                    ('rows', 1),
                    ('class', 'tag')]
        self.assertEqual(result, expected)

    def test_to_html(self):
        obj = self.cls()
        html = obj.to_html()
        expected = '<a class="btn-add" data-elt-id="tag">Add tag</a>'
        self.assertEqual(html, expected)

        html = obj.to_html(partial=True)
        expected = ('<div id="tag">'
                    '<label>tag</label>'
                    '<a class="btn-add hidden" '
                    'data-elt-id="tag">Add tag</a>'
                    '<a class="btn-delete" data-target="#tag" '
                    'title="Delete"></a>'
                    '<a data-comment-name="tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="1"></textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj._required = True
        html = obj.to_html()
        expected = ('<div id="tag">'
                    '<label>tag</label>'
                    '<a data-comment-name="tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '<textarea class="form-control tag" name="tag:_value" rows="1">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj.text = 'line1\nline2'
        html = obj.to_html()
        expected = ('<div id="tag">'
                    '<label>tag</label>'
                    '<a data-comment-name="tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '<textarea class="form-control tag" name="tag:_value" rows="2">'
                    'line1\nline2'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj.text = None
        obj.parent = type('MyListElement', (ListElement, ),
                           {'tagname': 'mytag',
                            '_attribute_names': [],
                            '_elts': [],
                            'children_classes': []})()
        html = obj.to_html()
        expected = ('<div id="tag">'
                    '<label>tag</label>'
                    '<a class="btn-delete btn-list" '
                    'data-target="#tag" title="Delete"></a>'
                    '<a data-comment-name="tag:_comment" class="btn-comment"'
                    ' title="Add comment"></a>'
                    '<textarea class="form-control tag" name="tag:_value" rows="1">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

    def test_to_html_readonly(self):
        obj = self.cls()
        obj.root.html_render = render.ReadonlyRender()
        html = obj.to_html()
        self.assertEqual(html, '')

        html = obj.to_html(partial=True)
        expected = ('<div id="tag">'
                    '<label>tag</label>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="1" readonly="readonly"></textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj._required = True
        html = obj.to_html()
        expected = ('<div id="tag">'
                    '<label>tag</label>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="1" readonly="readonly">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj.text = 'line1\nline2'
        html = obj.to_html()
        expected = ('<div id="tag">'
                    '<label>tag</label>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="2" readonly="readonly">'
                    'line1\nline2'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj.text = None
        obj.parent = type('MyListElement', (ListElement, ),
                           {'tagname': 'mytag',
                            '_attribute_names': [],
                            '_elts': [],
                            'children_classes': []})()
        html = obj.to_html()
        expected = ('<div id="tag">'
                    '<label>tag</label>'
                    '<textarea class="form-control tag" name="tag:_value" '
                    'rows="1" readonly="readonly">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)


class TestListElement(TestCase):

    def setUp(self):
        self.sub_cls = type('SubCls', (Element, ),
                            {'tagname': 'tag',
                             '_attribute_names': ['attr'],
                             'children_classes': []})
        self.cls = type('Cls', (ListElement,), {'tagname': 'list_cls',
                                                '_elts': [self.sub_cls]})

    def test__get_allowed_tagnames(self):
        self.assertEqual(self.cls._get_allowed_tagnames(), ['list_cls', 'tag'])

    def test_get_child_class(self):
        self.assertEqual(self.cls.get_child_class('tag'), self.sub_cls)
        self.assertEqual(self.cls.get_child_class('list_cls'), None)

    def test__get_value_from_parent(self):
        obj_cls = type('Cls', (Element,), {'tagname': 'tag',
                                           'children_classes': []})
        parent_obj_cls = type('Cls', (Element,), {'tagname': 'tg',
                                                  'children_classes': [obj_cls]})
        obj = obj_cls()
        parent_obj = parent_obj_cls()
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), None)
        parent_obj['tag'] = obj
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj)

    def test__get_value_from_parent_multiple(self):
        sub_cls = type('SubCls', (Element, ), {'tagname': 'tag1'})
        self.cls._elts += [sub_cls]
        obj_cls = type('Cls', (Element,), {'tagname': 'list_cls',
                                           'children_classes': []})
        parent_obj_cls = type('Cls', (Element,), {'tagname': 'tg',
                                                  'children_classes': [obj_cls]})
        parent_obj = parent_obj_cls()
        obj = obj_cls()
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), None)
        parent_obj['list_cls'] = obj
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj)

    def test_is_addable(self):
        obj = self.cls()
        self.assertEqual(obj.is_addable('tag'), True)
        self.assertEqual(obj.is_addable('test'), False)
        # Addable even we already have element defined
        obj.add('tag')
        self.assertEqual(obj.is_addable('tag'), True)

    def test__add(self):
        sub_cls = type('LisCls', (ListElement, ), {'tagname': 'tag',
                                                   '_elts': [],
                                                   'children_classes': []})
        parent_obj = type('PCls', (Element, ), {'tagname': 'tag1',
                                                'children_classes': [sub_cls]})()
        parent_obj['tag'] = sub_cls(parent_obj)

        self.assertEqual(parent_obj['tag'].root, parent_obj)
        try:
            obj1 = self.cls._create('tag', parent_obj, 'my value')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj1 = self.cls._create('tag', parent_obj)
        self.assertTrue(obj1.tagname, 'tag')
        self.assertEqual(obj1.parent, parent_obj['tag'])
        self.assertEqual(obj1.root, parent_obj)
        self.assertTrue(isinstance(obj1, Element))
        self.assertEqual(parent_obj['tag'], [obj1])

        obj2 = self.cls._create('tag', parent_obj)
        self.assertTrue(obj2.tagname, 'tag')
        self.assertEqual(obj2.parent, parent_obj['tag'])
        self.assertEqual(obj2.root, parent_obj)
        self.assertTrue(isinstance(obj2, Element))
        self.assertEqual(parent_obj['tag'], [obj1, obj2])

        self.cls._elts = [type('Cls', (TextElement, ),
                          {'tagname': 'tag',
                           'children_classes': []})]
        obj3 = self.cls._create('tag', parent_obj, 'my value')
        self.assertEqual(obj3.text, 'my value')

        obj4 = parent_obj['list_cls'].add('tag', index=0)
        self.assertEqual(parent_obj['list_cls'].index(obj4), 0)
        self.assertEqual(len(parent_obj['list_cls']), 4)

    def test__add_multiple(self):
        sub_cls = type('SubCls', (Element, ), {'tagname': 'tag1',
                                               'children_classes': []})
        self.cls._elts += [sub_cls]

        lelement = type('LisCls', (ListElement, ), {'tagname': 'list_cls',
                                                    '_elts': [],
                                                    'children_classes': []})

        parent_obj = type('PCls', (Element, ), {'tagname': 'tag1',
                                                'children_classes': [lelement]})()
        parent_obj['list_cls'] = lelement(parent_obj)
        obj1 = self.cls._create('tag', parent_obj)
        self.assertTrue(obj1.tagname, 'tag')
        self.assertEqual(obj1.parent, parent_obj['list_cls'])
        self.assertEqual(obj1.root, parent_obj)
        self.assertTrue(isinstance(obj1, Element))
        self.assertFalse(hasattr(parent_obj, 'tag'))
        self.assertEqual(parent_obj['list_cls'], [obj1])

        obj2 = self.cls._create('tag1', parent_obj)
        self.assertTrue(obj2.tagname, 'tag1')
        self.assertEqual(obj2.parent, parent_obj['list_cls'])
        self.assertEqual(obj2.root, parent_obj)
        self.assertTrue(isinstance(obj2, Element))
        self.assertEqual(parent_obj['list_cls'], [obj1, obj2])

    def test_add_list_of_list(self):
        dtd_str = '''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (subtext+)>
        <!ELEMENT subtext (#PCDATA)>
        '''
        dic = dtd_parser.parse(dtd_str=dtd_str)
        obj = dic['texts']()
        text = obj.add('text')
        subtext = text.add('subtext', 'value')
        self.assertEqual(subtext.text, 'value')

    def test_remove_empty_element(self):
        obj = self.cls()
        obj.append(None)
        obj.append(elements.EmptyElement(parent=obj))
        self.assertEqual(len(obj), 2)
        obj.remove_empty_element()
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj, [None])

    def test_to_xml(self):
        obj = self.cls()
        lis = obj.to_xml()
        self.assertEqual(lis, [])

        subobj = self.sub_cls()
        subobj._comment = 'comment'
        subobj._attributes = {'attr': 'value'}

        obj.append(subobj)
        lis = obj.to_xml()
        self.assertEqual(len(lis), 2)
        self.assertEqual(lis[0].text, 'comment')
        self.assertEqual(lis[1].tag, 'tag')

        obj = self.cls()
        obj._required = True
        lis = obj.to_xml()
        # Empty required with only one element, xml is created!
        self.assertEqual(len(lis), 1)
        self.assertEqual(lis[0].tag, 'tag')

        sub_cls = type('SubCls', (Element, ), {'tagname': 'tag1'})
        self.cls._elts += [sub_cls]
        obj = self.cls()
        obj._required = True
        lis = obj.to_xml()
        self.assertEqual(lis, [])

    def test__get_html_add_button(self):
        html = self.cls._get_html_add_button(None)
        expected = ('<a class="btn-add btn-list" '
                    'data-elt-id="list_cls:0:tag">New tag</a>')
        self.assertEqual(html, expected)

        html = self.cls._get_html_add_button(['prefix'], 10, 'css_class')
        expected = ('<a class="btn-add btn-list css_class" '
                    'data-elt-id="prefix:list_cls:10:tag">New tag</a>')
        self.assertEqual(html, expected)

        html = self.cls._get_html_add_button(['prefix'], 10, 'css_class')
        expected = ('<a class="btn-add btn-list css_class" '
                    'data-elt-id="prefix:list_cls:10:tag">New tag</a>')
        self.assertEqual(html, expected)

    def test__get_html_add_button_multiple(self):
        sub_cls = type('SubCls', (Element, ), {'tagname': 'tag1'})
        self.cls._elts += [sub_cls]
        html = self.cls._get_html_add_button(None)
        expected = ('<select class="btn-add btn-list">'
                    '<option>New tag/tag1</option>'
                    '<option value="list_cls:0:tag">tag</option>'
                    '<option value="list_cls:0:tag1">tag1</option>'
                    '</select>')
        self.assertEqual(html, expected)

    def test_to_html(self):
        obj = self.cls()
        html = obj.to_html()
        expected = ('<div class="list-container">'
                    '<a class="btn-add btn-list" '
                    'data-elt-id="list_cls:0:tag">New tag</a>'
                    '</div>')
        self.assertEqual(html, expected)

        html = obj.to_html(partial=True)
        expected = ('<div class="panel panel-default tag" id="list_cls:0:tag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-list_cls\:0\:tag">tag'
                    '<a class="btn-delete btn-list" '
                    'data-target="#list_cls:0:tag" title="Delete"></a>'
                    '<a data-comment-name="list_cls:0:tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-list_cls:0:tag">'
                    '</div></div>'
                    '<a class="btn-add btn-list" '
                    'data-elt-id="list_cls:1:tag">New tag</a>')
        self.assertEqual(html, expected)

        obj._required = True
        html = obj.to_html()
        expected = ('<div class="list-container">'
                    '<a class="btn-add btn-list" '
                    'data-elt-id="list_cls:0:tag">New tag</a>'
                    '<div class="panel panel-default tag" '
                    'id="list_cls:0:tag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-list_cls\:0\:tag">tag'
                    '<a class="btn-delete btn-list" '
                    'data-target="#list_cls:0:tag" title="Delete"></a>'
                    '<a data-comment-name="list_cls:0:tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-list_cls:0:tag">'
                    '</div></div>'
                    '<a class="btn-add btn-list" '
                    'data-elt-id="list_cls:1:tag">New tag</a>'
                    '</div>')
        self.assertEqual(html, expected)

        html = obj.to_html(offset=10)
        expected = ('<div class="list-container">'
                    '<a class="btn-add btn-list" '
                    'data-elt-id="list_cls:10:tag">New tag</a>'
                    '<div class="panel panel-default tag" id="list_cls:10:tag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-list_cls\:10\:tag">tag'
                    '<a class="btn-delete btn-list" '
                    'data-target="#list_cls:10:tag" title="Delete"></a>'
                    '<a data-comment-name="list_cls:10:tag:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-list_cls:10:tag">'
                    '</div></div>'
                    '<a class="btn-add btn-list" '
                    'data-elt-id="list_cls:11:tag">New tag</a>'
                    '</div>')
        self.assertEqual(html, expected)

    def test_to_html_readonly(self):
        obj = self.cls()
        obj.root.html_render = render.ReadonlyRender()
        html = obj.to_html()
        expected = '<div class="list-container"></div>'
        self.assertEqual(html, expected)

        html = obj.to_html(partial=True)
        expected = ('<div class="panel panel-default tag" id="list_cls:0:tag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-list_cls\:0\:tag">tag'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-list_cls:0:tag">'
                    '</div></div>')
        self.assertEqual(html, expected)

        obj._required = True
        html = obj.to_html()
        expected = ('<div class="list-container">'
                    '<div class="panel panel-default tag" '
                    'id="list_cls:0:tag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-list_cls\:0\:tag">tag'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-list_cls:0:tag">'
                    '</div></div>'
                    '</div>')
        self.assertEqual(html, expected)

        html = obj.to_html(offset=10)
        expected = ('<div class="list-container">'
                    '<div class="panel panel-default tag" id="list_cls:10:tag">'
                    '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-list_cls\:10\:tag">tag'
                    '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-list_cls:10:tag">'
                    '</div></div>'
                    '</div>')
        self.assertEqual(html, expected)

    def test_to_jstree_dict(self):
        obj = self.cls()
        result = obj.to_jstree_dict([])
        self.assertEqual(result, [])

        obj._required = True
        result = obj.to_jstree_dict([])
        expected = [{
            'attr': {'class': 'tree_list_cls tree_list_cls:0 tag',
                     'id': 'tree_list_cls:0:tag'},
            'children': [],
            'data': 'tag'}]
        self.assertEqual(result, expected)

    def test_walk(self):
        sub_cls = type('SubCls', (Element, ),
                       {'tagname': 'tag1',
                        'children_classes': []})
        self.cls._elts += [sub_cls]

        parent_obj = self.cls()
        obj1 = self.sub_cls(parent_obj)
        obj2 = sub_cls(parent_obj)

        parent_obj.extend([obj1, obj2])
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj1, obj2])

        sub_sub_cls = type('SubSubCls', (TextElement, ),
                       {'tagname': 'subsub',
                        'children_classes': []})
        self.sub_cls.children_classes = [sub_sub_cls]
        subsub1 = sub_sub_cls()
        obj1['subsub'] = subsub1
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj1, subsub1, obj2])

    def test_walk_list(self):
        parent_obj = type('ParentCls', (Element, ),
                       {'tagname': 'parent',
                        'children_classes': [self.cls]})()
        sub_sub_cls = type('SubSubCls', (TextElement, ),
                       {'tagname': 'subsub',
                        'children_classes': []})
        self.sub_cls.children_classes = [sub_sub_cls]
        obj = self.cls(parent_obj)
        parent_obj['tag'] = obj
        sub1 = self.sub_cls()
        sub2 = self.sub_cls()
        subsub1 = sub_sub_cls()
        sub1['subsub'] = subsub1
        obj.append(sub1)
        obj.append(sub2)

        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [sub1, subsub1, sub2])

    def test_get_or_add(self):
        obj = self.cls()
        try:
            obj.get_or_add('unexisting')
            assert 0
        except NotImplementedError:
            pass


class TestChoiceElement(TestCase):

    def setUp(self):
        self.sub_cls1 = type('SubCls', (Element, ),
                             {'tagname': 'tag1',
                              'children_classes': []})
        self.sub_cls2 = type('SubCls', (Element, ),
                             {'tagname': 'tag2',
                              'children_classes': []})
        self.cls = type('Cls', (ChoiceElement,),
                        {'tagname': 'choice_cls',
                         'children_classes': [],
                         '_elts': [self.sub_cls1,
                                   self.sub_cls2]})

    def test__get_allowed_tagnames(self):
        self.assertEqual(self.cls._get_allowed_tagnames(), ['tag1', 'tag2'])

    def test_get_child_class(self):
        self.assertEqual(self.cls.get_child_class('tag1'), self.sub_cls1)
        self.assertEqual(self.cls.get_child_class('tag2'), self.sub_cls2)

    def test__get_value_from_parent(self):
        sub_cls1 = type('SubSubCls', (TextElement, ),
                        {'tagname': 'tag1',
                         'children_classes': []})
        sub_cls2 = type('SubSubCls', (TextElement, ),
                        {'tagname': 'tag2',
                         'children_classes': []})
        parent_obj = type('ParentCls', (Element, ),
                          {'tagname': 'parent',
                           'children_classes': [sub_cls1, sub_cls2]})()
        obj1 = sub_cls1()
        obj2 = sub_cls2()
        self.assertTrue(obj1 != obj2)
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), None)
        parent_obj['tag2'] = obj1
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj1)
        parent_obj['tag1'] = obj2
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj2)

    def test__get_sub_value(self):
        sub_cls = type('SubSubCls', (TextElement, ),
                       {'tagname': 'tag1',
                        'children_classes': []})
        parent_obj = type('ParentCls', (Element, ),
                          {'tagname': 'parent',
                           'children_classes': [sub_cls]})()
        obj = sub_cls()
        result = self.cls._get_sub_value(parent_obj)
        self.assertFalse(result)
        self.cls._required = True
        result = self.cls._get_sub_value(parent_obj)
        self.assertFalse(result)
        parent_obj['tag1'] = obj
        self.assertEqual(self.cls._get_sub_value(parent_obj), obj)

    def test_is_addable(self):
        obj = self.cls()
        self.assertEqual(obj.is_addable('test'), False)

    def test_add(self):
        parent_obj = type('ParentCls', (Element, ),
                          {'tagname': 'parent',
                           'children_classes': [self.cls]})()
        obj = self.cls(parent_obj)

        try:
            obj.add('test')
        except Exception, e:
            self.assertEqual(str(e), 'Can\'t add element to ChoiceElement')

    def test__add(self):
        parent_obj = type('ParentCls', (Element, ),
                          {'tagname': 'parent',
                           'children_classes': [self.cls]})()
        try:
            obj1 = self.cls._create('tag1', parent_obj, 'my value')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj1 = self.cls._create('tag1', parent_obj)
        self.assertTrue(obj1.tagname, 'tag')
        self.assertEqual(obj1.parent, parent_obj)
        self.assertTrue(isinstance(obj1, Element))
        self.assertEqual(parent_obj['tag1'], obj1)

        parent = type('Cls', (TextElement, ),
                      {'tagname': 'tag',
                       'children_classes': []})()
        self.cls._elts = [type('Cls', (TextElement, ),
                          {'tagname': 'tag',
                           'children_classes': []})]
        obj2 = self.cls._create('tag', parent, 'my value')
        self.assertEqual(obj2.text, 'my value')
        self.assertEqual(obj2.parent, parent)

    def test__get_html_add_button(self):
        html = self.cls._get_html_add_button(None)
        expected = ('<select class="btn-add">'
                    '<option>New tag1/tag2</option>'
                    '<option value="tag1">tag1</option>'
                    '<option value="tag2">tag2</option>'
                    '</select>')
        self.assertEqual(html, expected)

        html = self.cls._get_html_add_button(['prefix'], 10, 'css_class')
        expected = ('<select class="btn-add css_class">'
                    '<option>New tag1/tag2</option>'
                    '<option value="prefix:10:tag1">tag1</option>'
                    '<option value="prefix:10:tag2">tag2</option>'
                    '</select>')
        self.assertEqual(html, expected)

    def test__to_html(self):
        parent_obj = type('ParentCls', (Element, ),
                          {'tagname': 'parent',
                           'children_classes': [self.cls]})()
        html = self.cls._to_html(parent_obj)
        expected = (
            '<select class="btn-add">'
            '<option>New tag1/tag2</option>'
            '<option value="tag1">tag1</option>'
            '<option value="tag2">tag2</option>'
            '</select>')
        self.assertEqual(html, expected)

        obj = self.cls()
        parent_obj['tag1'] = obj
        html = self.cls._to_html(parent_obj)
        expected = (
            '<div class="panel panel-default choice_cls" id="choice_cls">'
            '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-choice_cls">choice_cls'
            '<a data-comment-name="choice_cls:_comment" '
            'class="btn-comment" title="Add comment"></a>'
            '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-choice_cls">'
            '</div></div>')
        self.assertEqual(html, expected)

    def test_to_jstree_dict(self):
        obj = self.cls()
        result = obj.to_jstree_dict([])
        self.assertEqual(result, {})


class TestFunctions(TestCase):

    def test_get_obj_from_str_id(self):
        dtd_str = '''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:unexisting'
        try:
            html = get_obj_from_str_id(str_id, dtd_str=dtd_str)
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Unsupported tag unexisting')

        str_id = 'texts:text'
        html = get_obj_from_str_id(str_id, dtd_str=dtd_str)
        expected = (
            '<div id="texts:text">'
            '<label>text</label>'
            '<a data-comment-name="texts:text:_comment" '
            'class="btn-comment" title="Add comment"></a>'
            '<textarea class="form-control text" name="texts:text:_value" '
            'rows="1"></textarea>'
            '</div>')
        self.assertEqual(html, expected)

    def test_get_obj_from_str_id_list(self):
        dtd_str = '''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:list__text:0:text'
        html = get_obj_from_str_id(str_id, dtd_str=dtd_str)
        expected = ('<div id="texts:list__text:0:text">'
                    '<label>text</label>'
                    '<a class="btn-delete btn-list" '
                    'data-target="#texts:list__text:0:text" title="Delete"></a>'
                    '<a data-comment-name="texts:list__text:0:text:_comment" '
                    'class="btn-comment" title="Add comment"></a>'
                    '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
                    'rows="1">'
                    '</textarea>'
                    '</div>'
                    '<a class="btn-add btn-list" '
                    'data-elt-id="texts:list__text:1:text">New text</a>')
        self.assertEqual(html, expected)

        dtd_str = '''
        <!ELEMENT texts (list*)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:list__list:0:list:text'
        html = get_obj_from_str_id(str_id, dtd_str=dtd_str)
        expected = (
            '<div id="texts:list__list:0:list:text">'
            '<label>text</label>'
            '<a data-comment-name="texts:list__list:0:list:text:_comment" '
            'class="btn-comment" title="Add comment"></a>'
            '<textarea class="form-control text" name="texts:list__list:0:list:text:_value" '
            'rows="1"></textarea>'
            '</div>')
        self.assertEqual(html, expected)

    def test__get_previous_js_selectors(self):
        dtd_str = '''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts'
        obj, prefixes, index = elements._get_obj_from_str_id(str_id,
                                               dtd_str=dtd_str)
        lis = elements._get_previous_js_selectors(obj, prefixes, index)
        self.assertEqual(lis, [])

        lis = elements._get_previous_js_selectors(obj, prefixes, index)
        self.assertEqual(lis, [])

        str_id = 'texts:list__list:0:list:text'
        obj, prefixes, index = elements._get_obj_from_str_id(str_id,
                                               dtd_str=dtd_str)
        lis = elements._get_previous_js_selectors(obj, prefixes, index)
        expected = [('inside', '#tree_texts:list__list:0:list')]
        self.assertEqual(lis, expected)

        str_id = 'texts:list__list:0:list'
        obj, prefixes, index = elements._get_obj_from_str_id(str_id,
                                               dtd_str=dtd_str)
        lis = elements._get_previous_js_selectors(obj, prefixes, index)
        expected = [
            ('after', '.tree_texts:tag1'),
            ('inside', '#tree_texts')]
        self.assertEqual(lis, expected)

        str_id = 'texts:list__list:1:list'
        obj, prefixes, index = elements._get_obj_from_str_id(str_id,
                                               dtd_str=dtd_str)
        lis = elements._get_previous_js_selectors(obj, prefixes, index)
        expected = [('after', '.tree_texts:list__list:0')]
        self.assertEqual(lis, expected)

        str_id = 'texts:tag2'
        obj, prefixes, index = elements._get_obj_from_str_id(str_id,
                                               dtd_str=dtd_str)
        lis = elements._get_previous_js_selectors(obj, prefixes, index)
        expected = [('after', '.tree_texts:list__list'),
                    ('after', '.tree_texts:tag1'),
                    ('inside', '#tree_texts')]
        self.assertEqual(lis, expected)

    def test__get_html_from_obj(self):
        dtd_str = '''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts:tag2'
        obj, prefixes, index = elements._get_obj_from_str_id(str_id,
                                               dtd_str=dtd_str)
        result = elements._get_html_from_obj(obj, prefixes, index)
        expected = (
            '<div id="texts:tag2">'
            '<label>tag2</label>'
            '<a data-comment-name="texts:tag2:_comment" class="btn-comment" '
            'title="Add comment"></a>'
            '<textarea class="form-control tag2" name="texts:tag2:_value" '
            'rows="1"></textarea>'
            '</div>')
        self.assertEqual(result, expected)

        str_id = 'texts:list__list:1:list'
        obj, prefixes, index = elements._get_obj_from_str_id(str_id,
                                               dtd_str=dtd_str)
        result = elements._get_html_from_obj(obj, prefixes, index)
        expected = (
            '<div class="panel panel-default list" '
            'id="texts:list__list:1:list"><div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts\:list__list\:1\:list">list'
            '<a class="btn-delete btn-list" '
            'data-target="#texts:list__list:1:list" '
            'title="Delete"></a>'
            '<a data-comment-name="texts:list__list:1:list:_comment" '
            'class="btn-comment" title="Add comment"></a>'
            '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts:list__list:1:list">'
            '<div id="texts:list__list:1:list:text">'
            '<label>text</label>'
            '<a data-comment-name="texts:list__list:1:list:text:_comment" '
            'class="btn-comment" title="Add comment"></a>'
            '<textarea class="form-control text" name="texts:list__list:1:list:text:_value" '
            'rows="1"></textarea>'
            '</div>'
            '</div></div>'
            '<a class="btn-add btn-list" '
            'data-elt-id="texts:list__list:2:list">New list</a>')
        self.assertEqual(result, expected)

    def test_get_jstree_json_from_str_id(self):
        dtd_str = '''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts:tag2'
        result = elements.get_jstree_json_from_str_id(str_id, dtd_str=dtd_str)
        expected = {
            'previous': [
                ('after', '.tree_texts:list__list'),
                ('after', '.tree_texts:tag1'),
                ('inside', '#tree_texts')],
            'html': ('<div id="texts:tag2">'
                     '<label>tag2</label>'
                     '<a data-comment-name="texts:tag2:_comment" '
                     'class="btn-comment" title="Add comment"></a>'
                     '<textarea class="form-control tag2" name="texts:tag2:_value" '
                     'rows="1"></textarea></div>'),
            'jstree_data': {
                'data': 'tag2',
                'attr': {
                    'id': 'tree_texts:tag2',
                    'class': 'tree_texts:tag2 tag2'},
                'children': []}}
        self.assertEqual(result, expected)

    def test_get_display_data_from_obj(self):
        dtd_str = '''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text1)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts:list__list:0:list:text1'
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {
                            'text1': {'_value': 'Hello world'},
                        }
                    }
                ]
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        res = elements.get_display_data_from_obj(obj)
        expected = {
            'elt_id': 'texts:list__list:0:list:text1',
            'html': (
                '<div id="texts:list__list:0:list:text1">'
                '<label>text1</label>'
                '<a data-comment-name="texts:list__list:0:list:text1:_comment" '
                'class="btn-comment" title="Add comment"></a>'
                '<textarea class="form-control text1" '
                'name="texts:list__list:0:list:text1:_value" rows="1">'
                'Hello world</textarea>'
                '</div>'),
            'is_choice': False,
            'jstree_data': {
                'attr': {
                    'class': 'tree_texts:list__list:0:list:text1 text1',
                    'id': 'tree_texts:list__list:0:list:text1'},
                'children': [],
                'data': u'text1 <span class="_tree_text">(Hello world)</span>'
            },
            'previous': [('inside', '#tree_texts:list__list:0:list')]
        }
        self.assertEqual(res, expected)

        # Test with is_choice
        obj._is_choice = True
        res = elements.get_display_data_from_obj(obj)
        self.assertEqual(res['is_choice'], True)

        # Test with list object
        str_id = 'texts:list__list:0:list'
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {
                            'text1': {'_value': 'Hello world'},
                        }
                    }
                ]
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        res = elements.get_display_data_from_obj(obj)
        expected = {
            'elt_id': 'texts:list__list:0:list',
            'html': (
                '<div class="panel panel-default list" '
                'id="texts:list__list:0:list">'
                '<div class="panel-heading">'
                '<span data-toggle="collapse" '
                'href="#collapse-texts\\:list__list\\:0\\:list">list'
                '<a class="btn-delete btn-list" '
                'data-target="#texts:list__list:0:list" title="Delete"></a>'
                '<a data-comment-name="texts:list__list:0:list:_comment" '
                'class="btn-comment" title="Add comment"></a>'
                '</span>'
                '</div>'
                '<div class="panel-body panel-collapse collapse in" '
                'id="collapse-texts:list__list:0:list">'
                '<div id="texts:list__list:0:list:text1">'
                '<label>text1</label>'
                '<a data-comment-name="texts:list__list:0:list:text1:_comment"'
                ' class="btn-comment" title="Add comment"></a>'
                '<textarea class="form-control text1" '
                'name="texts:list__list:0:list:text1:_value" rows="1">'
                'Hello world</textarea>'
                '</div>'
                '</div>'
                '</div>'
                '<a class="btn-add btn-list" '
                'data-elt-id="texts:list__list:1:list">New list</a>'),
            'is_choice': False,
            'jstree_data': {
                'attr': {
                    'class': 'tree_texts:list__list tree_texts:list__list:0 list',
                    'id': 'tree_texts:list__list:0:list'},
                'children': [{
                    'attr': {
                        'class': 'tree_texts:list__list:0:list:text1 text1',
                        'id': 'tree_texts:list__list:0:list:text1'},
                    'children': [],
                    'data': ('text1 <span class="_tree_text">'
                             '(Hello world)</span>')}],
                'data': 'list'},
            'previous': [('after', '.tree_texts:tag1'),
                         ('inside', '#tree_texts')]
        }
        self.assertEqual(res, expected)

        obj.parent._elts = ['Fake1', 'Fake2']
        res = elements.get_display_data_from_obj(obj)
        self.assertEqual(res['is_choice'], True)

    def test_load_obj_from_id(self):
        dtd_str = '''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts'
        data = {}
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'texts')

        str_id = 'texts:tag2'
        data = {
            'texts': {
                'tag2': {
                    '_value': 'Hello world',
                }
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'tag2')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj.parent.tagname, 'texts')

        str_id = 'texts:list__list:0:list:text'
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {
                            'text': {'_value': 'Hello world'},
                        }
                    }
                ]
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'text')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj.parent.tagname, 'list')
        self.assertEqual(len(obj.parent.parent), 1)

        # Test with list but missing elements: we have the element of index 2
        # and not the ones for index 0, 1
        str_id = 'texts:list__list:2:list:text'
        data = {
            'texts': {
                'list__list': [
                    None,
                    None,
                    {
                        'list': {
                            'text': {'_value': 'Hello world'},
                        }
                    }
                ]
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'text')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj.parent.tagname, 'list')
        list_obj = obj.parent.parent
        self.assertEqual(len(list_obj), 3)
        self.assertTrue(isinstance(list_obj[0], elements.EmptyElement))
        self.assertTrue(isinstance(list_obj[1], elements.EmptyElement))

        # Test with list but missing elements: we don't have enough element
        str_id = 'texts:list__list:2:list:text'
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {
                            'text': {'_value': 'Hello world'},
                        }
                    }
                ]
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'text')
        self.assertEqual(obj.text, None)
        self.assertEqual(obj.parent.tagname, 'list')
        list_obj = obj.parent.parent
        self.assertEqual(len(list_obj), 3)
        self.assertFalse(isinstance(list_obj[0], elements.EmptyElement))
        self.assertTrue(isinstance(list_obj[1], elements.EmptyElement))
        self.assertFalse(isinstance(list_obj[2], elements.EmptyElement))
        self.assertEqual(list_obj[2], obj.parent)

        # Test with enough element, but the one we want is an empty one
        str_id = 'texts:list__list:1:list:text'
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {
                            'text': {'_value': 'Hello world'},
                        },
                    },
                    None,
                    {
                        'list': {
                            'text': {'_value': 'Hello world'},
                        },
                    }
                ]
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'text')
        self.assertEqual(obj.text, None)
        self.assertEqual(obj.parent.tagname, 'list')
        list_obj = obj.parent.parent
        self.assertEqual(len(list_obj), 3)
        self.assertFalse(isinstance(list_obj[0], elements.EmptyElement))
        # The good element has been generated
        self.assertFalse(isinstance(list_obj[1], elements.EmptyElement))
        self.assertFalse(isinstance(list_obj[2], elements.EmptyElement))
        self.assertEqual(list_obj[1], obj.parent)

    def test_load_obj_from_id_choices(self):
        dtd_str = '''
        <!ELEMENT texts ((tag1|tag2)*)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts'
        data = {}
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'texts')

        str_id = 'texts:list__tag1_tag2:0:tag1'
        data = {
            'texts': {
                'list__tag1_tag2': [
                    {
                        'tag1': {'_value': 'Hello world'}
                    }
                ]
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'tag1')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj.parent.tagname, 'list__tag1_tag2')

        dtd_str = '''
        <!ELEMENT texts (tag1|tag2)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts'
        data = {}
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'texts')

        str_id = 'texts:tag1'
        data = {
            'texts': {
                'tag1': {'_value': 'Hello world'}
            }
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'tag1')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj.parent.tagname, 'texts')

        data = {
            'texts': {}
        }
        obj = elements.load_obj_from_id(str_id, data, dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'tag1')
        self.assertEqual(obj.text, None)
        self.assertEqual(obj.parent.tagname, 'texts')

    def test_get_parent_to_add_obj(self):
        dtd_str = '''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts:list__list:0:list:text'
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {
                            'text': {'_value': 'Hello world'},
                        }
                    }
                ]
            }
        }
        source_id = 'texts:list__list:0:list:text'
        parentobj = elements.get_parent_to_add_obj(str_id, source_id, data,
                                                   dtd_str=dtd_str)
        # The 'text' element can be pasted here.
        self.assertEqual(parentobj, None)

        str_id = 'texts:list__list:0:list'
        source_id = 'texts:list__list:0:list'
        parentobj = elements.get_parent_to_add_obj(str_id, source_id, data,
                                                   dtd_str=dtd_str)
        self.assertEqual(parentobj.tagname, 'list__list')

        # Remove the 'text' element from 'list'
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {}
                    }
                ]
            }
        }
        str_id = 'texts:list__list:0:list'
        source_id = 'texts:list__list:0:list:text'
        parentobj = elements.get_parent_to_add_obj(str_id, source_id, data,
                                                   dtd_str=dtd_str)
        self.assertEqual(parentobj.tagname, 'list')

        # Try with missing element
        data = {
            'texts': {
                'list__list': []
            }
        }
        str_id = 'texts:list__list:10:list'
        source_id = 'texts:list__list:5:list'
        parentobj = elements.get_parent_to_add_obj(str_id, source_id, data,
                                                   dtd_str=dtd_str)
        self.assertEqual(parentobj.tagname, 'list__list')

        # Try with empty element
        # The str_id has no value so didn't exist, we want to make sure we
        # create it correctly
        dtd_str = '''
        <!ELEMENT texts (tag1, list*)>
        <!ELEMENT list (text)>
        <!ELEMENT text (tag2)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        data = {
            'texts': {
                'list__list': [
                    None,
                    None,
                    {
                        'list': {'text': {'tag2': {'_value': 'Hello'}}}
                    }
                ]
            }
        }
        str_id = 'texts:list__list:1:list'
        source_id = 'texts:list__list:2:list:text'
        parentobj = elements.get_parent_to_add_obj(str_id, source_id, data,
                                                   dtd_str=dtd_str)
        self.assertEqual(parentobj.tagname, 'list')
        lis = parentobj.parent
        self.assertTrue(isinstance(lis[0], elements.EmptyElement))
        self.assertEqual(lis[1], parentobj)

    def test_add_new_element_from_id(self):
        dtd_str = '''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts:list__list:0:list:text'
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {
                            'text': {'_value': 'Hello world'},
                        }
                    }
                ]
            }
        }
        source_id = 'texts:list__list:0:list:text'
        clipboard_data = {
            'texts': {
                'list__list': [
                    {
                        'list': {
                            'text': {'_value': 'Text to copy'},
                        }
                    }
                ]
            }
        }
        # 'text' element can't be added
        obj = elements.add_new_element_from_id(str_id, source_id, data,
                                               clipboard_data,
                                               dtd_str=dtd_str)
        self.assertEqual(obj, None)

        str_id = 'texts:list__list:0:list'
        source_id = 'texts:list__list:0:list'
        obj = elements.add_new_element_from_id(str_id, source_id, data,
                                               clipboard_data,
                                               dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'list')
        self.assertEqual(obj['text'].text, 'Text to copy')
        self.assertEqual(len(obj.parent), 2)
