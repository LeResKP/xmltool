#!/usr/bin/env python

import urllib2
import StringIO
from lxml import etree


def is_http_url(url):
    """Determine if the given url is on http(s).

    :param url: the url to check
    :type url: str
    :return: True if the given url is on http or https.
    :rtype: boolean
    """
    if url.startswith('http://') or url.startswith('https://'):
        return True
    return False


def get_dtd_content(url):
    """Get the content of url.

    :param url: the url of the dtd file.
    :type url: str
    :return: The content of the given url
    :rtype: string
    """
    if is_http_url(url):
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        s = response.read()
        response.close()
        return s

    return open(url, 'r').read()


def validate_xml(xml_obj, dtd_str):
    """Validate an XML object

    :param xml_obj: The XML object to validate
    :type xml_obj: etree.Element
    :param dtd_str: The dtd to use for the validation
    :type dtd_str: str
    :return: True. Raise an exception if the XML is not valid
    :rtype: bool
    """
    dtd_obj = etree.DTD(StringIO.StringIO(dtd_str))
    dtd_obj.assertValid(xml_obj)
    return True
