#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import tw2.core as twc
import tw2.core.testbase as tw2test
import os.path
from xmltools import dtd_parser, utils, factory
from xmltools.elements import (
    ElementV2,
    ElementListV2,
    TextElementV2,
    MultipleElementV2,
    get_obj_from_str,
)
import xmltools.elements as elements
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
import simplejson as json

_marker = object()


class FakeClass(object):
    pass


class TestElementV2(TestCase):

    def setUp(self):
        self.sub_cls = type('SubCls', (ElementV2,),
                            {'_tagname': 'subtag',
                             '_sub_elements': []})
        self.cls = type('Cls', (ElementV2, ), {'_tagname': 'tag',
                                               '_sub_elements': [self.sub_cls]})

    def test__get_allowed_tagnames(self):
        self.assertEqual(self.cls._get_allowed_tagnames(), ['tag'])

    def test__get_sub_element(self):
        self.assertEqual(self.cls._get_sub_element('subtag'), self.sub_cls)
        self.assertEqual(self.cls._get_sub_element('unexisting'), None)

    def test__get_value_from_parent(self):
        parent_obj = FakeClass()
        obj = ElementV2()
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), None)
        parent_obj.tag = obj
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj)

    def test__get_sub_value(self):
        parent_obj = FakeClass()
        obj = ElementV2()
        result = self.cls._get_sub_value(parent_obj)
        self.assertFalse(result)
        self.cls._required = True
        result = self.cls._get_sub_value(parent_obj)
        self.assertTrue(result)
        self.assertTrue(result != obj)
        parent_obj.tag = obj
        self.assertEqual(self.cls._get_sub_value(parent_obj), obj)

    def test__has_value(self):
        obj = self.cls()
        self.assertFalse(obj._has_value())
        obj.subtag = ElementV2()
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

    def test__add(self):
        parent_obj = FakeClass()
        obj = self.cls._add('tagname', parent_obj)
        self.assertEqual(obj._parent, parent_obj)
        self.assertTrue(isinstance(obj, ElementV2))
        self.assertEqual(parent_obj.tagname, obj)

        try:
            obj = ElementV2._add('tagname', parent_obj)
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'tagname already defined')

    def test_add(self):
        parent_obj = FakeClass()
        obj = self.cls()
        obj._parent = parent_obj
        newobj = obj.add('subtag')
        self.assertTrue(newobj)
        try:
            obj.add('unexisting')
        except Exception, e:
            self.assertEqual(str(e), 'Invalid child unexisting')

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
                    'class="btn-comment">Comment</a>')
        self.assertEqual(html, expected)

        obj._comment = 'my comment'
        html = obj._comment_to_html(['prefix'], None)
        expected = ('<a data-comment-name="prefix:tag:_comment" '
                    'class="btn-comment">Comment</a>'
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

        sub_cls1 = type('SubClsPrev', (ElementV2,), {'_tagname': 'prev'})
        sub_cls2 = type('SubClsElement', (ElementV2,),
                            {'_tagname': 'element',
                             '_attribute_names': ['attr']})
        cls = type('Cls', (ElementV2, ),
                   {'_tagname': 'tag',
                   '_sub_elements': [sub_cls1, sub_cls2]})
        obj = cls()
        obj.load_from_xml(xml)
        self.assertTrue(obj)
        self.assertFalse(obj._comment)
        self.assertFalse(obj._attributes)
        self.assertTrue(obj.prev)
        self.assertFalse(obj.prev._comment)
        self.assertFalse(obj.prev._attributes)
        self.assertTrue(obj.element)
        self.assertEqual(obj.element._comment, 'comment')
        self.assertEqual(obj.element._attributes, {'attr': 'value'})

    def test__load_extra_from_dict(self):
        obj = self.cls()
        obj._attribute_names = ['attr']
        dic = {'_comment': 'comment', '_attrs': {'attr': 'value'}}
        obj._load_extra_from_dict(dic)
        self.assertEqual(obj._comment, 'comment')
        self.assertEqual(obj._attributes, {'attr': 'value'})

    def test_load_from_dict(self):
        sub_cls1 = type('SubClsPrev', (ElementV2,), {'_tagname': 'prev'})
        sub_cls2 = type('SubClsElement', (ElementV2,),
                            {'_tagname': 'element',
                             '_attribute_names': ['attr']})
        cls = type('Cls', (ElementV2, ),
                   {'_tagname': 'tag',
                   '_sub_elements': [sub_cls1, sub_cls2]})
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
        self.assertTrue(obj.element)
        self.assertEqual(obj.element._comment, 'element comment')
        self.assertEqual(obj.element._attributes, {'attr': 'value'})

    def test_load_from_dict_sub_list(self):
        sub_cls = type('ElementV2', (ElementV2,),
                       {'_tagname': 'sub',
                        '_attribute_names': ['attr']})
        list_cls = type('ElementListV2', (ElementListV2,),
                            {'_tagname': 'element',
                             '_elts': [sub_cls]
                            })
        cls = type('Cls', (ElementV2, ),
                   {'_tagname': 'tag',
                   '_sub_elements': [list_cls]})
        obj = cls()
        dic = {}
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
        obj.load_from_dict(dic)
        self.assertTrue(obj)
        self.assertEqual(obj._comment, 'comment')
        self.assertFalse(obj._attributes)
        self.assertFalse(hasattr(obj, 'prev'))
        self.assertTrue(obj.sub)
        self.assertEqual(len(obj.sub), 1)
        self.assertEqual(obj.sub[0]._comment, 'element comment')
        self.assertEqual(obj.sub[0]._attributes, {'attr': 'value'})

    def test_to_xml(self):
        sub_cls = type('SubClsElement', (ElementV2,),
                            {'_tagname': 'element',
                             '_sub_elements': [],
                             '_attribute_names': ['attr']})
        cls = type('Cls', (ElementV2, ),
                   {'_tagname': 'tag',
                   '_sub_elements': [sub_cls]})
        obj = cls()
        obj.element = sub_cls()
        obj.element._comment = 'comment'
        obj.element._attributes = {'attr': 'value'}
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
        sub_cls = type('ElementV2', (ElementV2,),
                       {'_tagname': 'sub',
                        '_sub_elements': [],
                        '_attribute_names': ['attr']})
        list_cls = type('ElementListV2', (ElementListV2,),
                            {'_tagname': 'element',
                             '_elts': [sub_cls]
                            })
        cls = type('Cls', (ElementV2, ),
                   {'_tagname': 'tag',
                   '_sub_elements': [list_cls]})
        obj = cls()
        obj1 = sub_cls()
        obj1._comment = 'comment1'
        obj1._attributes = {'attr': 'value'}
        obj2 = sub_cls()
        obj2._comment = 'comment2'
        lis = list_cls()
        lis.append(obj1)
        lis.append(obj2)
        obj.sub = lis
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
        expected = ('<a class="btn btn-add-ajax" data-id="prefix:tag">'
                    'Add tag</a>')
        self.assertEqual(html, expected)

        html = self.cls._get_html_add_button(['prefix'], 1, 'css_class')
        expected = ('<a class="btn btn-add-ajax css_class" '
                    'data-id="prefix:1:tag">'
                    'Add tag</a>')
        self.assertEqual(html, expected)

        sub_cls = type('SubCls', (ElementV2,), {'_tagname': 'tag'})
        cls = type('MultipleCls', (MultipleElementV2,), {'_elts': [sub_cls]})
        self.cls._parent = cls
        self.cls._is_choice = True
        html = self.cls._get_html_add_button(['prefix'])
        expected = ('<select class="btn btn-add-ajax-choice">'
                    '<option>New tag</option>'
                    '<option value="prefix:tag">tag</option>'
                    '</select>')
        self.assertEqual(html, expected)

    def test__to_html(self):
        expected = ('<a class="btn btn-add-ajax" '
                    'data-id="subtag">Add subtag</a>')
        parent_obj = self.cls()
        html = self.sub_cls._to_html(parent_obj)
        self.assertTrue(html, expected)

        parent_obj.subtag = self.sub_cls()
        parent_obj.subtag._parent = parent_obj
        html = self.sub_cls._to_html(parent_obj)
        self.assertTrue(html, expected)

    def test_to_html(self):
        obj = self.cls()
        html = obj.to_html()
        expected1 = ('<fieldset class="tag"><legend>tag'
                    '<a data-comment-name="tag:_comment" class="btn-comment">'
                    'Comment</a>'
                    '</legend>'
                    '<fieldset class="subtag tag:subtag">'
                    '<legend>subtag'
                    '<a data-comment-name="tag:subtag:_comment" '
                    'class="btn-comment">Comment</a>'
                    '</legend>'
                    '</fieldset>'
                    '</fieldset>')
        self.assertEqual(html, expected1)

        obj._parent = 'my fake parent'
        html = obj.to_html()
        expected_button = ('<a class="btn btn-add-ajax" data-id="tag">'
                           'Add tag</a>')
        self.assertEqual(html, expected_button)

        html = obj.to_html(partial=True)
        expected2 = ('<fieldset class="tag">'
                    '<legend>tag'
                    '<a class="btn btn-add-ajax hidden" data-id="tag">'
                    'Add tag</a>'
                    '<a class="btn-delete-fieldset">Delete</a>'
                    '<a data-comment-name="tag:_comment" class="btn-comment">'
                    'Comment</a>'
                    '</legend>'
                    '<fieldset class="subtag tag:subtag">'
                    '<legend>subtag'
                    '<a data-comment-name="tag:subtag:_comment" '
                    'class="btn-comment">Comment</a>'
                    '</legend>'
                    '</fieldset>'
                    '</fieldset>')
        self.assertEqual(html, expected2)

        obj._required = True
        html = obj.to_html()
        self.assertEqual(html, expected1)

        obj._required = False
        obj.subtag = self.sub_cls()
        html = obj.to_html()
        self.assertEqual(html, expected2)


class TestTextElementV2(TestCase):

    def setUp(self):
        self.cls = type('Cls', (TextElementV2, ),
                        {'_tagname': 'tag',
                         '_attribute_names': ['attr']})

    def test___repr__(self):
        self.assertTrue(repr(self.cls()))

    def test__get_allowed_tagnames(self):
        self.assertEqual(self.cls._get_allowed_tagnames(), ['tag'])

    def test_load_from_xml(self):
        root = etree.Element('root')
        text = etree.Element('text')
        text.text = 'text'
        comment = etree.Comment('comment')
        root.append(comment)
        root.append(text)
        text.attrib['attr'] = 'value'
        obj = self.cls()
        obj.load_from_xml(text)
        self.assertEqual(obj._value, 'text')
        self.assertEqual(obj._comment, 'comment')
        self.assertEqual(obj._attributes, {'attr': 'value'})

    def test_load_from_dict(self):
        dic = {'tag': {'_value': 'text',
                       '_comment': 'comment',
                       '_attrs':{
                            'attr': 'value'
                       }}
              }
        obj = self.cls()
        obj.load_from_dict(dic)
        self.assertEqual(obj._value, 'text')
        self.assertEqual(obj._comment, 'comment')
        self.assertEqual(obj._attributes, {'attr': 'value'})

    def test_to_xml(self):
        obj = self.cls()
        obj._value = 'text'
        obj._comment = 'comment'
        obj._attributes = {'attr': 'value'}
        xml = obj.to_xml()
        self.assertTrue(xml.tag, 'tag')
        self.assertTrue(xml.text, 'text')
        self.assertTrue(xml.attrib, {'attr': 'value'})

    def test__get_html_attrs(self):
        obj = self.cls()
        result = obj._get_html_attrs(None)
        expected = ' name="tag:_value" id="tag" class="tag"'
        self.assertEqual(result, expected)

        result = obj._get_html_attrs(['prefix'])
        expected = (' name="prefix:tag:_value" id="prefix:tag" '
                    'class="prefix:tag"')
        self.assertEqual(result, expected)

        result = obj._get_html_attrs(['prefix'], 10)
        expected = (' name="prefix:10:tag:_value" id="prefix:10:tag" '
                    'class="prefix"')
        self.assertEqual(result, expected)

    def test_to_html(self):
        obj = self.cls()
        html = obj.to_html()
        expected = '<a class="btn btn-add-ajax" data-id="tag">Add tag</a>'
        self.assertEqual(html, expected)

        html = obj.to_html(partial=True)
        expected = ('<div>'
                    '<label>tag</label>'
                    '<a class="btn btn-add-ajax hidden" '
                    'data-id="tag">Add tag</a>'
                    '<a class="btn-delete">Delete</a>'
                    '<a data-comment-name="tag:_comment" '
                    'class="btn-comment">Comment</a>'
                    '<textarea name="tag:_value" id="tag" '
                    'class="tag"></textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj._required = True
        html = obj.to_html()
        expected = ('<div>'
                    '<label>tag</label>'
                    '<a data-comment-name="tag:_comment" '
                    'class="btn-comment">Comment</a>'
                    '<textarea name="tag:_value" id="tag" class="tag">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)

        obj._parent = ElementListV2()
        html = obj.to_html()
        expected = ('<div>'
                    '<label>tag</label>'
                    '<a class="btn-delete-list">Delete</a>'
                    '<a data-comment-name="tag:_comment" class="btn-comment">'
                    'Comment</a>'
                    '<textarea name="tag:_value" id="tag" class="tag">'
                    '</textarea>'
                    '</div>')
        self.assertEqual(html, expected)


class TestElementListV2(TestCase):


    def setUp(self):
        self.sub_cls = type('SubCls', (ElementV2, ),
                            {'_tagname': 'tag',
                             '_attribute_names': ['attr'],
                             '_sub_elements': []})
        self.cls = type('Cls', (ElementListV2,), {'_tagname': 'list_cls',
                                                  '_elts': [self.sub_cls]})

    def test__get_allowed_tagnames(self):
        self.assertEqual(self.cls._get_allowed_tagnames(), ['list_cls', 'tag'])

    def test__get_sub_element(self):
        self.assertEqual(self.cls._get_sub_element('tag'), self.sub_cls)
        self.assertEqual(self.cls._get_sub_element('list_cls'), None)

    def test__get_value_from_parent(self):
        parent_obj = FakeClass()
        obj = ElementV2()
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), None)
        parent_obj.tag = obj
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj)

    def test__get_value_from_parent_multiple(self):
        sub_cls = type('SubCls', (ElementV2, ), {'_tagname': 'tag1'})
        self.cls._elts += [sub_cls]
        parent_obj = FakeClass()
        obj = ElementV2()
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), None)
        parent_obj.list_cls = obj
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj)

    def test__add(self):
        parent_obj = FakeClass()
        parent_obj.tag = ElementListV2()
        obj1 = self.cls._add('tag', parent_obj)
        self.assertTrue(obj1._tagname, 'tag')
        self.assertEqual(obj1._parent, parent_obj.tag)
        self.assertTrue(isinstance(obj1, ElementV2))
        self.assertEqual(parent_obj.tag, [obj1])

        obj2 = self.cls._add('tag', parent_obj)
        self.assertTrue(obj2._tagname, 'tag')
        self.assertEqual(obj2._parent, parent_obj.tag)
        self.assertTrue(isinstance(obj2, ElementV2))
        self.assertEqual(parent_obj.tag, [obj1, obj2])

    def test__add_multiple(self):
        sub_cls = type('SubCls', (ElementV2, ), {'_tagname': 'tag1'})
        self.cls._elts += [sub_cls]

        parent_obj = FakeClass()
        parent_obj.list_cls = ElementListV2()
        obj1 = self.cls._add('tag', parent_obj)
        self.assertTrue(obj1._tagname, 'tag')
        self.assertEqual(obj1._parent, parent_obj.list_cls)
        self.assertTrue(isinstance(obj1, ElementV2))
        self.assertFalse(hasattr(parent_obj, 'tag'))
        self.assertEqual(parent_obj.list_cls, [obj1])

        obj2 = self.cls._add('tag1', parent_obj)
        self.assertTrue(obj2._tagname, 'tag1')
        self.assertEqual(obj2._parent, parent_obj.list_cls)
        self.assertTrue(isinstance(obj2, ElementV2))
        self.assertEqual(parent_obj.list_cls, [obj1, obj2])

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

        sub_cls = type('SubCls', (ElementV2, ), {'_tagname': 'tag1'})
        self.cls._elts += [sub_cls]
        obj = self.cls()
        obj._required = True
        lis = obj.to_xml()
        self.assertEqual(lis, [])

    def test__get_html_add_button(self):
        html = self.cls._get_html_add_button(None)
        expected = ('<a class="btn btn-add-ajax-list" '
                    'data-id="list_cls:0:tag">New tag</a>')
        self.assertEqual(html, expected)

        html = self.cls._get_html_add_button(['prefix'], 10, 'css_class')
        expected = ('<a class="btn btn-add-ajax-list css_class" '
                    'data-id="prefix:list_cls:10:tag">New tag</a>')
        self.assertEqual(html, expected)

        html = self.cls._get_html_add_button(['prefix'], 10, 'css_class')
        expected = ('<a class="btn btn-add-ajax-list css_class" '
                    'data-id="prefix:list_cls:10:tag">New tag</a>')
        self.assertEqual(html, expected)

    def test__get_html_add_button_multiple(self):
        sub_cls = type('SubCls', (ElementV2, ), {'_tagname': 'tag1'})
        self.cls._elts += [sub_cls]
        html = self.cls._get_html_add_button(None)
        expected = ('<select class="btn btn-add-ajax-choice-list">'
                    '<option>New tag/tag1</option>'
                    '<option value="list_cls:0:tag">tag</option>'
                    '<option value="list_cls:0:tag1">tag1</option>'
                    '</select>')
        self.assertEqual(html, expected)

    def test_to_html(self):
        obj = self.cls()
        html = obj.to_html()
        expected = ('<div class="list-container">'
                    '<a class="btn btn-add-ajax-list" '
                    'data-id="list_cls:0:tag">New tag</a>'
                    '</div>')
        self.assertEqual(html, expected)

        html = obj.to_html(partial=True)
        expected = ('<fieldset class="tag list_cls:0:tag">'
                    '<legend>tag'
                    '<a class="btn-delete-fieldset">Delete</a>'
                    '<a data-comment-name="list_cls:0:tag:_comment" '
                    'class="btn-comment">Comment</a>'
                    '</legend>'
                    '</fieldset>'
                    '<a class="btn btn-add-ajax-list" data-id="list_cls:1:tag">New tag</a>')
        self.assertEqual(html, expected)

        obj._required = True
        html = obj.to_html()
        expected = ('<div class="list-container">'
                    '<a class="btn btn-add-ajax-list" '
                    'data-id="list_cls:0:tag">New tag</a>'
                    '<fieldset class="tag list_cls:0:tag">'
                    '<legend>tag'
                    '<a class="btn-delete-fieldset">Delete</a>'
                    '<a data-comment-name="list_cls:0:tag:_comment" '
                    'class="btn-comment">Comment</a>'
                    '</legend>'
                    '</fieldset>'
                    '<a class="btn btn-add-ajax-list" '
                    'data-id="list_cls:1:tag">New tag</a>'
                    '</div>')
        self.assertEqual(html, expected)

        html = obj.to_html(offset=10)
        expected = ('<div class="list-container">'
                    '<a class="btn btn-add-ajax-list" '
                    'data-id="list_cls:10:tag">New tag</a>'
                    '<fieldset class="tag list_cls:10:tag">'
                    '<legend>tag'
                    '<a class="btn-delete-fieldset">Delete</a>'
                    '<a data-comment-name="list_cls:10:tag:_comment" '
                    'class="btn-comment">Comment</a>'
                    '</legend>'
                    '</fieldset>'
                    '<a class="btn btn-add-ajax-list" '
                    'data-id="list_cls:11:tag">New tag</a>'
                    '</div>')
        self.assertEqual(html, expected)


