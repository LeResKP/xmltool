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
