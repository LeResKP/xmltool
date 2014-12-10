from unittest import TestCase
from lxml import etree, html as lxml_html


class BaseTest(TestCase):

    def assertEqual_(self, html, expected):
        document_root = lxml_html.fromstring(html)
        h = etree.tostring(document_root, encoding='unicode',
                           pretty_print=True)
        document_root = lxml_html.fromstring(expected)
        e = etree.tostring(document_root, encoding='unicode',
                           pretty_print=True)
        self.maxDiff = None
        self.assertEqual(h, e)
