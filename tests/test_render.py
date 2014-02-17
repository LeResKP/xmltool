#!/usr/bin/env python

from unittest import TestCase
from xmltool.render import Render, ReadonlyRender
from xmltool.elements import TextElement


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
                    '_sub_elements': []})()
        attrs = ' class="test"'
        value = 'Hello world'
        res = r.text_element_to_html(obj, attrs, value)
        expected = ('<textarea class="form-control" class="test">'
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
                    '_sub_elements': []})()
        attrs = ' class="test"'
        value = 'Hello world'
        res = r.text_element_to_html(obj, attrs, value)
        expected = '<div>Hello world</div>'
        self.assertEqual(res, expected)
