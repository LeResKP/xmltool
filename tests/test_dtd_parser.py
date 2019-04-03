#!/usr/bin/env python

from unittest import TestCase
from xmltool import dtd_parser
from xmltool.elements import (
    TextElement,
    Element,
    ListElement,
    ChoiceElement,
    ChoiceListElement,
    InListMixin,
    InChoiceMixin,
)


MOVIE_DTD = u'''
<!ELEMENT Movie (is-publish?, name, year, directors, actors, resume?, critique*)>

<!-- My comment
that should be removed
<!ELEMENT fake (skipme+)>
-->
<!ENTITY % person "name, firstname" >
<!ELEMENT is-publish EMPTY>
<!ELEMENT directors (director+)>
<!ELEMENT actors (actor+)>
<!ELEMENT name (#PCDATA)>
<!ELEMENT firstname (#PCDATA)>
<!ELEMENT year (#PCDATA)>
<!ELEMENT director (%person;)>
<!ELEMENT actor (%person;)>
<!ELEMENT resume (#PCDATA)>
<!ELEMENT critique (#PCDATA)>
'''

MOVIE_XML_TITANIC = b'''<?xml version='1.0' encoding='UTF-8'?>
<Movie>
  <name>Titanic</name>
  <year>1997</year>
  <directors>
    <director>
      <name>Cameron</name>
      <firstname>James</firstname>
    </director>
  </directors>
  <actors>
    <actor>
      <name>DiCaprio</name>
      <firstname>Leonardo</firstname>
    </actor>
    <actor>
      <name>Winslet</name>
      <firstname>Kate</firstname>
    </actor>
    <actor>
      <name>Zane</name>
      <firstname>Billy</firstname>
    </actor>
  </actors>
  <resume>
     Resume of the movie
  </resume>
  <critique>critique1</critique>
  <critique>critique2</critique>
</Movie>
'''

MOVIE_XML_TITANIC_COMMENTS = b'''<?xml version='1.0' encoding='UTF-8'?>
<!-- Movie comment -->
<Movie>
  <!-- name comment -->
  <name>Titanic</name>
  <!-- year comment -->
  <year>1997</year>
  <!-- directors comment -->
  <directors>
    <!-- director comment -->
    <director>
      <!-- director name comment -->
      <name>Cameron</name>
      <!-- director firstname comment -->
      <firstname>James</firstname>
    </director>
  </directors>
  <!-- actors comment -->
  <actors>
    <!-- actor 1 comment -->
    <actor>
      <!-- actor 1 name comment -->
      <name>DiCaprio</name>
      <!-- actor 1 firstname comment -->
      <firstname>Leonardo</firstname>
    </actor>
    <!-- actor 2 comment -->
    <actor>
      <!-- actor 2 name comment -->
      <name>Winslet</name>
      <!-- actor 2 firstname comment -->
      <firstname>Kate</firstname>
    </actor>
    <!-- actor 3 comment -->
    <actor>
      <!-- actor 3 name comment -->
      <name>Zane</name>
      <!-- actor 3 firstname comment -->
      <firstname>Billy</firstname>
    </actor>
  </actors>
  <!-- resume comment -->
  <resume>
     Resume of the movie
  </resume>
  <!-- critique 1 comment -->
  <critique>critique1</critique>
  <!-- critique 2 comment -->
  <critique>critique2</critique>
</Movie>
'''

EXERCISE_DTD = u'''
<!ELEMENT Exercise (question, test)>
<!ELEMENT question (#PCDATA)>
<!ELEMENT test (qcm|mqm)>
<!ELEMENT qcm (choice+)>
<!ELEMENT mqm (choice+)>
<!ELEMENT choice (#PCDATA)>
'''


EXERCISE_XML = b'''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise SYSTEM "test.dtd">
<Exercise>
  <question>What is your favorite color?</question>
  <test>
    <mqm>
      <choice>blue</choice>
      <choice>red</choice>
      <choice>black</choice>
    </mqm>
  </test>
</Exercise>
'''

INVALID_EXERCISE_XML = b'''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise SYSTEM "test.dtd">
<Exercise>
  <question>What is your favorite color?</question>
  <test>
    <mqm>
    </mqm>
  </test>
</Exercise>
'''

