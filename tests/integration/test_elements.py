#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import tw2.core as twc
import tw2.core.testbase as tw2test
import os.path
from xmltool import dtd_parser, utils, factory
from xmltool.elements import (
    Element,
    ListElement,
    TextElement,
    ChoiceElement,
)
import xmltool.elements as elements
from ..test_dtd_parser import (
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


class ElementTester(TestCase):
    # Should be defined in the inheritance classes
    dtd_str = None
    xml = None
    expected_xml = None
    expected_html = _marker
    submit_data = None
    str_to_html = _marker
    js_selector = None

    def test_to_xml(self):
        if self.__class__ == ElementTester:
            return
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        tree = obj.to_xml()
        xml_str = etree.tostring(
            tree.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8',
        )
        if self.expected_xml:
            self.assertEqual(xml_str, self.expected_xml)
        else:
            self.assertEqual(xml_str, self.xml)

    def test_to_html(self):
        if self.__class__ == ElementTester:
            return
        if self.expected_html is None:
            return
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.to_html(), self.expected_html)

    def test_load_from_dict(self):
        if self.__class__ == ElementTester:
            return
        data = twc.validation.unflatten_params(self.submit_data)
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_dict(data)
        tree = obj.to_xml()
        xml_str = etree.tostring(
            tree.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8',
        )
        if self.expected_xml:
            self.assertEqual(xml_str, self.expected_xml)
        else:
            self.assertEqual(xml_str, self.xml)

    def test_get_obj_from_str(self):
        if self.__class__ == ElementTester:
            return
        if self.str_to_html is None:
            return
        for elt_str, expected_html in self.str_to_html:
            result = elements.get_obj_from_str_id(elt_str,
                                               dtd_str=self.dtd_str)
            self.assertEqual(result, expected_html)

    # TODO: add this when it works fine
    # def test_jstree(self):
    #     root = etree.fromstring(self.xml)
    #     dic = dtd_parser.parse(dtd_str=self.dtd_str)
    #     obj = dic[root.tag]()
    #     obj.load_from_xml(root)
    #     print obj.to_jstree_dict([])

    def test__get_previous_js_selectors(self):
        if self.__class__ == ElementTester:
            return
        if self.str_to_html is None:
            return
        for (elt_str, expected_html), selectors in zip(self.str_to_html,
                                                       self.js_selector):
            obj, prefixes, index = elements._get_obj_from_str_id(elt_str,
                                               dtd_str=self.dtd_str)
            lis = elements._get_previous_js_selectors(obj, prefixes, index)
            self.assertEqual(lis, selectors)


