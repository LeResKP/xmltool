#!/usr/bin/env python

from io import StringIO
from mock import patch
from xmltool.testbase import BaseTest
from lxml import etree
import os.path
from xmltool import dtd
from xmltool.elements import (
    ContainerElement,
    ListElement,
    TextElement,
    ChoiceElement,
    ChoiceListElement,
    update_eol,
    InListMixin,
    InChoiceMixin,
)
import xmltool.elements as elements
from .test_dtd_parser import (
    BOOK_XML,
    BOOK_DTD,
    EXERCISE_XML_2,
    EXERCISE_DTD_2,
    EXERCISE_DTD,
    MOVIE_DTD,
    MOVIE_XML_TITANIC,
    MOVIE_XML_TITANIC_COMMENTS,
)

_marker = object()


class FakeClass(object):
    root = None

    def __init__(self, *args, **kw):
        self.xml_elements = {}


class TestElement(BaseTest):
    def setUp(self):
        self.sub_cls = type(
            "SubCls", (ContainerElement,), {"tagname": "subtag", "children_classes": []}
        )
        self.cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "tag", "children_classes": [self.sub_cls]},
        )
        self.root_cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "root_tag", "children_classes": [self.cls]},
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls._parent_cls = self.cls

    def test_position(self):
        obj = self.cls()
        self.assertEqual(obj.position, None)

    def test__get_creatable_class_by_tagnames(self):
        self.assertEqual(self.cls._get_creatable_class_by_tagnames(), {"tag": self.cls})

    def test__get_creatable_subclass_by_tagnames(self):
        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {"subtag": self.sub_cls}
        self.assertEqual(res, expected)

        sub_cls1 = type(
            "SubCls1",
            (ContainerElement,),
            {
                "tagname": "subtag1",
                "children_classes": [],
                "_parent_cls": self.cls,
            },
        )
        self.cls.children_classes += [sub_cls1]

        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {
            "subtag": self.sub_cls,
            "subtag1": sub_cls1,
        }
        self.assertEqual(res, expected)

    def test__get_value_from_parent(self):
        obj = self.cls(self.root_obj)
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), obj)
        self.root_obj["tag"] = None
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)

    def test__get_sub_value(self):
        result = self.cls._get_sub_value(self.root_obj)
        self.assertFalse(result)
        self.cls._required = True
        obj = self.cls(self.root_obj)
        self.assertEqual(self.cls._get_sub_value(self.root_obj), obj)

        self.root_obj["tag"] = None
        result = self.cls._get_sub_value(self.root_obj)
        self.assertTrue(result)
        self.assertTrue(result != obj)

    def test__has_value(self):
        obj = self.cls()
        self.assertFalse(obj._has_value())
        obj["subtag"] = self.sub_cls()
        self.assertTrue(obj._has_value())

    def test_children(self):
        obj = self.cls()
        children = list(obj.children)
        self.assertEqual(children, [])

        sub = obj.add("subtag")
        children = list(obj.children)
        self.assertEqual(children, [sub])

    def test__children_with_required(self):
        obj = self.cls()
        children = list(obj._children_with_required)
        self.assertEqual(children, [])

        self.sub_cls._required = True
        children = list(obj._children_with_required)
        self.assertEqual(len(children), 1)
        self.assertTrue(isinstance(children[0], self.sub_cls))

    def test__full_children(self):
        obj = self.cls()
        children = list(obj._full_children)
        self.assertEqual(len(children), 1)
        self.assertTrue(isinstance(children[0], self.sub_cls))

    def test_root(self):
        self.assertEqual(self.root_obj.root, self.root_obj)
        obj = self.cls._create("subtag", self.root_obj)
        self.assertEqual(obj.root, self.root_obj)

    def test__add(self):
        try:
            obj = self.cls._create("tag", self.root_obj, "my value")
            assert False
        except Exception as e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj = self.cls._create("tag", self.root_obj)
        self.assertEqual(obj._parent_obj, self.root_obj)
        self.assertEqual(obj.root, self.root_obj)
        self.assertTrue(isinstance(obj, ContainerElement))
        self.assertEqual(self.root_obj["tag"], obj)

    def test_is_addable(self):
        obj = self.cls()
        res = obj.is_addable("test")
        self.assertEqual(res, False)

        res = obj.is_addable("subtag")
        self.assertEqual(res, True)

        obj["subtag"] = "somthing"
        res = obj.is_addable("subtag")
        self.assertEqual(res, False)

    def test_add(self):
        root_cls = type(
            "RootElement",
            (ContainerElement,),
            {
                "tagname": "root_element",
                "children_classes": [],
            },
        )
        root_obj = root_cls()
        obj = self.cls(root_obj)
        newobj = obj.add("subtag")
        self.assertTrue(newobj)
        try:
            obj.add("unexisting")
        except Exception as e:
            self.assertEqual(str(e), "Invalid child unexisting")

        root_obj = root_cls()
        obj = self.cls(root_obj)
        try:
            newobj = obj.add("subtag", "my value")
            assert 0
        except Exception as e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

    def test_delete(self):
        try:
            self.root_obj.delete()
            assert False
        except Exception as e:
            self.assertEqual(str(e), "Can't delete the root Element")

        obj = self.cls(self.root_obj)
        self.assertEqual(self.root_obj[self.cls.tagname], obj)
        obj.delete()
        self.assertEqual(self.root_obj.get(self.cls.tagname), None)

    def test_add_attribute(self):
        obj = self.cls()
        obj._attribute_names = ["attr1", "attr2"]
        obj.add_attribute("attr1", "value1")
        self.assertEqual(obj.attributes, {"attr1": "value1"})
        obj.add_attribute("attr2", "value2")
        self.assertEqual(obj.attributes, {"attr1": "value1", "attr2": "value2"})
        obj.add_attribute("attr2", "newvalue2")
        self.assertEqual(obj.attributes, {"attr1": "value1", "attr2": "newvalue2"})

        try:
            obj.add_attribute("unexisting", "newvalue2")
        except Exception as e:
            self.assertEqual(str(e), "Invalid attribute name: unexisting")

    def test__load_attributes_from_xml(self):
        obj = self.cls()
        obj._attribute_names = ["attr"]
        xml = etree.Element("test")
        xml.attrib["attr"] = "value"
        obj._load_attributes_from_xml(xml)
        self.assertEqual(obj.attributes, {"attr": "value"})

    def test__attributes_to_xml(self):
        xml = etree.Element("test")
        obj = self.cls()
        obj._attribute_names = ["attr"]
        obj._attributes_to_xml(xml)
        self.assertEqual(xml.attrib, {})
        dic = {"attr": "value"}
        obj.attributes = dic
        obj._attributes_to_xml(xml)
        self.assertEqual(xml.attrib, dic)

    def test__load_comment_from_xml(self):
        obj = self.cls()
        xml = etree.Element("test")
        self.assertEqual(obj.comment, None)
        obj._load_comment_from_xml(xml)
        self.assertEqual(obj.comment, None)

        for i in range(5):
            if i == 2:
                elt = etree.Element("sub")
            else:
                elt = etree.Comment("comment %i" % i)
            xml.append(elt)
        obj._load_comment_from_xml(xml.getchildren()[2])
        expected = "comment 0\ncomment 1\ncomment 3\ncomment 4"
        self.assertEqual(obj.comment, expected)

        obj = self.cls()
        xml = etree.Element("test")
        for i in range(3):
            elt = etree.Element("sub")
            xml.append(elt)
        obj._load_comment_from_xml(xml.getchildren()[2])
        self.assertEqual(obj.comment, None)

        obj = self.cls()
        xml = etree.Element("test")
        for i in range(5):
            if i in [0, 2, 4]:
                elt = etree.Element("sub")
            else:
                elt = etree.Comment("comment %i" % i)
            xml.append(elt)
        obj._load_comment_from_xml(xml.getchildren()[2])
        expected = "comment 1"
        self.assertEqual(obj.comment, expected)

    def test__comment_to_xml(self):
        xml = etree.Element("test")
        obj = self.cls()
        obj._comment_to_xml(xml)
        self.assertEqual(xml.getprevious(), None)

        obj.comment = "my comment"
        obj._comment_to_xml(xml)
        elt = xml.getprevious()
        self.assertEqual(elt.getprevious(), None)
        self.assertEqual(elt.text, "my comment")

    def test__load_extra_from_xml(self):
        xml = etree.Element("test")
        xml.append(etree.Element("prev"))
        elt = etree.Element("element")
        elt.attrib["attr"] = "value"
        xml.append(elt)
        xml.append(etree.Comment("comment"))
        obj = self.cls()
        obj._attribute_names = ["attr"]
        obj._load_extra_from_xml(xml.getchildren()[1])
        self.assertEqual(obj.comment, "comment")
        self.assertEqual(obj.attributes, {"attr": "value"})

    def test_load_from_xml(self):
        xml = etree.Element("test")
        xml.append(etree.Element("prev"))
        elt = etree.Element("element")
        elt.attrib["attr"] = "value"
        xml.append(elt)
        xml.append(etree.Comment("comment"))

        sub_cls1 = type(
            "SubClsPrev",
            (ContainerElement,),
            {"tagname": "prev", "children_classes": []},
        )
        sub_cls2 = type(
            "SubClsElement",
            (ContainerElement,),
            {
                "tagname": "element",
                "children_classes": [],
                "_attribute_names": ["attr"],
            },
        )
        cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "tag", "children_classes": [sub_cls1, sub_cls2]},
        )
        obj = cls()
        obj.load_from_xml(xml)
        self.assertTrue(obj)
        self.assertFalse(obj.comment)
        self.assertFalse(obj.attributes)
        self.assertTrue(obj["prev"])
        self.assertFalse(obj["prev"].comment)
        self.assertFalse(obj["prev"].attributes)
        self.assertTrue(obj["element"])
        self.assertEqual(obj["element"].comment, "comment")
        self.assertEqual(obj["element"].attributes, {"attr": "value"})

    def test_to_xml(self):
        sub_cls = type(
            "SubClsElement",
            (ContainerElement,),
            {
                "tagname": "element",
                "children_classes": [],
                "_attribute_names": ["attr"],
            },
        )
        cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "tag", "children_classes": [sub_cls]},
        )
        obj = cls()
        obj["element"] = sub_cls()
        obj["element"].comment = "comment"
        obj["element"].attributes = {"attr": "value"}
        xml = obj.to_xml()
        self.assertEqual(xml.tag, "tag")
        self.assertEqual(xml.attrib, {})
        self.assertEqual(len(xml.getchildren()), 2)
        comment = xml.getchildren()[0]
        self.assertEqual(comment.text, "comment")
        element = xml.getchildren()[1]
        self.assertEqual(element.tag, "element")
        self.assertEqual(element.attrib, {"attr": "value"})

    def test_to_xml_sub_list(self):
        sub_cls = type(
            "Element",
            (
                InListMixin,
                ContainerElement,
            ),
            {"tagname": "sub", "children_classes": [], "_attribute_names": ["attr"]},
        )
        list_cls = type(
            "ListElement",
            (ListElement,),
            {"tagname": "element", "_children_class": sub_cls},
        )
        cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "tag", "children_classes": [list_cls]},
        )
        list_cls._parent_cls = cls
        sub_cls._parent_cls = list_cls
        obj = cls()
        lis = list_cls(obj)
        obj1 = lis.add(sub_cls.tagname)
        obj1.comment = "comment1"
        obj1.attributes = {"attr": "value"}
        obj2 = lis.add(sub_cls.tagname)
        obj2.comment = "comment2"
        xml = obj.to_xml()
        self.assertEqual(xml.tag, "tag")
        self.assertEqual(len(xml.getchildren()), 4)
        (comment1, element1, comment2, element2) = xml.getchildren()
        self.assertEqual(comment1.text, "comment1")
        self.assertEqual(element1.tag, "sub")
        self.assertEqual(element1.attrib, {"attr": "value"})
        self.assertEqual(comment2.text, "comment2")
        self.assertEqual(element2.tag, "sub")
        self.assertEqual(element2.attrib, {})

    def test___getitem__(self):
        obj = self.cls()
        obj["subtag"] = "Hello world"
        self.assertEqual(obj["subtag"], "Hello world")
        try:
            self.assertEqual(obj["unexisting"], "Hello world")
            assert 0
        except KeyError as e:
            self.assertEqual(str(e), "'unexisting'")

    def test___contains__(self):
        obj = self.cls()
        obj["subtag"] = "Hello world"
        self.assertTrue("subtag" in obj)
        self.assertFalse("unexisting" in obj)

    def test_get_or_add(self):
        obj = self.cls()
        try:
            obj.get_or_add("unexisting")
            assert 0
        except Exception as e:
            self.assertEqual(str(e), "Invalid child unexisting")
        subtag = obj.get_or_add("subtag")
        self.assertTrue(subtag)
        self.assertEqual(subtag._parent_obj, obj)
        self.assertEqual(subtag.root, obj)

        subtag1 = obj.get_or_add("subtag")
        self.assertEqual(subtag1, subtag)

    def test_walk(self):
        parent_obj = self.cls()
        obj = self.sub_cls(parent_obj)

        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj])

        parent_obj["subtag"] = None
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [])

        sub_sub_cls = type(
            "SubSubCls",
            (TextElement,),
            {
                "tagname": "subsub",
                "children_classes": [],
                "_parent_cls": self.sub_cls,
            },
        )
        self.sub_cls.children_classes = [sub_sub_cls]

        obj = self.sub_cls(parent_obj)
        subsub1 = sub_sub_cls(obj)
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj, subsub1])

    def test_findall(self):
        parent_obj = self.cls()
        obj = self.sub_cls(parent_obj)
        lis = parent_obj.findall("subtag")
        self.assertEqual(lis, [obj])

        lis = parent_obj.findall("unexisting")
        self.assertEqual(lis, [])

    def test_write(self):
        filename = "tests/test.xml"
        self.assertFalse(os.path.isfile(filename))
        try:
            obj = self.cls()
            try:
                obj.write()
                assert 0
            except Exception as e:
                self.assertEqual(str(e), "No filename given")

            obj.dtd_url = None
            try:
                obj.write(filename)
                assert 0
            except Exception as e:
                self.assertEqual(str(e), "No dtd given")

            with patch("xmltool.dtd.DTD.validate_xml", return_value=True):
                obj.write(filename, dtd_url="http://dtd.url")

            obj.write(filename, dtd_url="http://dtd.url", validate=False)
            result = open(filename, "r").read()
            expected = (
                "<?xml version='1.0' encoding='UTF-8'?>\n"
                '<!DOCTYPE tag SYSTEM "http://dtd.url">\n'
                "<tag/>\n"
            )
            self.assertEqual(result, expected)

            obj.filename = filename
            obj.write(dtd_url="http://dtd.url", validate=False)

            obj.dtd_url = "http://dtd.url"
            obj.encoding = "iso-8859-1"
            obj.write(validate=False)
            result = open(filename, "r").read()
            expected = (
                "<?xml version='1.0' encoding='iso-8859-1'?>\n"
                '<!DOCTYPE tag SYSTEM "http://dtd.url">\n'
                "<tag/>\n"
            )
            self.assertEqual(result, expected)

            transform = lambda s: s.replace("tag", "replaced-tag")
            obj.write(validate=False, transform=transform)
            result = open(filename, "r").read()
            expected = (
                "<?xml version='1.0' encoding='iso-8859-1'?>\n"
                '<!DOCTYPE replaced-tag SYSTEM "http://dtd.url">\n'
                "<replaced-tag/>\n"
            )
            self.assertEqual(result, expected)
        finally:
            if os.path.isfile(filename):
                os.remove(filename)


