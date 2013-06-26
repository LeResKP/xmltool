#!/usr/bin/env python

import os
from lxml import etree
import simplejson as json
import dtd_parser
import utils

DEFAULT_ENCODING = 'UTF-8'


class Element(object):
    """After reading a dtd file we construct some Element
    """
    _tagname = None
    _attribute_names = None
    _attributes = None
    _sub_elements = None
    _required = False
    _parent = None
    _sourceline = None
    _comment = None
    _is_choice = False
    _is_empty = False

    # The following attributes should be used for the root element.
    _xml_filename = None
    _xml_dtd_url = None
    _xml_encoding = None


    @classmethod
    def _get_allowed_tagnames(cls):
        return [cls._tagname]

    @classmethod
    def _get_sub_element(cls, tagname):
        for e in cls._sub_elements:
            for tg in e._get_allowed_tagnames():
                if tg == tagname:
                    return e

    @classmethod
    def _get_value_from_parent(cls, parent_obj):
        return getattr(parent_obj, cls._tagname, None)

    @classmethod
    def _get_sub_value(cls, parent_obj):
        v = cls._get_value_from_parent(parent_obj)
        if not v and cls._required:
            v = cls()
        return v

    def _has_value(self):
        for elt in self._sub_elements:
            v = elt._get_value_from_parent(self)
            if v is not None:
                return True
        return False

    @classmethod
    def _get_prefixes(cls, prefixes, index, name=None):
        tmp_prefixes = list(prefixes or [])
        if index is not None:
            tmp_prefixes.append(str(index))
        tmp_prefixes.append(cls._tagname)
        if name is not None:
            tmp_prefixes.append(name)
        return tmp_prefixes

    @classmethod
    def _get_str_prefix(cls, prefixes, index, name=None):
        tmp_prefixes = cls._get_prefixes(prefixes, index, name)
        return ':'.join(tmp_prefixes)

    @classmethod
    def _add(cls, tagname, parent_obj, value=None):
        v = getattr(parent_obj, tagname, None)
        if v:
            raise Exception('%s already defined' % tagname)

        if value and not issubclass(cls, TextElement):
            raise Exception, "Can't set value to non TextElement"

        tmpobj = cls()
        setattr(parent_obj, tagname, tmpobj)
        tmpobj._parent = parent_obj
        if value:
            tmpobj._value = value
        return tmpobj

    def add(self, tagname, value=None):
        cls = self._get_sub_element(tagname)

        if cls is None:
            raise Exception('Invalid child %s' % tagname)

        obj = cls._add(tagname, self, value)
        return obj

    def add_attribute(self, name, value):
        if name not in self._attribute_names:
            raise Exception('Invalid attribute name: %s' % name)
        self._attributes = self._attributes or {}
        self._attributes[name] = value

    def _load_attributes_from_xml(self, xml):
        for k, v in xml.attrib.items():
            self.add_attribute(k,v)

    def _load_attributes_from_dict(self, dic):
        if not dic:
            return
        attrs = dic.pop('_attrs', None)
        if not attrs:
            return
        for k, v in attrs.items():
            self.add_attribute(k,v)

    def _attributes_to_xml(self, xml):
        if not self._attributes:
            return
        for k, v in self._attributes.items():
            xml.attrib[k] = v

    def _attributes_to_html(self, prefixes, index):
        if not self._attributes:
            return ''
        html = []
        name = self._get_str_prefix(prefixes, index)
        for k, v in self._attributes.items():
            html += ['<input value="%s" name="%s" id="%s" class="_attrs" />' % (
                v,
                '%s:_attrs:%s' % (name, k),
                '%s:_attrs:%s' % (name, k),
            )]
        return ''.join(html)

    def _load_comment_from_xml(self, xml):
        previous = xml
        comments = []
        while True:
            previous = previous.getprevious()
            if previous is None:
                break
            if not isinstance(previous, etree._Comment):
                break
            comments += [previous.text]

        comments.reverse()
        end_comments = []
        nextelt = xml
        # Only get the comment after the tag if we don't have any other tag
        while True:
            nextelt = nextelt.getnext()
            if nextelt is None:
                break
            if not isinstance(nextelt, etree._Comment):
                end_comments = []
                break
            end_comments += [nextelt.text]
        comments += end_comments
        self._comment = '\n'.join(comments) or None

    def _load_comment_from_dict(self, dic):
        self._comment = dic.pop('_comment', None)

    def _comment_to_xml(self, xml):
        if not self._comment:
            return None
        elt = etree.Comment(self._comment)
        xml.addprevious(elt)

    def _comment_to_html(self, prefixes, index):
        name = self._get_str_prefix(prefixes, index, name='_comment')
        if not self._comment:
            return (
                u'<a data-comment-name="%s" class="btn-comment">'
                u'Comment</a>') % name
        else:
            return (
                u'<a data-comment-name="{name}" '
                u'class="btn-comment has-comment" title="{comment}">'
                u'Comment</a>'
                u'<textarea class="_comment" name="{name}">{comment}</textarea>'
            ).format(
                name=name,
                comment=self._comment
            )

    def _load_extra_from_xml(self, xml):
        self._load_attributes_from_xml(xml)
        self._load_comment_from_xml(xml)
        self._sourceline = xml.sourceline

    def load_from_xml(self, xml):
        self._load_extra_from_xml(xml)
        for child in xml:
            if isinstance(child, etree._Comment):
                # The comments are loaded when we load the object
                continue
            obj = self.add(child.tag)
            obj.load_from_xml(child)

    def _load_extra_from_dict(self, data):
        self._load_attributes_from_dict(data)
        self._load_comment_from_dict(data)

    def load_from_dict(self, dic):
        data = dic.get(self._tagname)
        if not data:
            return
        self._load_extra_from_dict(data)
        for key, value in data.items():
            if isinstance(value, list):
                for d in value:
                    assert(len(d) == 1)
                    obj = self.add(d.keys()[0])
                    obj.load_from_dict(d)
            else:
                obj = self.add(key)
                obj.load_from_dict(data)

    def to_xml(self):
        xml = etree.Element(self._tagname)
        self._comment_to_xml(xml)
        self._attributes_to_xml(xml)
        for elt in self._sub_elements:
            v = elt._get_sub_value(self)

            if v is not None:
                e = v.to_xml()
                if isinstance(e, list):
                    xml.extend(e)
                else:
                    xml.append(e)
                    # NOTE: the attributes are already set but we need to add
                    # the comment here.
                    v._comment_to_xml(e)
        return xml

    @classmethod
    def _get_html_add_button(cls, prefixes, index=None, css_class=None):
        if cls._is_choice:
            return cls._parent._get_html_add_button(prefixes, index, css_class)

        value = cls._get_str_prefix(prefixes, index)
        css_classes = ['btn btn-add-ajax']
        if css_class:
            css_classes += [css_class]
        return ('<a class="%s" data-id="%s">'
                'Add %s</a>') % (
                    ' '.join(css_classes),
                    value,
                    cls._tagname)

    @classmethod
    def _to_html(cls, parent_obj, prefixes=None, index=None):
        v = cls._get_value_from_parent(parent_obj)
        if not v:
            # We always want an object since we need at least a add button.
            v = cls()
        return v.to_html(prefixes, index)

    def to_html(self, prefixes=None, index=None, delete_btn=False,
                add_btn=True,  partial=False):

        if not self._has_value() and not self._required and self._parent and not partial:
            # Add button!
            return self._get_html_add_button(prefixes, index)

        tmp_prefixes = self._get_prefixes(prefixes, index)
        sub_html = [self._attributes_to_html(prefixes, index)]
        for elt in self._sub_elements:
            tmp = elt._to_html(self, tmp_prefixes)
            if tmp:
                sub_html += [tmp]

        css_classes = [self._tagname]
        if len(tmp_prefixes) > 1:
            css_classes += [':'.join(tmp_prefixes)]
        legend = self._tagname
        legend += self._comment_to_html(prefixes, index)
        # Don't allow to delete root element!
        if (not self._required and self._parent and add_btn) or self._is_choice:
            legend += self._get_html_add_button(prefixes or [], index, 'hidden')
        if (not self._required and self._parent) or delete_btn or partial or self._is_choice:
            legend += '<a class="btn-delete-fieldset">Delete</a>'
        html = ['<fieldset class="%s" id="%s"><legend>%s</legend>' % (
            ' '.join(css_classes),
            ':'.join(tmp_prefixes),
            legend)]
        html.extend(sub_html)
        html += ['</fieldset>']
        return ''.join(html)

    @classmethod
    def _to_jstree_dict(cls, parent_obj, prefixes=None, index=None):
        v = cls._get_value_from_parent(parent_obj)
        if not v and cls._required:
            # We always want an object since we need at least a add button.
            v = cls()
        if v:
            return v.to_jstree_dict(prefixes, index)

    def to_jstree_dict(self, prefixes, index=None):
        tmp_prefixes = self._get_prefixes(prefixes, index)
        data = self._tagname
        value = getattr(self, '_value', None)
        if value:
            data += u' <span class="_tree_text">(%s)</span>' % (
                utils.truncate(value))

        css_class = 'tree_' +  ':'.join(prefixes or [])
        if index is not None:
            css_class += ' tree_' +  ':'.join((prefixes+[str(index)]))
        else:
            css_class += ':' + self._tagname

        dic = {
            'data': data,
            'attr': {
                'id': 'tree_' +  ':'.join(tmp_prefixes),
                'class': css_class,
            },
        }
        children = []
        for elt in self._sub_elements:
            v = elt._to_jstree_dict(self, tmp_prefixes)
            if v:
                children += [v]
        dic['children'] = children
        return dic

    def __getitem__(self, tagname):
        v = getattr(self, tagname, None)
        if not v:
            raise KeyError(tagname)
        return v

    def __contains__(self, tagname):
        return hasattr(self, tagname)

    def get_or_add(self, tagname):
        v = getattr(self, tagname, None)
        if v:
            return v
        return self.add(tagname)

    def walk(self):
        for elt in self._sub_elements:
            v = elt._get_value_from_parent(self)
            if not v:
                continue

            if isinstance(v, list):
                for e in v:
                    yield e
                    for s in e.walk():
                        yield s
            else:
                yield v
                for s in v.walk():
                    yield s

    def findall(self, tagname):
        lis = []
        for elt in self.walk():
            if elt._tagname == tagname:
                lis += [elt]
        return lis

    def find_parents(self, tagname):
        """Find all parents named tagname in element's parents

        :param tagname: (str) The tagname to look for
        :returns: (list) List of matching parents, ordered from the inside to
            the outside. This will return the object himself as first element
            if its tagname is the one we're looking for
        """
        res = []
        if self._tagname == tagname:
            res = [self]
        if self._parent is not None:
            res += self._parent.find_parents(tagname)
        return res

    def write(self, filename=None, encoding=None, dtd_url=None, validate=True,
              transform=None):
        filename = filename or self._xml_filename
        if not filename:
            raise Exception('No filename given')
        dtd_url = dtd_url or self._xml_dtd_url
        if not dtd_url:
            raise Exception('No dtd url given')
        encoding = encoding or self._xml_encoding or DEFAULT_ENCODING
        xml = self.to_xml()
        if validate:
            dtd_str = utils.get_dtd_content(dtd_url, os.path.dirname(filename))
            utils.validate_xml(xml, dtd_str)

        doctype = ('<!DOCTYPE %(root_tag)s SYSTEM "%(dtd_url)s">' % {
                      'root_tag': self._tagname,
                      'dtd_url': dtd_url,
                 })
        xml_str = etree.tostring(
            xml.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding=encoding,
            doctype=doctype)
        if transform:
            xml_str = transform(xml_str)
        open(filename, 'w').write(xml_str)


