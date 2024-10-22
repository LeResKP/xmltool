#!/usr/bin/env python

from io import StringIO, open
import os
import re
from lxml import etree


DEFAULT_ENCODING = "UTF-8"

# We expect just '\n' in the XML output
EOL = "\n"
eol_regex = re.compile(r"\r?\n|\r\n?")


def update_eol(text):
    """We only want EOL as end of line"""
    if isinstance(text, etree.CDATA):
        # Don't treat CDATA
        return text
    return eol_regex.sub(EOL, text)


class EmptyElement(object):
    """This object is used in the ListElement to keep the good index."""

    def __init__(self, parent_obj):
        self._parent_obj = parent_obj
        self._auto_added = False


class Element(object):
    """After reading a dtd file we construct some Element"""

    tagname = None
    _attribute_names = None
    attributes = None
    children_classes = None
    _required = False
    _parent_cls = None
    sourceline = None
    comment = None
    _is_empty = False

    # The following attributes should be used for the root element.
    filename = None
    dtd_url = None
    dtd_str = None
    encoding = None

    def __init__(self, parent_obj=None, parent=None, auto_added=False, *args, **kw):
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
        # Will be set to True when we add tag to render the object.  This flag
        # is used to know the object has been added by the code so we should
        # remove it in the code.
        self._auto_added = auto_added

    @property
    def position(self):
        """If the parent is a list, returns the position of self.
        Otherwise returns None
        """
        if not self._parent_obj:
            return None
        if not isinstance(self._parent_obj, ListElement):
            return None
        return self._parent_obj.index(self)

    @classmethod
    def _get_creatable_class_by_tagnames(cls):
        """Returns the possible classes addable for this class"""
        return {cls.tagname: cls}

    @classmethod
    def _get_creatable_subclass_by_tagnames(cls):
        """Returns the possible sub classes addable to this class"""
        dic = {}
        for c in cls.children_classes:
            dic.update(c._get_creatable_class_by_tagnames())
        return dic

    @classmethod
    def get_class_to_create(cls, tagname):
        """Returns the class to create according to the given tagname"""
        return cls._get_creatable_subclass_by_tagnames().get(tagname)

    @classmethod
    def _get_value_from_parent(cls, parent_obj):
        return parent_obj.xml_elements.get(cls.tagname)

    @classmethod
    def _get_sub_value(cls, parent_obj):
        v = cls._get_value_from_parent(parent_obj)
        if not v and cls._required:
            # TODO: Add flag on this object to know it's autoadded and delete
            # it when we finish to use it.
            # We have some side effect after we generate the HTML since we
            # create all object to at least have a add button
            v = cls(parent_obj, auto_added=True)
        return v

    def _has_value(self):
        for elt in self.children_classes:
            v = elt._get_value_from_parent(self)
            if v is not None:
                return True
        return False

    @property
    def children(self):
        """Iterator to get the children defined of an object."""
        for cls in self.children_classes:
            v = cls._get_value_from_parent(self)
            if v:
                if isinstance(v, list):
                    for subv in v:
                        yield subv
                else:
                    yield v

    @property
    def _children_with_required(self):
        """Iterator to get the children defined and the required of an object.
        If possible, We create on the fly the required object not defined.
        """
        for cls in self.children_classes:
            obj = cls._get_sub_value(self)
            if obj is not None:
                yield obj

    @property
    def _full_children(self):
        """Iterator to get all the children of an object.
        If possible, We create on the fly the all the child object.
        """
        for cls in self.children_classes:
            obj = cls._get_sub_value(self)
            if obj is None:
                obj = cls(self, auto_added=True)
            yield obj

    @classmethod
    def _create(cls, tagname, parent_obj, value=None, index=None):
        obj = cls(parent_obj)
        if value is not None:
            obj.set_text(value)
        return obj

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj"""
        if tagname in obj:
            raise Exception("%s is already defined" % tagname)

    def is_addable(self, tagname):
        """Check if the given tagname can be added to the object"""
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
            raise Exception("Invalid child %s" % tagname)

        # May raise an exception
        cls._check_addable(self, tagname)
        obj = cls._create(tagname, self, value, index)
        return obj

    def delete(self):
        if self._parent_obj is None:
            raise Exception("Can't delete the root Element")
        del self._parent_obj[self.tagname]

    def _delete_auto_added(self):
        if self._auto_added:
            self.delete()

    def set_text(self, value):
        raise Exception("Can't set value to non TextElement")

    def add_attribute(self, name, value):
        if name not in self._attribute_names:
            raise Exception("Invalid attribute name: %s" % name)
        self.attributes = self.attributes or {}
        self.attributes[name] = value

    def _load_attributes_from_xml(self, xml):
        for k, v in xml.attrib.items():
            self.add_attribute(k, v)

    def _attributes_to_xml(self, xml):
        if not self.attributes:
            return
        for k, v in self.attributes.items():
            xml.attrib[k] = v

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
        self.comment = "\n".join(comments) or None

    def _comment_to_xml(self, xml):
        if not self.comment:
            return None
        elt = etree.Comment(update_eol(self.comment))
        xml.addprevious(elt)

    def _load_extra_from_xml(self, xml):
        self._load_attributes_from_xml(xml)
        self._load_comment_from_xml(xml)
        self.sourceline = xml.sourceline

    def set_lxml_elt(self, xml):
        self._lxml_elt = xml
        d = getattr(self.root, "_cached_lxml_elts", None)
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

    def to_xml(self):
        xml = etree.Element(self.tagname)
        self._comment_to_xml(xml)
        self._attributes_to_xml(xml)
        for v in self._children_with_required:
            e = v.to_xml()
            v._delete_auto_added()
            if e is None:
                continue
            if isinstance(e, list):
                xml.extend(e)
            else:
                xml.append(e)
                # NOTE: the attributes are already set but we need to add
                # the comment here.
                v._comment_to_xml(e)
        return xml

    def __str__(self):
        xml = self.to_xml()
        if xml is not None:
            #  encoding='unicode' will force lxml to return a unicode string
            return etree.tostring(xml, pretty_print=True, encoding="unicode")
        return xml

    def __setitem__(self, tagname, value):
        # TODO: Perhaps we should check the value type and if the tagname is
        # allowed
        self.xml_elements[tagname] = value

    def __getitem__(self, tagname):
        v = self.xml_elements.get(tagname)
        if v is None:
            raise KeyError(tagname)
        return v

    def __delitem__(self, tagname):
        del self.xml_elements[tagname]

    def __contains__(self, tagname):
        return tagname in self.xml_elements

    def get(self, tagname):
        return self.xml_elements.get(tagname)

    def get_or_add(self, tagname, value=None, index=None):
        v = self.xml_elements.get(tagname)
        if v:
            return v
        return self.add(tagname, value=value, index=index)

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

    def write(
        self,
        filename=None,
        encoding=None,
        dtd_url=None,
        dtd_str=None,
        validate=True,
        transform=None,
    ):
        filename = filename or self.filename
        if not filename:
            raise Exception("No filename given")
        dtd_url = dtd_url or self.dtd_url
        dtd_str = dtd_str or self.dtd_str
        if not dtd_url and not dtd_str:
            raise Exception("No dtd given")
        encoding = encoding or self.encoding or DEFAULT_ENCODING
        xml = self.to_xml()
        if validate:
            url = dtd_url if dtd_url else StringIO(dtd_str)
            from . import dtd

            dtd.DTD(url, os.path.dirname(filename)).validate_xml(xml)

        doctype = '<!DOCTYPE %(root_tag)s SYSTEM "%(dtd_url)s">' % {
            "root_tag": self.tagname,
            "dtd_url": dtd_url,
        }

        xml_str = etree.tostring(
            xml.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding=encoding,
            doctype=doctype,
        )

        if transform:
            xml_str = transform(xml_str.decode(encoding)).encode(encoding)

        open(filename, "wb").write(xml_str)

    def xpath(self, xpath):
        lxml_elt = getattr(self, "_lxml_elt", None)
        if lxml_elt is None:
            raise Exception(
                "The xpath is only supported " "when the object is loaded from XML"
            )
        lis = self._lxml_elt.xpath(xpath)
        o = []
        for res in lis:
            elt = self.root._cached_lxml_elts.get(id(res))
            if elt:
                o += [elt]
            else:
                o += [res]
        return o


class ContainerElement(Element):
    pass


class TextElement(Element):
    text = None
    cdata = False

    def __repr__(self):
        return '<TextElement %s "%s">' % (self.tagname, (self.text or "").strip())

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
            self.text = ""

            # Get the comments
            comments = []
            for e in xml:
                if isinstance(e, etree._Comment):
                    comments += [e.text]
            if comments:
                self.comment = self.comment or ""
                if self.comment:
                    self.comment += "\n"
                self.comment += "\n".join(comments)

            for s in xml.itertext():
                if s in comments:
                    comments.remove(s)
                    continue
                # Don't support CDATA here, since it's a bit strange, we
                # already have comments with the text
                self.text += s
        else:
            # Didn't find any other way to detect CDATA. This way is not ideal
            # but it's working for simple case. Also it doesn't support mixed
            # content (text + CDATA) in the same element
            self.text = xml.text
            if etree.tostring(xml).split(b">")[1].startswith(b"<![CDATA["):
                self.cdata = True

        # We should have text != None to be sure we keep the existing empty tag.
        self.text = self.text or ""

    def to_xml(self):
        xml = etree.Element(self.tagname)
        # The comment can't be added here since we don't always have the parent
        # defined.
        self._attributes_to_xml(xml)
        if self._is_empty:
            if self.text:
                raise Exception("It's forbidden to have a value to an EMPTY tag")
            xml.text = None
        else:
            # We never set self.text to None to make sure when we export as string
            # we get a HTML format (no autoclose tag)
            xml.text = update_eol(self.text or "")
            if self.cdata:
                xml.text = etree.CDATA(xml.text)
        return xml


class InChoiceMixin(object):
    @classmethod
    def _create(cls, tagname, parent_obj, value=None, index=None):
        choice_parent_obj = parent_obj.get_or_add(cls._parent_cls.tagname)
        obj = cls(parent_obj=choice_parent_obj, parent=parent_obj)
        choice_parent_obj._value = obj
        # Remove the existing shortcut
        for c in choice_parent_obj._choice_classes:
            if c.tagname in parent_obj:
                del parent_obj[c.tagname]
        # Create the new shortcut
        parent_obj[obj.tagname] = obj
        if value is not None:
            obj.set_text(value)
        return obj

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj"""
        cls._parent_cls._check_addable(obj, tagname)

    def delete(self):
        self._parent_obj.delete()


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
        if value is not None:
            obj.set_text(value)
        return obj

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj"""
        # TODO: perhaps we have some check to do here
        # We can always add an element to a list.
        pass

    def delete(self):
        self._parent_obj.remove(self)


class BaseListElement(list, Element):
    def __init__(self, *args, **kw):
        # We only want to call the __init__ from Element since the __init__
        # with parameter from list wants to append an element to self
        Element.__init__(self, *args, **kw)

    def __str__(self):
        xml_lis = self.to_xml()
        return "\n".join(
            etree.tostring(xml, pretty_print=True, encoding="unicode")
            for xml in xml_lis
        )

    @classmethod
    def _get_creatable_class_by_tagnames(cls):
        # We need to add cls.tagname here to be able to create the list when we
        # call add('list_tagname')
        dic = cls._children_class._get_creatable_class_by_tagnames()
        dic[cls.tagname] = cls
        return dic

    @classmethod
    def _get_creatable_subclass_by_tagnames(cls):
        """Returns the possible sub classes addable to this class"""
        return {cls._children_class.tagname: cls._children_class}

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj"""
        # We can always add an element to a list.
        pass

    @classmethod
    def _create(cls, tagname, parent_obj, value=None, index=None):
        """Same function as ListElement without creating shortcut for direct
        access to object.
        """
        if tagname != cls.tagname:
            raise Exception("Unsupported tagname %s" % tagname)

        # Get the list element or create it
        lis = parent_obj.get(cls.tagname)
        if lis is None:
            lis = cls(parent_obj)
        if value is not None:
            # TODO: not really nice, it's just to raise the same Exception as
            # Element.set_text.
            lis.set_text(value)
        return lis

    def add(self, *args, **kw):
        # The logic to add Element to a list is on the parent
        return self._parent_obj.add(*args, **kw)

    def get_or_add(self, tagname, value=None, index=None):
        if index is None:
            raise Exception("Parameter index is required")

        if index < len(self):
            obj = self[index]
            if not isinstance(obj, EmptyElement):
                return obj
            # We shouldn't return an EmptyElement, we remove it and create the
            # good object.
            self.remove(obj)

        if len(self) < index:
            for i in range(index):
                if i < len(self):
                    continue
                elt = EmptyElement(parent_obj=self)
                self.append(elt)
        return self.add(tagname, value=value, index=index)

    def walk(self):
        for elt in self:
            yield elt
            for e in elt.walk():
                yield e

    def _before_render(self):
        # Nothing to do by default, it's just used in ListElement
        pass

    def _after_render(self):
        # Nothing to do by default, it's just used in ListElement
        pass

    def to_xml(self):
        self._before_render()
        lis = []
        for e in self:
            if isinstance(e, EmptyElement):
                continue
            if e.comment:
                elt = etree.Comment(e.comment)
                lis += [elt]
            lis += [e.to_xml()]
        self._after_render()
        return lis


