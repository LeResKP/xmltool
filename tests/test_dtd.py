#!/usr/bin/env python

from functools import partial
from lxml import etree
import mock
from unittest import TestCase

from xmltool import dtd


class TestDTD(TestCase):

    def test_content(self):
        url = ('https://raw.github.com/LeResKP/'
               'xmltool/master/tests/exercise.dtd')
        dtd_obj = dtd.DTD(url)
        http_content = dtd_obj.content
        self.assertTrue(http_content)

        url = 'tests/exercise.dtd'
        dtd_obj = dtd.DTD(url)
        fs_content = dtd_obj.content
        self.assertEqual(http_content, fs_content)

        url = 'exercise.dtd'
        dtd_obj = dtd.DTD(url, path='tests/')
        fs_content = dtd_obj.content
        self.assertEqual(http_content, fs_content)

    def test_content_cache(self):
        dtd_obj = dtd.DTD('myurl')

        with mock.patch('xmltool.dtd.DTD._fetch', lambda self: 'my content'):
            self.assertEqual(dtd_obj.content, 'my content')

        def fake_fetch(self, content):
            self._content = content
            return self._content

        content = '<!ELEMENT tag1 (subtag)>'

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