class TextElement(Element):
    _value = None
    _exists = False

    def __repr__(self):
        return '<TextElement %s "%s">' % (
            self._tagname,
            (self._value or '').strip())

    def load_from_xml(self, xml):
        self._load_extra_from_xml(xml)
        self._value = xml.text
        # We use _exists to know if the tag is defined in the XML.
        self._exists= True

    def load_from_dict(self, dic):
        data = dic[self._tagname]
        self._load_extra_from_dict(data)
        self._value = data.get('_value')

    def to_xml(self):
        xml = etree.Element(self._tagname)
        # The comment can't be added here since we don't always have the parent
        # defined.
        self._attributes_to_xml(xml)
        # We never set self.text to None to make sure when we export as string
        # we get a HTML format (no autoclose tag)
        if self._is_empty:
            if self._value:
                raise Exception(
                    'It\'s forbidden to have a value to an EMPTY tag')
            xml.text = None
        else:
            xml.text = self._value or ''
        return xml

    def _get_html_attrs(self, prefixes, index=None):
        prefixes = list(prefixes or [])
        if index is not None:
            # Don't add the index to the css_class
            css_class = ':'.join(prefixes)
            prefixes += [str(index)]
        else:
            css_class = ':'.join(prefixes + [self._tagname])
        prefixes += [self._tagname]
        html_id =  ':'.join(prefixes)
        prefixes += ['_value']
        name = ':'.join(prefixes)
        attrs = [
            ('name', name),
            ('id', html_id),
            ('class', css_class),
        ]
        attr = ' '.join(['%s="%s"' % (attrname, value)
                         for attrname, value in attrs])
        return ' ' + attr

    def to_html(self, prefixes=None, index=None, delete_btn=False,
                add_btn=True, partial=False):

        if (not self._exists and not self._value and
            not self._required and not partial):
            return self._get_html_add_button(prefixes, index)

        parent_is_list = isinstance(self._parent, ListElement)
        add_button = ''
        if (not parent_is_list and not self._required) or self._is_choice:
            add_button = self._get_html_add_button(prefixes, index, 'hidden')

        delete_button = ''
        if delete_btn or not self._required or self._is_choice or parent_is_list:
            if parent_is_list:
                delete_button = '<a class="btn-delete-list">Delete</a>'
            else:
                delete_button = '<a class="btn-delete">Delete</a>'

        return (
            u'<div data-id="{data_id}"><label>{label}</label>'
            u'{add_button}'
            u'{delete_button}'
            u'{comment}'
            u'{xmlattrs}'
            u'<textarea{attrs} rows="1">{value}</textarea></div>').format(
                data_id=self._get_str_prefix(prefixes, index),
                label=self._tagname,
                add_button=add_button,
                delete_button=delete_button,
                comment=self._comment_to_html(prefixes, index),
                attrs=self._get_html_attrs(prefixes, index),
                value=self._value or '',
                xmlattrs=self._attributes_to_html(prefixes, index),
            )


