#!/usr/bin/env python

import os
import re
from lxml import etree
import dtd_parser
import utils
from distutils.version import StrictVersion
from . import render


DEFAULT_ENCODING = 'UTF-8'
TREE_PREFIX = 'tree_'

# We expect just '\n' in the XML output
EOL = '\n'
eol_regex = re.compile(r'\r?\n|\r\n?')


def update_eol(text):
    """We only want EOL as end of line
    """
    return eol_regex.sub(EOL, text)


class EmptyElement(object):
    """This object is used in the ListElement to keep the good index.
    """
    def __init__(self, parent_obj):
        self._parent_obj = parent_obj


class Element(object):
    """After reading a dtd file we construct some Element
    """
    tagname = None
    _attribute_names = None
    _attributes = None
    children_classes = None
    _required = False
    _parent_cls = None
    sourceline = None
    _comment = None
    _is_choice = False
    _is_empty = False

    # The following attributes should be used for the root element.
    _xml_filename = None
    _xml_dtd_url = None
    _xml_encoding = None

    # The render used to make HTML rendering.
    # See render.py for more details
    html_render = None

    def __init__(self, parent_obj=None, parent=None, *args, **kw):
        super(Element, self).__init__(*args, **kw)
        # parent and parent_obj are differents where the element is in a list:
        # the parent_obj of the element is the list but the parent is the
        # parent of the list. It's because the ListElement is just a container
        # not a real element.
        self._parent_obj = parent_obj
        self.parent = parent
        if self.parent is None:
            self.parent = self._parent_obj
            if self.parent is not None:
                # Only attach the property if we don't have a given parent,
                # since when we pass the parent, the property is already
                # attached.
                self.parent[self.tagname] = self

        if self._parent_obj is not None:
            self.root = self._parent_obj.root
        else:
            self.root = self

        # Store the XML element here
        self.xml_elements = {}
        # Cache
        self._cache_prefixes = None

    @property
    def prefixes_no_cache(self):
        """Same function as prefixes, but we don't want to set cache here. This
        function is used when we construct the objects, so we can't add cache
        during the construction is not finished
        """
        prefixes = []
        if self._parent_obj:
            prefixes = self._parent_obj.prefixes_no_cache
            if isinstance(self._parent_obj, ListElement):
                prefixes += [str(self._parent_obj.index(self))]
        prefixes += [self.tagname]
        return prefixes

    @property
    def prefixes(self):
        """Get the list of prefixes for this object
        """
        if self._cache_prefixes is None:
            prefixes = []
            if self._parent_obj:
                prefixes = self._parent_obj.prefixes
                if isinstance(self._parent_obj, ListElement):
                    prefixes += [str(self._parent_obj.index(self))]
            self._cache_prefixes = prefixes + [self.tagname]
        return self._cache_prefixes

    @classmethod
    def _get_allowed_tagnames(cls):
        # TODO: delete those function and update the tests
        return [cls.tagname]

    @classmethod
    def _get_creatable_class_by_tagnames(cls):
        """Returns the possible classes addable for this class
        """
        return {cls.tagname: cls}

    @classmethod
    def _get_creatable_subclass_by_tagnames(cls):
        """Returns the possible sub classes addable to this class
        """
        dic = {}
        for c in cls.children_classes:
            dic.update(c._get_creatable_class_by_tagnames())
        return dic

    @classmethod
    def get_class_to_create(cls, tagname):
        """Returns the class to create according to the given tagname
        """
        return cls._get_creatable_subclass_by_tagnames().get(tagname)

    @classmethod
    def get_child_class(cls, tagname):
        # TODO: this function should return the child class corresponding to
        # the tagname. For example if the tagname is an element of a list if
        # should return the list cls

        # for e in cls.children_classes:
        #     for tg in e._get_allowed_tagnames():
        #         if tg == tagname:
        #             return e
        dic = cls._get_creatable_subclass_by_tagnames()
        return dic.get(tagname)

    @classmethod
    def _get_value_from_parent(cls, parent_obj):
        return parent_obj.xml_elements.get(cls.tagname)

    @classmethod
    def _get_sub_value(cls, parent_obj):
        v = cls._get_value_from_parent(parent_obj)
        if not v and cls._required:
            v = cls(parent_obj)
        return v

    def _has_value(self):
        for elt in self.children_classes:
            v = elt._get_value_from_parent(self)
            if v is not None:
                return True
        return False

    @classmethod
    def _get_prefixes(cls, prefixes, index, name=None):
        tmp_prefixes = list(prefixes or [])
        if index is not None:
            tmp_prefixes.append(str(index))
        tmp_prefixes.append(cls.tagname)
        if name is not None:
            tmp_prefixes.append(name)
        return tmp_prefixes

    @classmethod
    def _get_str_prefix(cls, prefixes, index, name=None):
        tmp_prefixes = cls._get_prefixes(prefixes, index, name)
        return ':'.join(tmp_prefixes)

    @classmethod
    def _create(cls, tagname, parent_obj, value=None, index=None):
        obj = cls(parent_obj)
        if value:
            obj.set_text(value)
        return obj

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj
        """
        if tagname in obj:
            raise Exception('%s is already defined' % tagname)

    def is_addable(self, tagname):
        """Check if the given tagname can be added to the object
        """
        cls = self.get_class_to_create(tagname)
        if cls is None:
            return False
        try:
            cls._check_addable(self, tagname)
            return True
        except:
            pass
        return False

    def add(self, tagname, value=None, index=None):
        cls = self.get_class_to_create(tagname)
        if cls is None:
            raise Exception('Invalid child %s' % tagname)

        # May raise an exception
        cls._check_addable(self, tagname)
        obj = cls._create(tagname, self, value, index)
        return obj

    def set_text(self, value):
        raise Exception("Can't set value to non TextElement")

    def add_attribute(self, name, value):
        if name not in self._attribute_names:
            raise Exception('Invalid attribute name: %s' % name)
        self._attributes = self._attributes or {}
        self._attributes[name] = value

    def _load_attributes_from_xml(self, xml):
        for k, v in xml.attrib.items():
            self.add_attribute(k, v)

    def _load_attributes_from_dict(self, dic):
        if not dic:
            return
        attrs = dic.pop('_attrs', None)
        if not attrs:
            return
        for k, v in attrs.items():
            self.add_attribute(k, v)

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
        elt = etree.Comment(update_eol(self._comment))
        xml.addprevious(elt)

    def _comment_to_html(self, prefixes, index):
        name = self._get_str_prefix(prefixes, index, name='_comment')
        if not self._comment:
            return (
                u'<a data-comment-name="%s" class="btn-comment" '
                u'title="Add comment"></a>') % name
        else:
            return (
                u'<a data-comment-name="{name}" '
                u'class="btn-comment has-comment" title="{comment}"></a>'
                u'<textarea class="_comment" name="{name}">{comment}'
                '</textarea>'
            ).format(
                name=name,
                comment=self._comment
            )

    def _load_extra_from_xml(self, xml):
        self._load_attributes_from_xml(xml)
        self._load_comment_from_xml(xml)
        self.sourceline = xml.sourceline

    def set_lxml_elt(self, xml):
        self._lxml_elt = xml
        d = getattr(self.root, '_cached_lxml_elts', None)
        if not d:
            d = {}
            self.root._cached_lxml_elts = d
        d[id(xml)] = self

    def load_from_xml(self, xml):
        self.set_lxml_elt(xml)
        self._load_extra_from_xml(xml)
        for child in xml:
            if isinstance(child, etree._Comment):
                # The comments are loaded when we load the object
                continue
            obj = self.add(child.tag)
            obj.load_from_xml(child)

    def _load_extra_from_dict(self, data, skip_extra=False):
        if skip_extra:
            if not data:
                return
            # We need to remove the attributes and comment from data since we
            # don't want to load them as Element.
            data.pop('_attrs', None)
            data.pop('_comment', None)
            return

        self._load_attributes_from_dict(data)
        self._load_comment_from_dict(data)

    def load_from_dict(self, dic, skip_extra=False):
        data = dic.get(self.tagname)
        if not data:
            return
        self._load_extra_from_dict(data, skip_extra=skip_extra)
        for key, value in data.items():
            if isinstance(value, list):
                for d in value:
                    if d is None:
                        # Add empty element to keep index in the list.
                        lis = self.add(key)
                        elt = EmptyElement(parent_obj=lis)
                        lis.append(elt)
                    else:
                        assert(len(d) == 1)
                        obj = self.add(d.keys()[0])
                        obj.load_from_dict(d, skip_extra=skip_extra)
            else:
                obj = self.add(key)
                obj.load_from_dict(data, skip_extra=skip_extra)

    def to_xml(self):
        xml = etree.Element(self.tagname)
        self._comment_to_xml(xml)
        self._attributes_to_xml(xml)
        for elt in self.children_classes:
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
            return cls._parent_cls._get_html_add_button(prefixes, index, css_class)

        value = cls._get_str_prefix(prefixes, index)
        css_classes = ['btn-add']
        if css_class:
            css_classes += [css_class]
        return '<a class="%s" data-elt-id="%s">Add %s</a>' % (
            ' '.join(css_classes),
            value,
            cls.tagname)

    @classmethod
    def _to_html(cls, parent_obj, prefixes=None, index=None):
        v = cls._get_value_from_parent(parent_obj)
        if not v:
            # We always want an object since we need at least a add button.
            v = cls(parent_obj)
        return v.to_html(prefixes, index)

    def get_html_render(self):
        """Render uses to make the textarea as HTML and a first decision about
        adding buttons and comments.
        """
        if self.root.html_render is None:
            # Set a default renderer
            self.root.html_render = render.Render()
        return self.root.html_render

    def to_html(self, prefixes=None, index=None, delete_btn=False,
                add_btn=True,  partial=False):

        renderer = self.get_html_render()
        if not self._has_value() and not self._required and self._parent_obj and not partial:
            if not renderer.add_add_button():
                return ''
            # Add button!
            return self._get_html_add_button(prefixes, index)

        tmp_prefixes = self._get_prefixes(prefixes, index)
        sub_html = [self._attributes_to_html(prefixes, index)]
        for elt in self.children_classes:
            tmp = elt._to_html(self, tmp_prefixes)
            if tmp:
                sub_html += [tmp]

        legend = self.tagname
        if renderer.add_add_button():
            if ((not self._required and self._parent_obj and add_btn)
               or self._is_choice):
                legend += self._get_html_add_button(prefixes or [],
                                                    index, 'hidden')

        ident = ':'.join(tmp_prefixes)
        if renderer.add_delete_button():
            # Don't allow to delete root element!
            if (not self._required and self._parent_obj) or delete_btn or partial or self._is_choice:
                # NOTE: we assume the parent is a list if index is not None
                if (index is not None):
                    legend += ('<a class="btn-delete btn-list" '
                               'data-target="#%s" title="Delete"></a>') % ident
                else:
                    legend += ('<a class="btn-delete" '
                               'data-target="#%s" title="Delete"></a>') % ident
        if renderer.add_comment():
            legend += self._comment_to_html(prefixes, index)
        html = [(
            u'<div class="panel panel-default {css_class}" id="{ident}">'
            u'<div class="panel-heading">'
            u'<span data-toggle="collapse" '
            u'href="#collapse-{escaped_id}">{legend}</span>'
            u'</div>'
            u'<div class="panel-body panel-collapse collapse in" '
            u'id="collapse-{ident}">').format(
                css_class=self.tagname,
                ident=ident,
                legend=legend,
                escaped_id='\\:'.join(tmp_prefixes),
            )]
        html.extend(sub_html)
        html += ['</div></div>']
        return ''.join(html)

    @classmethod
    def _to_jstree_dict(cls, parent_obj, prefixes=None, index=None):
        v = cls._get_value_from_parent(parent_obj)
        if not v and cls._required:
            # We always want an object since we need at least a add button.
            v = cls(parent_obj)
        if v is not None:
            return v.to_jstree_dict(prefixes, index)

    def to_jstree_dict(self, prefixes, index=None):
        tmp_prefixes = self._get_prefixes(prefixes, index)
        data = self.tagname
        value = getattr(self, 'text', None)
        if value:
            data += u' <span class="_tree_text">(%s)</span>' % (
                utils.truncate(value))

        css_class = TREE_PREFIX + ':'.join(prefixes or [])
        if index is not None:
            css_class += ' ' + TREE_PREFIX + ':'.join((prefixes+[str(index)]))
        else:
            if not prefixes:
                css_class += self.tagname
            else:
                # We don't want to have tree_:tagname
                css_class += ':' + self.tagname

        dic = {
            'data': data,
            'attr': {
                'id': TREE_PREFIX + ':'.join(tmp_prefixes),
                'class': '%s %s' % (css_class, self.tagname),
            },
        }
        children = []
        for elt in self.children_classes:
            v = elt._to_jstree_dict(self, tmp_prefixes)
            if v:
                if isinstance(v, list):
                    children += v
                else:
                    children += [v]
        dic['children'] = children
        return dic

    def __setitem__(self, tagname, value):
        # TODO: Perhaps we should check the value type and if the tagname is
        # allowed
        self.xml_elements[tagname] = value

    def __getitem__(self, tagname):
        v = self.xml_elements.get(tagname)
        if v is None:
            raise KeyError(tagname)
        return v

    def get(self, tagname):
        return self.xml_elements.get(tagname)

    def __contains__(self, tagname):
        return tagname in self.xml_elements

    def get_or_add(self, tagname):
        v = self.xml_elements.get(tagname)
        if v:
            return v
        return self.add(tagname)

    def walk(self):
        for elt in self.children_classes:
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
            if elt.tagname == tagname:
                lis += [elt]
        return lis

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

        doctype = '<!DOCTYPE %(root_tag)s SYSTEM "%(dtd_url)s">' % {
            'root_tag': self.tagname,
            'dtd_url': dtd_url}

        # Some etree versions are not valid according to StrictVersion so we
        # split it.
        etree_version = '.'.join(etree.__version__.split('.')[:2])
        if StrictVersion(etree_version) < StrictVersion('2.3'):
            xml_str = etree.tostring(
                xml.getroottree(),
                pretty_print=True,
                xml_declaration=True,
                encoding=encoding,
            )
            xml_str = xml_str.replace('<%s' % self.tagname,
                                      '%s\n<%s' % (doctype, self.tagname))
        else:
            xml_str = etree.tostring(
                xml.getroottree(),
                pretty_print=True,
                xml_declaration=True,
                encoding=encoding,
                doctype=doctype)
        if transform:
            xml_str = transform(xml_str)
        open(filename, 'w').write(xml_str)

    def xpath(self, xpath):
        lxml_elt = getattr(self, '_lxml_elt', None)
        if lxml_elt is None:
            raise Exception(
                'The xpath is only supported '
                'when the object is loaded from XML')
        lis = self._lxml_elt.xpath(xpath)
        o = []
        for res in lis:
            elt = self.root._cached_lxml_elts.get(id(res))
            if elt:
                o += [elt]
            else:
                o += [res]
        return o


class TextElement(Element):
    text = None
    _exists = False

    def __repr__(self):
        return '<TextElement %s "%s">' % (
            self.tagname,
            (self.text or '').strip())

    def set_text(self, value):
        self.text = value

    def load_from_xml(self, xml):
        """
        TODO: we should support to have sub element in TextElement
        """
        self.set_lxml_elt(xml)
        self._load_extra_from_xml(xml)
        if len(xml):
            # Special case: we have comments in the text element
            # Since on iteration we only get comment elements, we parse in 2
            # steps.
            self.text = ''

            # Get the comments
            comments = []
            for e in xml:
                if isinstance(e, etree._Comment):
                    comments += [e.text]
            if comments:
                self._comment = self._comment or ''
                if self._comment:
                    self._comment += '\n'
                self._comment += '\n'.join(comments)

            for s in xml.itertext():
                if s in comments:
                    comments.remove(s)
                    continue
                self.text += s
            self.text = self.text or None
        else:
            self.text = xml.text
        # We use _exists to know if the tag is defined in the XML.
        self._exists = True

    def load_from_dict(self, dic, skip_extra=False):
        data = dic[self.tagname]
        self._load_extra_from_dict(data, skip_extra=skip_extra)
        self.text = data.get('_value')

    def to_xml(self):
        xml = etree.Element(self.tagname)
        # The comment can't be added here since we don't always have the parent
        # defined.
        self._attributes_to_xml(xml)
        # We never set self.text to None to make sure when we export as string
        # we get a HTML format (no autoclose tag)
        if self._is_empty:
            if self.text:
                raise Exception(
                    'It\'s forbidden to have a value to an EMPTY tag')
            xml.text = None
        else:
            xml.text = update_eol(self.text or '')
        return xml

    def _get_html_attrs(self, prefixes, rows, index=None):
        """Get the HTML attributes to put on the textarea.

        :return: List of tuple like [('name', 'myname'), ...]
        """
        prefixes = list(prefixes or [])
        if index is not None:
            prefixes += [str(index)]

        prefixes += [self.tagname]
        prefixes += ['_value']
        name = ':'.join(prefixes)
        attrs = [
            ('name', name),
            ('rows', rows),
            ('class', self.tagname),
        ]
        return attrs

    def to_html(self, prefixes=None, index=None, delete_btn=False,
                add_btn=True, partial=False):
        renderer = self.get_html_render()
        if (not self._exists and not self.text and
           not self._required and not partial):
            if not renderer.add_add_button():
                return ''
            return self._get_html_add_button(prefixes, index)

        parent_is_list = isinstance(self._parent_obj, ListElement)
        add_button = ''
        if renderer.add_add_button():
            if (not parent_is_list and not self._required) or self._is_choice:
                add_button = self._get_html_add_button(prefixes,
                                                       index, 'hidden')

        delete_button = ''
        ident = self._get_str_prefix(prefixes, index)
        if renderer.add_delete_button():
            if (delete_btn or not self._required
               or self._is_choice or parent_is_list):
                if parent_is_list:
                    delete_button = (
                        '<a class="btn-delete btn-list" '
                        'data-target="#%s" title="Delete"></a>') % ident
                else:
                    delete_button = (
                        '<a class="btn-delete" '
                        'data-target="#%s" title="Delete"></a>') % ident

        value = self.text or ''
        cnt = value.count('\n')
        if cnt:
            cnt += 1
        rows = max(cnt, 1)
        attrs = self._get_html_attrs(prefixes, rows, index)
        render = self.get_html_render()
        textarea = render.text_element_to_html(self, attrs, value)

        comment = ''
        if renderer.add_comment():
            comment = self._comment_to_html(prefixes, index)
        return (
            u'<div id="{ident}"><label>{label}</label>'
            u'{add_button}'
            u'{delete_button}'
            u'{comment}'
            u'{xmlattrs}'
            u'{textarea}'
            u'</div>').format(
            ident=ident,
            label=self.tagname,
            add_button=add_button,
            delete_button=delete_button,
            comment=comment,
            textarea=textarea,
            xmlattrs=self._attributes_to_html(prefixes, index),
        )


class InListMixin(object):

    @classmethod
    def _create(cls, tagname, parent_obj, value=None, index=None):
        # Make sure the parent list is create and get it.
        list_parent_obj = parent_obj.get_or_add(cls._parent_cls.tagname)
        obj = cls(parent_obj=list_parent_obj, parent=parent_obj)
        if index is not None:
            list_parent_obj.insert(index, obj)
        else:
            list_parent_obj.append(obj)
        if value:
            obj.set_text(value)
        return obj

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj
        """
        # We can always add an element to a list.
        pass


