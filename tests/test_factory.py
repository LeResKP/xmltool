#!/usr/bin/env python

from xmltool.testbase import BaseTest
from lxml import etree
import os.path
from xmltool import factory, dtd_parser, elements, dtd
from xmltool.elements import escape_attr


class TestFactory(BaseTest):

    def test_create(self):
        obj = factory.create('Exercise', dtd_url='tests/exercise.dtd')
        self.assertEqual(obj.tagname, 'Exercise')

    def test_load(self):
        obj = factory.load('tests/exercise.xml')
        self.assertEqual(obj.tagname, 'Exercise')
        comment = obj['test'][1]['comments']['comment'][1]
        self.assertEqual(comment.text, '<div>My comment 2</div>')
        self.assertEqual(
            etree.tostring(comment.to_xml()),
            b'<comment><![CDATA[<div>My comment 2</div>]]></comment>')
        try:
            obj = factory.load('tests/exercise-notvalid.xml')
            assert 0
        except etree.DocumentInvalid as e:
            self.assertEqual(
                str(e),
                'Element comments content does not follow the DTD, expecting '
                '(comment)+, got (), line 17'
            )
        obj = factory.load('tests/exercise-notvalid.xml',
                                 validate=False)
        self.assertEqual(obj.tagname, 'Exercise')

    def test_load_string(self):
        xml_str = open('tests/exercise.xml', 'r').read()
        xml_str = xml_str.replace('exercise.dtd', 'tests/exercise.dtd')
        obj = factory.load_string(xml_str)
        self.assertEqual(obj.tagname, 'Exercise')
        try:
            xml_str = open('tests/exercise-notvalid.xml', 'r').read()
            xml_str = xml_str.replace('exercise.dtd', 'tests/exercise.dtd')
            obj = factory.load_string(xml_str)
            assert 0
        except etree.DocumentInvalid as e:
            self.assertEqual(
                str(e),
                'Element comments content does not follow the DTD, expecting '
                '(comment)+, got (), line 17'
            )

        xml_str = open('tests/exercise-notvalid.xml', 'r').read()
        xml_str = xml_str.replace('exercise.dtd', 'tests/exercise.dtd')
        obj = factory.load_string(xml_str,
                                 validate=False)
        self.assertEqual(obj.tagname, 'Exercise')

    def test_load_string_unicode(self):
        xml_str = open('tests/exercise-notvalid.xml', 'r').read()
        xml_str = xml_str.replace('exercise.dtd', 'tests/exercise.dtd')
        obj = factory.load_string(xml_str,
                                  validate=False)
        self.assertEqual(obj.tagname, 'Exercise')

    def test_generate_form(self):
        html = factory.generate_form('tests/exercise.xml')
        self.assertTrue('<form method="POST" id="xmltool-form">' in html)

        html = factory.generate_form('tests/exercise.xml',
                                     form_action='/action/submit')
        self.assertTrue('<form method="POST" action="/action/submit" '
                        'id="xmltool-form">' in html)
        self.assertTrue(
            '<input type="hidden" name="_xml_filename" id="_xml_filename" '
            'value="tests/exercise.xml" />' in html)
        self.assertTrue(
            '<input type="hidden" name="_xml_dtd_url" id="_xml_dtd_url" '
            'value="exercise.dtd" />' in
            html)
        self.assertTrue(
            '<input type="hidden" name="_xml_encoding" id="_xml_encoding" '
            'value="UTF-8" />' in html)

        self.assertTrue('<div class="panel panel-default '
                        'Exercise" id="Exercise">' in html)

    def test_generate_form_from_obj(self):
        obj = factory.load('tests/exercise.xml')
        html = factory.generate_form_from_obj(obj)
        self.assertTrue('<form method="POST" id="xmltool-form">' in html)
        self.assertTrue('id="_xml_filename" value=""' in html)

        html = factory.generate_form_from_obj(
            obj,
            form_attrs={'data-action': 'action'})
        self.assertTrue('<form method="POST" data-action="action" '
                        'id="xmltool-form">' in html)

        # Empty object
        dtd_url = 'tests/exercise.dtd'
        dic = dtd.DTD(dtd_url).parse()
        obj = dic['Exercise']()
        html = factory.generate_form_from_obj(obj)
        self.assertTrue('<form method="POST" id="xmltool-form">' in html)
        self.assertTrue('id="_xml_filename" value=""' in html)

    def test_update(self):
        filename = 'tests/test.xml'
        self.assertFalse(os.path.isfile(filename))
        try:
            data = {
                '_xml_encoding': 'UTF-8',
                '_xml_dtd_url': 'exercise.dtd',
                'Exercise': {},
            }
            obj = factory.update(filename, data)
            self.assertTrue(obj)
            result = open(filename, 'r').read()
            expected = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise SYSTEM "exercise.dtd">