class MultipleMixin(object):
    _elts = None

    @classmethod
    def _get_sub_element(cls, tagname):
        for e in cls._elts:
            if e._tagname == tagname:
                return e


class ListElement(list, MultipleMixin, Element):

    @classmethod
    def _get_allowed_tagnames(cls):
        lis = [cls._tagname]
        for e in cls._elts:
            lis += [e._tagname]
        return lis

    @classmethod
    def _add(cls, tagname, parent_obj, value=None):
        elt = cls._get_sub_element(tagname)
        if value and not issubclass(elt, TextElement):
            raise Exception, "Can't set value to non TextElement"

        tg = cls._tagname
        if len(cls._elts) == 1:
            tg = tagname

        lis = getattr(parent_obj, tg, None)
        if not lis:
            lis = cls()
            lis._parent = parent_obj
            setattr(parent_obj, tg, lis)
        tmpobj = elt()
        tmpobj._parent = lis
        if value:
            tmpobj._value = value
        lis.append(tmpobj)
        return tmpobj

    def to_xml(self):
        lis = []
        if not len(self) and self._required:
            if len(self._elts) == 1:
                e = self.add(self._elts[0]._tagname)
                self.append(e)

        for e in self:
            if e._comment:
                elt = etree.Comment(e._comment)
                lis += [elt]
            lis += [e.to_xml()]
        return lis

    @classmethod
    def _get_html_add_button(cls, prefixes, index=None, css_class=None):
        if index is None:
            # This element is a list, we should always have an index.
            index = 0
        if len(cls._elts) == 1:
            css_classes = ['btn btn-add-ajax-list']
            if css_class:
                css_classes += [css_class]

            tmp_prefixes = list(prefixes or []) + [
                cls._tagname, index, cls._elts[0]._tagname]
            data_id = ':'.join(
                map(str, filter((lambda x: x is not None), tmp_prefixes)))
            button = ('<a class="%s" '
                      'data-id="%s">New %s</a>') % (
                          ' '.join(css_classes),
                          data_id,
                          cls._elts[0]._tagname)
            return button

        assert not css_class
        button = '<select class="btn btn-add-ajax-choice-list">'
        options = '/'.join([e._tagname for e in cls._elts])
        button += '<option>New %s</option>' % options

        tmp_prefixes = list(prefixes or [])
        tmp_prefixes.append(cls._tagname)
        tmp_prefixes.append(str(index))
        prefix_str = ':'.join(tmp_prefixes)
        for e in cls._elts:
            button += '<option value="%s:%s">%s</option>' % (
                prefix_str,
                e._tagname,
                e._tagname)
        button += '</select>'
        return button

    @classmethod
    def _get_value_from_parent(cls, parent_obj):
        tg = cls._tagname
        if len(cls._elts) == 1:
            tg = cls._elts[0]._tagname
        return getattr(parent_obj, tg, None)

    def to_html(self, prefixes=None, index=None, delete_btn=False,
                add_btn=True, partial=False, offset=0):

        # We should not have the following parameter for this object
        assert self._attributes is None
        assert index is None

        if not len(self) and (self._required or partial):
            if len(self._elts) == 1:
                e = self.add(self._elts[0]._tagname)
                self.append(e)

        i = -1
        lis = []
        for i, e in enumerate(self):
            if not partial:
                lis += [self._get_html_add_button(prefixes, (i+offset))]
            force = False
            if i == 0 and (partial or self._required):
                force = True
            lis += [e.to_html(((prefixes or [])+[self._tagname]),
                              (i+offset),
                              delete_btn=True,
                              partial=force,
                              add_btn=False)]

        lis += [self._get_html_add_button(prefixes, i+offset+1)]

        if partial:
            return ''.join(lis)
        return '<div class="list-container">%s</div>' % ''.join(lis)

    def to_jstree_dict(self, prefixes, index=None, offset=0):
        if not len(self) and (self._required):
            if len(self._elts) == 1:
                e = self.add(self._elts[0]._tagname)
                self.append(e)

        lis = []
        for i, e in enumerate(self):
            v = e.to_jstree_dict((prefixes or [])+[self._tagname], i+offset)
            if v:
                lis += [v]
        return lis

    def get_or_add(self, tagname):
        raise NotImplementedError

    def walk(self):
        for elt in self:
            yield elt
            for e in elt.walk():
                yield e


