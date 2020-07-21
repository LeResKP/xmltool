#!/usr/bin/env python

from dogpile.cache.api import NO_VALUE
from io import StringIO
from lxml import etree
import mock
from unittest import TestCase
import six

from xmltool import cache, dtd
from xmltool.elements import (
    TextElement,
    Element,
)

from .test_dtd_parser import EXERCISE_XML, EXERCISE_DTD, INVALID_EXERCISE_XML


def fake_fetch(self, content):
    self._content = content
    return self._content


class TestDTD(TestCase):

    def test_content(self):
        url = ('https://raw.github.com/LeResKP/'
               'xmltool/master/tests/exercise.dtd')
        dtd_obj = dtd.DTD(url)
        http_content = dtd_obj.content
        self.assertTrue(http_content)
        self.assertEqual(dtd_obj._get_dtd_url(), url)

        url = 'tests/exercise.dtd'
        dtd_obj = dtd.DTD(url)
        fs_content = dtd_obj.content
        self.assertEqual(http_content, fs_content)
        self.assertEqual(dtd_obj._get_dtd_url(), url)

        url = 'exercise.dtd'
        dtd_obj = dtd.DTD(url, path='tests/')
        fs_content = dtd_obj.content
        self.assertEqual(http_content, fs_content)
        self.assertEqual(dtd_obj._get_dtd_url(), 'tests/exercise.dtd')

        dtd_obj._content = None
        with mock.patch('xmltool.cache.CACHE_TIMEOUT', 3600):
            dtd_obj = dtd_obj.content
            res = cache.region.get('xmltool.get_dtd_content.tests/exercise.dtd')
            self.assertTrue(res)
            self.assertNotEqual(res, NO_VALUE)

    def test_content_cache(self):
        dtd_obj = dtd.DTD('myurl')

        with mock.patch('xmltool.dtd.DTD._fetch', lambda self: 'my content'):
            self.assertEqual(dtd_obj.content, 'my content')

        content = (
            '<!ELEMENT tag1 (subtag)>'
            '<!ELEMENT subtag (#PCDATA)>'
        )

        with mock.patch('xmltool.cache.CACHE_TIMEOUT', 3600):
            with mock.patch('xmltool.dtd.DTD._fetch',
                            new=lambda self: fake_fetch(self, content)):
                self.assertEqual(dtd_obj.content, content)

            with mock.patch('xmltool.dtd.DTD._fetch',
                            new=lambda self: fake_fetch(self, 'new content')):
                self.assertEqual(dtd_obj.content, content)

    def test_validate(self):
        dtd_obj = dtd.DTD('myurl')
        dtd_obj._content = 'Invalid content'
        self.assertRaises(etree.DTDParseError, dtd_obj.validate)

        dtd_obj._content = (
            '<!ELEMENT tag1 (subtag)>'
            '<!ATTLIST tag1 id1 ID #IMPLIED>'
            '<!ATTLIST tag1 id2 ID #IMPLIED>'
        )
        self.assertRaises(dtd.ValidationError, dtd_obj.validate)

    def test__parse(self):
        dtd_str = u'''
            <!ELEMENT Exercise (question)>
            <!ELEMENT question (#PCDATA)>
        '''
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        self.assertEqual(len(dic), 2)
        self.assertTrue(issubclass(dic['Exercise'], Element))
        self.assertTrue(issubclass(dic['question'], TextElement))

    def test_parse(self):
        dtd_str = u'''
            <!ELEMENT Exercise (question)>
            <!ELEMENT question (#PCDATA)>
        '''

        dtd_obj = dtd.DTD(StringIO(dtd_str))
        dic = dtd_obj.parse()
        self.assertEqual(sorted(dic.keys()), sorted(['question', 'Exercise']))

        with mock.patch('xmltool.cache.CACHE_TIMEOUT', 3600):
            dic = dtd_obj.parse()
            self.assertEqual(sorted(dic.keys()),
                             sorted(['question', 'Exercise']))

            # The cache only works if we have an url
            dtd_obj._parsed_dict = None
            dtd_obj.url = 'my url'
            dic = dtd_obj.parse()
            dtd_str = u'''
                <!ELEMENT question (#PCDATA)>
            '''
            dtd_obj = dtd.DTD(StringIO(dtd_str))
            dtd_obj._parsed_dict = None
            dtd_obj.url = 'my url'
            dic = dtd_obj.parse()
            self.assertEqual(sorted(dic.keys()),
                             sorted(['question', 'Exercise']))

            dtd_obj.url = None
            dic = dtd_obj.parse()
            self.assertEqual(list(dic.keys()), ['question'])

    def test_validate_xml(self):
        dtd_obj = dtd.DTD(StringIO(EXERCISE_DTD))
        root = etree.fromstring(EXERCISE_XML)
        res = dtd_obj.validate_xml(root)
        self.assertTrue(res)
        try:
            root = etree.fromstring(INVALID_EXERCISE_XML)
            dtd_obj.validate_xml(root)
            assert 0
        except etree.DocumentInvalid:
            pass
