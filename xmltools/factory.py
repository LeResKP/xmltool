#!/usr/bin/env python

import tw2.core as twc
from lxml import etree
from dtd_parser import Generator
import utils


def load(xml_filename, validate_xml=True):
    """Generate a python object

    :param xml_filename: the XML filename we should load
    :param validate_xml: validate the XML before generating the python object.
    :type xml_filename: str
    :type validate_xml: bool
    :return: the generated python object
    :rtype: :class:`Element`
    """
    tree = etree.parse(xml_filename)
    dtd_url = tree.docinfo.system_url
    dtd_str = utils.get_dtd_content(dtd_url)
    if validate_xml:
        utils.validate_xml(tree, dtd_str)

    gen = Generator(dtd_url=dtd_url)
    obj = gen.generate_obj(tree.getroot())
    return obj


def generate_form(xml_filename, form_action=None, validate_xml=True):
    """Generate the HTML form for the given xml_filename.

    :param xml_filename: the XML filename we should load
    :param form_action: the action to put on the HTML form
    :param validate_xml: validate the XML before generating the form.
    :type xml_filename: str
    :type form_action: str
    :type validate_xml: bool
    :return: the generated HTML form
    :rtype: str
    """
    obj = load(xml_filename, validate_xml)
    form = obj._generator.generate_form(obj.tagname)
    form.set_value(obj)

    if form_action:
        form.action = form_action
    return form.display()


def update_xml_file(xml_filename, data, validate_xml=True, transform=None):
    """Update the file named xml_filename with data.

    :param xml_filename: the XML filename we should update
    :param data: the result of the submitted data.
    :param validate_xml: validate the updated XML before writing it.
    :type xml_filename: str
    :type data: dict style like: dict, webob.MultiDict, ...
    :type validate_xml: bool
    :param transform: function to transform the XML string just before
        writing it.
    :type transform: function
    :return: the object generated from the data
    :rtype: :class:`Element`
    """
    data = twc.validation.unflatten_params(data)

    encoding = data['_encoding']
    dtd_url = data['_dtd_url']
    root_tag = data['_root_tag']

    gen = Generator(dtd_url=dtd_url)
    obj = gen.dict_to_obj(root_tag, data)

    obj.write(xml_filename, encoding, validate_xml, transform)
    return obj

