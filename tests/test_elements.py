#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import os.path
from xmltools import dtd_parser, utils, factory
from xmltools.elements import TextElement, generate_id
from test_dtd_parser import (
    BOOK_XML, BOOK_DTD, EXERCISE_XML_2, EXERCISE_DTD_2, EXERCISE_DTD
)
import simplejson as json


class TestFunction(TestCase):

    def test_generate_id(self):
        class Comment(TextElement):
            tagname = 'comment'
        result = generate_id(Comment.tagname)
        expected = 'comment'
        self.assertEqual(result, expected)

        result = generate_id(Comment.tagname, prefix_id='prefix')
        expected = 'prefix:comment'
        self.assertEqual(result, expected)

        result = generate_id(Comment.tagname, prefix_id='prefix', index=10)
        expected = 'prefix:comment:10'
        self.assertEqual(result, expected)


class TestTextElement(TestCase):

    def test_init(self):
        elt = TextElement()
        self.assertEqual(elt.value, None)

        elt = TextElement(value='my value')
        self.assertEqual(elt.value, 'my value')

    def test_to_jstree_dict(self):
        dtd_str = '''
        <!ELEMENT prefix (prefix2*)>
        <!ELEMENT prefix2 (comment)>
        <!ELEMENT comment (#PCDATA)>
        '''
        gen = dtd_parser.Generator(dtd_str=dtd_str)

        class Comment(TextElement):
            tagname = 'comment'
            _generator = gen

        elt = Comment(value='my comment')
        self.assertEqual(elt.value, 'my comment')

        expected = {
            'data': 'comment',
            'attr': {
                'id': 'tree_comment',
                'class': 'tree_comment'},
            'metadata': {
                'id': 'comment',
                'replace_id': 'comment'
            }}
        result = elt.to_jstree_dict()
        self.assertEqual(result, expected)

        expected = {
            'data': 'comment (%s)' % elt.value,
            'attr': {
                'id': 'tree_comment',
                'class': 'tree_comment'},
            'metadata': {
                'id': 'comment',
                'replace_id': 'comment'
            }}
        result = elt.to_jstree_dict(value=elt.value)
        self.assertEqual(result, expected)

        expected = {
            'data': 'comment (%s)' % elt.value,
            'attr': {
                'id': 'tree_prefix:prefix2:1:comment',
                'class': 'tree_prefix:prefix2:1:comment'},
            'metadata': {
                'id': 'prefix:prefix2:1:comment',
                'replace_id': 'prefix:prefix2:1:comment'
            }}
        result = elt.to_jstree_dict(
            value=elt.value, prefix_id='prefix:prefix2:1')
        self.assertEqual(result, expected)

        expected = {
            'data': 'comment (%s)' % elt.value,
            'attr': {
                'id': 'tree_prefix:prefix2:1:comment:4',
                'class': 'tree_prefix:prefix2:1:comment'},
            'metadata': {
                'id': 'prefix:prefix2:1:comment:4',
                'replace_id': 'prefix:prefix2:1:comment:4'
            }}
        result = elt.to_jstree_dict(
            value=elt.value,
            prefix_id='prefix:prefix2:1',
            number=4)
        self.assertEqual(result, expected)

        dtd_str = '''
        <!ELEMENT prefix (prefix2*)>
        <!ELEMENT prefix2 ((positive-comment|negative-comment)*)>
        <!ELEMENT positive-comment (#PCDATA)>
        <!ELEMENT negative-comment (#PCDATA)>
        '''
        gen = dtd_parser.Generator(dtd_str=dtd_str)
        Comment._generator = gen
        expected = {
            'data': 'comment (%s)' % elt.value,
            'attr': {
                'id': 'tree_prefix:prefix2:1:_positive-comment_negative-comment:4:comment',
                'class': 'tree_prefix:prefix2:1:_positive-comment_negative-comment:4'},
            'metadata': {
                'id': 'prefix:prefix2:1:_positive-comment_negative-comment:4:comment',
                'replace_id': 'prefix:prefix2:1:_positive-comment_negative-comment'
            }}
        result = elt.to_jstree_dict(
            value=elt.value,
            prefix_id='prefix:prefix2:1:_positive-comment_negative-comment:4',
            )
        self.assertEqual(result, expected)

    def test_to_jstree_json(self):
        class Comment(TextElement):
            tagname = 'comment'
        elt = Comment(value='my comment')

        dict_result = elt.to_jstree_dict()
        json_result = elt.to_jstree_json()
        self.assertEqual(json_result, json.dumps(dict_result))