EXERCISE_DTD_2 = u'''
<!ELEMENT Exercise (number, test*)>
<!ELEMENT test (question, (qcm|mqm)*, comments?)>
<!ELEMENT qcm (choice+)>
<!ELEMENT mqm (choice+)>
<!ELEMENT comments (comment+)>
<!ELEMENT number (#PCDATA)>
<!ELEMENT comment (#PCDATA)>
<!ELEMENT question (#PCDATA)>
<!ELEMENT choice (#PCDATA)>

<!ATTLIST Exercise idexercise ID #IMPLIED>
<!ATTLIST test idtest ID #IMPLIED>
<!ATTLIST test name PCDATA #IMPLIED>
<!ATTLIST qcm idqcm ID #IMPLIED>
<!ATTLIST mqm idmqm ID #IMPLIED>
<!ATTLIST comments idcomments ID #IMPLIED>
<!ATTLIST comment idcomment ID #IMPLIED>
<!ATTLIST question idquestion ID #IMPLIED>
<!ATTLIST choice idchoice ID #IMPLIED>
'''

EXERCISE_XML_2 = b'''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise SYSTEM "test.dtd">
<Exercise idexercise="1">
  <number>1</number>
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
      <comment idcomment="1">My comment 1</comment>
      <comment idcomment="2">My comment 2</comment>
    </comments>
  </test>
</Exercise>
'''

EXERCISE_DTD_3 = u'''
<!ELEMENT Exercise (number, test+)>
<!ELEMENT test (question, (qcm|mqm), comments?)>
<!ELEMENT qcm (choice+)>
<!ELEMENT mqm (choice+)>
<!ELEMENT comments (comment+)>
<!ELEMENT number (#PCDATA)>
<!ELEMENT comment (#PCDATA)>
<!ELEMENT question (#PCDATA)>
<!ELEMENT choice (#PCDATA)>
'''

EXERCISE_DTD_4 = u'''
<!ELEMENT Exercise (number, test+)>
<!ELEMENT test (question, (qcm|mqm), (positive-comments|negative-comments)*)>
<!ELEMENT qcm (choice+)>
<!ELEMENT mqm (choice+)>
<!ELEMENT positive-comments (comment+)>
<!ELEMENT negative-comments (comment+)>
<!ELEMENT number (#PCDATA)>
<!ELEMENT comment (#PCDATA)>
<!ELEMENT question (#PCDATA)>
<!ELEMENT choice (#PCDATA)>
'''

BOOK_DTD = u'''
<!ELEMENT Book (ISBN, book-title, book-resume, comments)>
<!ELEMENT ISBN (#PCDATA)>
<!ELEMENT book-title (#PCDATA)>
<!ELEMENT book-resume (#PCDATA)>
<!ELEMENT comments (comment*)>
<!ELEMENT comment (#PCDATA)>
'''

BOOK_XML = b'''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Book SYSTEM "test.dtd">
<Book>
  <ISBN>JFJEFBQN</ISBN>
  <book-title>How to use XML tools?</book-title>
  <book-resume>This is the resume of the book</book-resume>
  <comments>
    <comment>First comment</comment>
    <comment>Second comment</comment>
  </comments>
</Book>'''