class ChoiceElement(MultipleMixin, Element):

    @classmethod
    def _get_allowed_tagnames(cls):
        lis = []
        for e in cls._elts:
            lis += [e._tagname]
        return lis

    @classmethod
    def _add(cls, tagname, parent_obj, value=None):
        for elt in cls._elts:
            if hasattr(parent_obj, elt._tagname):
                raise Exception('%s already defined' % elt._tagname)

        elt = cls._get_sub_element(tagname)
        if value and not issubclass(elt, TextElement):
            raise Exception, "Can't set value to non TextElement"

        tmpobj = elt()
        tmpobj._parent = parent_obj
        if value:
            tmpobj._value = value
        setattr(parent_obj, tagname, tmpobj)
        return tmpobj

    @classmethod
    def _get_html_add_button(cls, prefixes, index=None, css_class=None):
        """
        ..note:: index is not used here since we never have list of this
        element.
        """
        css_classes = ['btn', 'btn-add-ajax-choice']
        if css_class:
            css_classes += [css_class]

        button = '<select class="%s">' % ' '.join(css_classes)
        button += '<option>New %s</option>' % '/'.join([e._tagname for e in cls._elts])
        for e in cls._elts:
            button += '<option value="%s">%s</option>' % (
                e._get_str_prefix(prefixes, index, None),
                e._tagname)
        button += '</select>'
        return button

    @classmethod
    def _get_value_from_parent(cls, parent_obj):
        for elt in cls._elts:
            v = getattr(parent_obj, elt._tagname, None)
            if v:
                return v

    @classmethod
    def _to_html(cls, parent_obj, prefixes=None, index=None):
        v = cls._get_value_from_parent(parent_obj)
        if not v:
            return cls._get_html_add_button(prefixes, index)
        return v.to_html(prefixes, index)

    @classmethod
    def _get_sub_value(cls, parent_obj):
        # We don't know which object to insert, so do nothing if None
        return cls._get_value_from_parent(parent_obj)

    def to_jstree_dict(self, prefixes, index=None):
        # Nothing to add in for this object
        return {}

