#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
from xmltool import utils
from test_dtd_parser import EXERCISE_XML, EXERCISE_DTD, INVALID_EXERCISE_XML
import webob


class TestUtils(TestCase):

    def test_is_http_url(self):
        url = 'file.txt'
        self.assertFalse(utils.is_http_url(url))
        url = 'http://file.txt'
        self.assertTrue(utils.is_http_url(url))
        url = 'https://file.txt'
        self.assertTrue(utils.is_http_url(url))

    def test_get_dtd_content(self):
        url = ('https://raw.github.com/LeResKP/'
               'xmltool/master/tests/exercise.dtd')
        http_content = utils.get_dtd_content(url)
        url = 'tests/exercise.dtd'
        fs_content = utils.get_dtd_content(url)
        self.assertEqual(http_content, fs_content)
        url = 'exercise.dtd'
        fs_content = utils.get_dtd_content(url, path='tests/')
        self.assertEqual(http_content, fs_content)

    def test_validate_xml(self):
        root = etree.fromstring(EXERCISE_XML)
        utils.validate_xml(root, EXERCISE_DTD)
        try:
            root = etree.fromstring(INVALID_EXERCISE_XML)
            utils.validate_xml(root, EXERCISE_DTD)
            assert 0
        except etree.DocumentInvalid:
            pass

    def test_to_int(self):
        result = utils.to_int('bob')
        self.assertEqual(result, None)

        result = utils.to_int('10')
        self.assertEqual(result, 10)

    def test_truncate(self):
        s = 'This text should be truncated'
        self.assertEqual(utils.truncate(s, 11), 'This text...')
        self.assertEqual(utils.truncate(s, 25), 'This text should be...')
        self.assertEqual(utils.truncate(s, 60), s)

    def test_numdict_to_list(self):
        dic = {
            'test': {'0': {'test1': {'value': 'v1'}},
                     '1': {'test1': {'value': 'v2'}}
                    }
        }
        utils.numdict_to_list(dic)
        expected = {
            'test': [{'test1': {'value': 'v1'}},
                     {'test1': {'value': 'v2'}}]}
        self.assertEqual(dic, expected)

        dic = {
            'test': {'1': {'test1': {'value': 'v1'}},
                     '3': {'test1': {'value': 'v2'}}
                    }
        }
        utils.numdict_to_list(dic)
        expected = {
            'test': [
                None,
                {'test1': {'value': 'v1'}},
                None,
                {'test1': {'value': 'v2'}}
            ]}
        self.assertEqual(dic, expected)

        dic = {
            'test': {}
        }
        utils.numdict_to_list(dic)
        expected = {
            'test': []
        }
        self.assertEqual(dic, expected)

        dic = {
            'test': {
                '1': {'test1': {'value': 'v1'}},
                '2': {'test1': {'value': 'v2'}},
                '3': {'test1': {'value': 'v3'}},
                '4': {'test1': {'value': 'v4'}},
                '5': {'test1': {'value': 'v5'}},
                '6': {'test1': {'value': 'v6'}},
                '7': {'test1': {'value': 'v7'}},
                '8': {'test1': {'value': 'v8'}},
                '9': {'test1': {'value': 'v9'}},
                '10': {'test1': {'value': 'v10'}}
            }
        }
        utils.numdict_to_list(dic)
        expected = {
            'test': [
                None,
                {'test1': {'value': 'v1'}},
                {'test1': {'value': 'v2'}},
                {'test1': {'value': 'v3'}},
                {'test1': {'value': 'v4'}},
                {'test1': {'value': 'v5'}},
                {'test1': {'value': 'v6'}},
                {'test1': {'value': 'v7'}},
                {'test1': {'value': 'v8'}},
                {'test1': {'value': 'v9'}},
                {'test1': {'value': 'v10'}},
            ]
        }
        self.assertEqual(dic, expected)

    def test_unflatten_params(self):
        dic = {
            'test:0:test1:value': 'v1',
            'test:1:test1:value': 'v2',
        }
        result = utils.unflatten_params(dic)
        expected = {
            'test': [{'test1': {'value': 'v1'}},
                     {'test1': {'value': 'v2'}}]}
        self.assertEqual(result, expected)

        if not hasattr(webob, 'MultiDict'):
            dic = webob.multidict.MultiDict(dic)
        else:
            dic = webob.MultiDict(dic)
        result = utils.unflatten_params(dic)
        self.assertEqual(result, expected)