class TestElementPCDATA(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Hello world</text>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div data-id="texts:text">'
        '<label>text</label>'
        '<a data-comment-name="texts:text:_comment" class="btn-comment">'
        'Comment</a>'
        '<textarea name="texts:text:_value" id="texts:text" class="texts:text" rows="1">'
        'Hello world</textarea>'
        '</div>'
        '</fieldset>'
    )
    submit_data = {'texts:text:_value': 'Hello world'}

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div data-id="texts:text">'
         '<label>text</label>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:text:_value" id="texts:text" '
         'class="texts:text" rows="1"></textarea>'
         '</div>'
         '</fieldset>'
        ),
        ('texts:text',
         '<div data-id="texts:text">'
         '<label>text</label>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:text:_value" id="texts:text" '
         'class="texts:text" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._tagname, 'texts')
        self.assertEqual(obj._sourceline, 2)
        self.assertEqual(obj.text._value, 'Hello world')
        self.assertEqual(obj.text._sourceline, 3)

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)

        cls = classes['texts']
        obj = cls()
        text = obj.add('text')
        self.assertEqual(text._tagname, 'text')
        self.assertEqual(obj.text, text)


    def test_add_bad_child(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        try:
            obj.add('unexisiting')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Invalid child unexisiting')


class TestElementPCDATAEmpty(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div data-id="texts:text">'
        '<label>text</label>'
        '<a data-comment-name="texts:text:_comment" class="btn-comment">'
        'Comment</a>'
        '<textarea name="texts:text:_value" id="texts:text" class="texts:text" rows="1">'
        '</textarea>'
        '</div>'
        '</fieldset>'
    )
    submit_data = {}

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div data-id="texts:text">'
         '<label>text</label>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:text:_value" id="texts:text" '
         'class="texts:text" rows="1"></textarea>'
         '</div>'
         '</fieldset>'
        ),
        ('texts:text',
         '<div data-id="texts:text">'
         '<label>text</label>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:text:_value" id="texts:text" '
         'class="texts:text" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]


class TestElementPCDATANotRequired(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Hello world</text>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div data-id="texts:text">'
        '<label>text</label>'
        '<a class="btn btn-add-ajax hidden" data-id="texts:text">Add text</a>'
        '<a class="btn-delete">Delete</a>'
        '<a data-comment-name="texts:text:_comment" class="btn-comment">'
        'Comment</a>'
        '<textarea name="texts:text:_value" id="texts:text" '
        'class="texts:text" rows="1">Hello world</textarea>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {'texts:text:_value': 'Hello world'}

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<a class="btn btn-add-ajax" data-id="texts:text">Add text</a>'
         '</fieldset>'
        ),
        ('texts:text',
         '<div data-id="texts:text">'
         '<label>text</label>'
         '<a class="btn btn-add-ajax hidden" data-id="texts:text">Add text</a>'
         '<a class="btn-delete">Delete</a>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:text:_value" id="texts:text" '
         'class="texts:text" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]


class TestElementPCDATAEmptyNotRequired(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<a class="btn btn-add-ajax" data-id="texts:text">Add text</a>'
        '</fieldset>'
    )
    submit_data = {}

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<a class="btn btn-add-ajax" data-id="texts:text">Add text</a>'
         '</fieldset>'
        ),
        ('texts:text',
         '<div data-id="texts:text">'
         '<label>text</label>'
         '<a class="btn btn-add-ajax hidden" data-id="texts:text">Add text</a>'
         '<a class="btn-delete">Delete</a>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:text:_value" id="texts:text" '
         'class="texts:text" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]


class TestElementPCDATAEmptyNotRequiredDefined(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div data-id="texts:text">'
        '<label>text</label>'
        '<a class="btn btn-add-ajax hidden" data-id="texts:text">Add text</a>'
        '<a class="btn-delete">Delete</a>'
        '<a data-comment-name="texts:text:_comment" class="btn-comment">'
        'Comment</a>'
        '<textarea name="texts:text:_value" id="texts:text" '
        'class="texts:text" rows="1"></textarea>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {'texts:text:_value': ''}

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<a class="btn btn-add-ajax" data-id="texts:text">Add text</a>'
         '</fieldset>'
        ),
        ('texts:text',
         '<div data-id="texts:text">'
         '<label>text</label>'
         '<a class="btn btn-add-ajax hidden" data-id="texts:text">Add text</a>'
         '<a class="btn-delete">Delete</a>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:text:_value" id="texts:text" '
         'class="texts:text" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]

class TestListElement(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Tag 1</text>
  <text>Tag 2</text>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:0:text">New text</a>'
        '<div data-id="texts:list__text:0:text">'
        '<label>text</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text:0:text:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text:0:text:_value" '
        'id="texts:list__text:0:text" class="texts:list__text" rows="1">'
        'Tag 1</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:1:text">New text</a>'
        '<div data-id="texts:list__text:1:text">'
        '<label>text</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text:1:text:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text:1:text:_value" '
        'id="texts:list__text:1:text" class="texts:list__text" rows="1">'
        'Tag 2</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:2:text">New text</a>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {
        'texts:list__text:0:text:_value': 'Tag 1',
        'texts:list__text:1:text:_value': 'Tag 2',
    }

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div class="list-container">'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:0:text">New text</a>'
         '<div data-id="texts:list__text:0:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:0:text:_value" '
         'id="texts:list__text:0:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:1:text">New text</a>'
         '</div>'
         '</fieldset>'
        ),
        ('texts:list__text:0:text',
         '<div data-id="texts:list__text:0:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:0:text:_value" '
         'id="texts:list__text:0:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:1:text">New text</a>'
        ),
        ('texts:list__text:10:text',
         '<div data-id="texts:list__text:10:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:10:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:10:text:_value" '
         'id="texts:list__text:10:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:11:text">New text</a>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', '.tree_texts:list__text:9')],
    ]

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        text1 = obj.add('text')
        self.assertEqual(text1._tagname, 'text')
        self.assertEqual(len(obj.text), 1)
        self.assertEqual(obj.text[0], text1)

        text2 = obj.add('text')
        self.assertEqual(text2._tagname, 'text')
        self.assertEqual(len(obj.text), 2)
        self.assertEqual(obj.text[1], text2)

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._tagname, 'texts')
        self.assertEqual(obj._sourceline, 2)
        self.assertEqual(obj.text[0]._value, 'Tag 1')
        self.assertEqual(obj.text[0]._sourceline, 3)
        self.assertEqual(obj.text[1]._value, 'Tag 2')
        self.assertEqual(obj.text[1]._sourceline, 4)


class TestListElementEmpty(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''

    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:0:text">New text</a>'
        '<div data-id="texts:list__text:0:text">'
        '<label>text</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text:0:text:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text:0:text:_value" '
        'id="texts:list__text:0:text" class="texts:list__text" rows="1">'
        '</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:1:text">New text</a>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {}

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div class="list-container">'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:0:text">New text</a>'
         '<div data-id="texts:list__text:0:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:0:text:_value" '
         'id="texts:list__text:0:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:1:text">New text</a>'
         '</div>'
         '</fieldset>'
        ),
        ('texts:list__text:0:text',
         '<div data-id="texts:list__text:0:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:0:text:_value" '
         'id="texts:list__text:0:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:1:text">New text</a>'
        ),
        ('texts:list__text:10:text',
         '<div data-id="texts:list__text:10:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:10:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:10:text:_value" '
         'id="texts:list__text:10:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:11:text">New text</a>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', '.tree_texts:list__text:9')],
    ]


class TestListElementNotRequired(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Tag 1</text>
  <text>Tag 2</text>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:0:text">New text</a>'
        '<div data-id="texts:list__text:0:text">'
        '<label>text</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text:0:text:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text:0:text:_value" '
        'id="texts:list__text:0:text" class="texts:list__text" rows="1">'
        'Tag 1</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:1:text">New text</a>'
        '<div data-id="texts:list__text:1:text">'
        '<label>text</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text:1:text:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text:1:text:_value" '
        'id="texts:list__text:1:text" class="texts:list__text" rows="1">'
        'Tag 2</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:2:text">New text</a>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {
        'texts:list__text:0:text:_value': 'Tag 1',
        'texts:list__text:1:text:_value': 'Tag 2',
    }

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div class="list-container">'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:0:text">New text</a>'
         '</div>'
         '</fieldset>'
        ),
        ('texts:list__text:0:text',
         '<div data-id="texts:list__text:0:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:0:text:_value" '
         'id="texts:list__text:0:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:1:text">New text</a>'
        ),
        ('texts:list__text:10:text',
         '<div data-id="texts:list__text:10:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:10:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:10:text:_value" '
         'id="texts:list__text:10:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:11:text">New text</a>'
        )
    ]
    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', '.tree_texts:list__text:9')],
    ]