class TestContainerElement(BaseTest):
    def setUp(self):
        self.sub_cls = type(
            "SubCls", (ContainerElement,), {"tagname": "subtag", "children_classes": []}
        )
        self.cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "tag", "children_classes": [self.sub_cls]},
        )
        self.root_cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "root_tag", "children_classes": [self.cls]},
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls._parent_cls = self.cls


class TestTextElement(BaseTest):
    def setUp(self):
        self.sub_cls = type(
            "SubCls", (ContainerElement,), {"tagname": "subtag", "children_classes": []}
        )
        self.cls = type(
            "Cls",
            (TextElement,),
            {
                "tagname": "tag",
                "children_classes": [self.sub_cls],
                "_attribute_names": ["attr"],
            },
        )
        self.root_cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "parent_tag", "children_classes": [self.cls]},
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls._parent_cls = self.cls

    def test___repr__(self):
        self.assertTrue(repr(self.cls()))

    def test_position(self):
        obj = self.cls()
        self.assertEqual(obj.position, None)

    def test__get_creatable_class_by_tagnames(self):
        res = self.cls._get_creatable_class_by_tagnames()
        expected = {"tag": self.cls}
        self.assertEqual(res, expected)

    def test__get_creatable_subclass_by_tagnames(self):
        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {"subtag": self.sub_cls}
        self.assertEqual(res, expected)

    def test__add(self):
        obj = self.cls._create("tagname", self.root_obj, "my value")
        self.assertEqual(obj.text, "my value")
        self.assertEqual(obj._parent_obj, self.root_obj)

    def test_load_from_xml(self):
        root = etree.Element("root")
        text = etree.Element("text")
        text.text = "text"
        empty = etree.Element("empty")
        comment = etree.Comment("comment")
        root.append(comment)
        root.append(text)
        root.append(empty)
        text.attrib["attr"] = "value"
        obj = self.cls()
        obj.load_from_xml(text)
        self.assertEqual(obj.text, "text")
        self.assertEqual(obj.comment, "comment")
        self.assertEqual(obj.attributes, {"attr": "value"})

        text.text = "Hello world"
        comment1 = etree.Comment("comment inside a tag")
        text.append(comment1)

        obj = self.cls()
        obj.load_from_xml(text)
        self.assertEqual(obj.text, "Hello world")
        self.assertEqual(obj.comment, "comment\ncomment inside a tag")
        self.assertEqual(obj.attributes, {"attr": "value"})

        obj = self.cls()
        obj.load_from_xml(empty)
        self.assertEqual(obj.text, "")
        self.assertEqual(obj.comment, None)

    def test_to_xml(self):
        obj = self.cls()
        obj.text = "text"
        obj.comment = "comment"
        obj.attributes = {"attr": "value"}
        xml = obj.to_xml()
        self.assertTrue(xml.tag, "tag")
        self.assertTrue(xml.text, "text")
        self.assertTrue(xml.attrib, {"attr": "value"})

        obj = self.cls()
        obj.text = etree.CDATA("<div>HTML</div>")
        xml = obj.to_xml()
        self.assertEqual(etree.tostring(xml), b"<tag><![CDATA[<div>HTML</div>]]></tag>")

        obj = self.cls()
        obj.text = "<div>HTML</div>"
        xml = obj.to_xml()
        self.assertEqual(etree.tostring(xml), b"<tag>&lt;div&gt;HTML&lt;/div&gt;</tag>")

        obj = self.cls()
        obj._is_empty = True
        obj.text = "text"
        try:
            xml = obj.to_xml()
            assert 0
        except Exception as e:
            self.assertEqual(str(e), "It's forbidden to have a value to an EMPTY tag")
        obj.text = None
        xml = obj.to_xml()
        self.assertEqual(xml.tag, "tag")
        self.assertEqual(xml.text, None)
        self.assertEqual(xml.attrib, {})


