#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import os.path
from xmltools import factory


class TestFactory(TestCase):

    def test_load(self):
        obj = factory.load('tests/exercise.xml')
        self.assertEqual(obj.tagname, 'Exercise')
        try:
            obj = factory.load('tests/exercise-notvalid.xml')
            assert 0
        except etree.DocumentInvalid:
            pass

        obj = factory.load('tests/exercise-notvalid.xml',
                                 validate_xml=False)
        self.assertEqual(obj.tagname, 'Exercise')

    def test_load_string(self):
        xml_str = open('tests/exercise.xml', 'r').read()
        obj = factory.load_string(xml_str)
        self.assertEqual(obj.tagname, 'Exercise')
        try:
            xml_str = open('tests/exercise-notvalid.xml', 'r').read()
            obj = factory.load_string(xml_str)
            assert 0
        except etree.DocumentInvalid:
            pass

        xml_str = open('tests/exercise-notvalid.xml', 'r').read()
        obj = factory.load_string(xml_str,
                                 validate_xml=False)
        self.assertEqual(obj.tagname, 'Exercise')

    def test_generate_form(self):
        html = factory.generate_form('tests/exercise.xml')
        self.assertTrue('<form method="POST" id="xmltools-form">' in html)

        html = factory.generate_form('tests/exercise.xml',
                                        form_action='/action/submit')
        self.assertTrue('<form action="/action/submit" method="POST" '
                        'id="xmltools-form">' in html)

    def test_update_xml_file(self):
        filename = 'tests/test.xml'
        self.assertFalse(os.path.isfile(filename))
        try:
            data = {
                '_encoding': 'UTF-8',
                '_dtd_url': 'http://xml-tools.lereskp.fr/static/exercise.dtd',
                '_root_tag': 'Exercise',
                'Exercise.question': 'How are you?',
            }
            obj = factory.update_xml_file(filename, data)
            self.assertTrue(obj)
            result = open(filename, 'r').read()
            expected = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise PUBLIC "http://xml-tools.lereskp.fr/static/exercise.dtd" "http://xml-tools.lereskp.fr/static/exercise.dtd">
<Exercise>
  <number/>
</Exercise>
'''
            self.assertEqual(result, expected)
            transform_func = lambda  txt: txt.replace('number',
                                                      'number-updated')
            obj = factory.update_xml_file(filename, data,
                                          transform=transform_func)
            self.assertTrue(obj)
            result = open(filename, 'r').read()
            expected = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise PUBLIC "http://xml-tools.lereskp.fr/static/exercise.dtd" "http://xml-tools.lereskp.fr/static/exercise.dtd">
<Exercise>
  <number-updated/>
</Exercise>
'''
            self.assertEqual(result, expected)
        finally:
            if os.path.isfile(filename):
                os.remove(filename)

    def test_get_jstree_node_data(self):
        dtd_url = 'http://xml-tools.lereskp.fr/static/exercise.dtd'
        elt_id = 'Exercise:question'
        dic = factory.get_jstree_node_data(dtd_url, elt_id)
        self.assertEqual(len(dic), 2)
        expected_elt = {
            'data': 'question', 
            'attr': {'id': 'tree_Exercise:question',
                     'class': 'tree_Exercise:question'},
            'metadata': {'id': 'Exercise:question'}}
        self.assertEqual(dic['elt'], expected_elt)
        expected_previous = [('.tree_Exercise:test', 'after'),
                             ('#tree_Exercise:number', 'after'),
                             ('.tree_:Exercise', 'inside')]
        self.assertEqual(dic['previous'], expected_previous)