class TestListElementEmptyNotRequired(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" '
        'class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text:0:text">New text</a>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {}

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div class="list-container">'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:0:text">New text</a>'
         '</div>'
         '</fieldset>'
        ),
        ('texts:list__text:0:text',
         '<div data-id="texts:list__text:0:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:0:text:_value" '
         'id="texts:list__text:0:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:1:text">New text</a>'
        ),
        ('texts:list__text:10:text',
         '<div data-id="texts:list__text:10:text">'
         '<label>text</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text:10:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:10:text:_value" '
         'id="texts:list__text:10:text" class="texts:list__text" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text:11:text">New text</a>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', '.tree_texts:list__text:9')],
    ]


class TestListElementElementEmpty(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (subtext)>
        <!ELEMENT subtext (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>
    <subtext></subtext>
  </text>
</texts>
'''

    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" data-id="texts:list__text:0:text">'
        'New text</a>'
        '<fieldset class="text texts:list__text:0:text" id="texts:list__text:0:text">'
        '<legend>text'
        '<a data-comment-name="texts:list__text:0:text:_comment" '
        'class="btn-comment">Comment</a>'
        '<a class="btn-delete-fieldset">Delete</a>'
        '</legend>'
        '<div data-id="texts:list__text:0:text:subtext">'
        '<label>subtext</label>'
        '<a data-comment-name="texts:list__text:0:text:subtext:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text:0:text:subtext:_value" '
        'id="texts:list__text:0:text:subtext" '
        'class="texts:list__text:0:text:subtext" rows="1"></textarea>'
        '</div>'
        '</fieldset>'
        '<a class="btn btn-add-ajax-list" data-id="texts:list__text:1:text">'
        'New text</a>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {}

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">'
         'Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div class="list-container">'
         '<a class="btn btn-add-ajax-list" data-id="texts:list__text:0:text">'
         'New text</a>'
         '<fieldset class="text texts:list__text:0:text" id="texts:list__text:0:text">'
         '<legend>text'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div data-id="texts:list__text:0:text:subtext">'
         '<label>subtext</label>'
         '<a data-comment-name="texts:list__text:0:text:subtext:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:0:text:subtext:_value" '
         'id="texts:list__text:0:text:subtext" '
         'class="texts:list__text:0:text:subtext" rows="1"></textarea>'
         '</div>'
         '</fieldset>'
         '<a class="btn btn-add-ajax-list" data-id="texts:list__text:1:text">'
         'New text</a>'
         '</div>'
         '</fieldset>'
        ),
        ('texts:list__text:1:text',
         '<fieldset class="text texts:list__text:1:text" id="texts:list__text:1:text">'
         '<legend>text'
         '<a data-comment-name="texts:list__text:1:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div data-id="texts:list__text:1:text:subtext">'
         '<label>subtext</label>'
         '<a data-comment-name="texts:list__text:1:text:subtext:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text:1:text:subtext:_value" '
         'id="texts:list__text:1:text:subtext" '
         'class="texts:list__text:1:text:subtext" rows="1"></textarea>'
         '</div>'
         '</fieldset>'
         '<a class="btn btn-add-ajax-list" data-id="texts:list__text:2:text">'
         'New text</a>'
        )
    ]

    js_selector = [
        [],
        [('after', '.tree_texts:list__text:0')],
        [('after', '.tree_texts:list__text:9')],
    ]


choice_str_to_html = [
    ('texts',
     '<fieldset class="texts" id="texts">'
     '<legend>texts'
     '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
     '<a class="btn-delete-fieldset">Delete</a>'
     '</legend>'
     '<select class="btn btn-add-ajax-choice">'
     '<option>New text1/text2</option>'
     '<option value="texts:text1">text1</option>'
     '<option value="texts:text2">text2</option>'
     '</select>'
     '</fieldset>'
    ),
    ('texts:text1',
     '<div data-id="texts:text1">'
     '<label>text1</label>'
     '<select class="btn btn-add-ajax-choice hidden">'
     '<option>New text1/text2</option>'
     '<option value="texts:text1">text1</option>'
     '<option value="texts:text2">text2</option>'
     '</select>'
     '<a class="btn-delete">Delete</a>'
     '<a data-comment-name="texts:text1:_comment" class="btn-comment">'
     'Comment</a>'
     '<textarea name="texts:text1:_value" id="texts:text1" '
     'class="texts:text1" rows="1"></textarea>'
     '</div>'
    )
]

choice_js_selector = [
        [],
        [('inside', '#tree_texts')],
    ]


class TestElementChoice(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text1|text2)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div data-id="texts:text1">'
        '<label>text1</label>'
        '<select class="btn btn-add-ajax-choice hidden">'
        '<option>New text1/text2</option>'
        '<option value="texts:text1">text1</option>'
        '<option value="texts:text2">text2</option>'
        '</select>'
        '<a class="btn-delete">Delete</a>'
        '<a data-comment-name="texts:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:text1:_value" '
        'id="texts:text1" class="texts:text1" rows="1">Tag 1</textarea>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {
        'texts:text1:_value': 'Tag 1',
    }

    str_to_html = choice_str_to_html
    js_selector = choice_js_selector

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        text1 = obj.add('text1')
        self.assertEqual(text1._tagname, 'text1')
        self.assertEqual(obj.text1, text1)

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._tagname, 'texts')
        self.assertEqual(obj._sourceline, 2)
        self.assertEqual(obj.text1._value, 'Tag 1')
        self.assertEqual(obj.text1._sourceline, 3)
        self.assertFalse(hasattr(obj, 'text2'))

        xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text2>Tag 2</text2>
</texts>'''
        root = etree.fromstring(xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._tagname, 'texts')
        self.assertEqual(obj._sourceline, 2)
        self.assertEqual(obj.text2._value, 'Tag 2')
        self.assertEqual(obj.text2._sourceline, 3)
        self.assertFalse(hasattr(obj, 'text1'))


class TestElementChoiceEmpty(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text1|text2)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" '
        'class="btn-comment">Comment</a>'
        '</legend>'
        '<select class="btn btn-add-ajax-choice">'
        '<option>New text1/text2</option>'
        '<option value="texts:text1">text1</option>'
        '<option value="texts:text2">text2</option>'
        '</select>'
        '</fieldset>'
    )

    submit_data = {}
    str_to_html = choice_str_to_html
    js_selector = choice_js_selector



class TestElementChoiceNotRequired(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text1|text2)?>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div data-id="texts:text1">'
        '<label>text1</label>'
        '<select class="btn btn-add-ajax-choice hidden">'
        '<option>'
        'New text1/text2</option>'
        '<option value="texts:text1">'
        'text1</option>'
        '<option value="texts:text2">'
        'text2</option>'
        '</select>'
        '<a class="btn-delete">Delete</a>'
        '<a data-comment-name="texts:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:text1:_value" '
        'id="texts:text1" class="texts:text1" rows="1">Tag 1</textarea>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {
        'texts:text1:_value': 'Tag 1',
    }
    str_to_html = choice_str_to_html
    js_selector = choice_js_selector