class MultipleMixin(object):
    _choice_classes = None

    @classmethod
    def _get_creatable_class_by_tagnames(cls):
        dic = {}
        for c in cls._choice_classes:
            dic[c.tagname] = c
        return dic

    @classmethod
    def _get_creatable_subclass_by_tagnames(cls):
        """Returns the possible sub classes addable to this class
        """
        dic = {}
        for c in cls._choice_classes:
            dic.update(c._get_creatable_class_by_tagnames())
        return dic


class ListElement(list, MultipleMixin, Element):

    def __init__(self, *args, **kw):
        # We only want to call the __init__ from Element since the __init__
        # with parameter from list wants to append an element to self
        Element.__init__(self, *args, **kw)

    @classmethod
    def _get_allowed_tagnames(cls):
        # TODO: delete those function and update the tests
        return [cls.tagname] + [e.tagname for e in cls._choice_classes]

    @classmethod
    def _get_creatable_class_by_tagnames(cls):
        dic = super(ListElement, cls)._get_creatable_class_by_tagnames()
        dic[cls.tagname] = cls
        return dic

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj
        """
        # We can always add an element to a list.
        pass

    def add(self, *args, **kw):
        # The logic to add Element to a list is on the parent
        return self._parent_obj.add(*args, **kw)

    @classmethod
    def _create(cls, tagname, parent_obj, value=None, index=None):
        if tagname != cls.tagname:
            raise Exception('Unsupported tagname %s' % tagname)

        # Get the list element or create it
        lis = parent_obj.get(cls.tagname)
        if lis is None:
            lis = cls(parent_obj)
            if len(cls._choice_classes) == 1:
                # Create a shortcut since we only have one element
                parent_obj[cls._choice_classes[0].tagname] = lis
        if value:
            # TODO: not really nice, it's just to raise the same Exception as
            # Element.set_text.
            lis.set_text(value)
        return lis

    def remove_empty_element(self):
        """Remove the empty elements from this list since it should not be
        in the XML nor HTML.
        """
        to_remove = []
        for e in self:
            if isinstance(e, EmptyElement):
                to_remove += [e]
        for e in to_remove:
            self.remove(e)

    def to_xml(self):
        self.remove_empty_element()
        lis = []
        if not len(self) and self._required:
            if len(self._choice_classes) == 1:
                e = self.add(self._choice_classes[0].tagname)

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
        if len(cls._choice_classes) == 1:
            css_classes = ['btn-add btn-list']
            if css_class:
                css_classes += [css_class]

            tmp_prefixes = list(prefixes or []) + [
                cls.tagname, index, cls._choice_classes[0].tagname]
            data_id = ':'.join(
                map(str, filter((lambda x: x is not None), tmp_prefixes)))
            button = ('<a class="%s" '
                      'data-elt-id="%s">New %s</a>') % (
                          ' '.join(css_classes),
                          data_id,
                          cls._choice_classes[0].tagname)
            return button

        assert not css_class
        button = '<select class="btn-add btn-list">'
        options = '/'.join([e.tagname for e in cls._choice_classes])
        button += '<option>New %s</option>' % options

        tmp_prefixes = list(prefixes or [])
        tmp_prefixes.append(cls.tagname)
        tmp_prefixes.append(str(index))
        prefix_str = ':'.join(tmp_prefixes)
        for e in cls._choice_classes:
            button += '<option value="%s:%s">%s</option>' % (
                prefix_str,
                e.tagname,
                e.tagname)
        button += '</select>'
        return button

    @classmethod
    def _get_value_from_parent(cls, parent_obj):
        tg = cls.tagname
        if len(cls._choice_classes) == 1:
            tg = cls._choice_classes[0].tagname
        return parent_obj.xml_elements.get(tg)

    def to_html(self, prefixes=None, index=None, delete_btn=False,
                add_btn=True, partial=False, offset=0):

        self.remove_empty_element()
        # We should not have the following parameter for this object
        assert self._attributes is None
        assert index is None

        if not len(self) and (self._required or partial):
            if len(self._choice_classes) == 1:
                e = self.add(self._choice_classes[0].tagname)

        renderer = self.get_html_render()
        i = -1
        lis = []
        for i, e in enumerate(self):
            if not partial and renderer.add_add_button():
                lis += [self._get_html_add_button(prefixes, (i+offset))]
            force = False
            if i == 0 and (partial or self._required):
                force = True
            lis += [e.to_html(((prefixes or [])+[self.tagname]),
                              (i+offset),
                              delete_btn=True,
                              partial=force,
                              add_btn=False)]

        if renderer.add_add_button():
            lis += [self._get_html_add_button(prefixes, i+offset+1)]

        if partial:
            return ''.join(lis)
        return '<div class="list-container">%s</div>' % ''.join(lis)

    def to_jstree_dict(self, prefixes, index=None, offset=0):
        if not len(self) and (self._required):
            if len(self._choice_classes) == 1:
                e = self.add(self._choice_classes[0].tagname)

        lis = []
        for i, e in enumerate(self):
            v = e.to_jstree_dict((prefixes or [])+[self.tagname], i+offset)
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
        # TODO: delete those function and update the tests
        return [e.tagname for e in cls._choice_classes]

    @classmethod
    def _create(cls, tagname, parent_obj, value=None, index=None):
        elt_cls = cls.get_class_to_create(tagname)
        return elt_cls._create(tagname, parent_obj, value, index)

    def add(self, *args, **kw):
        raise Exception('Can\'t add element to ChoiceElement')

    def is_addable(self, tagname):
        # Nothing is addable to ChoiceElement
        return False

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj
        """
        # If one of the different choice is already added, we can't add
        # anything.
        for elt in cls._choice_classes:
            if elt.tagname in obj:
                err = '%s is already defined' % elt.tagname
                if elt.tagname != tagname:
                    err = '%s is defined so you can\'t add %s' % (elt.tagname,
                                                                  tagname)
                raise Exception(err)

    @classmethod
    def _get_html_add_button(cls, prefixes, index=None, css_class=None):
        """
        ..note:: index is not used here since we never have list of this
        element.
        """
        css_classes = ['btn-add']
        if css_class:
            css_classes += [css_class]

        button = '<select class="%s">' % ' '.join(css_classes)
        button += '<option>New %s</option>' % '/'.join([e.tagname for e in cls._choice_classes])
        for e in cls._choice_classes:
            button += '<option value="%s">%s</option>' % (
                e._get_str_prefix(prefixes, index, None),
                e.tagname)
        button += '</select>'
        return button

    @classmethod
    def _get_value_from_parent(cls, parent_obj):
        for elt in cls._choice_classes:
            v = parent_obj.xml_elements.get(elt.tagname)
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
        raise NotImplementedError
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
        tmp_cls = obj.get_child_class(s)
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