def _get_obj_from_str_id(str_id, dtd_url=None, dtd_str=None):
    # Will raise an exception if both dtd_url or dtd_str are None or set
    dic = dtd_parser.parse(dtd_url=dtd_url, dtd_str=dtd_str)
    splitted = str_id.split(':')
    prefixes = []
    s = splitted.pop(0)
    prefixes += [s]
    cls = dic[s]
    obj = cls()
    index = None
    while splitted:
        s = splitted.pop(0)
        prefixes += [s]
        tmp_cls = obj._get_sub_element(s)
        if not tmp_cls:
            raise Exception('Unsupported tag %s' % s)

        if issubclass(tmp_cls, ListElement):
            # Remove the id
            index = splitted.pop(0)
            if len(splitted) > 1:
                prefixes += [index]
                index = None
            s = splitted.pop(0)
            prefixes += [s]

        obj = obj.add(s)
    return obj, prefixes, index


def _get_previous_js_selectors(obj, prefixes, index):
    lis = []

    parent = obj._parent
    if not parent:
        return lis

    parent_is_list = isinstance(parent, ListElement)
    tmp_prefixes = prefixes[:-1]
    if parent_is_list:
        parent = parent._parent
        if int(index) > 0:
            index = int(index) - 1
            lis += [
                ('after', '.tree_%s' % ':'.join(tmp_prefixes + [str(index)]))]
            return lis
        tmp_prefixes = tmp_prefixes[:-1]

    sub = parent._get_sub_element(obj._tagname)

    for elt in parent._sub_elements:
        if elt == sub:
            break
        tmp_prefix = list(tmp_prefixes) + [elt._tagname]
        lis += [('after', '.tree_%s' % ':'.join(tmp_prefix))]

    lis.reverse()
    lis += [('inside', '#tree_%s' % ':'.join(tmp_prefixes))]
    return lis