class TestElementChoiceEmptyNotRequired(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text1|text2)?>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" '
        'class="btn-comment">Comment</a>'
        '</legend>'
        '<select class="btn btn-add-ajax-choice">'
        '<option>New text1/text2</option>'
        '<option value="texts:text1">text1</option>'
        '<option value="texts:text2">text2</option>'
        '</select>'
        '</fieldset>'
    )

    submit_data = {}
    str_to_html = choice_str_to_html
    js_selector = choice_js_selector



choicelist_str_to_html = [
    ('texts',
     '<fieldset class="texts" id="texts">'
     '<legend>texts'
     '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
     '<a class="btn-delete-fieldset">Delete</a>'
     '</legend>'
     '<div class="list-container">'
     '<select class="btn btn-add-ajax-choice-list">'
     '<option>New text1/text2</option>'
     '<option value="texts:list__text1_text2:0:text1">text1</option>'
     '<option value="texts:list__text1_text2:0:text2">text2</option>'
     '</select>'
     '</div>'
     '</fieldset>'
    ),
    ('texts:list__text1_text2:0:text1',
     '<div data-id="texts:list__text1_text2:0:text1">'
     '<label>text1</label>'
     '<a class="btn-delete-list">Delete</a>'
     '<a data-comment-name="texts:list__text1_text2:0:text1:_comment" '
     'class="btn-comment">Comment</a>'
     '<textarea name="texts:list__text1_text2:0:text1:_value" '
     'id="texts:list__text1_text2:0:text1" '
     'class="texts:list__text1_text2" rows="1"></textarea>'
     '</div>'
     '<select class="btn btn-add-ajax-choice-list">'
     '<option>New text1/text2</option>'
     '<option value="texts:list__text1_text2:1:text1">text1</option>'
     '<option value="texts:list__text1_text2:1:text2">text2</option>'
     '</select>'
    ),
    ('texts:list__text1_text2:10:text1',
     '<div data-id="texts:list__text1_text2:10:text1">'
     '<label>text1</label>'
     '<a class="btn-delete-list">Delete</a>'
     '<a data-comment-name="texts:list__text1_text2:10:text1:_comment" '
     'class="btn-comment">Comment</a>'
     '<textarea name="texts:list__text1_text2:10:text1:_value" '
     'id="texts:list__text1_text2:10:text1" '
     'class="texts:list__text1_text2" rows="1"></textarea>'
     '</div>'
     '<select class="btn btn-add-ajax-choice-list">'
     '<option>New text1/text2</option>'
     '<option value="texts:list__text1_text2:11:text1">text1</option>'
     '<option value="texts:list__text1_text2:11:text2">text2</option>'
     '</select>'
    )
]

choice_list_js_selector = [
        [],
        [('inside', '#tree_texts')],
    ]

