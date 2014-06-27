#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import os.path
from xmltool import factory, dtd_parser


class TestFactory(TestCase):

    def test_load(self):
        obj = factory.load('tests/exercise.xml')
        self.assertEqual(obj.tagname, 'Exercise')
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
        except etree.DocumentInvalid, e:
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
        xml_str = unicode(xml_str)
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
        dic = dtd_parser.parse(dtd_url=dtd_url)
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
            except Exception, e:
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
                    '<a class="btn-add" data-elt-id="choice">'
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
                    '<a class="btn-add" data-elt-id="choice">'
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
                    '<a class="btn-add" data-elt-id="choice">'
                    'Add choice</a>'
                    '</form>')
        self.assertEqual(result, expected)