def load_obj_from_id(str_id, data, dtd_url=None, dtd_str=None):
    """Create a root object with the given data.
    We return the sub object found according to the given str_id.
    """
    dic = dtd_parser.parse(dtd_url=dtd_url, dtd_str=dtd_str)
    splitted = str_id.split(':')
    s = splitted.pop(0)

    # Get the root object
    obj = dic[s]()
    obj.load_from_dict(data)

    # Find the good object according to the given id
    subobj = obj
    while splitted:
        s = splitted.pop(0)
        try:
            # import pdb; pdb.set_trace()
            s = int(s)
            # The sub id just after an integer is for the type object, we don't
            # need it here.
            subelt = splitted.pop(0)
            while len(subobj) < s:
                # We don't have enough element, add some empty one
                elt = EmptyElement(parent_obj=subobj)
                subobj.append(elt)
            # If the last element is missing we should add the right element
            # type
            while len(subobj) < (s+1):
                subobj.add(subelt)
            subobj = subobj[s]

            if isinstance(subobj, EmptyElement):
                # The element is empty, we remove it and create the good one!
                subobj._parent_obj.remove(subobj)
                subobj = subobj._parent_obj.add(subelt, index=s)
        except ValueError:
            if s not in subobj:
                subobj.add(s)
            subobj = subobj[s]

    return subobj