class TestListElement(BaseTest):
    def setUp(self):
        self.sub_cls = type(
            "SubCls",
            (
                InListMixin,
                ContainerElement,
            ),
            {"tagname": "subtag", "_attribute_names": ["attr"], "children_classes": []},
        )
        self.cls = type(
            "Cls", (ListElement,), {"tagname": "tag", "_children_class": self.sub_cls}
        )
        self.root_cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "parent_tag", "children_classes": [self.cls]},
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls._parent_cls = self.cls

    def test_position(self):
        self.assertEqual(self.root_obj.position, None)

        obj = self.root_cls()
        sub1 = obj.add("subtag")
        sub2 = obj.add("subtag")
        self.assertEqual(sub1.position, 0)
        self.assertEqual(sub2.position, 1)

    def test__get_creatable_class_by_tagnames(self):
        res = self.cls._get_creatable_class_by_tagnames()
        expected = {
            "subtag": self.sub_cls,
            "tag": self.cls,
        }
        self.assertEqual(res, expected)

    def test__get_creatable_subclass_by_tagnames(self):
        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {
            "subtag": self.sub_cls,
        }
        self.assertEqual(res, expected)

    def test__get_value_from_parent(self):
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)
        list_obj = self.cls(self.root_obj)
        obj = list_obj.add(self.sub_cls.tagname)
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), [obj])

    def test_children(self):
        obj = self.root_cls()
        sub1 = obj.add("subtag")
        sub2 = obj.add("subtag")
        children = list(obj.children)
        self.assertEqual(children, [sub1, sub2])

    def test_is_addable(self):
        obj = self.root_obj.add(self.cls.tagname)
        # Can't add same object as child
        self.assertEqual(obj.is_addable(self.cls.tagname), False)
        self.assertEqual(obj.is_addable("subtag"), True)
        self.assertEqual(obj.is_addable("test"), False)
        # Addable even we already have element defined
        obj.add("subtag")
        self.assertEqual(obj.is_addable("subtag"), True)

    def test__add(self):
        try:
            obj1 = self.cls._create("tag", self.root_obj, "my value")
            assert False
        except Exception as e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj1 = self.cls._create("tag", self.root_obj)
        self.assertTrue(obj1.tagname, "tag")
        self.assertEqual(obj1._parent_obj, self.root_obj)
        self.assertEqual(obj1.root, self.root_obj)
        self.assertTrue(isinstance(obj1, ListElement))
        self.assertEqual(self.root_obj["tag"].root, self.root_obj)

        # Since the object already exists it just return it!
        obj2 = self.cls._create("tag", self.root_obj)
        self.assertEqual(obj1, obj2)

        try:
            self.cls._create("unexisting", self.root_obj)
            assert False
        except Exception as e:
            self.assertEqual(str(e), "Unsupported tagname unexisting")

    def test_add_list_of_list(self):
        dtd_str = """
        <!ELEMENT texts (text+)>
        <!ELEMENT text (subtext+)>
        <!ELEMENT subtext (#PCDATA)>
        """
        dic = dtd.DTD(StringIO(dtd_str)).parse()
        obj = dic["texts"]()
        text = obj.add("text")
        subtext = text.add("subtext", "value")
        self.assertEqual(subtext.text, "value")

        # We can add another text
        obj.add("text")

        # List already exists, it just returns it
        list_obj = obj.add(text._parent_cls.tagname)
        self.assertEqual(text._parent_obj, list_obj)

        l = list_obj.add(text._parent_cls.tagname)
        self.assertEqual(list_obj, l)

    def test_delete(self):
        list_obj = self.root_obj.add(self.cls.tagname)
        obj = list_obj.add("subtag")
        self.assertEqual(len(list_obj), 1)

        obj.delete()
        self.assertEqual(len(list_obj), 0)

        self.assertEqual(self.root_obj["tag"], list_obj)
        self.assertEqual(self.root_obj["subtag"], list_obj)
        list_obj.delete()
        self.assertEqual(self.root_obj.get("tag"), None)
        self.assertEqual(self.root_obj.get("subtag"), None)

    def test_to_xml(self):
        obj = self.root_cls().add(self.cls.tagname)
        lis = obj.to_xml()
        self.assertEqual(lis, [])

        subobj = self.sub_cls()
        subobj.comment = "comment"
        subobj.attributes = {"attr": "value"}

        obj.append(subobj)
        lis = obj.to_xml()
        self.assertEqual(len(lis), 2)
        self.assertEqual(lis[0].text, "comment")
        self.assertEqual(lis[1].tag, "subtag")

        obj = self.root_cls().add(self.cls.tagname)
        obj._required = True
        lis = obj.to_xml()
        # Empty required with only one element, xml is created!
        self.assertEqual(len(lis), 1)
        self.assertEqual(lis[0].tag, "subtag")

    def test_walk_list(self):
        sub_sub_cls = type(
            "SubSubCls",
            (TextElement,),
            {"tagname": "subsubtag", "children_classes": []},
        )
        self.sub_cls.children_classes = [sub_sub_cls]
        obj = self.cls(self.root_obj)
        self.root_obj["subtag"] = obj
        sub1 = self.sub_cls()
        sub2 = self.sub_cls()
        subsub1 = sub_sub_cls()
        sub1["subsubtag"] = subsub1
        obj.append(sub1)
        obj.append(sub2)

        lis = [e for e in self.root_obj.walk()]
        self.assertEqual(lis, [sub1, subsub1, sub2])

    def test_get_or_add(self):
        obj = self.cls(self.root_obj)
        try:
            obj.get_or_add("unexisting")
            assert False
        except Exception as e:
            self.assertEqual(str(e), "Parameter index is required")

        subobj = obj.get_or_add("subtag", index=1)
        self.assertEqual(len(obj), 2)

        subobj1 = obj.get_or_add("subtag", index=1)
        self.assertEqual(subobj, subobj1)

        obj = self.cls(self.root_obj)
        subobj = obj.get_or_add("subtag", index=0)
        self.assertEqual(len(obj), 1)

        subobj1 = obj.get_or_add("subtag", index=0)
        self.assertEqual(subobj, subobj1)


