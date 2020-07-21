#!/usr/bin/env python

import six
from io import StringIO
from unittest import TestCase
from xmltool.testbase import BaseTest
import json
from lxml import etree, html
import os.path
from xmltool import dtd_parser, factory, render, dtd
from xmltool.elements import (
    EmptyElement,
    escape_attr,
)
from xmltool.factory import (
    get_data_from_str_id_for_html_display,
    _get_data_for_html_display,
)
from xmltool.utils import unflatten_params
from ..test_dtd_parser import (
    MOVIE_DTD,
    MOVIE_XML_TITANIC_COMMENTS,
)

_marker = object()


class ElementTester(BaseTest):
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
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
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
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual_(obj._to_html(), self.expected_html)

    def test_load_from_dict(self):
        if self.__class__ == ElementTester:
            return
        data = unflatten_params(self.submit_data)
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
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
            obj = factory._get_obj_from_str_id(elt_str,
                                                dtd_str=self.dtd_str)
            self.assertEqual_(obj.to_html(), expected_html)

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
            obj = factory._get_obj_from_str_id(elt_str,
                                               dtd_str=self.dtd_str)
            lis = obj.get_previous_js_selectors()
            self.assertEqual(lis, selectors)


class TestElementPCDATA(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Hello world</text>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div id="texts:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a data-comment-name="texts:text:_comment" class="btn-comment" '
        'title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:text:_value" rows="1">'
        'Hello world</textarea>'
        '</div>'
        '</div></div>'
    )
    submit_data = {'texts:text:_value': 'Hello world'}

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div id="texts:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
         '</div>'
         '</div></div>'
        ),
        ('texts:text',
         '<div id="texts:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['text'].text, 'Hello world')
        self.assertEqual(obj['text'].sourceline, 3)

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)

        cls = classes['texts']
        obj = cls()
        text = obj.add('text')
        self.assertEqual(text.tagname, 'text')
        self.assertEqual(obj['text'], text)

    def test_add_bad_child(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        try:
            obj.add('unexisiting')
            assert 0
        except Exception as e:
            self.assertEqual(str(e), 'Invalid child unexisiting')


class TestElementPCDATAEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div id="texts:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a data-comment-name="texts:text:_comment" class="btn-comment" '
        'title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:text:_value" rows="1">'
        '</textarea>'
        '</div>'
        '</div></div>'
    )
    submit_data = {}

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div id="texts:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
         '</div>'
         '</div></div>'
        ),
        ('texts:text',
         '<div id="texts:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]


class TestElementPCDATANotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Hello world</text>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div id="texts:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-add btn-add-text hidden" data-elt-id="texts:text">Add text</a>'
        '<a class="btn-delete" data-target="#texts:text" title="Delete"></a>'
        '<a data-comment-name="texts:text:_comment" class="btn-comment" '
        'title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:text:_value" rows="1">Hello world</textarea>'
        '</div>'
        '</div></div>'
    )

    submit_data = {'texts:text:_value': 'Hello world'}

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<a class="btn-add btn-add-text" data-elt-id="texts:text">Add text</a>'
         '</div></div>'
        ),
        ('texts:text',
         '<div id="texts:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-add btn-add-text hidden" data-elt-id="texts:text">Add text</a>'
         '<a class="btn-delete" data-target="#texts:text" title="Delete"></a>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]


class TestElementPCDATAEmptyNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<a class="btn-add btn-add-text" data-elt-id="texts:text">Add text</a>'
        '</div></div>'
    )
    submit_data = {}

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<a class="btn-add btn-add-text" data-elt-id="texts:text">Add text</a>'
         '</div></div>'
        ),
        ('texts:text',
         '<div id="texts:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-add btn-add-text hidden" data-elt-id="texts:text">Add text</a>'
         '<a class="btn-delete" data-target="#texts:text" title="Delete"></a>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]


class TestElementPCDATAEmptyNotRequiredDefined(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div id="texts:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-add btn-add-text hidden" data-elt-id="texts:text">Add text</a>'
        '<a class="btn-delete" data-target="#texts:text" title="Delete"></a>'
        '<a data-comment-name="texts:text:_comment" class="btn-comment" '
        'title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
        '</div>'
        '</div></div>'
    )

    submit_data = {'texts:text:_value': ''}

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<a class="btn-add btn-add-text" data-elt-id="texts:text">Add text</a>'
         '</div></div>'
        ),
        ('texts:text',
         '<div id="texts:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-add btn-add-text hidden" data-elt-id="texts:text">Add text</a>'
         '<a class="btn-delete" data-target="#texts:text" title="Delete"></a>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')]
    ]


class TestListElement(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Tag 1</text>
  <text>Tag 2</text>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:0:text">New text</a>'
        '<div id="texts:list__text:0:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text:0:text" title="Delete"></a>'
        '<a data-comment-name="texts:list__text:0:text:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
        'rows="1">'
        'Tag 1</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:1:text">New text</a>'
        '<div id="texts:list__text:1:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text:1:text" title="Delete"></a>'
        '<a data-comment-name="texts:list__text:1:text:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:list__text:1:text:_value" '
        'rows="1">'
        'Tag 2</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:2:text">New text</a>'
        '</div>'
        '</div></div>'
    )

    submit_data = {
        'texts:list__text:0:text:_value': 'Tag 1',
        'texts:list__text:1:text:_value': 'Tag 2',
    }

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div class="list-container">'
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:0:text">New text</a>'
         '<div id="texts:list__text:0:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:0:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
         'rows="1"></textarea>'
         '</div>'
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:1:text">New text</a>'
         '</div>'
         '</div></div>'
        ),
        ('texts:list__text:0:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:0:text">New text</a>'
         '<div id="texts:list__text:0:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:0:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
         'rows="1"></textarea>'
         '</div>'
        ),
        ('texts:list__text:10:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:10:text">New text</a>'
         '<div id="texts:list__text:10:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:10:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:10:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:10:text:_value" '
         'rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', escape_attr('#tree_texts:list__text:9:text'))],
    ]

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        text1 = obj.add('text')
        self.assertEqual(text1.tagname, 'text')
        self.assertEqual(len(obj['text']), 1)
        self.assertEqual(obj['text'][0], text1)

        text2 = obj.add('text')
        self.assertEqual(text2.tagname, 'text')
        self.assertEqual(len(obj['text']), 2)
        self.assertEqual(obj['text'][1], text2)

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['text'][0].text, 'Tag 1')
        self.assertEqual(obj['text'][0].sourceline, 3)
        self.assertEqual(obj['text'][1].text, 'Tag 2')
        self.assertEqual(obj['text'][1].sourceline, 4)


class TestListElementEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''

    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:0:text">New text</a>'
        '<div id="texts:list__text:0:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text:0:text" title="Delete"></a>'
        '<a data-comment-name="texts:list__text:0:text:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
        'rows="1">'
        '</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:1:text">New text</a>'
        '</div>'
        '</div></div>'
    )

    submit_data = {}

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div class="list-container">'
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:0:text">New text</a>'
         '<div id="texts:list__text:0:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:0:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
         'rows="1"></textarea>'
         '</div>'
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:1:text">New text</a>'
         '</div>'
         '</div></div>'
        ),
        ('texts:list__text:0:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:0:text">New text</a>'
         '<div id="texts:list__text:0:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:0:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
         'rows="1"></textarea>'
         '</div>'
        ),
        ('texts:list__text:10:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:10:text">New text</a>'
         '<div id="texts:list__text:10:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:10:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:10:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:10:text:_value" '
         'rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', escape_attr('#tree_texts:list__text:9:text'))],
    ]


class TestListElementNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Tag 1</text>
  <text>Tag 2</text>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:0:text">New text</a>'
        '<div id="texts:list__text:0:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text:0:text" title="Delete"></a>'
        '<a data-comment-name="texts:list__text:0:text:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
        'rows="1">'
        'Tag 1</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:1:text">New text</a>'
        '<div id="texts:list__text:1:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text:1:text" title="Delete"></a>'
        '<a data-comment-name="texts:list__text:1:text:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text" name="texts:list__text:1:text:_value" '
        'rows="1">'
        'Tag 2</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:2:text">New text</a>'
        '</div>'
        '</div></div>'
    )

    submit_data = {
        'texts:list__text:0:text:_value': 'Tag 1',
        'texts:list__text:1:text:_value': 'Tag 2',
    }

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div class="list-container">'
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:0:text">New text</a>'
         '</div>'
         '</div></div>'
        ),
        ('texts:list__text:0:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:0:text">New text</a>'
         '<div id="texts:list__text:0:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:0:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
         'rows="1"></textarea>'
         '</div>'
        ),
        ('texts:list__text:10:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:10:text">New text</a>'
         '<div id="texts:list__text:10:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:10:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:10:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:10:text:_value" '
         'rows="1"></textarea>'
         '</div>'
        )
    ]
    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', escape_attr('#tree_texts:list__text:9:text'))],
    ]


class TestListElementEmptyNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text btn-list" '
        'data-elt-id="texts:list__text:0:text">New text</a>'
        '</div>'
        '</div></div>'
    )

    submit_data = {}

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div class="list-container">'
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:0:text">New text</a>'
         '</div>'
         '</div></div>'
        ),
        ('texts:list__text:0:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:0:text">New text</a>'
         '<div id="texts:list__text:0:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:0:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:0:text:_value" '
         'rows="1"></textarea>'
         '</div>'
        ),
        ('texts:list__text:10:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:10:text">New text</a>'
         '<div id="texts:list__text:10:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:10:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:10:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:list__text:10:text:_value" '
         'rows="1"></textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after', escape_attr('#tree_texts:list__text:9:text'))],
    ]


class TestListElementElementEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (subtext)>
        <!ELEMENT subtext (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>
    <subtext></subtext>
  </text>
</texts>
'''

    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text btn-list" data-elt-id="texts:list__text:0:text">'
        'New text</a>'
        '<div class="panel panel-default text" '
        'id="texts:list__text:0:text">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts\:list__text\:0\:text">text'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text:0:text" title="Delete"/>'
        '<a data-comment-name="texts:list__text:0:text:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts:list__text:0:text">'
        '<div id="texts:list__text:0:text:subtext" class="xt-container-subtext">'
        '<label>subtext</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a data-comment-name="texts:list__text:0:text:subtext:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control subtext" name="texts:list__text:0:text:subtext:_value" '
        'rows="1"></textarea>'
        '</div>'
        '</div></div>'
        '<a class="btn-add btn-add-text btn-list" data-elt-id="texts:list__text:1:text">'
        'New text</a>'
        '</div>'
        '</div></div>'
    )

    submit_data = {}

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" '
         'title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div class="list-container">'
         '<a class="btn-add btn-add-text btn-list" data-elt-id="texts:list__text:0:text">'
         'New text</a>'
         '<div class="panel panel-default text" '
         'id="texts:list__text:0:text">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts\:list__text\:0\:text">text'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:0:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:0:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts:list__text:0:text">'
         '<div id="texts:list__text:0:text:subtext" class="xt-container-subtext">'
         '<label>subtext</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a data-comment-name="texts:list__text:0:text:subtext:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control subtext" name="texts:list__text:0:text:subtext:_value" '
         'rows="1"></textarea>'
         '</div>'
         '</div></div>'
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:1:text">'
         'New text</a>'
         '</div>'
         '</div></div>'
        ),
        ('texts:list__text:1:text',
         '<a class="btn-add btn-add-text btn-list" '
         'data-elt-id="texts:list__text:1:text">'
         'New text</a>'
         '<div class="panel panel-default text" id="texts:list__text:1:text">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts\:list__text\:1\:text">text'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text:1:text" title="Delete"></a>'
         '<a data-comment-name="texts:list__text:1:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts:list__text:1:text">'
         '<div id="texts:list__text:1:text:subtext" class="xt-container-subtext">'
         '<label>subtext</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a data-comment-name="texts:list__text:1:text:subtext:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control subtext" name="texts:list__text:1:text:subtext:_value" '
         'rows="1"></textarea>'
         '</div>'
         '</div></div>'
        )
    ]

    js_selector = [
        [],
        [('after', escape_attr('#tree_texts:list__text:0:text'))],
        [('after', escape_attr('#tree_texts:list__text:9:text'))],
    ]


choice_str_to_html = [
    ('texts',
     '<div class="panel panel-default texts" id="texts">'
     '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
     '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
     '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
     '<select class="btn-add">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:text2">text2</option>'
     '</select>'
     '</div></div>'
    ),
    ('texts:text1',
     '<div id="texts:text1" class="xt-container-text1">'
     '<label>text1</label>'
     '<span class="btn-external-editor" '
     'ng-click="externalEditor(this)"></span>'
     '<select class="btn-add hidden">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:text2">text2</option>'
     '</select>'
     '<a class="btn-delete" data-target="#texts:text1" title="Delete"></a>'
     '<a data-comment-name="texts:text1:_comment" class="btn-comment" '
     'title="Add comment"></a>'
     '<textarea class="form-control text1" name="texts:text1:_value" rows="1"></textarea>'
     '</div>'
    )
]

choice_js_selector = [
        [],
        [('inside', '#tree_texts')],
    ]


class TestElementChoice(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1|text2)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div id="texts:text1" class="xt-container-text1">'
        '<label>text1</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<select class="btn-add hidden">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:text2">text2</option>'
        '</select>'
        '<a class="btn-delete" data-target="#texts:text1" title="Delete"></a>'
        '<a data-comment-name="texts:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text1" name="texts:text1:_value" '
        'rows="1">Tag 1</textarea>'
        '</div>'
        '</div></div>'
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
        self.assertEqual(text1.tagname, 'text1')
        self.assertEqual(obj['text1'], text1)

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['text1'].text, 'Tag 1')
        self.assertEqual(obj['text1'].sourceline, 3)
        self.assertFalse(hasattr(obj, 'text2'))

        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text2>Tag 2</text2>
</texts>'''
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['text2'].text, 'Tag 2')
        self.assertEqual(obj['text2'].sourceline, 3)
        self.assertFalse(hasattr(obj, 'text1'))


class TestElementChoiceEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1|text2)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<select class="btn-add">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:text2">text2</option>'
        '</select>'
        '</div></div>'
    )

    submit_data = {}
    str_to_html = choice_str_to_html
    js_selector = choice_js_selector


class TestElementChoiceNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1|text2)?>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div id="texts:text1" class="xt-container-text1">'
        '<label>text1</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<select class="btn-add hidden">'
        '<option>'
        'New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:text1">'
        'text1</option>'
        '<option class="xt-option-text2" value="texts:text2">'
        'text2</option>'
        '</select>'
        '<a class="btn-delete" data-target="#texts:text1" title="Delete"></a>'
        '<a data-comment-name="texts:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text1" name="texts:text1:_value" '
        'rows="1">Tag 1</textarea>'
        '</div>'
        '</div></div>'
    )

    submit_data = {
        'texts:text1:_value': 'Tag 1',
    }
    str_to_html = choice_str_to_html
    js_selector = choice_js_selector


class TestElementChoiceEmptyNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1|text2)?>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<select class="btn-add">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:text2">text2</option>'
        '</select>'
        '</div></div>'
    )

    submit_data = {}
    str_to_html = choice_str_to_html
    js_selector = choice_js_selector


choicelist_str_to_html = [
    ('texts',
     '<div class="panel panel-default texts" id="texts">'
     '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
     '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
     '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
     '<div class="list-container">'
     '<select class="btn-add btn-list">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:list__text1_text2:0:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:list__text1_text2:0:text2">text2</option>'
     '</select>'
     '</div>'
     '</div></div>'
    ),
    ('texts:list__text1_text2:0:text1',
     '<select class="btn-add btn-list">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:list__text1_text2:0:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:list__text1_text2:0:text2">text2</option>'
     '</select>'
     '<div id="texts:list__text1_text2:0:text1" class="xt-container-text1">'
     '<label>text1</label>'
     '<span class="btn-external-editor" '
     'ng-click="externalEditor(this)"></span>'
     '<a class="btn-delete btn-list" '
     'data-target="#texts:list__text1_text2:0:text1" title="Delete"></a>'
     '<a data-comment-name="texts:list__text1_text2:0:text1:_comment" '
     'class="btn-comment" title="Add comment"></a>'
     '<textarea class="form-control text1" name="texts:list__text1_text2:0:text1:_value" '
     'rows="1"></textarea>'
     '</div>'
    ),
    ('texts:list__text1_text2:10:text1',
     '<select class="btn-add btn-list">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:list__text1_text2:10:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:list__text1_text2:10:text2">text2</option>'
     '</select>'
     '<div id="texts:list__text1_text2:10:text1" class="xt-container-text1">'
     '<label>text1</label>'
     '<span class="btn-external-editor" '
     'ng-click="externalEditor(this)"></span>'
     '<a class="btn-delete btn-list" '
     'data-target="#texts:list__text1_text2:10:text1" title="Delete"></a>'
     '<a data-comment-name="texts:list__text1_text2:10:text1:_comment" '
     'class="btn-comment" title="Add comment"></a>'
     '<textarea class="form-control text1" name="texts:list__text1_text2:10:text1:_value" '
     'rows="1"></textarea>'
     '</div>'
    )
]

choice_list_js_selector = [
        [],
        [('inside', '#tree_texts')],
    ]

class TestElementChoiceList(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
  <text2>Tag 2</text2>
  <text1>Tag 3</text1>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:0:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:0:text2">text2</option>'
        '</select>'
        '<div id="texts:list__text1_text2:0:text1" class="xt-container-text1">'
        '<label>text1</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1_text2:0:text1" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1_text2:0:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text1" name="texts:list__text1_text2:0:text1:_value" '
        'rows="1">Tag 1</textarea>'
        '</div>'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:1:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:1:text2">text2</option>'
        '</select>'
        '<div id="texts:list__text1_text2:1:text2" class="xt-container-text2">'
        '<label>text2</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1_text2:1:text2" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1_text2:1:text2:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text2" name="texts:list__text1_text2:1:text2:_value" '
        'rows="1">Tag 2</textarea>'
        '</div>'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:2:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:2:text2">text2</option>'
        '</select>'
        '<div id="texts:list__text1_text2:2:text1" class="xt-container-text1">'
        '<label>text1</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1_text2:2:text1" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1_text2:2:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text1" name="texts:list__text1_text2:2:text1:_value" '
        'rows="1">Tag 3</textarea>'
        '</div>'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:3:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:3:text2">text2</option>'
        '</select>'
        '</div>'
        '</div></div>'
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
        self.assertEqual(obj['list__text1_text2'], [text1])
        text2 = obj.add('text2')
        self.assertEqual(obj['list__text1_text2'], [text1, text2])

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['list__text1_text2'][0].text, 'Tag 1')
        self.assertEqual(obj['list__text1_text2'][0].sourceline, 3)
        self.assertEqual(obj['list__text1_text2'][1].text, 'Tag 2')
        self.assertEqual(obj['list__text1_text2'][1].sourceline, 4)
        self.assertEqual(obj['list__text1_text2'][2].text, 'Tag 3')
        self.assertEqual(obj['list__text1_text2'][2].sourceline, 5)


class TestElementChoiceListEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:0:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:0:text2">text2</option>'
        '</select>'
        '</div>'
        '</div></div>'
    )

    submit_data = {}
    str_to_html = choicelist_str_to_html
    js_selector = choice_list_js_selector


class TestElementChoiceListNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
  <text2>Tag 2</text2>
  <text1>Tag 3</text1>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:0:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:0:text2">text2</option>'
        '</select>'
        '<div id="texts:list__text1_text2:0:text1" class="xt-container-text1">'
        '<label>text1</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1_text2:0:text1" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1_text2:0:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text1" name="texts:list__text1_text2:0:text1:_value" '
        'rows="1">Tag 1</textarea>'
        '</div>'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:1:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:1:text2">text2</option>'
        '</select>'
        '<div id="texts:list__text1_text2:1:text2" class="xt-container-text2">'
        '<label>text2</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1_text2:1:text2" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1_text2:1:text2:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text2" name="texts:list__text1_text2:1:text2:_value" '
        'rows="1">Tag 2</textarea>'
        '</div>'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:2:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:2:text2">text2</option>'
        '</select>'
        '<div id="texts:list__text1_text2:2:text1" class="xt-container-text1">'
        '<label>text1</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1_text2:2:text1" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1_text2:2:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text1" name="texts:list__text1_text2:2:text1:_value" '
        'rows="1">Tag 3</textarea>'
        '</div>'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:3:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:3:text2">text2</option>'
        '</select>'
        '</div>'
        '</div></div>'
    )

    submit_data = {
        'texts:list__text1_text2:0:text1:_value': 'Tag 1',
        'texts:list__text1_text2:1:text2:_value': 'Tag 2',
        'texts:list__text1_text2:2:text1:_value': 'Tag 3',
    }

    str_to_html = choicelist_str_to_html
    js_selector = choice_list_js_selector


class TestElementChoiceListEmptyNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts ((text1|text2)*)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<select class="btn-add btn-list">'
        '<option>New text1/text2</option>'
        '<option class="xt-option-text1" value="texts:list__text1_text2:0:text1">text1</option>'
        '<option class="xt-option-text2" value="texts:list__text1_text2:0:text2">text2</option>'
        '</select>'
        '</div>'
        '</div></div>'
    )

    submit_data = {}
    str_to_html = choicelist_str_to_html
    js_selector = choice_list_js_selector


class TestListElementOfList(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1*)>
        <!ELEMENT text1 (text2+)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
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
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text1 btn-list" '
        'data-elt-id="texts:list__text1:0:text1">New text1</a>'
        '<div class="panel panel-default text1" '
        'id="texts:list__text1:0:text1">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts\:list__text1\:0\:text1">text1'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1:0:text1" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1:0:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts:list__text1:0:text1">'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text2 btn-list" '
        'data-elt-id="texts:list__text1:0:text1:list__text2:0:text2">New text2</a>'
        '<div id="texts:list__text1:0:text1:list__text2:0:text2" '
        'class="xt-container-text2">'
        '<label>text2</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1:0:text1:list__text2:0:text2"'
        ' title="Delete"></a>'
        '<a data-comment-name="texts:list__text1:0:text1:list__text2:0:text2:'
        '_comment" class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text2" name="texts:list__text1:0:text1:list__text2:0:text2:_value" '
        'rows="1">text2-1</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text2 btn-list" '
        'data-elt-id="texts:list__text1:0:text1:list__text2:1:text2">New text2</a>'
        '<div id="texts:list__text1:0:text1:list__text2:1:text2" '
        'class="xt-container-text2">'
        '<label>text2</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1:0:text1:list__text2:1:text2"'
        ' title="Delete"></a>'
        '<a data-comment-name="texts:list__text1:0:text1:list__text2:1:text2'
        ':_comment" class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text2" name="texts:list__text1:0:text1:list__text2:1:text2:_value" '
        'rows="1">text2-2</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text2 btn-list" '
        'data-elt-id="texts:list__text1:0:text1:list__text2:2:text2">New text2</a>'
        '</div>'
        '</div></div>'
        '<a class="btn-add btn-add-text1 btn-list" '
        'data-elt-id="texts:list__text1:1:text1">New text1</a>'
        '<div class="panel panel-default text1" '
        'id="texts:list__text1:1:text1">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts\:list__text1\:1\:text1">text1'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1:1:text1" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1:1:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts:list__text1:1:text1">'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text2 btn-list" data-elt-id="texts:list__text1:1:text1:'
        'list__text2:0:text2">New text2</a>'
        '<div id="texts:list__text1:1:text1:list__text2:0:text2" '
        'class="xt-container-text2">'
        '<label>text2</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1:1:text1:list__text2:0:text2"'
        ' title="Delete"></a>'
        '<a data-comment-name="texts:list__text1:1:text1:list__text2:0:text2:'
        '_comment" class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text2" name="texts:list__text1:1:text1:list__text2:0:text2:_value" '
        'rows="1">text2-3</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text2 btn-list" '
        'data-elt-id="texts:list__text1:1:text1:list__text2:1:text2">New text2</a>'
        '</div>'
        '</div></div>'
        '<a class="btn-add btn-add-text1 btn-list" '
        'data-elt-id="texts:list__text1:2:text1">New text1</a>'
        '</div>'
        '</div></div>'
    )

    submit_data = {
        'texts:list__text1:0:text1:list__text2:0:text2:_value': 'text2-1',
        'texts:list__text1:0:text1:list__text2:1:text2:_value': 'text2-2',
        'texts:list__text1:1:text1:list__text2:0:text2:_value': 'text2-3',
    }
    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div class="list-container">'
         '<a class="btn-add btn-add-text1 btn-list" '
         'data-elt-id="texts:list__text1:0:text1">New text1</a>'
         '</div>'
         '</div></div>'
        ),
        ('texts:list__text1:0:text1',
         '<a class="btn-add btn-add-text1 btn-list" '
         'data-elt-id="texts:list__text1:0:text1">New text1</a>'
         '<div class="panel panel-default text1" id="texts:list__text1:0:text1">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts\:list__text1\:0\:text1">'
         'text1'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text1:0:text1" title="Delete"></a>'
         '<a data-comment-name="texts:list__text1:0:text1:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts:list__text1:0:text1">'
         '<div class="list-container">'
         '<a class="btn-add btn-add-text2 btn-list" '
         'data-elt-id="texts:list__text1:0:text1:list__text2:0:text2">New text2</a>'
         '<div id="texts:list__text1:0:text1:list__text2:0:text2" '
         'class="xt-container-text2">'
         '<label>text2</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text1:0:text1:list__text2:0:text2"'
         ' title="Delete"></a>'
         '<a data-comment-name="texts:list__text1:0:text1:list__text2:0:'
         'text2:_comment" class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text2" name="texts:list__text1:0:text1:list__text2:0:text2:'
         '_value" rows="1"></textarea>'
         '</div>'
         '<a class="btn-add btn-add-text2 btn-list" '
         'data-elt-id="texts:list__text1:0:text1:list__text2:1:text2">'
         'New text2</a>'
         '</div>'
         '</div></div>'
        ),
        ('texts:list__text1:0:text1:list__text2:3:text2',
         '<a class="btn-add btn-add-text2 btn-list" '
         'data-elt-id="texts:list__text1:0:text1:list__text2:3:text2">New text2</a>'
         '<div id="texts:list__text1:0:text1:list__text2:3:text2" '
         'class="xt-container-text2">'
         '<label>text2</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a class="btn-delete btn-list" '
         'data-target="#texts:list__text1:0:text1:list__text2:3:text2"'
         ' title="Delete"></a>'
         '<a data-comment-name="texts:list__text1:0:text1:list__text2:3:'
         'text2:_comment" class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text2" name="texts:list__text1:0:text1:list__text2:3:text2:_value" '
         'rows="1">'
         '</textarea>'
         '</div>'
        )
    ]

    js_selector = [
        [],
        [('inside', '#tree_texts')],
        [('after',
          escape_attr('#tree_texts:list__text1:0:text1:list__text2:2:text2'))],
    ]


