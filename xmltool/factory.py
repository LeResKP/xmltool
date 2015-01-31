#!/usr/bin/env python

import os
from lxml import etree
from StringIO import StringIO
import dtd_parser
import utils
import elements


def create(root_tag, dtd_url=None, dtd_str=None):
    """Create a python object for the given root_tag

    :param root_tag: The root tag to create
    :param dtd_url: The dtd url
    :param dtd_str: The dtd as string
    """
    dic = dtd_parser.parse(dtd_url=dtd_url, dtd_str=dtd_str)
    if root_tag not in dic:
        raise Exception('Bad root_tag %s, '
                        'it\'s not supported by the dtd' % root_tag)
    obj = dic[root_tag]()
    obj.dtd_url = dtd_url
    obj.dtd_str = dtd_str
    obj.encoding = elements.DEFAULT_ENCODING
    return obj


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

    dic = dtd_parser.parse(dtd_str=dtd_str,
                           cache_key='xmltool.parse.%s' % dtd_url)
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
                           validate=True, form_attrs=None):
    hidden_inputs = (
        '<input type="hidden" name="_xml_filename" '
        'id="_xml_filename" value="%s" />'
        '<input type="hidden" name="_xml_dtd_url" '
        'id="_xml_dtd_url" value="%s" />'
        '<input type="hidden" name="_xml_encoding" '
        'id="_xml_encoding" value="%s" />'
    ) % (
        form_filename or '',
        obj.dtd_url,
        obj.encoding or elements.DEFAULT_ENCODING,
    )
    attrs = {}
    if form_attrs:
        attrs = form_attrs.copy()
    if 'id' not in attrs:
        attrs['id'] = 'xmltool-form'
    if form_action:
        attrs['action'] = form_action

    attrs_str = ' '.join(['%s="%s"' % tple for tple in attrs.items()])
    html = ['<form method="POST" %s>' % attrs_str]
    html += [hidden_inputs]
    html += [obj._to_html()]
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
    dic = dtd_parser.parse(dtd_url=dtd_url, path=os.path.dirname(filename))
    obj = dic[root_tag]()

    obj.load_from_dict(data)
    obj.write(filename, encoding, dtd_url=dtd_url, validate=validate,
              transform=transform)
    return obj


def new(dtd_url, root_tag, form_action=None, form_attrs=None):
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

    attrs = {}
    if form_attrs:
        attrs = form_attrs.copy()
    if 'id' not in attrs:
        attrs['id'] = 'xmltool-form'
    if form_action:
        attrs['action'] = form_action

    attrs_str = ' '.join(['%s="%s"' % tple for tple in attrs.items()])
    html = ['<form method="POST" %s>' % attrs_str]
    html += [hidden_inputs]
    html += [obj._to_html()]
    html += ['</form>']
    return ''.join(html)


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


def _get_obj_from_str_id(str_id, dtd_url=None, dtd_str=None, data=None):
    """Load object according to the given str_id

    ..note:: If data is passed load the data to this object
    """
    # Will raise an exception if both dtd_url or dtd_str are None or set
    dic = dtd_parser.parse(dtd_url=dtd_url, dtd_str=dtd_str)
    splitted = str_id.split(':')
    s = splitted.pop(0)
    cls = dic[s]
    obj = cls()
    if data:
        obj.load_from_dict(data)
    index = None
    while splitted:
        s = splitted.pop(0)
        obj = obj.get_or_add(s, index=index)
        if len(splitted) > 0:
            index = None
        if isinstance(obj, list):
            index = int(splitted.pop(0))

    if isinstance(obj, elements.TextElement) and obj.text is None:
        obj.set_text('')
    return obj


def _get_parent_to_add_obj(elt_id, tagname, data, dtd_url=None, dtd_str=None):
    """Create element from data and elt_id and determine if tagname can be
    added to it or its parent.
    """
    target_obj = _get_obj_from_str_id(elt_id, dtd_url=dtd_url, dtd_str=dtd_str,
                                      data=data)

    if target_obj.is_addable(tagname):
        return target_obj
    if target_obj._parent_obj.is_addable(tagname):
        return target_obj._parent_obj
    return None


def _get_data_for_html_display(obj):
    """Returns the data need to display the object in HTML.
    """
    return {
        'jstree_data': obj.to_jstree_dict(),
        'previous': obj.get_previous_js_selectors(),
        'html': obj.to_html(),
        'elt_id': ':'.join(obj.prefixes),
    }


def _add_new_element_from_id(elt_id, data, clipboard_data, dtd_url=None,
                             dtd_str=None, skip_extra=False):
    """Create an element from data and elt_id. This function should be used to
    make some copy/paste.

    :param skip_extra: If True we don't load the attributes nor the comments
    :type skip_extra: bool
    """
    keys = clipboard_data.keys()
    assert(len(keys) == 1)
    tagname = keys[0]
    parentobj = _get_parent_to_add_obj(elt_id, tagname, data, dtd_url=dtd_url,
                                       dtd_str=dtd_str)
    if not parentobj:
        return None

    obj = parentobj.add(tagname)
    obj.load_from_dict(clipboard_data, skip_extra=skip_extra)
    return obj


def get_new_element_data_for_html_display(*args, **kw):
    """Create new sub object according to the given params and returns the data
    to display it.
    """
    obj = _add_new_element_from_id(*args, **kw)
    if not obj:
        return None
    return _get_data_for_html_display(obj)


def get_data_from_str_id_for_html_display(str_id, dtd_url=None, dtd_str=None):
    """Get the sub object corresponding to the given str_id and returns the
    data to display it.
    """
    obj = _get_obj_from_str_id(str_id, dtd_url, dtd_str)
    return _get_data_for_html_display(obj)