class TestChoiceListElement(BaseTest):
    def setUp(self):
        self.sub_cls1 = type(
            "SubCls1",
            (
                InListMixin,
                ContainerElement,
            ),
            {
                "tagname": "subtag1",
                "_attribute_names": ["attr"],
                "children_classes": [],
            },
        )
        self.sub_cls2 = type(
            "SubCls2",
            (
                InListMixin,
                ContainerElement,
            ),
            {
                "tagname": "subtag2",
                "_attribute_names": ["attr"],
                "children_classes": [],
            },
        )
        self.cls = type(
            "Cls",
            (ChoiceListElement,),
            {"tagname": "tag", "_choice_classes": [self.sub_cls1, self.sub_cls2]},
        )
        self.root_cls = type(
            "Cls",
            (ContainerElement,),
            {"tagname": "parent_tag", "children_classes": [self.cls]},
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls1._parent_cls = self.cls
        self.sub_cls2._parent_cls = self.cls

    def test_children(self):
        obj = self.root_cls()
        children = list(obj.children)
        self.assertEqual(children, [])
        sub1 = obj.add("subtag1")
        sub2 = obj.add("subtag2")
        children = list(obj.children)
        self.assertEqual(children, [sub1, sub2])

    def test_delete(self):
        root_obj = self.root_cls()
        list_obj = self.cls(root_obj)
        obj = self.sub_cls1(list_obj, parent=root_obj)
        list_obj.append(obj)

        self.assertEqual(len(list_obj), 1)
        self.assertEqual(root_obj["tag"], list_obj)

        obj.delete()
        self.assertEqual(len(list_obj), 0)
        self.assertEqual(root_obj["tag"], list_obj)

        list_obj.delete()
        self.assertEqual(root_obj.get("tag"), None)

    def test__get_value_from_parent_multiple(self):
        root_obj = self.root_cls()
        list_obj = self.cls(root_obj)
        obj = self.sub_cls1(list_obj, parent=root_obj)
        list_obj.append(obj)
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)
        self.root_obj["subtag"] = list_obj
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)
        self.root_obj["tag"] = list_obj
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), [obj])

    def test_to_xml(self):
        obj = self.root_cls().add(self.cls.tagname)
        obj._required = True
        lis = obj.to_xml()
        self.assertEqual(lis, [])

    def test_walk(self):
        root_obj = self.root_cls()
        parent_obj = self.cls()
        obj1 = self.sub_cls1(parent_obj=parent_obj, parent=root_obj)
        obj2 = self.sub_cls2(parent_obj=parent_obj, parent=root_obj)

        parent_obj.extend([obj1, obj2])
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj1, obj2])

        sub_sub_cls = type(
            "SubSubCls", (TextElement,), {"tagname": "subsub", "children_classes": []}
        )
        self.sub_cls1.children_classes = [sub_sub_cls]
        subsub1 = sub_sub_cls()
        obj1["subsub"] = subsub1
        lis = [e for e in parent_obj.walk()]
        self.assertEqual(lis, [obj1, subsub1, obj2])


