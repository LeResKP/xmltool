#!/usr/bin/env python

from unittest import TestCase
from xmltool.render import (
    Render,
    ReadonlyRender,
    ContenteditableRender,
    CKeditorRender,
    attrs_to_str
)
from xmltool.elements import TextElement


class TestFunctions(TestCase):

    def test_attrs_to_str(self):
        res = attrs_to_str([])
        self.assertEqual(res, '')
        res = attrs_to_str([('name', 'myname')])
        self.assertEqual(res, ' name="myname"')

        res = attrs_to_str([('name', 'myname'), ('name', 'myname2')])
        self.assertEqual(res, ' name="myname myname2"')


class TestRender(TestCase):

    def test_add_add_button(self):
        r = Render()
        self.assertEqual(r.add_add_button(), True)

    def test_add_delete_button(self):
        r = Render()
        self.assertEqual(r.add_delete_button(), True)

    def test_add_comment(self):
        r = Render()
        self.assertEqual(r.add_comment(), True)

    def test_text_element_to_html(self):
        r = Render()
        obj = type('SubSubCls', (TextElement, ),
                   {'tagname': 'subsub',
                    'children_classes': []})()
        attrs = [('class', 'test')]
        value = 'Hello world'
        res = r.text_element_to_html(obj, attrs, value)
        expected = ('<textarea class="form-control test">'
                    'Hello world</textarea>')
        self.assertEqual(res, expected)


class TestReadonlyRender(TestCase):

    def test_add_add_button(self):
        r = ReadonlyRender()
        self.assertEqual(r.add_add_button(), False)

    def test_add_delete_button(self):
        r = ReadonlyRender()
        self.assertEqual(r.add_delete_button(), False)

    def test_add_comment(self):
        r = ReadonlyRender()
        self.assertEqual(r.add_comment(), False)

    def test_text_element_to_html(self):
        r = ReadonlyRender()
        obj = type('SubSubCls', (TextElement, ),
                   {'tagname': 'subsub',
                    'children_classes': []})()
        attrs = [('class', 'test')]
        value = 'Hello world'
        res = r.text_element_to_html(obj, attrs, value)
        expected = ('<textarea class="form-control test" '
                    'readonly="readonly">Hello world</textarea>')
        self.assertEqual(res, expected)


class TestContenteditableRender(TestCase):

    def test_add_add_button(self):
        r = ContenteditableRender()
        self.assertEqual(r.add_add_button(), True)

    def test_add_delete_button(self):
        r = ContenteditableRender()
        self.assertEqual(r.add_delete_button(), True)

    def test_add_comment(self):
        r = ContenteditableRender()
        self.assertEqual(r.add_comment(), True)

    def test_text_element_to_html(self):
        r = ContenteditableRender()
        obj = type('SubSubCls', (TextElement, ),
                   {'tagname': 'subsub',
                    'children_classes': []})()
        attrs = [('class', 'test')]
        value = 'Hello world'
        res = r.text_element_to_html(obj, attrs, value)
        expected = (
            '<textarea class="form-control hidden test">'
            'Hello world</textarea>'
            '<div class="contenteditable form-control subsub" '
            'contenteditable="true" spellcheck="false" '
            'id="subsub:_contenteditable">Hello world</div>')
        self.assertEqual(res, expected)

        r = ContenteditableRender(
            extra_div_attrs_func=lambda obj: [('class', 'plop')])
        obj = type('SubSubCls', (TextElement, ),
                   {'tagname': 'subsub',
                    'children_classes': []})()
        attrs = [('class', 'test')]
        value = 'Hello world'
        res = r.text_element_to_html(obj, attrs, value)
        expected = (
            '<textarea class="form-control hidden test">'
            'Hello world</textarea>'
            '<div class="contenteditable form-control subsub plop" '
            'contenteditable="true" spellcheck="false" '
            'id="subsub:_contenteditable">Hello world</div>')
        self.assertEqual(res, expected)

        value = 'Hello world\nNew line'
        res = r.text_element_to_html(obj, attrs, value)
        expected = (
            '<textarea class="form-control hidden test">'
            'Hello world\nNew line</textarea>'
            '<div class="contenteditable form-control subsub plop" '
            'contenteditable="true" spellcheck="false" '
            'id="subsub:_contenteditable">Hello world<br />New line</div>')
        self.assertEqual(res, expected)


class TestCKeditorRender(TestCase):

    def test_text_element_to_html(self):
        r = CKeditorRender()
        obj = type('SubSubCls', (TextElement, ),
                   {'tagname': 'subsub',
                    'children_classes': []})()
        attrs = [('class', 'test')]
        value = '  Hello world\nNew line'
        res = r.text_element_to_html(obj, attrs, value)
        expected = (
            '<textarea class="form-control hidden test">'
            '  Hello world\nNew line</textarea>'
            '<div class="contenteditable form-control subsub" '
            'contenteditable="true" spellcheck="false" '
            'id="subsub:_contenteditable"> &nbsp;Hello world<br />New line'
            '</div>')
        self.assertEqual(res, expected)
