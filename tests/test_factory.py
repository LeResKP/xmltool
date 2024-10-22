#!/usr/bin/env python

from xmltool.testbase import BaseTest
from lxml import etree
from xmltool import factory


class TestFactory(BaseTest):
    def test_create(self):
        obj = factory.create("Exercise", dtd_url="tests/exercise.dtd")
        self.assertEqual(obj.tagname, "Exercise")

    def test_load(self):
        obj = factory.load("tests/exercise.xml")
        self.assertEqual(obj.tagname, "Exercise")
        comment = obj["test"][1]["comments"]["comment"][1]
        self.assertEqual(comment.text, "<div>My comment 2</div>")
        self.assertEqual(
            etree.tostring(comment.to_xml()),
            b"<comment><![CDATA[<div>My comment 2</div>]]></comment>",
        )
        try:
            obj = factory.load("tests/exercise-notvalid.xml")
            assert 0
        except etree.DocumentInvalid as e:
            self.assertEqual(
                str(e),
                "Element comments content does not follow the DTD, expecting "
                "(comment)+, got (), line 17",
            )
        obj = factory.load("tests/exercise-notvalid.xml", validate=False)
        self.assertEqual(obj.tagname, "Exercise")

    def test_load_string(self):
        xml_str = open("tests/exercise.xml", "r").read()
        xml_str = xml_str.replace("exercise.dtd", "tests/exercise.dtd")
        obj = factory.load_string(xml_str)
        self.assertEqual(obj.tagname, "Exercise")
        try:
            xml_str = open("tests/exercise-notvalid.xml", "r").read()
            xml_str = xml_str.replace("exercise.dtd", "tests/exercise.dtd")
            obj = factory.load_string(xml_str)
            assert 0
        except etree.DocumentInvalid as e:
            self.assertEqual(
                str(e),
                "Element comments content does not follow the DTD, expecting "
                "(comment)+, got (), line 17",
            )

        xml_str = open("tests/exercise-notvalid.xml", "r").read()
        xml_str = xml_str.replace("exercise.dtd", "tests/exercise.dtd")
        obj = factory.load_string(xml_str, validate=False)
        self.assertEqual(obj.tagname, "Exercise")

    def test_load_string_unicode(self):
        xml_str = open("tests/exercise-notvalid.xml", "r").read()
        xml_str = xml_str.replace("exercise.dtd", "tests/exercise.dtd")
        obj = factory.load_string(xml_str, validate=False)
        self.assertEqual(obj.tagname, "Exercise")
