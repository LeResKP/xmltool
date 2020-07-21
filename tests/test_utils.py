#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
from xmltool import utils
from .test_dtd_parser import EXERCISE_XML, EXERCISE_DTD, INVALID_EXERCISE_XML
import webob


class TestUtils(TestCase):

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