class TestElementChoiceList(ElementTester):
    dtd_str = '''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
  <text2>Tag 2</text2>
  <text1>Tag 3</text1>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:0:text1">text1</option>'
        '<option value="texts:list__text1_text2:0:text2">text2</option>'
        '</select>'
        '<div data-id="texts:list__text1_text2:0:text1">'
        '<label>text1</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1_text2:0:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1_text2:0:text1:_value" '
        'id="texts:list__text1_text2:0:text1" '
        'class="texts:list__text1_text2" rows="1">Tag 1</textarea>'
        '</div>'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:1:text1">text1</option>'
        '<option value="texts:list__text1_text2:1:text2">text2</option>'
        '</select>'
        '<div data-id="texts:list__text1_text2:1:text2">'
        '<label>text2</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1_text2:1:text2:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1_text2:1:text2:_value" '
        'id="texts:list__text1_text2:1:text2" '
        'class="texts:list__text1_text2" rows="1">Tag 2</textarea>'
        '</div>'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:2:text1">text1</option>'
        '<option value="texts:list__text1_text2:2:text2">text2</option>'
        '</select>'
        '<div data-id="texts:list__text1_text2:2:text1">'
        '<label>text1</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1_text2:2:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1_text2:2:text1:_value" '
        'id="texts:list__text1_text2:2:text1" '
        'class="texts:list__text1_text2" rows="1">Tag 3</textarea>'
        '</div>'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:3:text1">text1</option>'
        '<option value="texts:list__text1_text2:3:text2">text2</option>'
        '</select>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {
        'texts:list__text1_text2:0:text1:_value': 'Tag 1',
        'texts:list__text1_text2:1:text2:_value': 'Tag 2',
        'texts:list__text1_text2:2:text1:_value': 'Tag 3',
    }
    str_to_html = choicelist_str_to_html
    js_selector = choice_list_js_selector


    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        text1 = obj.add('text1')
        self.assertEqual(obj.list__text1_text2, [text1])
        text2 = obj.add('text2')
        self.assertEqual(obj.list__text1_text2, [text1, text2])

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._tagname, 'texts')
        self.assertEqual(obj._sourceline, 2)
        self.assertEqual(obj.list__text1_text2[0]._value, 'Tag 1')
        self.assertEqual(obj.list__text1_text2[0]._sourceline, 3)
        self.assertEqual(obj.list__text1_text2[1]._value, 'Tag 2')
        self.assertEqual(obj.list__text1_text2[1]._sourceline, 4)
        self.assertEqual(obj.list__text1_text2[2]._value, 'Tag 3')
        self.assertEqual(obj.list__text1_text2[2]._sourceline, 5)


class TestElementChoiceListEmpty(ElementTester):
    dtd_str = '''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:0:text1">text1</option>'
        '<option value="texts:list__text1_text2:0:text2">text2</option>'
        '</select>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {}
    str_to_html = choicelist_str_to_html
    js_selector = choice_list_js_selector


class TestElementChoiceListNotRequired(ElementTester):
    dtd_str = '''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
  <text2>Tag 2</text2>
  <text1>Tag 3</text1>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:0:text1">text1</option>'
        '<option value="texts:list__text1_text2:0:text2">text2</option>'
        '</select>'
        '<div data-id="texts:list__text1_text2:0:text1">'
        '<label>text1</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1_text2:0:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1_text2:0:text1:_value" '
        'id="texts:list__text1_text2:0:text1" '
        'class="texts:list__text1_text2" rows="1">Tag 1</textarea>'
        '</div>'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:1:text1">text1</option>'
        '<option value="texts:list__text1_text2:1:text2">text2</option>'
        '</select>'
        '<div data-id="texts:list__text1_text2:1:text2">'
        '<label>text2</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1_text2:1:text2:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1_text2:1:text2:_value" '
        'id="texts:list__text1_text2:1:text2" '
        'class="texts:list__text1_text2" rows="1">Tag 2</textarea>'
        '</div>'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:2:text1">text1</option>'
        '<option value="texts:list__text1_text2:2:text2">text2</option>'
        '</select>'
        '<div data-id="texts:list__text1_text2:2:text1">'
        '<label>text1</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1_text2:2:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1_text2:2:text1:_value" '
        'id="texts:list__text1_text2:2:text1" '
        'class="texts:list__text1_text2" rows="1">Tag 3</textarea>'
        '</div>'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:3:text1">text1</option>'
        '<option value="texts:list__text1_text2:3:text2">text2</option>'
        '</select>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {
        'texts:list__text1_text2:0:text1:_value': 'Tag 1',
        'texts:list__text1_text2:1:text2:_value': 'Tag 2',
        'texts:list__text1_text2:2:text1:_value': 'Tag 3',
    }

    str_to_html = choicelist_str_to_html
    js_selector = choice_list_js_selector


class TestElementChoiceListEmptyNotRequired(ElementTester):
    dtd_str = '''
        <!ELEMENT texts ((text1|text2)*)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<select class="btn btn-add-ajax-choice-list">'
        '<option>New text1/text2</option>'
        '<option value="texts:list__text1_text2:0:text1">text1</option>'
        '<option value="texts:list__text1_text2:0:text2">text2</option>'
        '</select>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {}
    str_to_html = choicelist_str_to_html
    js_selector = choice_list_js_selector