def get_parent_to_add_obj(elt_id, source_id, data, dtd_url=None, dtd_str=None):
    """Create element from data and elt_id and determine if source_id can be
    added to it or its parent.
    """
    target_obj = load_obj_from_id(elt_id, data, dtd_url=dtd_url,
                                  dtd_str=dtd_str)
    if isinstance(target_obj, EmptyElement):
        # The target is an empty object, we remove it and replace it by the
        # right object.
        parent_obj = target_obj._parent_obj
        assert(isinstance(parent_obj, ListElement))
        index = parent_obj.index(target_obj)
        parent_obj.pop(index)
        # Should always been the -2:
        # -1 is the object we want to copy
        # -2 is the container, should also be a list
        # normally a ListElement is at least 3 elements
        tagname = source_id.split(':')[-2]
        if not parent_obj.is_addable(tagname):
            return None
        target_obj = parent_obj.add(tagname, index=index)

    tagname = source_id.split(':')[-1]
    parent_obj = None
    if target_obj.is_addable(tagname):
        return target_obj

    parent_obj = target_obj._parent_obj
    if parent_obj and parent_obj.is_addable(tagname):
        return parent_obj

    return None


def add_new_element_from_id(elt_id, source_id, data, clipboard_data, dtd_url=None,
                            dtd_str=None, skip_extra=False):
    """Create an element from data and elt_id. We get the parent to add
    source_id with the clipboard_data. This function should be used to make
    some copy/paste.

    :param skip_extra: If True we don't load the attributes nor the comments
    :type skip_extra: bool
    """
    parentobj = get_parent_to_add_obj(elt_id, source_id, data, dtd_url=dtd_url,
                                      dtd_str=dtd_str)
    if not parentobj:
        return None

    tagname = source_id.split(':')[-1]
    obj = parentobj.add(tagname)

    for s in source_id.split(':')[:-1]:
        try:
            s = int(s)
        except:
            pass
        clipboard_data = clipboard_data[s]
    obj.load_from_dict(clipboard_data, skip_extra=skip_extra)
    return obj