class TestElementWithAttributes(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text, text1*)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT text1 (#PCDATA)>

        <!ATTLIST texts idtexts ID #IMPLIED>
        <!ATTLIST texts name CDATA "">
        <!ATTLIST text idtext ID #IMPLIED>
        <!ATTLIST text1 idtext1 CDATA "">
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts idtexts="id_texts" name="my texts">
  <text idtext="id_text">Hello world</text>
  <text1 idtext1="id_text1_1">My text 1</text1>
  <text1>My text 2</text1>
</texts>
'''
    expected_html = (
        '<div class="panel panel-default texts" id="texts">'
        '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
        '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
        '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
        '<a name="idtexts=id_texts"></a>'
        '<input value="id_texts" name="texts:_attrs:idtexts" '
        'id="texts:_attrs:idtexts" class="_attrs" />'
        '<a name="name=my texts"></a>'
        '<input value="my texts" name="texts:_attrs:name" '
        'id="texts:_attrs:name" class="_attrs" />'
        '<div id="texts:text" class="xt-container-text">'
        '<label>text</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a data-comment-name="texts:text:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<a name="idtext=id_text"></a>'
        '<input value="id_text" name="texts:text:_attrs:idtext" '
        'id="texts:text:_attrs:idtext" class="_attrs" />'
        '<textarea class="form-control text" name="texts:text:_value" rows="1">Hello world</textarea>'
        '</div>'
        '<div class="list-container">'
        '<a class="btn-add btn-add-text1 btn-list" data-elt-id="texts:list__text1:0:text1">'
        'New text1</a>'
        '<div id="texts:list__text1:0:text1" class="xt-container-text1">'
        '<label>text1</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1:0:text1" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1:0:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<a name="idtext1=id_text1_1"></a>'
        '<input value="id_text1_1" '
        'name="texts:list__text1:0:text1:_attrs:idtext1" '
        'id="texts:list__text1:0:text1:_attrs:idtext1" '
        'class="_attrs" />'
        '<textarea class="form-control text1" name="texts:list__text1:0:text1:_value" rows="1">'
        'My text 1</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text1 btn-list" data-elt-id="texts:list__text1:1:text1">'
        'New text1</a>'
        '<div id="texts:list__text1:1:text1" class="xt-container-text1">'
        '<label>text1</label>'
        '<span class="btn-external-editor" '
        'ng-click="externalEditor(this)"></span>'
        '<a class="btn-delete btn-list" '
        'data-target="#texts:list__text1:1:text1" title="Delete"></a>'
        '<a data-comment-name="texts:list__text1:1:text1:_comment" '
        'class="btn-comment" title="Add comment"></a>'
        '<textarea class="form-control text1" name="texts:list__text1:1:text1:_value" rows="1">'
        'My text 2</textarea>'
        '</div>'
        '<a class="btn-add btn-add-text1 btn-list" data-elt-id="texts:list__text1:2:text1">'
        'New text1</a>'
        '</div>'
        '</div></div>'
    )

    str_to_html = [
        ('texts',
         '<div class="panel panel-default texts" id="texts">'
         '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
         '<a data-comment-name="texts:_comment" class="btn-comment" '
         'title="Add comment"></a>'
         '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
         '<div id="texts:text" class="xt-container-text">'
         '<label>text</label>'
         '<span class="btn-external-editor" '
         'ng-click="externalEditor(this)"></span>'
         '<a data-comment-name="texts:text:_comment" '
         'class="btn-comment" title="Add comment"></a>'
         '<textarea class="form-control text" name="texts:text:_value" rows="1"></textarea>'
         '</div>'
         '<div class="list-container">'
         '<a class="btn-add btn-add-text1 btn-list" '
         'data-elt-id="texts:list__text1:0:text1">New text1</a>'
         '</div>'
         '</div></div>')
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
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._attribute_names, ['idtexts', 'name'])
        self.assertEqual(obj.attributes, {
            'idtexts': 'id_texts',
            'name': 'my texts',
        })
        self.assertEqual(obj['text']._attribute_names, ['idtext'])
        self.assertEqual(obj['text'].attributes, {
            'idtext': 'id_text',
        })
        self.assertEqual(obj['text1'][0]._attribute_names, ['idtext1'])
        self.assertEqual(obj['text1'][0].attributes, {
            'idtext1': 'id_text1_1',
        })
        self.assertEqual(obj['text1'][1]._attribute_names, ['idtext1'])
        self.assertEqual(obj['text1'][1].attributes, None)

    def test_walk(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = [e for e in obj.walk()]
        expected = [obj['text']] + obj['text1']
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
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.sourceline, 3)
        self.assertEqual(obj['name'].text, 'Titanic')
        self.assertEqual(obj['name'].comment, ' name comment ')
        self.assertEqual(obj['name'].sourceline, 5)
        self.assertEqual(obj['resume'].text, '\n     Resume of the movie\n  ')
        self.assertEqual(obj['resume'].comment, ' resume comment ')
        self.assertEqual(obj['resume'].sourceline, 43)
        self.assertEqual(obj['year'].text, '1997')
        self.assertEqual(obj['year'].comment, ' year comment ')
        self.assertEqual(obj['year'].sourceline, 7)
        self.assertEqual([c.text for c in obj['critique']], ['critique1', 'critique2'])
        self.assertEqual(obj['critique'][0].comment, ' critique 1 comment ')
        self.assertEqual(obj['critique'][1].comment, ' critique 2 comment ')
        self.assertEqual(len(obj['actors']['actor']), 3)
        self.assertEqual(len(obj['directors']['director']), 1)
        self.assertEqual(obj['actors'].comment, ' actors comment ')
        self.assertEqual(obj['actors']['actor'][0].sourceline, 21)
        self.assertEqual(obj['actors']['actor'][0].comment, ' actor 1 comment ')
        self.assertEqual(obj['actors']['actor'][0]['name'].text, 'DiCaprio')
        self.assertEqual(obj['actors']['actor'][0]['name'].comment,
                         ' actor 1 name comment ')
        self.assertEqual(obj['actors']['actor'][0]['name'].sourceline, 23)
        self.assertEqual(obj['actors']['actor'][0]['firstname'].text, 'Leonardo')
        self.assertEqual(obj['actors']['actor'][0]['firstname'].comment,
                         ' actor 1 firstname comment ')
        self.assertEqual(obj['actors']['actor'][1].comment, ' actor 2 comment ')
        self.assertEqual(obj['actors']['actor'][1]['name'].text, 'Winslet')
        self.assertEqual(obj['actors']['actor'][1]['name'].comment,
                         ' actor 2 name comment ')
        self.assertEqual(obj['actors']['actor'][1]['firstname'].text, 'Kate')
        self.assertEqual(obj['actors']['actor'][1]['firstname'].comment,
                         ' actor 2 firstname comment ')
        self.assertEqual(obj['actors']['actor'][2].comment,
                         ' actor 3 comment ')
        self.assertEqual(obj['actors']['actor'][2]['name'].text, 'Zane')
        self.assertEqual(obj['actors']['actor'][2]['name'].comment,
                         ' actor 3 name comment ')
        self.assertEqual(obj['actors']['actor'][2]['firstname'].text, 'Billy')
        self.assertEqual(obj['actors']['actor'][2]['firstname'].comment,
                         ' actor 3 firstname comment ')
        self.assertEqual(obj['directors'].comment, ' directors comment ')
        self.assertEqual(obj['directors']['director'][0]['name'].text, 'Cameron')
        self.assertEqual(obj['directors']['director'][0]['name'].comment,
                         ' director name comment ')
        self.assertEqual(obj['directors']['director'][0]['firstname'].text, 'James')
        self.assertEqual(obj['directors']['director'][0]['firstname'].comment,
                         ' director firstname comment ')


class TestWalk(TestCase):
    dtd_str = u'''
        <!ELEMENT texts (text, text1*)>
        <!ELEMENT text (t1|t2)>
        <!ELEMENT text1 (text11, text)>
        <!ELEMENT t1 (#PCDATA)>
        <!ELEMENT t2 (#PCDATA)>
        <!ELEMENT text11 (#PCDATA)>

        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
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
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = [e for e in obj.walk()]
        expected = [
            obj['text'],
            obj['text']['t1'],
            obj['text1'][0],
            obj['text1'][0]['text11'],
            obj['text1'][0]['text'],
            obj['text1'][0]['text']['t1'],
            obj['text1'][1],
            obj['text1'][1]['text11'],
            obj['text1'][1]['text'],
            obj['text1'][1]['text']['t2'],
        ]
        self.assertEqual(lis, expected)

    def test_findall(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = obj.findall('text11')
        expected = [
            obj['text1'][0]['text11'],
            obj['text1'][1]['text11'],
        ]
        self.assertEqual(lis, expected)

        lis = obj.findall('t1')
        expected = [
            obj['text']['t1'],
            obj['text1'][0]['text']['t1'],
        ]
        self.assertEqual(lis, expected)

        lis = obj['text1'].findall('text11')
        expected = [
            obj['text1'][0]['text11'],
            obj['text1'][1]['text11'],
        ]
        self.assertEqual(lis, expected)


class TestXPath(TestCase):
    dtd_str = MOVIE_DTD
    xml = MOVIE_XML_TITANIC_COMMENTS

    def test_xpath(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()

        try:
            res = obj.xpath('Movie')
            assert(False)
        except Exception as e:
            self.assertEqual(
                str(e),
                'The xpath is only supported '
                'when the object is loaded from XML')

        obj.load_from_xml(root)
        # Since obj is Movie it didn't match
        res = obj.xpath('Movie')
        self.assertEqual(len(res), 0)

        res = obj.xpath('/Movie')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], obj)

        res = obj.xpath('directors')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], obj['directors'])
        res = obj.xpath('//actors/actor')
        self.assertEqual(len(res), 3)
        self.assertEqual(res, obj['actors']['actor'])

        actor_obj = obj['actors']['actor'][0]
        res = actor_obj.xpath('/Movie')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], obj)

        res = actor_obj.xpath('..')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], actor_obj._parent_obj._parent_obj)