class TestMultipleElementV2(TestCase):

    def setUp(self):
        self.sub_cls1 = type('SubCls', (ElementV2, ), {'_tagname': 'tag1'})
        self.sub_cls2 = type('SubCls', (ElementV2, ), {'_tagname': 'tag2'})
        self.cls = type('Cls', (MultipleElementV2,),
                        {'_tagname': 'choice_cls',
                         '_sub_elements': [],
                         '_elts': [self.sub_cls1,
                                   self.sub_cls2]})

    def test__get_allowed_tagnames(self):
        self.assertEqual(self.cls._get_allowed_tagnames(), ['tag1', 'tag2'])

    def test__get_sub_element(self):
        self.assertEqual(self.cls._get_sub_element('tag1'), self.sub_cls1)
        self.assertEqual(self.cls._get_sub_element('tag2'), self.sub_cls2)

    def test__get_value_from_parent(self):
        parent_obj = FakeClass()
        obj1 = ElementV2()
        obj2 = ElementV2()
        self.assertTrue(obj1 != obj2)
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), None)
        parent_obj.tag2 = obj1
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj1)
        parent_obj.tag1 = obj2
        self.assertEqual(self.cls._get_value_from_parent(parent_obj), obj2)

    def test__get_sub_value(self):
        parent_obj = FakeClass()
        obj = ElementV2()
        result = self.cls._get_sub_value(parent_obj)
        self.assertFalse(result)
        self.cls._required = True
        result = self.cls._get_sub_value(parent_obj)
        self.assertFalse(result)
        parent_obj.tag1 = obj
        self.assertEqual(self.cls._get_sub_value(parent_obj), obj)

    def test__add(self):
        parent_obj = FakeClass()
        obj1 = self.cls._add('tag1', parent_obj)
        self.assertTrue(obj1._tagname, 'tag')
        self.assertEqual(obj1._parent, parent_obj)
        self.assertTrue(isinstance(obj1, ElementV2))
        self.assertEqual(parent_obj.tag1, obj1)

        try:
            self.cls._add('tag2', parent_obj)
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'tag1 already defined')

        try:
            self.cls._add('tag1', parent_obj)
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'tag1 already defined')

    def test__get_html_add_button(self):
        html = self.cls._get_html_add_button(None)
        expected = ('<select class="btn btn-add-ajax-choice">'
                    '<option>New tag1/tag2</option>'
                    '<option value="tag1">tag1</option>'
                    '<option value="tag2">tag2</option>'
                    '</select>')
        self.assertEqual(html, expected)

        html = self.cls._get_html_add_button(['prefix'], 10, 'css_class')
        expected = ('<select class="btn btn-add-ajax-choice css_class">'
                    '<option>New tag1/tag2</option>'
                    '<option value="prefix:10:tag1">tag1</option>'
                    '<option value="prefix:10:tag2">tag2</option>'
                    '</select>')
        self.assertEqual(html, expected)

    def test__to_html(self):
        parent_obj = ElementV2()
        html = self.cls._to_html(parent_obj)
        expected = (
            '<select class="btn btn-add-ajax-choice">'
            '<option>New tag1/tag2</option>'
            '<option value="tag1">tag1</option>'
            '<option value="tag2">tag2</option>'
            '</select>')
        self.assertEqual(html, expected)

        obj = self.cls()
        parent_obj.tag1 = obj
        html = self.cls._to_html(parent_obj)
        expected = (
            '<fieldset class="choice_cls">'
            '<legend>choice_cls'
            '<a data-comment-name="choice_cls:_comment" '
            'class="btn-comment">Comment</a>'
            '</legend>'
            '</fieldset>')
        self.assertEqual(html, expected)