def _get_previous_js_selectors(obj, prefixes, index):
    lis = []

    parent = obj._parent_obj
    if not parent:
        return lis

    parent_is_list = isinstance(parent, ListElement)
    tmp_prefixes = prefixes[:-1]
    if parent_is_list:
        parent = parent._parent_obj
        if int(index) > 0:
            index = int(index) - 1
            lis += [
                ('after', '.%s%s' % (
                    TREE_PREFIX,
                    ':'.join(tmp_prefixes + [str(index)])))]
            return lis
        tmp_prefixes = tmp_prefixes[:-1]

    # TODO hack: remove this!
    tagname = obj.tagname
    if isinstance(obj, InListMixin):
        tagname = obj._parent_obj.tagname

    # if obj._is_choice:
    #     tagname = obj._parent_obj.tagname

    sub = parent.get_child_class(tagname)
    if sub._is_choice:
        # HACK: because get_child_class returns a sub child of class
        sub = sub._parent_cls
    assert(sub)

    for elt in parent.children_classes:
        if elt == sub:
            break
        tmp_prefix = list(tmp_prefixes) + [elt.tagname]
        lis += [('after', '.%s%s' % (
            TREE_PREFIX,
            ':'.join(tmp_prefix)))]

    lis.reverse()
    lis += [('inside', '#%s%s' % (
        TREE_PREFIX,
        ':'.join(tmp_prefixes)))]
    return lis