def generate_html_block(html, css_class, attrs=''):
    return '<div class="%s"%s>%s</div>' % (css_class, attrs, html)


def generate_javascript_unittest(xml, dtd_str, tagname):
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        obj.root.html_renderer = render.Render()
        obj.root.html_renderer.add_add_button = lambda: False
        obj = obj[tagname]

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input'
        )
        obj.insert(0, EmptyElement(parent_obj=obj))
        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected'
        )
        test_html = generate_html_block(
            input_html + expected_html,
            'dom-test',
            ' prefix="%(tn)s:0:" newprefix="%(tn)s:1:"' % {
                'tn': obj._prefix_str,
            }
        )

        input_html = generate_html_block(
            obj._get_html_add_button(index=0),
            'dom-input'
        )
        expected_html = generate_html_block(
            obj._get_html_add_button(index=1),
            'dom-expected'
        )
        test_button_html = generate_html_block(
            input_html + expected_html,
            'dom-test',
            ' prefix="%(tn)s:0:" newprefix="%(tn)s:1:"' % {
                'tn': obj._prefix_str,
            }
        )
        return test_html + test_button_html


class TestJavascript(TestCase):

    def test_updatePrefixAttrs(self):
        lis = []
        dtd_str = u'''
            <!ELEMENT texts (text+)>
            <!ELEMENT text (#PCDATA)>
            '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Tag 1</text>
</texts>
'''
        lis += [generate_javascript_unittest(xml, dtd_str, 'text')]

        dtd_str = u'''
            <!ELEMENT texts (text+)>
            <!ELEMENT text (subtext)>
            <!ELEMENT subtext (#PCDATA)>
            '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>
    <subtext>Hello</subtext>
  </text>
</texts>
'''
        lis += [generate_javascript_unittest(xml, dtd_str, 'text')]

        dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