class TestFunctions(TestCase):

    def test_get_obj_from_str(self):
        dtd_str = '''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:unexisting'
        try:
            html = get_obj_from_str(str_id, dtd_str=dtd_str)
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Unsupported tag unexisting')

        str_id = 'texts:text'
        html = get_obj_from_str(str_id, dtd_str=dtd_str)
        expected = (
            '<div>'
            '<label>text</label>'
            '<a data-comment-name="texts:text:_comment" '
            'class="btn-comment">Comment</a>'
            '<textarea name="texts:text:_value" id="texts:text" '
            'class="texts:text"></textarea>'
            '</div>')
        self.assertEqual(html, expected)

    def test_get_obj_from_str_list(self):
        dtd_str = '''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:list__text:0:text'
        html = get_obj_from_str(str_id, dtd_str=dtd_str)
        expected = ('<div>'
                    '<label>text</label>'
                    '<a class="btn-delete-list">Delete</a>'
                    '<a data-comment-name="texts:list__text:0:text:_comment" '
                    'class="btn-comment">Comment</a>'
                    '<textarea name="texts:list__text:0:text:_value" '
                    'id="texts:list__text:0:text" class="texts:list__text">'
                    '</textarea>'
                    '</div>'
                    '<a class="btn btn-add-ajax-list" '
                    'data-id="texts:list__text:1:text">New text</a>')
        self.assertEqual(html, expected)

        dtd_str = '''
        <!ELEMENT texts (list*)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:list__list:0:list:text'
        html = get_obj_from_str(str_id, dtd_str=dtd_str)
        expected = (
            '<div>'
            '<label>text</label>'
            '<a data-comment-name="texts:list__list:0:list:text:_comment" '
            'class="btn-comment">Comment</a>'
            '<textarea name="texts:list__list:0:list:text:_value" '
            'id="texts:list__list:0:list:text" '
            'class="texts:list__list:0:list:text"></textarea>'
            '</div>')
        self.assertEqual(html, expected)