class TestListElementOfList(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text1*)>
        <!ELEMENT text1 (text2+)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>
    <text2>text2-1</text2>
    <text2>text2-2</text2>
  </text1>
  <text1>
    <text2>text2-3</text2>
  </text1>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text1:0:text1">New text1</a>'
        '<fieldset class="text1 texts:list__text1:0:text1" id="texts:list__text1:0:text1">'
        '<legend>text1'
        '<a data-comment-name="texts:list__text1:0:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<a class="btn-delete-fieldset">Delete</a>'
        '</legend>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text1:0:text1:list__text2:0:text2">New text2</a>'
        '<div data-id="texts:list__text1:0:text1:list__text2:0:text2">'
        '<label>text2</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1:0:text1:list__text2:0:text2:'
        '_comment" class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1:0:text1:list__text2:0:text2:_value" '
        'id="texts:list__text1:0:text1:list__text2:0:text2" '
        'class="texts:list__text1:0:text1:list__text2" rows="1">text2-1</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text1:0:text1:list__text2:1:text2">New text2</a>'
        '<div data-id="texts:list__text1:0:text1:list__text2:1:text2">'
        '<label>text2</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1:0:text1:list__text2:1:text2'
        ':_comment" class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1:0:text1:list__text2:1:text2:_value" '
        'id="texts:list__text1:0:text1:list__text2:1:text2" '
        'class="texts:list__text1:0:text1:list__text2" rows="1">text2-2</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text1:0:text1:list__text2:2:text2">New text2</a>'
        '</div>'
        '</fieldset>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text1:1:text1">New text1</a>'
        '<fieldset class="text1 texts:list__text1:1:text1" id="texts:list__text1:1:text1">'
        '<legend>text1'
        '<a data-comment-name="texts:list__text1:1:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<a class="btn-delete-fieldset">Delete</a>'
        '</legend>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" data-id="texts:list__text1:1:text1:'
        'list__text2:0:text2">New text2</a>'
        '<div data-id="texts:list__text1:1:text1:list__text2:0:text2">'
        '<label>text2</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1:1:text1:list__text2:0:text2:'
        '_comment" class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1:1:text1:list__text2:0:text2:_value" '
        'id="texts:list__text1:1:text1:list__text2:0:text2" '
        'class="texts:list__text1:1:text1:list__text2" rows="1">text2-3</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text1:1:text1:list__text2:1:text2">New text2</a>'
        '</div>'
        '</fieldset>'
        '<a class="btn btn-add-ajax-list" '
        'data-id="texts:list__text1:2:text1">New text1</a>'
        '</div>'
        '</fieldset>'
    )

    submit_data = {
        'texts:list__text1:0:text1:list__text2:0:text2:_value': 'text2-1',
        'texts:list__text1:0:text1:list__text2:1:text2:_value': 'text2-2',
        'texts:list__text1:1:text1:list__text2:0:text2:_value': 'text2-3',
    }
    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div class="list-container">'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text1:0:text1">New text1</a>'
         '</div>'
         '</fieldset>'
        ),
        ('texts:list__text1:0:text1',
         '<fieldset class="text1 texts:list__text1:0:text1" id="texts:list__text1:0:text1">'
         '<legend>'
         'text1'
         '<a data-comment-name="texts:list__text1:0:text1:_comment" '
         'class="btn-comment">Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div class="list-container">'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text1:0:text1:list__text2:0:text2">New text2</a>'
         '<div data-id="texts:list__text1:0:text1:list__text2:0:text2">'
         '<label>text2</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text1:0:text1:list__text2:0:'
         'text2:_comment" class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text1:0:text1:list__text2:0:text2:'
         '_value" id="texts:list__text1:0:text1:list__text2:0:text2" '
         'class="texts:list__text1:0:text1:list__text2" rows="1"></textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text1:0:text1:list__text2:1:text2">'
         'New text2</a>'
         '</div>'
         '</fieldset>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text1:1:text1">New text1</a>'
        ),
        ('texts:list__text1:0:text1:list__text2:3:text2',
         '<div data-id="texts:list__text1:0:text1:list__text2:3:text2">'
         '<label>text2</label>'
         '<a class="btn-delete-list">Delete</a>'
         '<a data-comment-name="texts:list__text1:0:text1:list__text2:3:'
         'text2:_comment" class="btn-comment">Comment</a>'
         '<textarea name="texts:list__text1:0:text1:list__text2:3:text2:_value" '
         'id="texts:list__text1:0:text1:list__text2:3:text2" '
         'class="texts:list__text1:0:text1:list__text2" rows="1">'
         '</textarea>'
         '</div>'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text1:0:text1:list__text2:4:text2">New text2</a>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', '.tree_texts:list__text1:0:text1:list__text2:2')],
    ]