def get_obj_from_str_id(str_id, dtd_url=None, dtd_str=None):
    obj, prefixes, index = _get_obj_from_str_id(str_id, dtd_url, dtd_str)
    if isinstance(obj._parent, ListElement):
        index = int(index or 0)
        tmp = obj.to_html(prefixes[:-1], index, add_btn=False, partial=True)
        tmp += obj._parent._get_html_add_button(prefixes[:-2], index+1)
        return tmp

    return obj.to_html(prefixes[:-1], index, partial=True)

def _get_html_from_obj(obj, prefixes, index):
    if isinstance(obj._parent, ListElement):
        index = int(index or 0)
        tmp = obj.to_html(prefixes[:-1], index, add_btn=False, partial=True)
        tmp += obj._parent._get_html_add_button(prefixes[:-2], index+1)
        return tmp

    return obj.to_html(prefixes[:-1], index, partial=True)

def get_jstree_json_from_str_id(str_id, dtd_url=None, dtd_str=None):
    obj, prefixes, index = _get_obj_from_str_id(str_id, dtd_url, dtd_str)
    return {
        'jstree_data': obj.to_jstree_dict(prefixes[:-1], index),
        'previous': _get_previous_js_selectors(obj, prefixes, index),
        'html': _get_html_from_obj(obj, prefixes, index),
    }