def get_obj_from_str_id(str_id, dtd_url=None, dtd_str=None):
    obj, prefixes, index = _get_obj_from_str_id(str_id, dtd_url, dtd_str)
    if isinstance(obj._parent_obj, ListElement):
        index = int(index or 0)
        tmp = obj.to_html(prefixes[:-1], index, add_btn=False, partial=True)
        tmp += obj._parent_obj._get_html_add_button(prefixes[:-2], index+1)
        return tmp

    return obj.to_html(prefixes[:-1], index, partial=True)


def _get_html_from_obj(obj, prefixes, index):
    if isinstance(obj._parent_obj, ListElement):
        index = int(index or 0)
        tmp = obj.to_html(prefixes[:-1], index, add_btn=False, partial=True)
        tmp += obj._parent_obj._get_html_add_button(prefixes[:-2], index+1)
        return tmp

    return obj.to_html(prefixes[:-1], index, partial=True)


def get_jstree_json_from_str_id(str_id, dtd_url=None, dtd_str=None):
    obj, prefixes, index = _get_obj_from_str_id(str_id, dtd_url, dtd_str)
    return {
        # Since we are calling to_jstree_dict from the object we need to remove
        # its prefix because it will be added in this method.
        'jstree_data': obj.to_jstree_dict(prefixes[:-1], index),
        'previous': _get_previous_js_selectors(obj, prefixes, index),
        'html': _get_html_from_obj(obj, prefixes, index),
    }


