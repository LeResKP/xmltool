#!/usr/bin/env python

import tw2.core as twc
from lxml import etree
import re
from StringIO import StringIO
from dtd_parser import Generator
import utils

xml_declaration_re = re.compile(r'(<\?xml [^>]*\?>)')


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


def load_string(xml_str, validate_xml=True):
    """Generate a python object

    :param xml_str: the XML file as string
    :type xml_str: str
    :param validate_xml: validate the XML before generating the python object.
    :type validate_xml: bool
    :return: the generated python object
    :rtype: :class:`Element`
    """
    # We remove the xml declaration since it's not supported to load xml with
    # it in lxml
    xml_str = xml_declaration_re.sub('', xml_str)
    return load(StringIO(xml_str), validate_xml)


def generate_form(xml_filename, form_action=None, validate_xml=True, **kwargs):
    """Generate the HTML form for the given xml_filename.

    :param xml_filename: the XML filename we should load
    :type xml_filename: str
    :param form_action: the action to put on the HTML form
    :type form_action: str
    :param validate_xml: validate the XML before generating the form.
    :type validate_xml: bool
    :param kwargs: Some extra values passed to the form generator. It's usefull
                   if you want to pass a custom _filename, for example if you
                   work with relative filename.
    :type kwargs: dict
    :return: the generated HTML form
    :rtype: str
    """
    if '_filename' not in kwargs:
        kwargs['_filename'] = xml_filename
    obj = load(xml_filename, validate_xml)
    form = obj._generator.generate_form(obj.tagname, **kwargs)
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

    # We don't need the root tag to generate the dict.
    data = data[root_tag]
    gen = Generator(dtd_url=dtd_url)
    obj = gen.dict_to_obj(root_tag, data)

    obj.write(xml_filename, encoding, validate_xml, transform)
    return obj


def get_jstree_node_data(dtd_url, elt_id):
    """Generate the data need to add a jstree node.

    :param dtd_url: the dtd url we are working on.
    :type dtd_url: str
    :param elt_id: the HTML id attribute of the element we are adding.
    :type elt_id: str
    :return: The node element and the possible previous postions where we can
    insert it.
    :rtype: dict
    """
    gen = Generator(dtd_url=dtd_url)
    cls, ident, parent_id = gen.split_id(elt_id)
    elt = cls.to_jstree_dict(prefix_id=parent_id, number=ident)
    previous = gen.get_previous_element_for_jstree(elt_id)
    return {
        'elt': elt,
        'previous': previous,
    }