class TestElementWithAttributes(ElementTester):
    dtd_str = '''
        <!ELEMENT texts (text, text1*)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT text1 (#PCDATA)>

        <!ATTLIST texts idtexts ID #IMPLIED>
        <!ATTLIST texts name ID #IMPLIED>
        <!ATTLIST text idtext ID #IMPLIED>
        <!ATTLIST text1 idtext1 ID #IMPLIED>
        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts idtexts="id_texts" name="my texts">
  <text idtext="id_text">Hello world</text>
  <text1 idtext1="id_text1_1">My text 1</text1>
  <text1>My text 2</text1>
</texts>
'''
    expected_html = (
        '<fieldset class="texts" id="texts">'
        '<legend>texts'
        '<a data-comment-name="texts:_comment" class="btn-comment">Comment</a>'
        '</legend>'
        '<input value="id_texts" name="texts:_attrs:idtexts" '
        'id="texts:_attrs:idtexts" class="_attrs" />'
        '<input value="my texts" name="texts:_attrs:name" '
        'id="texts:_attrs:name" class="_attrs" />'
        '<div data-id="texts:text">'
        '<label>text</label>'
        '<a data-comment-name="texts:text:_comment" '
        'class="btn-comment">Comment</a>'
        '<input value="id_text" name="texts:text:_attrs:idtext" '
        'id="texts:text:_attrs:idtext" class="_attrs" />'
        '<textarea name="texts:text:_value" id="texts:text" '
        'class="texts:text" rows="1">Hello world</textarea>'
        '</div>'
        '<div class="list-container">'
        '<a class="btn btn-add-ajax-list" data-id="texts:list__text1:0:text1">'
        'New text1</a>'
        '<div data-id="texts:list__text1:0:text1">'
        '<label>text1</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1:0:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<input value="id_text1_1" '
        'name="texts:list__text1:0:text1:_attrs:idtext1" '
        'id="texts:list__text1:0:text1:_attrs:idtext1" '
        'class="_attrs" />'
        '<textarea name="texts:list__text1:0:text1:_value" '
        'id="texts:list__text1:0:text1" class="texts:list__text1" rows="1">'
        'My text 1</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" data-id="texts:list__text1:1:text1">'
        'New text1</a>'
        '<div data-id="texts:list__text1:1:text1">'
        '<label>text1</label>'
        '<a class="btn-delete-list">Delete</a>'
        '<a data-comment-name="texts:list__text1:1:text1:_comment" '
        'class="btn-comment">Comment</a>'
        '<textarea name="texts:list__text1:1:text1:_value" '
        'id="texts:list__text1:1:text1" class="texts:list__text1" rows="1">'
        'My text 2</textarea>'
        '</div>'
        '<a class="btn btn-add-ajax-list" data-id="texts:list__text1:2:text1">'
        'New text1</a>'
        '</div>'
        '</fieldset>'
    )

    str_to_html = [
        ('texts',
         '<fieldset class="texts" id="texts">'
         '<legend>texts'
         '<a data-comment-name="texts:_comment" class="btn-comment">'
         'Comment</a>'
         '<a class="btn-delete-fieldset">Delete</a>'
         '</legend>'
         '<div data-id="texts:text">'
         '<label>text</label>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment">Comment</a>'
         '<textarea name="texts:text:_value" id="texts:text" '
         'class="texts:text" rows="1"></textarea>'
         '</div>'
         '<div class="list-container">'
         '<a class="btn btn-add-ajax-list" '
         'data-id="texts:list__text1:0:text1">New text1</a>'
         '</div>'
         '</fieldset>')
    ]

    js_selector = [
        [],
    ]

    submit_data = {
        'texts:_attrs:idtexts': 'id_texts',
        'texts:_attrs:name': 'my texts',
        'texts:text:_value': 'Hello world',
        'texts:text:_attrs:idtext': 'id_text',
        'texts:list__text1:0:text1:_value': 'My text 1',
        'texts:list__text1:0:text1:_attrs:idtext1': 'id_text1_1',
        'texts:list__text1:1:text1:_value': 'My text 2',
    }

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._attribute_names, ['idtexts', 'name'])
        self.assertEqual(obj._attributes, {
            'idtexts': 'id_texts',
            'name': 'my texts',
        })
        self.assertEqual(obj.text._attribute_names, ['idtext'])
        self.assertEqual(obj.text._attributes, {
            'idtext': 'id_text',
        })
        self.assertEqual(obj.text1[0]._attribute_names, ['idtext1'])
        self.assertEqual(obj.text1[0]._attributes, {
            'idtext1': 'id_text1_1',
        })
        self.assertEqual(obj.text1[1]._attribute_names, ['idtext1'])
        self.assertEqual(obj.text1[1]._attributes, None)

    def test_walk(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = [e for e in obj.walk()]
        expected = [obj.text] + obj.text1
        self.assertEqual(lis, expected)


class TestElementComments(ElementTester):
    dtd_str = MOVIE_DTD
    xml = MOVIE_XML_TITANIC_COMMENTS

    expected_html = None

    submit_data = {
        'Movie:_comment': ' Movie comment ',
        'Movie:name:_value': 'Titanic',
        'Movie:name:_comment': ' name comment ',
        'Movie:year:_value': '1997',
        'Movie:year:_comment': ' year comment ',
        'Movie:directors:_comment': ' directors comment ',
        'Movie:directors:list__director:0:director:_comment': ' director comment ',
        'Movie:directors:list__director:0:director:name:_value': 'Cameron',
        'Movie:directors:list__director:0:director:name:_comment': ' director name comment ',
        'Movie:directors:list__director:0:director:firstname:_value': 'James',
        'Movie:directors:list__director:0:director:firstname:_comment': ' director firstname comment ',
        'Movie:actors:_comment': ' actors comment ',
        'Movie:actors:list__actor:0:actor:_comment': ' actor 1 comment ',
        'Movie:actors:list__actor:0:actor:name:_value': 'DiCaprio',
        'Movie:actors:list__actor:0:actor:name:_comment': ' actor 1 name comment ',
        'Movie:actors:list__actor:0:actor:firstname:_value': 'Leonardo',
        'Movie:actors:list__actor:0:actor:firstname:_comment': ' actor 1 firstname comment ',
        'Movie:actors:list__actor:1:actor:_comment': ' actor 2 comment ',
        'Movie:actors:list__actor:1:actor:name:_value': 'Winslet',
        'Movie:actors:list__actor:1:actor:name:_comment': ' actor 2 name comment ',
        'Movie:actors:list__actor:1:actor:firstname:_value': 'Kate',
        'Movie:actors:list__actor:1:actor:firstname:_comment': ' actor 2 firstname comment ',
        'Movie:actors:list__actor:2:actor:_comment': ' actor 3 comment ',
        'Movie:actors:list__actor:2:actor:name:_value': 'Zane',
        'Movie:actors:list__actor:2:actor:name:_comment': ' actor 3 name comment ',
        'Movie:actors:list__actor:2:actor:firstname:_value': 'Billy',
        'Movie:actors:list__actor:2:actor:firstname:_comment': ' actor 3 firstname comment ',
        'Movie:resume:_comment': ' resume comment ',
        'Movie:resume:_value': '\n     Resume of the movie\n  ',
        'Movie:list__critique:0:critique:_comment': ' critique 1 comment ',
        'Movie:list__critique:0:critique:_value': 'critique1',
        'Movie:list__critique:1:critique:_comment': ' critique 2 comment ',
        'Movie:list__critique:1:critique:_value': 'critique2',
    }
    str_to_html = None

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._sourceline, 3)
        self.assertEqual(obj.name._value, 'Titanic')
        self.assertEqual(obj.name._comment, ' name comment ')
        self.assertEqual(obj.name._sourceline, 5)
        self.assertEqual(obj.resume._value, '\n     Resume of the movie\n  ')
        self.assertEqual(obj.resume._comment, ' resume comment ')
        self.assertEqual(obj.resume._sourceline, 43)
        self.assertEqual(obj.year._value, '1997')
        self.assertEqual(obj.year._comment, ' year comment ')
        self.assertEqual(obj.year._sourceline, 7)
        self.assertEqual([c._value for c in obj.critique], ['critique1', 'critique2'])
        self.assertEqual(obj.critique[0]._comment, ' critique 1 comment ')
        self.assertEqual(obj.critique[1]._comment, ' critique 2 comment ')
        self.assertEqual(len(obj.actors.actor), 3)
        self.assertEqual(len(obj.directors.director), 1)
        self.assertEqual(obj.actors._comment, ' actors comment ')
        self.assertEqual(obj.actors.actor[0]._sourceline, 21)
        self.assertEqual(obj.actors.actor[0]._comment, ' actor 1 comment ')
        self.assertEqual(obj.actors.actor[0].name._value, 'DiCaprio')
        self.assertEqual(obj.actors.actor[0].name._comment,
                         ' actor 1 name comment ')
        self.assertEqual(obj.actors.actor[0].name._sourceline, 23)
        self.assertEqual(obj.actors.actor[0].firstname._value, 'Leonardo')
        self.assertEqual(obj.actors.actor[0].firstname._comment,
                         ' actor 1 firstname comment ')
        self.assertEqual(obj.actors.actor[1]._comment, ' actor 2 comment ')
        self.assertEqual(obj.actors.actor[1].name._value, 'Winslet')
        self.assertEqual(obj.actors.actor[1].name._comment,
                         ' actor 2 name comment ')
        self.assertEqual(obj.actors.actor[1].firstname._value, 'Kate')
        self.assertEqual(obj.actors.actor[1].firstname._comment,
                         ' actor 2 firstname comment ')
        self.assertEqual(obj.actors.actor[2]._comment,
                         ' actor 3 comment ')
        self.assertEqual(obj.actors.actor[2].name._value, 'Zane')
        self.assertEqual(obj.actors.actor[2].name._comment,
                         ' actor 3 name comment ')
        self.assertEqual(obj.actors.actor[2].firstname._value, 'Billy')
        self.assertEqual(obj.actors.actor[2].firstname._comment,
                         ' actor 3 firstname comment ')
        self.assertEqual(obj.directors._comment, ' directors comment ')
        self.assertEqual(obj.directors.director[0].name._value, 'Cameron')
        self.assertEqual(obj.directors.director[0].name._comment,
                         ' director name comment ')
        self.assertEqual(obj.directors.director[0].firstname._value, 'James')
        self.assertEqual(obj.directors.director[0].firstname._comment,
                         ' director firstname comment ')


