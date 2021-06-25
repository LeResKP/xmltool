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
        raise Exception('Bad root_tag %s, '
                        'it\'s not supported by the dtd' % root_tag)
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
    path = (os.path.dirname(filename)
            if not isinstance(filename, BytesIO) else None)

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
        xml_str = BytesIO(xml_str.encode('utf-8'))
    return load(xml_str, validate)


def update(filename, data, validate=True, transform=None):
    """Update the file named filename with data.

    :param filename: the XML filename we should update
    :param data: the result of the submitted data.
    :param validate: validate the updated XML before writing it.
    :type filename: str
    :type data: dict style like: dict, webob.MultiDict, ...
    :type validate: bool
    :param transform: function to transform the XML string just before
        writing it.
    :type transform: function
    :return: the object generated from the data
    :rtype: :class:`Element`
    """
    data = utils.unflatten_params(data)
    encoding = data.pop('_xml_encoding')
    dtd_url = data.pop('_xml_dtd_url')

    if len(data) != 1:
        raise Exception('Bad data')

    root_tag = list(data.keys())[0]

    dic = dtd.DTD(dtd_url, path=os.path.dirname(filename)).parse()
    obj = dic[root_tag]()

    obj.load_from_dict(data)
    obj.write(filename, encoding, dtd_url=dtd_url, validate=validate,
              transform=transform)
    return obj


def getElementData(elt_id, data):
    """Get the dic from data to load last element of elt_id
    """
    data = utils.unflatten_params(data)
    lis = elt_id.split(':')
    tagname = lis[-1]
    for v in lis:
        try:
            if isinstance(data, list):
                v = int(v)
            data = data[v]
        except (KeyError, IndexError):
            data = {}
            break
    return {tagname: data}