class TestElement(TestCase):

    def test_init(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)
        self.assertEqual(obj.child_tagnames, ['number', 'test'])
        self.assertEqual(obj.test[0].child_tagnames,
                         ['question', '_qcm_mqm', 'comments'])

    def test__get_element(self):
        root = etree.fromstring(BOOK_XML)
        gen = dtd_parser.Generator(dtd_str=BOOK_DTD)
        obj = gen.generate_obj(root)
        result = obj._get_element('unexisting')
        self.assertEqual(result, None)
        result = obj._get_element('ISBN')
        self.assertEqual(result.tagname, 'ISBN')

    def test__get_element_conditional(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)
        result = obj.test[0]._get_element('qcm')
        self.assertEqual(result, None)
        result = obj.test[0]._get_element('_qcm_mqm')
        self.assertEqual(result.tagname, '_qcm_mqm')

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
        o = gen.create_obj('ISBN')
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
        book = gen.create_obj('Book')
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
            self.assertEqual(str(e), 'Invalid child unexisting')

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
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD)
        exercise = gen.create_obj('Exercise')
        exercise.create('question', 'my question')
        test = exercise.create('test')
        qcm1 = test.create('qcm')
        choice_list = qcm1.create('choice')
        choice_list.add('choice 1')
        choice_list.add('choice 2')
        expected = '''<Exercise>
  <question>my question</question>
  <test>
    <qcm>
      <choice>choice 1</choice>
      <choice>choice 2</choice>
    </qcm>
  </test>
</Exercise>
'''
        self.assertEqual(exercise.to_xml(), expected)

    def test_create_exercise_conditional(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD)
        exercise = gen.create_obj('Exercise')
        exercise.create('question', 'my question')
        test = exercise.create('test')
        qcm = test.create('qcm')

        try:
            mqm = test.create('mqm')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), "You can't add a mqm since it already contains a qcm")

    def test_to_jstree_dict(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        expected = {
            'children': [
                {'data': 'comment',
                 'attr': {
                     'id': 'tree_Exercise:comments:comment:1',
                     'class': 'tree_Exercise:comments:comment'},
                 'metadata': {
                     'id': 'Exercise:comments:comment:1',
                     'replace_id': 'Exercise:comments:comment:1'
                 }}],
            'data': 'comments',
            'attr': {
                'id': 'tree_Exercise:comments',
                'class': 'tree_Exercise:comments'},
            'metadata': {
                'id': 'Exercise:comments',
                'replace_id': 'Exercise:comments'
            }}
        result = gen.dtd_classes['comments'].to_jstree_dict('Exercise')
        self.assertEqual(result, expected)

        expected = {
            'data': 'question (Exercise)',
            'attr': {
                'id': 'tree_question',
                'class': 'tree_question'},
            'metadata': {
                'id': 'question',
                'replace_id': 'question'
            }}
        result = gen.dtd_classes['question'].to_jstree_dict('Exercise')
        self.assertEqual(result, expected)

        expected = {
            'children': [
                {'data': 'question',
                 'attr': {'id': 'tree_Exercise:test:question',
                          'class': 'tree_Exercise:test:question'},
                 'metadata': {
                     'id': 'Exercise:test:question',
                     'replace_id': 'Exercise:test:question'
                 }}],
            'data': 'test',
            'attr': {
                'id': 'tree_Exercise:test',
                'class': 'tree_Exercise:test'},
            'metadata': {
                'id': 'Exercise:test',
                'replace_id': 'Exercise:test'
            }}
        result = gen.dtd_classes['test'].to_jstree_dict('Exercise')
        self.assertEqual(result, expected)

        expected = {
            'children': [
                {'data': 'choice',
                 'attr': {
                     'id': 'tree_Exercise:qcm:choice:1',
                     'class': 'tree_Exercise:qcm:choice'},
                 'metadata': {
                     'id': 'Exercise:qcm:choice:1',
                     'replace_id': 'Exercise:qcm:choice:1'
                 }}],
            'data': 'qcm',
            'attr': {
                'id': 'tree_Exercise:qcm',
                'class': 'tree_Exercise:qcm'},
            'metadata': {
                'id': 'Exercise:qcm',
                'replace_id': 'Exercise:qcm'
            }}
        result = gen.dtd_classes['qcm'].to_jstree_dict('Exercise')
        self.assertEqual(result, expected)

        expected = {
            'children': [
                {'data': 'choice',
                 'attr': {
                     'id': 'tree_Exercise:qcm:0:choice:1',
                     'class': 'tree_Exercise:qcm:0:choice'},
                 'metadata': {
                     'id': 'Exercise:qcm:0:choice:1',
                     'replace_id': 'Exercise:qcm:0:choice:1'
                 }}],
            'data': 'qcm',
            'attr': {
                'id': 'tree_Exercise:qcm:0',
                'class': 'tree_Exercise:qcm'},
            'metadata': {
                'id': 'Exercise:qcm:0',
                'replace_id': 'Exercise:qcm:0'
            }}
        result = gen.dtd_classes['qcm'].to_jstree_dict('Exercise', number=0)
        self.maxDiff = None
        self.assertEqual(result, expected)

    def test_to_jstree_json(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        json_result = gen.dtd_classes['qcm'].to_jstree_json('Exercise', number=0)
        dict_result = gen.dtd_classes['qcm'].to_jstree_dict('Exercise', number=0)
        self.assertEqual(json_result, json.dumps(dict_result))

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
        exercise = gen.create_obj('Exercise')
        test = exercise.create('test')

        test1 = test.add()
        test1.create('question', 'question 1')
        comment = test1.create('comments').create('comment')
        comment.add(text='comment1')
        comment.add(text='comment2')
        comment.add(text='comment3', position=1)

        test2 = test.add()
        test2.create('question', 'question 2')

        expected = '''<?xml version='1.0' encoding='UTF-8'?>
<Exercise>
  <number/>
  <test>
    <question>question 1</question>
    <comments>
      <comment>comment1</comment>
      <comment>comment3</comment>
      <comment>comment2</comment>
    </comments>
  </test>
  <test>
    <question>question 2</question>
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

        test3 = obj.test.add(position=0)
        comment = test3.create('comments').create('comment')
        comment.add(text='comment 3').attrs['idcomment'] = '11'

        comment = obj.test[2]['comments']['comment']
        comment.add(text='comment 4', position=0)

        expected = '''<?xml version='1.0' encoding='UTF-8'?>
<Exercise idexercise="1">
  <number>1</number>
  <test>
    <question/>
    <comments>
      <comment idcomment="11">comment 3</comment>
    </comments>
  </test>
  <test idtest="1" name="color">
    <question idquestion="1">What is your favorite color?</question>
    <mqm idmqm="1">
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
      <comment>comment 4</comment>
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
        exercise = gen.create_obj('Exercise')
        test = exercise.create('test')
        try:
            test.add(text='text')
            assert 0
        except Exception, e:
            self.assertEqual(str(e),"Can't set value to non TextElement")


class TestMultipleElementList(TestCase):

    # TODO: fix code to make this test passes
    # def test_add(self):
    #     gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
    #     exercise = gen.create_obj('Exercise')
    #     test = exercise.create('test')

    #     test1 = test.add()
    #     test1.create('question', 'question 1')
    #     qcms = test1.create('_qcm_mqm')
    #     qcm1 = qcms.add()
    #     choices1 = qcm1.create('choice')
    #     choices1.add(text='choice1')
    #     choices1.add(text='choice2')
    #     choices1.add(text='choice3', position=1)
    #     qcm2 = qcms.add()
    #     choices2 = qcm2.create('choice')
    #     choices2.add(text='choice4')
    #     choices2.add(text='choice5')
    #     choices2.add(text='choice6', position=1)

    #     test2 = test.add()
    #     test2.create('question', 'question 2')
    #     mqms = test2.create('mqm')
    #     mqm1 = mqms.add()
    #     mqm1.attrs['idmqm'] = '1'
    #     choices1 = mqm1.create('choice')
    #     choices1.add(text='choice1')

    #     expected = '''<?xml version='1.0' encoding='UTF-8'?>
    # <Exercise>
    #   <number/>
    #   <test>
    #     <question>question 1</question>
    #     <qcm>
    #       <choice>choice1</choice>
    #       <choice>choice3</choice>
    #       <choice>choice2</choice>
    #     </qcm>
    #     <qcm>
    #       <choice>choice4</choice>
    #       <choice>choice6</choice>
    #       <choice>choice5</choice>
    #     </qcm>
    #   </test>
    #   <test>
    #     <question>question 2</question>
    #     <mqm idmqm="1">
    #       <choice>choice1</choice>
    #     </mqm>
    #   </test>
    # </Exercise>
    # '''
    #     xml = gen.obj_to_xml(exercise)
    #     xml_str = etree.tostring(
    #         xml.getroottree(),
    #         pretty_print=True,
    #         xml_declaration=True,
    #         encoding='UTF-8')
    #     self.assertEqual(xml_str, expected)

    def test_add_on_existing_obj(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)

        mqm3 = obj.test[0]._qcm_mqm.add('mqm', position=0)
        choices = mqm3.create('choice')
        choices.add(text='choice 3').attrs['idchoice'] = '11'

        choices1 = obj.test[0]._qcm_mqm[1].choice
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

