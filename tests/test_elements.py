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

    def test_contains(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        self.assertFalse('unexisting' in obj)
        self.assertTrue('ISBN' in obj)

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

        try:
            book.create('unexisting')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), 'Unexisting tagname unexisting')

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

        comment.add('comment 1')
        comment.add('comment 2')
        comment.add('comment 3', 1)
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
    <comment>comment 3</comment>
    <comment>comment 2</comment>
  </comments>
</Book>
'''
        self.assertEqual(xml_str, expected)

    def test_create_exercise(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        exercise = gen.create_obj('Exercise')
        test_list = exercise.create('test')
        test1 = test_list.add()
        test1.create('question', 'my question')
        qcm_list = test1.create('qcm')
        qcm1 = qcm_list.add()
        choice_list = qcm1.create('choice')
        choice_list.add('choice 1')
        choice_list.add('choice 2')
        expected = '''<Exercise>
  <number/>
  <test>
    <question>my question</question>
    <qcm>
      <choice>choice 1</choice>
      <choice>choice 2</choice>
    </qcm>
  </test>
</Exercise>
'''
        self.assertEqual(exercise.to_xml(), expected)

    def test_create_exercise_conditional(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        exercise = gen.create_obj('Exercise')
        test_list = exercise.create('test')
        test1 = test_list.add()
        test1.create('question', 'my question')
        qcm_list = test1.create('qcm')

        try:
            mqm_list = test1.create('mqm')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), "You can't add a mqm since it already contains a qcm")

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
            transform_func = lambda  txt: txt.replace('comments',
                                                      'comments-updated')
            obj.write(filename, validate_xml=False, transform=transform_func)
            new_content = open(filename, 'r').read()
            self.assertTrue('comments-updated' in new_content)
        finally:
            utils.validate_xml = old_validate
            if os.path.isfile(filename):
                os.remove(filename)


class TestElementList(TestCase):

    def test_add(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        cls = gen.dtd_classes['Exercise']
        exercise = cls()
        test = exercise.create('test')

        test1 = test.add()
        test1.create('question', 'question 1')
        qcms = test1.create('qcm')
        qcm1 = qcms.add()
        choices1 = qcm1.create('choice')
        choices1.add(text='choice1')
        choices1.add(text='choice2')
        choices1.add(text='choice3', position=1)
        qcm2 = qcms.add()
        choices2 = qcm2.create('choice')
        choices2.add(text='choice4')
        choices2.add(text='choice5')
        choices2.add(text='choice6', position=1)

        test2 = test.add()
        test2.create('question', 'question 2')
        mqms = test2.create('mqm')
        mqm1 = mqms.add()
        mqm1.attrs['idmqm'] = '1'
        choices1 = mqm1.create('choice')
        choices1.add(text='choice1')

        expected = '''<?xml version='1.0' encoding='UTF-8'?>
<Exercise>
  <number/>
  <test>
    <question>question 1</question>
    <qcm>
      <choice>choice1</choice>
      <choice>choice3</choice>
      <choice>choice2</choice>
    </qcm>
    <qcm>
      <choice>choice4</choice>
      <choice>choice6</choice>
      <choice>choice5</choice>
    </qcm>
  </test>
  <test>
    <question>question 2</question>
    <mqm idmqm="1">
      <choice>choice1</choice>
    </mqm>
  </test>
</Exercise>
'''
        xml = gen.obj_to_xml(exercise)
        xml_str = etree.tostring(
            xml.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8')
        self.assertEqual(xml_str, expected)

    def test_add_on_existing_obj(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)

        mqm3 = obj.test[0].mqm.add(position=0)
        choices = mqm3.create('choice')
        choices.add(text='choice 3').attrs['idchoice'] = '11'

        choices1 = obj.test[0].mqm[1].choice
        choices1.add(text='choice 4', position=0)

        expected = '''<?xml version='1.0' encoding='UTF-8'?>
<Exercise idexercise="1">
  <number>1</number>
  <test idtest="1" name="color">
    <question idquestion="1">What is your favorite color?</question>
    <mqm>
      <choice idchoice="11">choice 3</choice>
    </mqm>
    <mqm idmqm="1">
      <choice>choice 4</choice>
      <choice idchoice="1">blue</choice>
      <choice idchoice="2">red</choice>
      <choice idchoice="3">black</choice>
    </mqm>
    <mqm idmqm="2">
      <choice idchoice="4">magenta</choice>
      <choice idchoice="5">orange</choice>
      <choice idchoice="6">yellow</choice>
    </mqm>
  </test>
  <test idtest="2">
    <question idquestion="2">Have you got a pet?</question>
    <qcm idqcm="1">
      <choice idchoice="7">yes</choice>
      <choice idchoice="8">no</choice>
    </qcm>
    <qcm idqcm="2">
      <choice idchoice="9">yes</choice>
      <choice idchoice="10">no</choice>
    </qcm>
    <comments idcomments="1">
      <comment idcomment="1">My comment 1</comment>
      <comment idcomment="2">My comment 2</comment>
    </comments>
  </test>
</Exercise>
'''
        xml = gen.obj_to_xml(obj)
        xml_str = etree.tostring(
            xml.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8')
        self.assertEqual(xml_str, expected)

    def test_add_text_not_allowed(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        cls = gen.dtd_classes['Exercise']
        exercise = cls()
        test = exercise.create('test')
        try:
            test.add(text='text')
            assert 0
        except Exception, e:
            self.assertEqual(str(e),"Can't set value to non TextElement")