class TestWalk(TestCase):
    dtd_str = '''
        <!ELEMENT texts (text, text1*)>
        <!ELEMENT text (t1|t2)>
        <!ELEMENT text1 (text11, text)>
        <!ELEMENT t1 (#PCDATA)>
        <!ELEMENT t2 (#PCDATA)>
        <!ELEMENT text11 (#PCDATA)>

        '''
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>
    <t1>t1</t1>
  </text>
  <text1>
    <text11>My text 1</text11>
    <text>
      <t1>t11</t1>
    </text>
  </text1>
  <text1>
    <text11>My text 2</text11>
    <text>
      <t2>t11</t2>
    </text>
  </text1>
</texts>
'''

    def test_walk(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = [e for e in obj.walk()]
        expected = [
            obj.text,
            obj.text.t1,
            obj.text1[0],
            obj.text1[0].text11,
            obj.text1[0].text,
            obj.text1[0].text.t1,
            obj.text1[1],
            obj.text1[1].text11,
            obj.text1[1].text,
            obj.text1[1].text.t2,
        ]
        self.assertEqual(lis, expected)

    def test_findall(self):
        root = etree.fromstring(self.xml)
        dic = dtd_parser.parse(dtd_str=self.dtd_str)
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = obj.findall('text11')
        expected = [
            obj.text1[0].text11,
            obj.text1[1].text11,
        ]
        self.assertEqual(lis, expected)

        lis = obj.findall('t1')
        expected = [
            obj.text.t1,
            obj.text1[0].text.t1,
        ]
        self.assertEqual(lis, expected)

        lis = obj.text1.findall('text11')
        expected = [
            obj.text1[0].text11,
            obj.text1[1].text11,
        ]
        self.assertEqual(lis, expected)