</texts>
'''
        lis += [generate_javascript_unittest(xml, dtd_str, 'list__text1_text2')]

        dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (subtext)>
        <!ELEMENT text2 (subtext)>
        <!ELEMENT subtext (#PCDATA)>
        '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>
    <subtext>Tag 1</subtext>
  </text1>
</texts>
'''
        lis += [generate_javascript_unittest(xml, dtd_str, 'list__text1_text2')]

        filename = 'webmedia/js/test/fixtures/updatePrefixAttrs.html'
        document_root = html.fromstring(''.join(lis))
        h = etree.tostring(document_root, encoding='unicode',
                           pretty_print=True)
        open(filename, 'w').write(h)

    def test_jstree_utils(self):
        dtd_str = u'''
            <!ELEMENT texts (text+)>
            <!ELEMENT text (subtext)>
            <!ELEMENT subtext (#PCDATA)>
            '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>
    <subtext>Hello</subtext>
  </text>
</texts>
'''
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)

        h = '''<div id="tree"></div><div id="form-container">
        <form id="xmltool-form">%s</form>
        </div>''' % obj.to_html()
        document_root = html.fromstring(h)
        h = etree.tostring(document_root, encoding='unicode',
                           pretty_print=True)
        filename = 'webmedia/js/test/fixtures/jstree_utils.html'
        open(filename, 'w').write(h)

        js = json.dumps(obj.to_jstree_dict())
        filename = 'webmedia/js/test/fixtures/jstree_utils.json'
        open(filename, 'w').write(js)

        text = obj.add('text')
        subtext = text.add('subtext')
        subtext.text = 'World'
        dic = _get_data_for_html_display(text)

        filename = 'webmedia/js/test/fixtures/paste.json'
        open(filename, 'w').write(json.dumps(dic))

        filename = 'webmedia/js/test/fixtures/paste_expected.json'
        dic = _get_data_for_html_display(obj)
        open(filename, 'w').write(json.dumps(dic))

        text = obj.add('text')
        subtext = text.add('subtext')
        subtext.text = '!'

        js = json.dumps(obj.to_jstree_dict())
        filename = 'webmedia/js/test/fixtures/nodes.json'
        open(filename, 'w').write(js)

    def test_add_element(self):
        dtd_str = u'''
            <!ELEMENT texts (text?)>
            <!ELEMENT text (#PCDATA)>
            '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts></texts>'''

        lis = []
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )

        o = obj.add('text', '')

        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "[data-elt-id='%s']" % escape_attr(o._prefix_str)
        dic = get_data_from_str_id_for_html_display(ident,
                                          dtd_str=dtd_str)

        filename = 'js/test/fixtures/add_element/1.json'
        open(os.path.join('webmedia', filename), 'w').write(json.dumps(dic))

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            'data-url="%s"'
            ' data-btn-selector="%s"'
            ' data-id="%s"' % (filename, btn_selector, ident),
        )
        lis += [test_html]

        dtd_str = u'''
        <!ELEMENT texts (text1|text2)?>
        <!ELEMENT text1 (subtext)>
        <!ELEMENT text2 (subtext)>
        <!ELEMENT subtext (#PCDATA)>
        '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts></texts>'''
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )

        o = obj.add('text1')

        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "option[value='%s']" % escape_attr(
            o._prefix_str)
        dic = get_data_from_str_id_for_html_display(ident,
                                          dtd_str=dtd_str)
        filename = 'js/test/fixtures/add_element/2.json'
        open(os.path.join('webmedia', filename), 'w').write(json.dumps(dic))

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            'data-url="%s"'
            ' data-btn-selector="%s"'
            ' data-id="%s"' % (filename, btn_selector, ident),
        )
        lis += [test_html]

        dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (subtext)>
        <!ELEMENT text2 (subtext)>
        <!ELEMENT subtext (#PCDATA)>
        '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>
    <subtext>Tag 1</subtext>
  </text1>
  <text2>
    <subtext>Tag 2</subtext>
  </text2>
</texts>
'''
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )

        o = obj['list__text1_text2'].add('text1', index=0)

        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "option[value='%s']" % escape_attr(
            o._prefix_str)
        dic = get_data_from_str_id_for_html_display(ident,
                                          dtd_str=dtd_str)
        filename = 'js/test/fixtures/add_element/3.json'
        open(os.path.join('webmedia', filename), 'w').write(json.dumps(dic))

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            'data-url="%s"'
            ' data-btn-selector="%s"'
            ' data-id="%s"' % (filename, btn_selector, ident),
        )
        lis += [test_html]

        o._parent_obj.remove(o)
        o = obj['list__text1_text2'].add('text1', index=1)

        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "option[value='%s']" % escape_attr(
            o._prefix_str)
        dic = get_data_from_str_id_for_html_display(ident,
                                          dtd_str=dtd_str)
        filename = 'js/test/fixtures/add_element/4.json'
        open(os.path.join('webmedia', filename), 'w').write(json.dumps(dic))

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            'data-url="%s"'
            ' data-btn-selector="%s"'
            ' data-id="%s"' % (filename, btn_selector, ident),
        )
        lis += [test_html]

        o._parent_obj.remove(o)
        o = obj['list__text1_text2'].add('text1', index=2)

        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "option[value='%s']" % escape_attr(
            o._prefix_str)
        dic = get_data_from_str_id_for_html_display(ident,
                                          dtd_str=dtd_str)
        filename = 'js/test/fixtures/add_element/5.json'
        open(os.path.join('webmedia', filename), 'w').write(json.dumps(dic))

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            'data-url="%s"'
            ' data-btn-selector="%s"'
            ' data-id="%s"' % (filename, btn_selector, ident),
        )
        lis += [test_html]

        dtd_str = u'''
            <!ELEMENT texts (text+)>
            <!ELEMENT text (subtext)>
            <!ELEMENT subtext (#PCDATA)>
            '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>
    <subtext>Hello</subtext>
  </text>
  <text>
    <subtext>World</subtext>
  </text>
</texts>
'''
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )

        o = obj['list__text'].add('text', index=0)

        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "[data-elt-id='%s']" % escape_attr(
            o._prefix_str)
        dic = get_data_from_str_id_for_html_display(ident,
                                          dtd_str=dtd_str)
        filename = 'js/test/fixtures/add_element/6.json'
        open(os.path.join('webmedia', filename), 'w').write(json.dumps(dic))

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            'data-url="%s"'
            ' data-btn-selector="%s"'
            ' data-id="%s"' % (filename, btn_selector, ident),
        )
        lis += [test_html]

        o._parent_obj.remove(o)
        o = obj['list__text'].add('text', index=1)

        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "[data-elt-id='%s']" % escape_attr(
            o._prefix_str)
        dic = get_data_from_str_id_for_html_display(ident,
                                          dtd_str=dtd_str)
        filename = 'js/test/fixtures/add_element/7.json'
        open(os.path.join('webmedia', filename), 'w').write(json.dumps(dic))

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            'data-url="%s"'
            ' data-btn-selector="%s"'
            ' data-id="%s"' % (filename, btn_selector, ident),
        )
        lis += [test_html]

        o._parent_obj.remove(o)
        o = obj['list__text'].add('text', index=2)

        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "[data-elt-id='%s']" % escape_attr(
            o._prefix_str)
        dic = get_data_from_str_id_for_html_display(ident,
                                          dtd_str=dtd_str)
        filename = 'js/test/fixtures/add_element/8.json'
        open(os.path.join('webmedia', filename), 'w').write(json.dumps(dic))

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            'data-url="%s"'
            ' data-btn-selector="%s"'
            ' data-id="%s"' % (filename, btn_selector, ident),
        )
        lis += [test_html]

        filename = 'webmedia/js/test/fixtures/add_element/test.html'
        open(filename, 'w').write('<div>%s</div>' % ''.join(lis))

        document_root = html.fromstring(''.join(lis))
        h = etree.tostring(document_root, encoding='unicode',
                           pretty_print=True)
        filename = 'webmedia/js/test/fixtures/add_element/test-debug.html'
        open(filename, 'w').write(h)

    def test_remove_element(self):
        dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (subtext)>
        <!ELEMENT text2 (subtext?)>
        <!ELEMENT subtext (#PCDATA)>
        '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>
    <subtext>Tag 1</subtext>
  </text1>
  <text2>
    <subtext>Tag 2</subtext>
  </text2>
  <text2>
    <subtext>Tag 3</subtext>
  </text2>
  <text2>
    <subtext>Tag 4</subtext>
  </text2>
</texts>
'''
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)

        lis = []

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )
        self.assertEqual(len(obj['list__text1_text2']), 4)
        o = obj['list__text1_text2'][0]
        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "[data-target='#%s']" % escape_attr(ident)
        o.delete()
        self.assertEqual(len(obj['list__text1_text2']), 3)

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            ' data-btn-selector="%s"' % btn_selector
        )
        lis += [test_html]

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )

        o = obj['list__text1_text2'][1]
        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "[data-target='#%s']" % escape_attr(ident)
        o.delete()
        self.assertEqual(len(obj['list__text1_text2']), 2)
        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            ' data-btn-selector="%s"' % btn_selector
        )
        lis += [test_html]

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )

        o = obj['list__text1_text2'][1]['subtext']
        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "[data-target='#%s']" % escape_attr(ident)
        o.delete()
        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            ' data-btn-selector="%s"' % btn_selector
        )
        lis += [test_html]

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )

        o = obj['list__text1_text2'][-1]
        ident = ':'.join(o.prefixes_no_cache)
        btn_selector = "[data-target='#%s']" % escape_attr(ident)
        o.delete()
        self.assertEqual(len(obj['list__text1_text2']), 1)
        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_jstree + input_html + expected_jstree + expected_html,
            'dom-test',
            ' data-btn-selector="%s"' % btn_selector
        )
        lis += [test_html]

        filename = 'webmedia/js/test/fixtures/remove_element.html'
        open(filename, 'w').write('<div>%s</div>' % ''.join(lis))

    def test_move_element(self):
        lis = []
        dtd_str = u'''
        <!ELEMENT texts (text)>
        <!ELEMENT text (block, (subtext1|subtext2)*)>
        <!ELEMENT subtext1 (minitext*)>
        <!ELEMENT subtext2 (minitext*)>
        <!ELEMENT block (#PCDATA)>
        <!ELEMENT minitext (#PCDATA)>
        '''
        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