class DtdParser(TestCase):

    def test_cleanup(self):
        value = 'Hello\nWorld, my name is John\r'
        expected = 'HelloWorld, my name is John'
        self.assertEqual(dtd_parser.cleanup(value), expected)

    def test_parse_element(self):
        element = 'Movie(name,year,directors,actors,resume?,critique*)'
        expected = ('Movie', 'name,year,directors,actors,resume?,critique*')
        self.assertEqual(dtd_parser.parse_element(element), expected)

        element = 'Movie  (   name,   year,directors,actors,resume?,critique*)'
        expected = ('Movie', 'name,year,directors,actors,resume?,critique*')
        self.assertEqual(dtd_parser.parse_element(element), expected)

    def test_parse_element_exception(self):
        element = 'Movie (name,year,directors,actors,resume?,critique*'
        try:
            dtd_parser.parse_element(element)
            assert 0
        except Exception as e:
            self.assertEqual( str(e), 'Unbalanced parenthesis %s' % element)

    def test_parse_element_exception_empty(self):
        try:
            dtd_parser.parse_element('')
            assert 0
        except Exception as e:
            self.assertEqual(str(e), 'Error parsing element ')

    def test_parse_entity(self):
        entity = '%person"name,firstname"'
        expected = ('%person', "name,firstname")
        self.assertEqual(dtd_parser.parse_entity(entity), expected)

    def test_parse_entity_exception(self):
        entity = '%personname,firstname"'
        self.assertRaises(Exception, dtd_parser.parse_entity, entity)

    def test_split_list(self):
        lis = [1, 2, 3, 4, 5, 6]
        expected = [[1, 2, 3], [4, 5, 6]]
        self.assertEqual(dtd_parser.split_list(lis, 3), expected)
        lis = [1, 2, 3, 4, 5, 6, 7]
        expected = [[1, 2], [3, 4], [5, 6], [7]]
        self.assertEqual(dtd_parser.split_list(lis, 2), expected)

    def test_parse_attribute(self):
        attr = 'Exercise idexercise ID #IMPLIED'
        result = dtd_parser.parse_attribute(attr)
        expected = ('Exercise', [('idexercise', 'ID', '#IMPLIED')])
        self.assertEqual(result, expected)
        attr = 'Exercise idexercise\n ID #IMPLIED'
        result = dtd_parser.parse_attribute(attr)
        expected = ('Exercise', [('idexercise', 'ID', '#IMPLIED')])
        self.assertEqual(result, expected)

    def test_dtd_to_dict(self):
        expected = {
            'name': {'elts': '#PCDATA', 'attrs': []},
            'firstname': {'elts': '#PCDATA', 'attrs': []},
            'is-publish': {'elts': 'EMPTY', 'attrs': []},
            'resume': {'elts': '#PCDATA', 'attrs': []},
            'Movie': {
                'elts': ('is-publish?,name,year,directors,'
                         'actors,resume?,critique*'), 'attrs': []},
            'actor': {'elts': 'name,firstname', 'attrs': []},
            'director': {'elts': 'name,firstname', 'attrs': []},
            'directors': {'elts': 'director+', 'attrs': []},
            'actors': {'elts': 'actor+', 'attrs': []},
            'year': {'elts': '#PCDATA', 'attrs': []},
            'critique': {'elts': '#PCDATA', 'attrs': []},
            }
        dic = dtd_parser.dtd_to_dict_v2(MOVIE_DTD)
        self.assertEqual(dic, expected)

    def test_dtd_to_dict_with_spaces(self):

        dtd_str = '''
            <!ELEMENT   Exercise   (question, test)  >
            <!ELEMENT empty  EMPTY 
            >
            <!ELEMENT question  ( #PCDATA )
            >
            <!ELEMENT test ( qcm | mqm)   >
            <!ELEMENT qcm (choice + ) >
            <!ELEMENT mqm  (choice + )>
            <!ELEMENT choice (
            #PCDATA   )
            >'''
        expected = {
            'Exercise': {'elts': 'question,test', 'attrs': []},
            'choice': {'elts': '#PCDATA', 'attrs': []},
            'empty': {'elts': 'EMPTY', 'attrs': []},
            'mqm': {'elts': 'choice+', 'attrs': []},
            'qcm': {'elts': 'choice+', 'attrs': []},
            'question': {'elts': '#PCDATA', 'attrs': []},
            'test': {'elts': 'qcm|mqm', 'attrs': []},
        }
        dic = dtd_parser.dtd_to_dict_v2(dtd_str)
        self.assertEqual(dic, expected)

    def test_dtd_to_dict_attrs(self):
        expected = {
            'comment': {'elts': '#PCDATA',
                        'attrs': [('idcomment', 'ID', '#IMPLIED')]},
            'question': {'elts': '#PCDATA',
                         'attrs': [('idquestion', 'ID', '#IMPLIED')]},
            'mqm': {'elts': 'choice+',
                    'attrs': [('idmqm', 'ID', '#IMPLIED')]},
            'number': {'elts': '#PCDATA', 'attrs': []},
            'comments': {'elts': 'comment+',
                         'attrs': [('idcomments', 'ID', '#IMPLIED')]},
            'choice': {'elts': '#PCDATA',
                       'attrs': [('idchoice', 'ID', '#IMPLIED')]},
            'Exercise': {'elts': 'number,test*',
                         'attrs': [('idexercise', 'ID', '#IMPLIED')]},
            'test': {'elts': 'question,(qcm|mqm)*,comments?',
                     'attrs': [('idtest', 'ID', '#IMPLIED'),
                               ('name', 'PCDATA', '#IMPLIED')]},
            'qcm': {'elts': 'choice+',
                    'attrs': [('idqcm', 'ID', '#IMPLIED')]}
            }
        dic = dtd_parser.dtd_to_dict_v2(EXERCISE_DTD_2)
        self.assertEqual(dic, expected)

    def test_parse_dtd_to_dict_exception(self):
        dtd = '<!PLOP Movie (name, year, directors, actors, resume?, critique*)>'
        self.assertRaises(Exception, dtd_parser.dtd_to_dict_v2, dtd)

    def test__parse_elts(self):
        elts = '#PCDATA'
        lis = dtd_parser._parse_elts(elts)
        expected = [('#PCDATA', True, False, [])]
        self.assertEqual(lis, expected)

        elts = 'tag?'
        lis = dtd_parser._parse_elts(elts)
        expected = [('tag', False, False, [])]
        self.assertEqual(lis, expected)

        elts = 'tag*'
        lis = dtd_parser._parse_elts(elts)
        expected = [('tag', False, True, [])]
        self.assertEqual(lis, expected)

        elts = 'tag+'
        lis = dtd_parser._parse_elts(elts)
        expected = [('tag', True, True, [])]
        self.assertEqual(lis, expected)

        elts = '(tag1|tag2)+'
        lis = dtd_parser._parse_elts(elts)
        expected = [('tag1_tag2', True, True, [
            ('tag1', True, False, []),
            ('tag2', True, False, [])
        ])]
        self.assertEqual(lis, expected)

        elts = '(#PCDATA|tag1|tag2)*'
        lis = dtd_parser._parse_elts(elts)
        expected = [
            ('#PCDATA_tag1_tag2', False, True, [
                ('#PCDATA', True, False, []),
                ('tag1', True, False, []),
                ('tag2', True, False, [])]
            )]
        self.assertEqual(lis, expected)

    def test__create_class_dict(self):
        dtd_dict = {
            'tag': {'elts': '#PCDATA', 'attrs': [('idtag', 'ID', '#IMPLIED')]},
        }
        dic = dtd_parser._create_class_dict(dtd_dict)
        self.assertEqual(len(dic), 1)
        tag = dic['tag']
        self.assertTrue(issubclass(tag, TextElement))
        self.assertEqual(tag.tagname, 'tag')
        self.assertEqual(tag._is_empty, False)
        self.assertEqual(tag._attribute_names, ['idtag'])
        self.assertEqual(tag.children_classes, [])

        dtd_dict = {
            'tag': {'elts': '(#PCDATA|tag1|tag2)*', 'attrs': []},
        }
        dic = dtd_parser._create_class_dict(dtd_dict)
        self.assertEqual(len(dic), 1)
        tag = dic['tag']
        self.assertTrue(issubclass(tag, TextElement))
        self.assertEqual(tag.tagname, 'tag')
        self.assertEqual(tag._is_empty, False)
        self.assertEqual(tag._attribute_names, [])
        self.assertEqual(tag.children_classes, [])
        # dtd_dict has changed because of the mixed content
        self.assertEqual(
            dtd_dict, {'tag': {'elts': 'tag1?,tag2?', 'attrs': []}})

        dtd_dict = {
            'tag': {'elts': '(tag1)*', 'attrs': []},
        }
        dic = dtd_parser._create_class_dict(dtd_dict)
        self.assertEqual(len(dic), 1)
        tag = dic['tag']
        self.assertTrue(issubclass(tag, Element))
        self.assertEqual(tag.tagname, 'tag')
        self.assertEqual(tag._is_empty, False)
        self.assertEqual(tag._attribute_names, [])
        self.assertEqual(tag.children_classes, [])

        dtd_dict = {
            'tag': {'elts': '(tag1|tag2)', 'attrs': []},
        }
        dic = dtd_parser._create_class_dict(dtd_dict)
        self.assertEqual(len(dic), 1)
        tag = dic['tag']
        self.assertTrue(issubclass(tag, Element))
        self.assertEqual(tag.tagname, 'tag')
        self.assertEqual(tag._is_empty, False)
        self.assertEqual(tag._attribute_names, [])
        self.assertEqual(tag.children_classes, [])

        dtd_dict = {
            'tag': {'elts': 'EMPTY', 'attrs': []},
        }
        dic = dtd_parser._create_class_dict(dtd_dict)
        self.assertEqual(len(dic), 1)
        tag = dic['tag']
        self.assertTrue(issubclass(tag, TextElement))
        self.assertEqual(tag.tagname, 'tag')
        self.assertEqual(tag._is_empty, True)
        self.assertEqual(tag.children_classes, [])

    def test__create_new_class(self):
        dtd_dict = {
            'tag': {'elts': 'tag1', 'attrs': [('idtag', 'ID', '#IMPLIED')]},
        }
        class_dic = dtd_parser._create_class_dict(dtd_dict)
        cls = dtd_parser._create_new_class(
            class_dic, 'tag', required=False, islist=False, conditionals=[])
        self.assertTrue(issubclass(cls, Element))
        self.assertEqual(cls.__name__, 'tag')
        self.assertEqual(cls._required, False)

        cls = dtd_parser._create_new_class(
            class_dic, 'tag', required=True, islist=False, conditionals=[])
        self.assertTrue(issubclass(cls, Element))
        self.assertEqual(cls.__name__, 'tag')
        self.assertEqual(cls._required, True)

        cls = dtd_parser._create_new_class(
            class_dic, 'tag', required=True, islist=True, conditionals=[])
        self.assertTrue(issubclass(cls, ListElement))
        self.assertEqual(cls.__name__, 'tagList')
        self.assertEqual(cls._required, True)
        self.assertEqual(cls._children_class._parent_cls, cls)
        self.assertEqual(cls._children_class._required, True)
        self.assertTrue(issubclass(cls._children_class, InListMixin))

        dtd_dict = {
            'tag': {'elts': '(tag1|tag2)', 'attrs': []},
            'tag1': {'elts': 'sub1', 'attrs': []},
            'tag2': {'elts': 'sub2', 'attrs': []},
        }
        conditionals = [
            ('tag1', True, False, []),
            ('tag2', True, False, []),
        ]
        class_dic = dtd_parser._create_class_dict(dtd_dict)
        try:
            cls = dtd_parser._create_new_class(
                class_dic, 'tag1_tag2', required=True, islist=False,
                conditionals=[])
            assert(False)
        except Exception as e:
            self.assertEqual(
                str(e),
                'You should provide a base_cls or conditionals for tag1_tag2')

        cls = dtd_parser._create_new_class(
            class_dic, 'tag1_tag2', required=True, islist=False,
            conditionals=conditionals)
        self.assertTrue(issubclass(cls, ChoiceElement))
        self.assertEqual(cls.__name__, 'tag1_tag2Choice')
        self.assertEqual(cls._required, True)
        self.assertEqual(len(cls._choice_classes), 2)
        elt1 = cls._choice_classes[0]
        elt2 = cls._choice_classes[1]
        self.assertEqual(elt1._parent_cls, cls)
        self.assertTrue(issubclass(elt1, InChoiceMixin))
        self.assertEqual(elt1._required, True)
        self.assertEqual(elt2._parent_cls, cls)
        self.assertTrue(issubclass(elt2, InChoiceMixin))
        self.assertEqual(elt2._required, True)

        cls = dtd_parser._create_new_class(
            class_dic, 'tag1_tag2', required=True, islist=True,
            conditionals=conditionals)
        self.assertTrue(issubclass(cls, ChoiceListElement))
        self.assertEqual(cls.__name__, 'tag1_tag2ChoiceList')
        self.assertEqual(cls._required, True)
        self.assertEqual(len(cls._choice_classes), 2)
        elt1 = cls._choice_classes[0]
        elt2 = cls._choice_classes[1]
        self.assertEqual(elt1._parent_cls, cls)
        self.assertEqual(elt1._required, True)
        self.assertTrue(issubclass(elt1, InListMixin))
        self.assertEqual(elt2._parent_cls, cls)
        self.assertEqual(elt2._required, True)
        self.assertTrue(issubclass(elt2, InListMixin))

    def test__create_classes(self):
        dtd_dict = {
            'tag': {'elts': '#PCDATA', 'attrs': []},
        }
        class_dict = dtd_parser._create_classes(dtd_dict)
        self.assertEqual(len(class_dict), 1)
        tag = class_dict['tag']
        self.assertEqual(tag.__name__, 'tag')
        self.assertEqual(tag._required, False)
        self.assertEqual(tag.children_classes, [])

        dtd_dict = {
            'tag': {'elts': 'subtag', 'attrs': []},
            'subtag': {'elts': '#PCDATA', 'attrs': []},
        }
        class_dict = dtd_parser._create_classes(dtd_dict)
        self.assertEqual(len(class_dict), 2)
        tag = class_dict['tag']
        subtag = class_dict['subtag']
        self.assertEqual(len(tag.children_classes), 1)
        self.assertTrue(issubclass(tag.children_classes[0], subtag))
        subtag = tag.children_classes[0]
        self.assertEqual(tag.__name__, 'tag')
        self.assertEqual(tag._required, False)
        self.assertEqual(subtag.__name__, 'subtag')
        self.assertEqual(subtag._required, True)
        self.assertEqual(subtag.children_classes, [])
        self.assertEqual(subtag._parent_cls, tag)
