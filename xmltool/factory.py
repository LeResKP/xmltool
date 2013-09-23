#!/usr/bin/env python

import os
from lxml import etree
from StringIO import StringIO
import dtd_parser
import utils
import elements


def load(filename, validate=True):
    """Generate a python object

    :param filename: the XML filename we should load
    :param validate: validate the XML before generating the python object.
    :type filename: str
    :type validate: bool
    :return: the generated python object
    :rtype: :class:`Element`
    """
    tree = etree.parse(filename)
    dtd_url = tree.docinfo.system_url
    path = isinstance(filename, basestring) and os.path.dirname(filename) or None
    dtd_str = utils.get_dtd_content(dtd_url, path)
    if validate:
        utils.validate_xml(tree, dtd_str)

    dic = dtd_parser.parse(dtd_str=dtd_str)
    root = tree.getroot()
    obj = dic[root.tag]()
    obj.load_from_xml(root)
    obj._xml_filename = filename
    obj._xml_dtd_url = dtd_url
    obj._xml_encoding = tree.docinfo.encoding
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
    if type(xml_str) == unicode:
        xml_str = xml_str.encode('utf-8')
    return load(StringIO(xml_str), validate)


def generate_form(filename, form_action=None, form_filename=None, validate=True):
    """Generate the HTML form for the given filename.

    :param filename: the XML filename we should load
    :type filename: str
    :param form_action: the action to put on the HTML form
    :type form_action: str
    :param validate: validate the XML before generating the form.
    :type validate: bool
    :return: the generated HTML form
    :rtype: str
    """
    if not form_filename:
        form_filename = filename
    obj = load(filename, validate)
    return generate_form_from_obj(obj, form_action, form_filename, validate)


def generate_form_from_obj(obj, form_action=None, form_filename=None,
                           validate=True):
    hidden_inputs = (
        '<input type="hidden" name="_xml_filename" '
        'id="_xml_filename" value="%s" />'
        '<input type="hidden" name="_xml_dtd_url" '
        'id="_xml_dtd_url" value="%s" />'
        '<input type="hidden" name="_xml_encoding" '
        'id="_xml_encoding" value="%s" />'
    ) % (
        form_filename,
        obj._xml_dtd_url,
        obj._xml_encoding or elements.DEFAULT_ENCODING,
    )

    html = []
    if form_action:
        html += ['<form action="%s" method="POST" '
                 'id="xmltool-form">' % form_action]
    else:
        html += ['<form method="POST" id="xmltool-form">']
    html += [hidden_inputs]
    html += [obj.to_html()]
    html += ['</form>']
    return ''.join(html)


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

    root_tag = data.keys()[0]
    dic = dtd_parser.parse(dtd_url=dtd_url)
    obj = dic[root_tag]()

    obj.load_from_dict(data)
    obj.write(filename, encoding, dtd_url, validate, transform)
    return obj


def new(dtd_url, root_tag, form_action=None):
    dic = dtd_parser.parse(dtd_url=dtd_url)
    obj = dic[root_tag]()

    # Merge the following line with the function which generate the form!
    hidden_inputs = (
        '<input type="hidden" name="_xml_filename" '
        'id="_xml_filename" value="" />'
        '<input type="hidden" name="_xml_dtd_url" '
        'id="_xml_dtd_url" value="%s" />'
        '<input type="hidden" name="_xml_encoding" '
        'id="_xml_encoding" value="%s" />'
    ) % (
        dtd_url,
        elements.DEFAULT_ENCODING,
    )

    html = []
    if form_action:
        html += ['<form action="%s" method="POST" '
                 'id="xmltool-form">' % form_action]
    else:
        html += ['<form method="POST" id="xmltool-form">']
    html += [hidden_inputs]
    html += [obj.to_html()]
    html += ['</form>']
    return ''.join(html)