<text>
  <block>tag 0</block>
  <subtext1>
    <minitext>tag 1</minitext>
  </subtext1>
  <subtext2>
    <minitext>tag 2</minitext>
    <minitext>tag 3</minitext>
  </subtext2>
  <subtext1>
    <minitext>tag 4</minitext>
  </subtext1>
  <subtext1>
    <minitext>tag 5</minitext>
  </subtext1>
</text>
</texts>'''
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)

        input_html = generate_html_block(
            obj.to_html(),
            'dom-input-html'
        )
        input_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-input-jstree'
        )

        # Move first obj in position 1
        lis_obj = obj['text']['list__subtext1_subtext2']
        sub1 = lis_obj[0]
        from_ident = ':'.join(sub1.prefixes_no_cache)
        to_position = 1
        sub1.delete()
        lis_obj.insert(to_position, sub1)

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_html + input_jstree + expected_html + expected_jstree,
            'dom-test',
            ' data-id="%s"'
            # We should get to_position + 1 because we have an element before
            # the list: when we get node.children we get all children not only
            # the list children
            ' data-children-index="%s"'
            ' data-position="after"' % (from_ident, to_position + 1)
        )
        lis += [test_html]

        obj = dic[root.tag]()
        obj.load_from_xml(root)

        # Move first obj in last position (3)
        lis_obj = obj['text']['list__subtext1_subtext2']
        sub1 = lis_obj[0]
        from_ident = ':'.join(sub1.prefixes_no_cache)
        to_position = 3
        sub1.delete()
        lis_obj.insert(to_position, sub1)

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_html + input_jstree + expected_html + expected_jstree,
            'dom-test',
            ' data-id="%s"'
            # We should get to_position + 1 because we have an element before
            # the list: when we get node.children we get all children not only
            # the list children
            ' data-children-index="%s"'
            ' data-position="after"' % (from_ident, to_position + 1)
        )
        lis += [test_html]

        obj = dic[root.tag]()
        obj.load_from_xml(root)

        # Move second obj in position 2
        lis_obj = obj['text']['list__subtext1_subtext2']
        sub1 = lis_obj[1]
        from_ident = ':'.join(sub1.prefixes_no_cache)
        to_position = 2
        sub1.delete()
        lis_obj.insert(to_position, sub1)

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_html + input_jstree + expected_html + expected_jstree,
            'dom-test',
            ' data-id="%s"'
            # We should get to_position + 1 because we have an element before
            # the list: when we get node.children we get all children not only
            # the list children
            ' data-children-index="%s"'
            ' data-position="after"' % (from_ident, to_position + 1)
        )
        lis += [test_html]

        obj = dic[root.tag]()
        obj.load_from_xml(root)

        # Move last obj in position 0
        lis_obj = obj['text']['list__subtext1_subtext2']
        sub1 = lis_obj[-1]
        from_ident = ':'.join(sub1.prefixes_no_cache)
        to_position = 0
        sub1.delete()
        lis_obj.insert(to_position, sub1)

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_html + input_jstree + expected_html + expected_jstree,
            'dom-test',
            ' data-id="%s"'
            # We should get to_position + 1 because we have an element before
            # the list: when we get node.children we get all children not only
            # the list children
            ' data-children-index="%s"'
            ' data-position="before"' % (from_ident, to_position + 1)
        )
        lis += [test_html]

        obj = dic[root.tag]()
        obj.load_from_xml(root)

        # Move last obj in position 1
        lis_obj = obj['text']['list__subtext1_subtext2']
        sub1 = lis_obj[-1]
        from_ident = ':'.join(sub1.prefixes_no_cache)
        to_position = 1
        sub1.delete()
        lis_obj.insert(to_position, sub1)

        expected_html = generate_html_block(
            obj.to_html(),
            'dom-expected-html'
        )
        expected_jstree = generate_html_block(
            json.dumps(obj.to_jstree_dict()),
            'dom-expected-jstree'
        )

        test_html = generate_html_block(
            input_html + input_jstree + expected_html + expected_jstree,
            'dom-test',
            ' data-id="%s"'
            # We should get to_position + 1 because we have an element before
            # the list: when we get node.children we get all children not only
            # the list children
            ' data-children-index="%s"'
            ' data-position="before"' % (from_ident, to_position + 1)
        )
        lis += [test_html]


        filename = 'webmedia/js/test/fixtures/move_element.html'
        open(filename, 'w').write('<div>%s</div>' % ''.join(lis))