class TestChoiceElement(BaseTest):
    def setUp(self):
        self.sub_cls1 = type(
            "SubCls",
            (
                InChoiceMixin,
                ContainerElement,
            ),
            {"tagname": "subtag1", "children_classes": []},
        )
        self.sub_cls2 = type(
            "SubCls",
            (
                InChoiceMixin,
                ContainerElement,
            ),
            {"tagname": "subtag2", "children_classes": []},
        )
        self.cls = type(
            "Cls",
            (ChoiceElement,),
            {
                "tagname": "tag",
                "children_classes": [],
                "_choice_classes": [self.sub_cls1, self.sub_cls2],
            },
        )
        self.root_cls = type(
            "ParentCls",
            (ContainerElement,),
            {"tagname": "root_tag", "children_classes": [self.cls]},
        )
        self.root_obj = self.root_cls()
        self.cls._parent_cls = self.root_cls
        self.sub_cls1._parent_cls = self.cls
        self.sub_cls2._parent_cls = self.cls

    def test_position(self):
        self.assertEqual(self.root_obj.position, None)
        obj1 = self.sub_cls1()
        obj2 = self.sub_cls2()

        self.assertEqual(obj1.position, None)
        self.assertEqual(obj2.position, None)

    def test__get_creatable_class_by_tagnames(self):
        res = self.cls._get_creatable_class_by_tagnames()
        expected = {
            "subtag1": self.sub_cls1,
            "subtag2": self.sub_cls2,
            "tag": self.cls,
        }
        self.assertEqual(res, expected)

    def test__get_creatable_subclass_by_tagnames(self):
        res = self.cls._get_creatable_subclass_by_tagnames()
        expected = {
            "subtag1": self.sub_cls1,
            "subtag2": self.sub_cls2,
        }
        self.assertEqual(res, expected)

    def test__get_value_from_parent(self):
        obj1 = self.sub_cls1()
        obj2 = self.sub_cls2()
        self.assertTrue(obj1 != obj2)
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), None)
        obj1 = self.root_obj.add("subtag1")
        self.assertEqual(self.cls._get_value_from_parent(self.root_obj), obj1)

    def test__get_sub_value(self):
        obj = self.sub_cls1()
        result = self.cls._get_sub_value(self.root_obj)
        self.assertFalse(result)
        self.cls._required = True
        result = self.cls._get_sub_value(self.root_obj)
        self.assertTrue(result)
        # The created object is a ChoiceElement
        self.assertTrue(isinstance(result, self.cls))
        obj = self.root_obj.add("subtag1")
        self.assertEqual(self.cls._get_sub_value(self.root_obj), obj)

    def test_children(self):
        obj = self.root_cls()
        children = list(obj.children)
        self.assertEqual(children, [])
        sub1 = obj.add("subtag1")
        children = list(obj.children)
        self.assertEqual(children, [sub1])

    def test_is_addable(self):
        obj = self.cls()
        self.assertEqual(obj.is_addable("test"), False)

    def test_add(self):
        root_cls = type(
            "ParentCls",
            (ContainerElement,),
            {"tagname": "parent", "children_classes": [self.cls]},
        )
        root_obj = root_cls()
        obj = self.cls(root_obj)

        try:
            obj.add("test")
        except Exception as e:
            self.assertEqual(str(e), "Invalid child test")

        obj1 = obj.add("subtag1")
        self.assertEqual(obj1._parent_obj, obj)
        self.assertEqual(obj1.parent, root_obj)
        self.assertEqual(root_obj["subtag1"], obj1)
        self.assertEqual(root_obj["tag"], obj)

        root_obj = root_cls()
        choice_obj = root_obj.add("tag")
        choice_obj.add("subtag1")

        choice_obj1 = root_obj.add("tag")
        # It's the same object when we add we just get it if defined
        self.assertEqual(choice_obj, choice_obj1)

        try:
            choice_obj.add("subtag1")
            assert False
        except Exception as e:
            self.assertEqual(str(e), "subtag1 is already defined")

        try:
            choice_obj.add("subtag2")
            assert False
        except Exception as e:
            self.assertEqual(str(e), "subtag1 is defined so you can't add subtag2")

        self.cls._choice_classes = [
            type(
                "Cls",
                (
                    InChoiceMixin,
                    TextElement,
                ),
                {"tagname": "subtag", "children_classes": [], "_parent_cls": self.cls},
            )
        ]

        root_obj = root_cls()
        choice_obj2 = root_obj.add("tag")
        obj2 = choice_obj2.add("subtag", "my value")
        self.assertEqual(obj2.text, "my value")
        self.assertEqual(obj2._parent_obj, choice_obj2)
        self.assertEqual(obj2.parent, root_obj)

    def test__add(self):
        try:
            obj1 = self.cls._create("tag", self.root_obj, "my value")
            assert False
        except Exception as e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        obj1 = self.cls._create("tag", self.root_obj)
        self.assertEqual(obj1.tagname, "tag")
        self.assertEqual(obj1._parent_obj, self.root_obj)
        self.assertTrue(isinstance(obj1, ChoiceElement))
        self.assertEqual(self.root_obj["tag"], obj1)

    def test_delete(self):
        obj = self.cls(self.root_obj)
        obj1 = obj.add("subtag1")
        self.assertEqual(self.root_obj[self.cls.tagname], obj)
        self.assertEqual(self.root_obj.get(self.sub_cls1.tagname), obj1)
        self.assertEqual(obj._value, obj1)

        obj1.delete()
        self.assertEqual(self.root_obj.get(self.cls.tagname), None)
        self.assertEqual(self.root_obj.get(self.sub_cls1.tagname), None)

        obj = self.cls(self.root_obj)
        obj1 = obj.add("subtag1")
        self.assertEqual(self.root_obj[self.cls.tagname], obj)
        self.assertEqual(self.root_obj.get(self.sub_cls1.tagname), obj1)
        self.assertEqual(obj._value, obj1)

        obj.delete()
        self.assertFalse(self.cls.tagname in self.root_obj)
        self.assertFalse("subtag1" in self.root_obj)


class TestFunctions(BaseTest):
    def test_update_eol(self):
        res = update_eol("Hello\r\n")
        self.assertEqual(res, "Hello\n")

        res = update_eol("Hello\n")
        self.assertEqual(res, "Hello\n")

        elements.EOL = "\r\n"
        res = update_eol("Hello\r\n")
        self.assertEqual(res, "Hello\r\n")

        res = update_eol("Hello\n")
        self.assertEqual(res, "Hello\r\n")

        res = update_eol("Hello\r")
        self.assertEqual(res, "Hello\r\n")
