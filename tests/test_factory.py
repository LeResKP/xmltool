#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import os.path
from xmltools import factory


class TestFactory(TestCase):

    def test_load(self):
        obj = factory.load('tests/exercise.xml')
        self.assertEqual(obj._tagname, 'Exercise')
        try:
            obj = factory.load('tests/exercise-notvalid.xml')
            assert 0
        except etree.DocumentInvalid, e:
            self.assertEqual(
                str(e),
                'Element comments content does not follow the DTD, expecting '
                '(comment)+, got (), line 17'
            )
        obj = factory.load('tests/exercise-notvalid.xml',
                                 validate=False)
        self.assertEqual(obj._tagname, 'Exercise')

    def test_load_string(self):
        xml_str = open('tests/exercise.xml', 'r').read()
        obj = factory.load_string(xml_str)
        self.assertEqual(obj._tagname, 'Exercise')
        try:
            xml_str = open('tests/exercise-notvalid.xml', 'r').read()
            obj = factory.load_string(xml_str)
            assert 0
        except etree.DocumentInvalid, e:
            self.assertEqual(
                str(e),
                'Element comments content does not follow the DTD, expecting '
                '(comment)+, got (), line 17'
            )

        xml_str = open('tests/exercise-notvalid.xml', 'r').read()
        obj = factory.load_string(xml_str,
                                 validate=False)
        self.assertEqual(obj._tagname, 'Exercise')

    def test_generate_form(self):
        html = factory.generate_form('tests/exercise.xml')
        self.assertTrue('<form method="POST" id="xmltools-form">' in html)

        html = factory.generate_form('tests/exercise.xml',
                                        form_action='/action/submit')
        self.assertTrue('<form action="/action/submit" method="POST" '
                        'id="xmltools-form">' in html)
        self.assertTrue(
            '<input type="hidden" name="_xml_filename" id="_xml_filename" '
            'value="tests/exercise.xml" />' in html)
        self.assertTrue(
            '<input type="hidden" name="_xml_dtd_url" id="_xml_dtd_url" '
            'value="http://xml-tools.lereskp.fr/static/exercise.dtd" />' in
            html)
        self.assertTrue(
            '<input type="hidden" name="_xml_encoding" id="_xml_encoding" '
            'value="UTF-8" />' in html)

        self.assertTrue('<fieldset class="Exercise">' in html)

    def test_update(self):
        filename = 'tests/test.xml'
        self.assertFalse(os.path.isfile(filename))
        try:
            data = {
                '_xml_encoding': 'UTF-8',
                '_xml_dtd_url': 'http://xml-tools.lereskp.fr/static/exercise.dtd',
                'Exercise': {},
            }
            obj = factory.update(filename, data)
            self.assertTrue(obj)
            result = open(filename, 'r').read()
            expected = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise SYSTEM "http://xml-tools.lereskp.fr/static/exercise.dtd">
<Exercise>
  <number/>
</Exercise>
'''
            self.assertEqual(result, expected)
            transform_func = lambda  txt: txt.replace('number',
                                                      'number-updated')
            obj = factory.update(filename, data, transform=transform_func)
            self.assertTrue(obj)
            result = open(filename, 'r').read()
            expected = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise SYSTEM "http://xml-tools.lereskp.fr/static/exercise.dtd">
<Exercise>
  <number-updated/>
</Exercise>
'''
            self.assertEqual(result, expected)
        finally:
            if os.path.isfile(filename):
                os.remove(filename)

