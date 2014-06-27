#!/usr/bin/env python

import os
import urllib2
import requests
import StringIO
from lxml import etree
import re
import webob


# This hack helps work with different versions of WebOb
if not hasattr(webob, 'MultiDict'):
    webob.MultiDict = webob.multidict.MultiDict


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


def get_dtd_content(url, path=None):
    """Get the content of url.

    :param url: the url of the dtd file.
    :type url: str
    :param path: the path to use for a local file.
    :type path: str
    :return: The content of the given url
    :rtype: string
    """
    if is_http_url(url):
        res = requests.get(url, timeout=5)
        # Use res.content instead of res.text because we want string. If we get
        # unicode, it fails when creating classes with type().
        return res.content

    if path and not url.startswith('/'):
        url = os.path.join(path, url)
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


def to_int(value):
    try:
        return int(value)
    except ValueError:
        return None


def truncate(s, limit=30):
    limit += 1
    if len(s) > limit:
        s = s[:limit]
        for i in xrange(len(s), 0, -1):
            if s[i-1] == ' ':
                return s.rstrip() + '...'
            s = s[:-1]
    return s


# Basically the same function as in tw2.core.validation.
# We don't want to have a lot of dependancies just for this function.
def unflatten_params(params):
    """This performs the first stage of validation. It takes a dictionary where
    some keys will be compound names, such as "form:subform:field" and converts
    this into a nested dict/list structure. It also performs unicode decoding.
    """
    if isinstance(params, webob.MultiDict):
        params = params.mixed()
    # TODO: the encoding can be in the given params, use it!
    enc = 'utf-8'
    for p in params:
        if isinstance(params[p], str):
            # Can raise an exception!
            params[p] = params[p].decode(enc)

    out = {}
    for pname in params:
        dct = out
        elements = pname.split(':')
        for e in elements[:-1]:
            dct = dct.setdefault(e, {})
        dct[elements[-1]] = params[pname]

    numdict_to_list(out)
    return out


number_re = re.compile('^\d+$')


def numdict_to_list(dct):
    for k, v in dct.items():
        if isinstance(v, dict):
            numdict_to_list(v)

            if all(number_re.match(k) for k in v):
                lis = []
                if v:
                    for index in range(int(max(map(int, v.keys()))) + 1):
                        value = None
                        if str(index) in v:
                            value = v[str(index)]
                        lis += [value]
                dct[k] = lis