class ListElement(BaseListElement):
    def __init__(self, *args, **kw):
        super(ListElement, self).__init__(*args, **kw)
        # Create a shortcut
        self._parent_obj[self._children_class.tagname] = self

    def delete(self):
        super(ListElement, self).delete()
        # delete the shortcut
        del self._parent_obj[self._children_class.tagname]

    def _before_render(self):
        super(ListElement, self)._before_render()

        if not len(self) and self._required:
            obj = self.add(self._children_class.tagname)
            obj._auto_added = True

    def _after_render(self):
        super(ListElement, self)._before_render()
        for o in self:
            if o._auto_added:
                o.delete()


class MultipleMixin(object):
    _choice_classes = None

    @classmethod
    def _get_creatable_class_by_tagnames(cls):
        dic = {}
        for c in cls._choice_classes:
            dic[c.tagname] = c
        dic[cls.tagname] = cls
        return dic

    @classmethod
    def _get_creatable_subclass_by_tagnames(cls):
        """Returns the possible sub classes addable to this class"""
        dic = {}
        for c in cls._choice_classes:
            dic.update(c._get_creatable_class_by_tagnames())
        return dic


class ChoiceListElement(MultipleMixin, BaseListElement):
    pass


class ChoiceElement(MultipleMixin, Element):
    # TODO: we should have an init to define this attribute
    _value = None

    @classmethod
    def _create(cls, tagname, parent_obj, value=None, index=None):
        if tagname != cls.tagname:
            raise Exception("Unsupported tagname %s" % tagname)

        # Get the list element or create it
        choice = parent_obj.get(cls.tagname)
        if choice is None:
            choice = cls(parent_obj)
        if value is not None:
            choice.set_text(value)
        return choice

    def add(self, *args, **kw):
        # The logic to add Element to a choice is on the parent
        return self._parent_obj.add(*args, **kw)

    def delete(self):
        super(ChoiceElement, self).delete()
        # Delete the shortcut
        parent_obj = self._parent_obj
        for c in self._choice_classes:
            if c.tagname in parent_obj:
                del parent_obj[c.tagname]
                return

    def is_addable(self, tagname):
        # Nothing is addable to ChoiceElement
        return False

    @classmethod
    def _check_addable(cls, obj, tagname):
        """Check if the given tagname is addable to the given obj"""
        if tagname == cls.tagname:
            # TODO: we should be able to add existing tag: in this case it just
            # returns the existing on like the ListElement but it's not logic.
            # We have get_or_add to do this.
            return True
        # If one of the different choice is already added, we can't add
        # anything.
        for elt in cls._choice_classes:
            if elt.tagname in obj:
                err = "%s is already defined" % elt.tagname
                if elt.tagname != tagname:
                    err = "%s is defined so you can't add %s" % (elt.tagname, tagname)
                raise Exception(err)

    @classmethod
    def _get_value_from_parent(cls, parent_obj):
        obj = parent_obj.xml_elements.get(cls.tagname)
        if obj:
            return obj._value

    def to_xml(self):
        if self._value:
            return self._value.to_xml()
