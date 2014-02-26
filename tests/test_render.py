#!/usr/bin/env python

from unittest import TestCase
from xmltool.render import Render, ReadonlyRender, attrs_to_str
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