<Exercise>
  <number></number>
</Exercise>
'''
            self.assertEqual(result, expected)
            data = {
                '_xml_encoding': 'UTF-8',
                '_xml_dtd_url': 'exercise.dtd',
                'Exercise': {},
                'fake': {},
            }
            try:
                obj = factory.update(filename, data)
                assert 0
            except Exception as e:
                self.assertEqual(str(e), 'Bad data')

            data = {
                '_xml_encoding': 'UTF-8',
                '_xml_dtd_url': 'exercise.dtd',
                'Exercise': {},
            }
            transform_func = lambda  txt: txt.replace('number',
                                                      'number-updated')
            obj = factory.update(filename, data, transform=transform_func)
            self.assertTrue(obj)
            result = open(filename, 'r').read()
            expected = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise SYSTEM "exercise.dtd">
<Exercise>
  <number-updated></number-updated>
</Exercise>
'''
            self.assertEqual(result, expected)
        finally:
            if os.path.isfile(filename):
                os.remove(filename)

    def test_new(self):
        dtd_url = 'tests/exercise.dtd'
        root_tag = 'choice'
        result = factory.new(dtd_url, root_tag)
        expected = ('<form method="POST" id="xmltool-form">'
                    '<input type="hidden" name="_xml_filename" '
                    'id="_xml_filename" value="" />'
                    '<input type="hidden" name="_xml_dtd_url" '
                    'id="_xml_dtd_url" '
                    'value="tests/exercise.dtd" '
                    '/>'
                    '<input type="hidden" name="_xml_encoding" '
                    'id="_xml_encoding" value="UTF-8" />'
                    '<a class="btn-add btn-add-choice" data-elt-id="choice">'
                    'Add choice</a>'
                    '</form>')
        self.assertEqual(result, expected)

        result = factory.new(dtd_url, root_tag, '/submit')
        expected = ('<form method="POST" action="/submit" id="xmltool-form">'
                    '<input type="hidden" name="_xml_filename" '
                    'id="_xml_filename" value="" />'
                    '<input type="hidden" name="_xml_dtd_url" '
                    'id="_xml_dtd_url" '
                    'value="tests/exercise.dtd" '
                    '/>'
                    '<input type="hidden" name="_xml_encoding" '
                    'id="_xml_encoding" value="UTF-8" />'
                    '<a class="btn-add btn-add-choice" data-elt-id="choice">'
                    'Add choice</a>'
                    '</form>')
        self.assertEqual(result, expected)

        result = factory.new(dtd_url, root_tag, '/submit',
                             form_attrs={'data-action': 'action'})
        expected = ('<form method="POST" action="/submit" '
                    'data-action="action" id="xmltool-form">'
                    '<input type="hidden" name="_xml_filename" '
                    'id="_xml_filename" value="" />'
                    '<input type="hidden" name="_xml_dtd_url" '
                    'id="_xml_dtd_url" '
                    'value="tests/exercise.dtd" '
                    '/>'
                    '<input type="hidden" name="_xml_encoding" '
                    'id="_xml_encoding" value="UTF-8" />'
                    '<a class="btn-add btn-add-choice" data-elt-id="choice">'
                    'Add choice</a>'
                    '</form>')
        self.assertEqual(result, expected)

    def test_getElementData(self):
        data = {}
        elt_id = 'texts:list__list:1:list:text'
        res = factory.getElementData(elt_id, data)
        self.assertEqual(res, {'text': {}})

        data = {
            'texts': {
                'list__list': [
                    {'list': {'text': {'_value': 'Hello'}}},
                ]
            }
        }
        res = factory.getElementData(elt_id, data)
        self.assertEqual(res, {'text': {}})

        data = {
            'texts': {
                'list__list': [
                    {'list': {'text': {'_value': 'Hello'}}},
                    {'list': {'text': {'_value': 'world'}}}
                ]
            }
        }
        res = factory.getElementData(elt_id, data)
        self.assertEqual(res, {'text': {'_value': 'world'}})

    def test__get_obj_from_str_id_html(self):
        dtd_str = u'''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:unexisting'
        try:
            obj = factory._get_obj_from_str_id(str_id, dtd_str=dtd_str)
            html = obj.to_html()
            assert(False)
        except Exception as e:
            self.assertEqual(str(e), 'Invalid child unexisting')

        str_id = 'texts:text'
        obj = factory._get_obj_from_str_id(str_id, dtd_str=dtd_str)
        html = obj.to_html()
        expected = (
            '<div id="texts:text" class="xt-container-text">'
            '<label>text</label>'
            '<span class="btn-external-editor" '
            'ng-click="externalEditor(this)"></span>'
            '<a data-comment-name="texts:text:_comment" '
            'class="btn-comment" title="Add comment"></a>'
            '<textarea class="form-control text" name="texts:text:_value" '
            'rows="1"></textarea>'
            '</div>')
        self.assertEqual(html, expected)

    def test__get_obj_from_str_id_list(self):
        dtd_str = u'''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:list__text:0:text'
        obj = factory._get_obj_from_str_id(str_id, dtd_str=dtd_str)
        html = obj.to_html()
        expected = (
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
        )
        self.assertEqual_(html, expected)

        dtd_str = u'''
        <!ELEMENT texts (list*)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        '''
        str_id = 'texts:list__list:0:list:text'
        obj = factory._get_obj_from_str_id(str_id, dtd_str=dtd_str)
        html = obj.to_html()
        expected = (
            '<div id="texts:list__list:0:list:text" class="xt-container-text">'
            '<label>text</label>'
            '<span class="btn-external-editor" '
            'ng-click="externalEditor(this)">'
            '</span>'
            '<a data-comment-name="texts:list__list:0:list:text:_comment" '
            'class="btn-comment" title="Add comment"></a>'
            '<textarea class="form-control text" name="texts:list__list:0:list:text:_value" '
            'rows="1"></textarea>'
            '</div>')
        self.assertEqual(html, expected)

    def test__get_obj_from_str_id(self):
        dtd_str = u'''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts'
        data = {}
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'texts')

        str_id = 'texts:tag2'
        data = {
            'texts': {
                'tag2': {
                    '_value': 'Hello world',
                }
            }
        }
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'tag2')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj._parent_obj.tagname, 'texts')

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
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'text')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj._parent_obj.tagname, 'list')
        self.assertEqual(len(obj._parent_obj._parent_obj), 1)

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
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'text')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj._parent_obj.tagname, 'list')
        list_obj = obj._parent_obj._parent_obj
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
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'text')
        self.assertEqual(obj.text, '')
        self.assertEqual(obj._parent_obj.tagname, 'list')
        list_obj = obj._parent_obj._parent_obj
        self.assertEqual(len(list_obj), 3)
        self.assertFalse(isinstance(list_obj[0], elements.EmptyElement))
        self.assertTrue(isinstance(list_obj[1], elements.EmptyElement))
        self.assertFalse(isinstance(list_obj[2], elements.EmptyElement))
        self.assertEqual(list_obj[2], obj._parent_obj)

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
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'text')
        self.assertEqual(obj.text, '')
        self.assertEqual(obj._parent_obj.tagname, 'list')
        list_obj = obj._parent_obj._parent_obj
        self.assertEqual(len(list_obj), 3)
        self.assertFalse(isinstance(list_obj[0], elements.EmptyElement))
        # The good element has been generated
        self.assertFalse(isinstance(list_obj[1], elements.EmptyElement))
        self.assertFalse(isinstance(list_obj[2], elements.EmptyElement))
        self.assertEqual(list_obj[1], obj._parent_obj)

    def test__get_obj_from_str_id_choices(self):
        dtd_str = u'''
        <!ELEMENT texts ((tag1|tag2)*)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts'
        data = {}
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
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
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'tag1')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj._parent_obj.tagname, 'list__tag1_tag2')

        dtd_str = u'''
        <!ELEMENT texts (tag1|tag2)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts'
        data = {}
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'texts')

        str_id = 'texts:tag1'
        data = {
            'texts': {
                'tag1': {'_value': 'Hello world'}
            }
        }
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'tag1')
        self.assertEqual(obj.text, 'Hello world')
        self.assertEqual(obj._parent_obj.tagname, 'choice__tag1_tag2')
        self.assertEqual(obj.parent.tagname, 'texts')

        data = {
            'texts': {}
        }
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        self.assertEqual(obj.tagname, 'tag1')
        self.assertEqual(obj.text, '')
        self.assertEqual(obj._parent_obj.tagname, 'choice__tag1_tag2')
        self.assertEqual(obj.parent.tagname, 'texts')

    def test_get_data_from_str_id_for_html_display(self):
        dtd_str = u'''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        str_id = 'texts:tag2'
        result = factory.get_data_from_str_id_for_html_display(str_id, dtd_str=dtd_str)
        expected = {
            'previous': [
                ('after', escape_attr('.tree_texts:list__list') + ':last'),
                ('after', escape_attr('.tree_texts:tag1') + ':last'),
                ('inside', escape_attr('#tree_texts'))],
            'html': ('<div id="texts:tag2" class="xt-container-tag2">'
                     '<label>tag2</label>'
                     '<span class="btn-external-editor" '
                     'ng-click="externalEditor(this)"></span>'
                     '<a data-comment-name="texts:tag2:_comment" '
                     'class="btn-comment" title="Add comment"></a>'
                     '<textarea class="form-control tag2" name="texts:tag2:_value" '
                     'rows="1"></textarea></div>'),
            'jstree_data': {
                'text': 'tag2',
                'li_attr': {
                    'class': 'tree_texts:tag2 tag2'
                },
                'a_attr': {
                    'id': 'tree_texts:tag2',
                },
                'children': [],
                'state': {'opened': True},
            },
            'elt_id': str_id,
        }
        self.assertEqual(result, expected)

    def test__get_data_for_html_display(self):
        dtd_str = u'''
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
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        res = factory._get_data_for_html_display(obj)
        expected = {
            'elt_id': 'texts:list__list:0:list:text1',
            'html': (
                '<div id="texts:list__list:0:list:text1" '
                'class="xt-container-text1">'
                '<label>text1</label>'
                '<span class="btn-external-editor" '
                'ng-click="externalEditor(this)">'
                '</span>'
                '<a data-comment-name="texts:list__list:0:list:text1:_comment" '
                'class="btn-comment" title="Add comment"></a>'
                '<textarea class="form-control text1" '
                'name="texts:list__list:0:list:text1:_value" rows="1">'
                'Hello world</textarea>'
                '</div>'),
            'jstree_data': {
                'li_attr': {
                    'class': 'tree_texts:list__list:0:list:text1 text1',
                },
                'a_attr': {
                    'id': 'tree_texts:list__list:0:list:text1'
                },
                'children': [],
                'text': u'text1 <span class="_tree_text">(Hello world)</span>',
                'state': {'opened': True},
            },
            'previous': [
                ('inside', escape_attr('#tree_texts:list__list:0:list'))
            ]
        }
        self.assertEqual(res, expected)

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
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        res = factory._get_data_for_html_display(obj)
        expected = {
            'elt_id': 'texts:list__list:0:list',
            'html': (
                '<a class="btn-add btn-add-list btn-list" '
                'data-elt-id="texts:list__list:0:list">New list</a>'
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
                '<div id="texts:list__list:0:list:text1" '
                'class="xt-container-text1">'
                '<label>text1</label>'
                '<span class="btn-external-editor" '
                'ng-click="externalEditor(this)">'
                '</span>'
                '<a data-comment-name="texts:list__list:0:list:text1:_comment"'
                ' class="btn-comment" title="Add comment"></a>'
                '<textarea class="form-control text1" '
                'name="texts:list__list:0:list:text1:_value" rows="1">'
                'Hello world</textarea>'
                '</div>'
                '</div>'
                '</div>'
            ),
            'jstree_data': {
                'li_attr': {
                    'class': 'tree_texts:list__list list',
                },
                'a_attr': {
                    'id': 'tree_texts:list__list:0:list'
                },
                'children': [{
                    'li_attr': {
                        'class': 'tree_texts:list__list:0:list:text1 text1',
                    },
                    'a_attr': {
                        'id': 'tree_texts:list__list:0:list:text1'
                    },
                    'children': [],
                    'text': ('text1 <span class="_tree_text">'
                             '(Hello world)</span>'),
                    'state': {'opened': True},
                }],
                'text': 'list',
                'state': {'opened': True},
            },
            'previous': [
                ('after', escape_attr('.tree_texts:tag1') + ':last'),
                ('inside', '#tree_texts')
            ]
        }
        self.assertEqual(res, expected)

        # Test with a choice
        dtd_str = u'''
        <!ELEMENT texts (tag1, list*, tag2)>
        <!ELEMENT list (text1|text2)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
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
        obj = factory._get_obj_from_str_id(str_id,
                                           dtd_str=dtd_str,
                                           data=data)
        res = factory._get_data_for_html_display(obj)
        expected = {
            'elt_id': 'texts:list__list:0:list:text1',
            'html': (
                '<div id="texts:list__list:0:list:text1" '
                'class="xt-container-text1">'
                '<label>text1</label>'
                '<span class="btn-external-editor" '
                'ng-click="externalEditor(this)">'
                '</span>'
                '<select class="btn-add hidden">'
                '<option>New text1/text2</option>'
                '<option class="xt-option-text1" '
                'value="texts:list__list:0:list:text1">text1</option>'
                '<option class="xt-option-text2" '
                'value="texts:list__list:0:list:text2">text2</option>'
                '</select>'
                '<a class="btn-delete" '
                'data-target="#texts:list__list:0:list:text1" title="Delete">'
                '</a>'
                '<a data-comment-name="texts:list__list:0:list:text1:_comment" '
                'class="btn-comment" title="Add comment"></a>'
                '<textarea class="form-control text1" '
                'name="texts:list__list:0:list:text1:_value" rows="1">'
                'Hello world</textarea>'
                '</div>'),
            'jstree_data': {
                'li_attr': {
                    'class': 'tree_texts:list__list:0:list:text1 text1',
                },
                'a_attr': {
                    'id': 'tree_texts:list__list:0:list:text1'
                },
                'children': [],
                'text': u'text1 <span class="_tree_text">(Hello world)</span>',
                'state': {'opened': True},
            },
            'previous': [
                ('inside', escape_attr('#tree_texts:list__list:0:list'))
            ]
        }
        self.assertEqual(res, expected)

    def test__get_parent_to_add_obj(self):
        dtd_str = u'''
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
        parentobj, index = factory._get_parent_to_add_obj(
            str_id, 'text', data, dtd_str=dtd_str)
        # The 'text' element can be pasted here.
        self.assertEqual(parentobj, None)
        self.assertEqual(index, None)

        str_id = 'texts:list__list:0:list'
        parentobj, index = factory._get_parent_to_add_obj(
            str_id, 'list', data, dtd_str=dtd_str)
        self.assertEqual(parentobj.tagname, 'list__list')
        self.assertEqual(index, 1)

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
        parentobj, index = factory._get_parent_to_add_obj(
            str_id, 'text', data, dtd_str=dtd_str)
        self.assertEqual(parentobj.tagname, 'list')
        self.assertEqual(index, 0)

        # Try with missing element
        data = {
            'texts': {
                'list__list': []
            }
        }
        str_id = 'texts:list__list:10:list'
        parentobj, index = factory._get_parent_to_add_obj(
            str_id, 'list', data, dtd_str=dtd_str)
        self.assertEqual(parentobj.tagname, 'list__list')
        self.assertEqual(index, 11)

        # Try with empty element
        # The str_id has no value so didn't exist, we want to make sure we
        # create it correctly
        dtd_str = u'''
        <!ELEMENT texts (tag1, list*)>
        <!ELEMENT list (text)>
        <!ELEMENT text (tag2)>
        <!ELEMENT tag1 (#PCDATA)>
        <!ELEMENT tag2 (#PCDATA)>
        '''
        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {'text': {'tag2': {'_value': 'Hello1'}}}
                    },
                    None,
                    {
                        'list': {'text': {'tag2': {'_value': 'Hello3'}}}
                    }
                ]
            }
        }
        str_id = 'texts:list__list:1:list'
        parentobj, index = factory._get_parent_to_add_obj(
            str_id, 'text', data, dtd_str=dtd_str)
        self.assertEqual(parentobj.tagname, 'list')
        lis = parentobj._parent_obj
        self.assertEqual(lis[1], parentobj)
        self.assertEqual(index, 0)

        data = {
            'texts': {
                'list__list': [
                    {
                        'list': {'text': {'tag2': {'_value': 'Hello1'}}}
                    },
                    {
                        'list': {'text': {'tag2': {'_value': 'Hello2'}}}
                    },
                    {
                        'list': {'text': {'tag2': {'_value': 'Hello3'}}}
                    }
                ]
            }
        }
        str_id = 'texts:list__list:1:list'
        parentobj, index = factory._get_parent_to_add_obj(
            str_id, 'text', data, dtd_str=dtd_str)
        # text already exists, can't add it
        self.assertEqual(parentobj, None)
        self.assertEqual(index, None)

    def test__add_new_element_from_id(self):
        dtd_str = u'''
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
        clipboard_data = {
            'list': {
                'text': {'_value': 'Text to copy'},
            }
        }
        # 'text' element can't be added
        obj = factory._add_new_element_from_id(str_id, data,
                                               clipboard_data,
                                               dtd_str=dtd_str)
        self.assertEqual(obj, None)

        str_id = 'texts:list__list:0:list'
        obj = factory._add_new_element_from_id(str_id, data,
                                               clipboard_data,
                                               dtd_str=dtd_str)
        self.assertEqual(obj.tagname, 'list')
        self.assertEqual(obj['text'].text, 'Text to copy')
        self.assertEqual(len(obj._parent_obj), 2)