def get_display_data_from_obj(obj):
    # TODO: refactor this function with get_jstree_json_from_str_id
    # We should not have to pass the prefixes and index, each Element should be
    # able to calculate it! Currently it sucks!
    index = None
    prefixes = obj.prefixes
    if obj._parent_obj and isinstance(obj._parent_obj, ListElement):
        index = int(obj.prefixes[-2])
        prefixes = prefixes[:-1]

    html = _get_html_from_obj(obj, prefixes, index)

    prefixes = obj.prefixes[:-1]
    if isinstance(obj._parent_obj, ListElement):
        index = prefixes[-1]
        prefixes = prefixes[:-1]
        jstree_data = obj.to_jstree_dict(prefixes, index=index)
    else:
        jstree_data = obj.to_jstree_dict(prefixes)

    prefixes = obj.prefixes
    if obj._parent_obj and isinstance(obj._parent_obj, ListElement):
        prefixes = prefixes[:-1]

    is_choice = obj._is_choice
    if not is_choice and isinstance(obj._parent_obj, ListElement):
        # Check if there is multiple possible element in the list
        is_choice = (len(obj._parent_obj._choice_classes) != 1)

    return {
        'jstree_data': jstree_data,
        'previous': _get_previous_js_selectors(obj, prefixes, index),
        'html': html,
        'elt_id': ':'.join(obj.prefixes),
        'is_choice': is_choice,
    }
