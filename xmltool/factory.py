#!/usr/bin/env python

import os
from lxml import etree
from io import StringIO, BytesIO, IOBase
from . import utils
from . import elements
from . import dtd


def create(root_tag, dtd_url=None, dtd_str=None):
    """Create a python object for the given root_tag

    :param root_tag: The root tag to create
    :param dtd_url: The dtd url
    :param dtd_str: The dtd as string
    """
    url = dtd_url if dtd_url else StringIO(dtd_str)
    dtd_obj = dtd.DTD(url)
    dic = dtd_obj.parse()
    if root_tag not in dic:
        raise Exception("Bad root_tag %s, " "it's not supported by the dtd" % root_tag)
    obj = dic[root_tag]()
    obj.dtd_url = dtd_url
    obj.encoding = elements.DEFAULT_ENCODING
    return obj


def load(filename, validate=True):
    """Generate a python object

    :param filename: XML filename or Byte like object we should load
    :param validate: validate the XML before generating the python object.
    :type filename: str
    :type validate: bool
    :return: the generated python object
    :rtype: :class:`Element`
    """
    parser = etree.XMLParser(strip_cdata=False)
    tree = etree.parse(filename, parser=parser)
    dtd_url = tree.docinfo.system_url
    path = os.path.dirname(filename) if not isinstance(filename, BytesIO) else None

    dtd_obj = dtd.DTD(dtd_url, path)
    if validate:
        dtd_obj.validate_xml(tree)

    dic = dtd_obj.parse()
    root = tree.getroot()
    obj = dic[root.tag]()
    obj.load_from_xml(root)
    obj.filename = filename
    obj.dtd_url = dtd_url
    obj.encoding = tree.docinfo.encoding
    return obj


def load_string(xml_str, validate=True):
    """Generate a python object

    :param xml_str: the XML file as string
    :type xml_str: str
    :param validate: validate the XML before generating the python object.
    :type validate: bool
    :return: the generated python object
    :rtype: :class:`Element`
    """
    if not isinstance(xml_str, BytesIO):
        # TODO: Get encoding from the dtd file (xml tag).
        xml_str = BytesIO(xml_str.encode("utf-8"))
    return load(xml_str, validate)
