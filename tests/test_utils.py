#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
from xmltools import utils
from test_dtd_parser import EXERCISE_XML, EXERCISE_DTD, INVALID_EXERCISE_XML


class TestUtils(TestCase):

    def test_is_http_url(self):
        url = 'file.txt'
        self.assertFalse(utils.is_http_url(url))
        url = 'http://file.txt'
        self.assertTrue(utils.is_http_url(url))
        url = 'https://file.txt'
        self.assertTrue(utils.is_http_url(url))

    def test_get_dtd_content(self):
        url = 'http://xml-tools.lereskp.fr/static/exercise.dtd'
        http_content = utils.get_dtd_content(url)
        url = 'tests/exercise.dtd'
        fs_content = utils.get_dtd_content(url)
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
