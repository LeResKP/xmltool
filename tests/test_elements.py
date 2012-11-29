#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import os.path
from xmltools import dtd_parser, utils, factory
from test_dtd_parser import BOOK_XML, BOOK_DTD, EXERCISE_XML_2, EXERCISE_DTD_2


class test_Element(TestCase):

    def test__get_element(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        result = obj._get_element('unexisting')
        self.assertEqual(result, None)
        result = obj._get_element('ISBN')
        self.assertEqual(result.name, 'ISBN')

    def test__get_element_conditional(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)
        result = obj.test[0]._get_element('qcm')
        self.assertEqual(result.name, '(qcm|mqm)')

    def test_getitem(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        self.assertTrue(obj['ISBN'].value, 'JFJEFBQN')
        self.assertTrue(obj['ISBN'].value, obj.ISBN)
        self.assertTrue(obj['book-title'].value, 'How to use XML tools?')
        self.assertTrue(obj['book-resume'].value, 'This is the resume of the book')
        self.assertTrue(obj['comments']['comment'][0].value, 'First comment')
        self.assertTrue(obj['comments']['comment'][1].value, 'Second comment')

    def test_setitem(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        obj['comments'] = None
        xml = gen.obj_to_xml(obj)
        xml_str = etree.tostring(
            xml.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8')
        expected = '''<?xml version='1.0' encoding='UTF-8'?>
<Book>
  <ISBN>JFJEFBQN</ISBN>
  <book-title>How to use XML tools?</book-title>
  <book-resume>This is the resume of the book</book-resume>
  <comments/>
</Book>
'''
        self.assertEqual(xml_str, expected)

    def test_setitem_good_type(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        o = gen.dtd_classes['ISBN']()
        o.value = 'NEW_ISBN'
        obj['ISBN'] = o

    def test_setitem_wrong_list(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        try:
            obj['comments']['comment'] = 'my comment'
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Wrong type for comment')

    def test_setitem_list(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        # TODO: we should check the type in the list
        obj['comments']['comment'] = ['my comment']


    def test_setitem_wrong_type(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        try:
            obj['ISBN'] = 'isbn'
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Wrong type for ISBN')

    def test_setitem_invalid_child(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        try:
            obj['invalid'] = 'invalid value'
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Invalid child invalid')

    def test_setattr_wrong_type(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        try:
            obj.ISBN = 'isbn'
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Wrong type for ISBN')

    def test_setattr_invalid_child(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        try:
            obj.invalid = 'invalid value'
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Invalid child invalid')

    def test_create(self):
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        cls = gen.dtd_classes['Book']
        book = cls()
        book.create('ISBN', 'ISBN_VALUE')
        xml = gen.obj_to_xml(book)
        xml_str = etree.tostring(
            xml.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8')
        expected = '''<?xml version='1.0' encoding='UTF-8'?>
<Book>
  <ISBN>ISBN_VALUE</ISBN>
  <book-title/>
  <book-resume/>
  <comments/>
</Book>
'''
        self.assertEqual(xml_str, expected)
        try:
            book.create('ISBN', 'ISBN_VALUE')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'ISBN already defined')

        book.create('book-title', 'The title of the book')
        book.create('book-resume', 'The resume of the book')

        try:
            book.create('comments', 'The resume of the book')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), "Can't set value to non TextElement")

        comments = book.create('comments')
        comment = comments.create('comment')
        self.assertEqual(comment, [])

        # TODO: Add custom class to manage the list to create easily new
        # element
        cls = gen.dtd_classes['comment']
        comment += [cls('comment 1')]
        comment += [cls('comment 2')]

        xml = gen.obj_to_xml(book)
        xml_str = etree.tostring(
            xml.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8')
        expected = '''<?xml version='1.0' encoding='UTF-8'?>
<Book>
  <ISBN>ISBN_VALUE</ISBN>
  <book-title>The title of the book</book-title>
  <book-resume>The resume of the book</book-resume>
  <comments>
    <comment>comment 1</comment>
    <comment>comment 2</comment>
  </comments>
</Book>
'''
        self.assertEqual(xml_str, expected)

    def test_write(self):
        def FakeValidate(*args, **kwargs):
            raise etree.DocumentInvalid('Error')

        filename = 'tests/test.xml'
        self.assertFalse(os.path.isfile(filename))
        old_validate = utils.validate_xml
        try:
            obj = factory.load('tests/exercise.xml')
            obj.write(filename)
            new_content = open(filename, 'r').read()
            old_content = open('tests/exercise.xml', 'r').read()
            self.assertEqual(new_content, old_content)

            utils.validate_xml = FakeValidate
            try:
                obj.write(filename)
                assert 0
            except etree.DocumentInvalid:
                pass
            obj.write(filename, validate_xml=False)
        finally:
            utils.validate_xml = old_validate
            if os.path.isfile(filename):
                os.remove(filename)
