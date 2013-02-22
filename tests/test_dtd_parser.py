#!/usr/bin/env python

from unittest import TestCase
from lxml import etree
import __builtin__
from xmltools import dtd_parser, forms
import tw2.core.testbase as tw2test
import simplejson as json


def fake_open(content, *args):
    class Fake(object):
        def read(self):
            return content
    return Fake()

MOVIE_DTD = '''
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

MOVIE_XML_TITANIC = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Movie SYSTEM "test.dtd">
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

MOVIE_XML_TITANIC_COMMENTS = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Movie SYSTEM "test.dtd">
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

EXERCISE_DTD = '''
<!ELEMENT Exercise (question, test)>
<!ELEMENT question (#PCDATA)>
<!ELEMENT test (qcm|mqm)>
<!ELEMENT qcm (choice+)>
<!ELEMENT mqm (choice+)>
<!ELEMENT choice (#PCDATA)>
'''


EXERCISE_XML = '''<?xml version='1.0' encoding='UTF-8'?>
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

INVALID_EXERCISE_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise SYSTEM "test.dtd">
<Exercise>
  <question>What is your favorite color?</question>
  <test>
    <mqm>
    </mqm>
  </test>
</Exercise>
'''

EXERCISE_DTD_2 = '''
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

EXERCISE_XML_2 = '''<?xml version='1.0' encoding='UTF-8'?>
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

EXERCISE_DTD_3 = '''
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

EXERCISE_DTD_4 = '''
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

BOOK_DTD = '''
<!ELEMENT Book (ISBN, book-title, book-resume, comments)>
<!ELEMENT ISBN (#PCDATA)>
<!ELEMENT book-title (#PCDATA)>
<!ELEMENT book-resume (#PCDATA)>
<!ELEMENT comments (comment*)>
<!ELEMENT comment (#PCDATA)>
'''

BOOK_XML = '''<?xml version='1.0' encoding='UTF-8'?>
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

    def test_clear_value(self):
        self.assertEqual(dtd_parser.clear_value(None), '')
        self.assertEqual(dtd_parser.clear_value(dtd_parser.UNDEFINED), '')
        self.assertEqual(dtd_parser.clear_value(" Hello "), ' Hello ')

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
        self.assertRaises(Exception, dtd_parser.parse_element, element)

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
            'name': '#PCDATA',
            'firstname': '#PCDATA',
            'is-publish': 'EMPTY',
            'resume': '#PCDATA',
            'Movie': 'is-publish?,name,year,directors,actors,resume?,critique*', 
            'actor': 'name,firstname',
            'director': 'name,firstname',
            'directors': 'director+',
            'actors': 'actor+',
            'year': '#PCDATA',
            'critique': '#PCDATA'
            }
        dtd, dtd_attrs = dtd_parser.dtd_to_dict(MOVIE_DTD)
        self.assertEqual(dtd, expected)
        self.assertEqual(dtd_attrs, {})

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
            'Exercise': 'question,test',
            'choice': '#PCDATA',
            'empty': 'EMPTY',
            'mqm': 'choice+',
            'qcm': 'choice+',
            'question': '#PCDATA',
            'test': 'qcm|mqm'}
        dtd, dtd_attrs = dtd_parser.dtd_to_dict(dtd_str)
        self.assertEqual(dtd, expected)
        self.assertEqual(dtd_attrs, {})

    def test_dtd_to_dict_attrs(self):
        expected = {
            'name': '#PCDATA', 
            'firstname': '#PCDATA', 
            'resume': '#PCDATA', 
            'Movie': 'name,year,directors,actors,resume?,critique*', 
            'actor': 'name,firstname', 
            'director': 'name,firstname', 
            'directors': 'director+', 
            'actors': 'actor+', 
            'year': '#PCDATA', 
            'critique': '#PCDATA'
            }

        expected = {
            'comment': '#PCDATA',
            'question': '#PCDATA',
            'mqm': 'choice+',
            'number': '#PCDATA',
            'comments': 'comment+',
            'choice': '#PCDATA',
            'Exercise': 'number,test*',
            'test': 'question,(qcm|mqm)*,comments?',
            'qcm': 'choice+'
            }
        expected_attrs = {
            'comment': [('idcomment', 'ID', '#IMPLIED')],
            'question': [('idquestion', 'ID', '#IMPLIED')],
            'mqm': [('idmqm', 'ID', '#IMPLIED')],
            'comments': [('idcomments', 'ID', '#IMPLIED')],
            'choice': [('idchoice', 'ID', '#IMPLIED')],
            'Exercise': [('idexercise', 'ID', '#IMPLIED')],
            'test': [('idtest', 'ID', '#IMPLIED'),
                     ('name', 'PCDATA', '#IMPLIED')],
            'qcm': [('idqcm', 'ID', '#IMPLIED')]
            }
        dtd, dtd_attrs = dtd_parser.dtd_to_dict(EXERCISE_DTD_2)
        self.assertEqual(dtd, expected)
        self.assertEqual(dtd_attrs, expected_attrs)

    def test_parse_dtd_to_dict_exception(self):
        dtd = '<!PLOP Movie (name, year, directors, actors, resume?, critique*)>'
        self.assertRaises(Exception, dtd_parser.dtd_to_dict, dtd)

    def test_get_child(self):
        root = etree.Element('root')
        sub1 = etree.SubElement(root, 'sub1')
        sub1.text = 'sub1'
        sub2 = etree.SubElement(root, 'sub1')
        sub2.text = 'sub2'
        result = dtd_parser.get_child('sub1', root).text
        self.assertTrue(result, sub1.text)

    def test_get_children(self):
        root = etree.Element('root')
        sub1 = etree.SubElement(root, 'sub1')
        sub1.text = 'sub1'
        sub2 = etree.SubElement(root, 'sub1')
        sub2.text = 'sub2'
        results = [e.text for e in dtd_parser.get_children('sub1', root)]
        self.assertTrue(results, [sub1.text, sub2.text])


class test_SubElement(TestCase):

    def test_init(self):
        text = 'actor'
        elt = dtd_parser.SubElement(text)
        self.assertEqual(elt.tagname, 'actor')
        self.assertTrue(elt.required)
        self.assertFalse(elt.islist)

    def test_init_no_required(self):
        text = 'actor?'
        elt = dtd_parser.SubElement(text)
        self.assertEqual(elt.tagname, 'actor')
        self.assertFalse(elt.required)
        self.assertFalse(elt.islist)

    def test_init_list(self):
        text = 'actor*'
        elt = dtd_parser.SubElement(text)
        self.assertEqual(elt.tagname, 'actor')
        self.assertFalse(elt.required)
        self.assertTrue(elt.islist)

    def test_init_list_required(self):
        text = 'actor+'
        elt = dtd_parser.SubElement(text)
        self.assertEqual(elt.tagname, 'actor')
        self.assertTrue(elt.required)
        self.assertTrue(elt.islist)

    def test_init_conditional(self):
        text = '(qcm|mqm)*'
        elt = dtd_parser.SubElement(text)
        self.assertEqual(elt.tagname, '_qcm_mqm')
        self.assertFalse(elt.required)
        self.assertTrue(elt.islist)
        self.assertTrue(['qcm', 'mqm'], elt._conditional_names)
        qcm, mqm = elt.conditional_sub_elements
        self.assertEqual(qcm.tagname, 'qcm')
        self.assertTrue(qcm.required)
        self.assertFalse(qcm.islist)
        self.assertEqual(mqm.tagname, 'mqm')
        self.assertTrue(mqm.required)
        self.assertFalse(mqm.islist)

    def test_repr(self):
        text = 'actor*'
        elt = dtd_parser.SubElement(text)
        self.assertTrue(repr(elt))


class TestGenerator1(TestCase):

    def test_init(self):
        self.assertRaises(ValueError, dtd_parser.Generator)
        self.assertTrue(dtd_parser.Generator(dtd_str=MOVIE_DTD))
        dic, dtd_attrs = dtd_parser.dtd_to_dict(MOVIE_DTD)
        old_open = __builtin__.open
        try:
            __builtin__.open = fake_open
            self.assertTrue(dtd_parser.Generator(dtd_url=MOVIE_DTD))
        finally:
            __builtin__.open = old_open

    def test_dtd_classes(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        self.assertEqual(len(gen.dtd_classes), 11)
        for key in ['is-publish', 'name', 'firstname', 'year', 'resume', 'critique']:
            cls = gen.dtd_classes[key]
            self.assertTrue(issubclass(cls,
                dtd_parser.TextElement))
            if key == 'is-publish':
                self.assertEqual(cls.empty, True)
            else:
                self.assertEqual(cls.empty, False)
        cls = gen.dtd_classes['Movie']
        self.assertEqual(cls.__name__, 'Movie')
        self.assertEqual(len(cls._sub_elements), 7)
        for (key, expected) in [('directors', 1),
                                ('actors', 1),
                                ('director', 2),
                                ('actor', 2)]:
            cls = gen.dtd_classes[key]
            self.assertEqual(len(cls._sub_elements), expected)

    def test_create_obj(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        actor = gen.create_obj('actor')
        self.assertTrue(actor)

        try:
            gen.create_obj('unexisting')
            assert 0
        except Exception, e:
            self.assertEqual(str(e), "Tagname unexisting doesn't exist")

    def test_get_key_from_xml(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        text = 'actor+'
        elt = dtd_parser.SubElement(text)
        key = gen.get_key_from_xml(elt, None)
        self.assertEqual(key, 'actor')

        text = '(qcm|mqm)*'
        elt = dtd_parser.SubElement(text)
        root = etree.Element('root')
        etree.SubElement(root, 'qcm')
        key = gen.get_key_from_xml(elt, root)
        self.assertEqual(key, 'qcm')

        root = etree.Element('root')
        key = gen.get_key_from_xml(elt, root)
        self.assertEqual(key, None)

    def test_set_attrs_to_obj(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        text = 'actor+'
        elt = dtd_parser.SubElement(text)
        root = etree.Element('root')
        root.attrib['id'] = '1'
        gen.set_attrs_to_obj(elt, root)
        self.assertEqual(elt.attrs, {})

        elt._attrs = [('id', 'ID', '#IMPLIED'),
                      ('name', 'ID', '#IMPLIED'),
                      ]
        gen.set_attrs_to_obj(elt, root)
        self.assertEqual(elt.attrs, root.attrib)

    def test_set_comment_to_obj(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        root = etree.Element('root')
        class Fake(object): pass
        obj = Fake()
        obj._comment = None
        gen.set_comment_to_obj(obj, root)
        self.assertEqual(obj._comment, None)

        root.addprevious(etree.Comment('comment 1'))
        gen.set_comment_to_obj(obj, root)
        self.assertEqual(obj._comment, 'comment 1')

        obj._comment = None
        root.addprevious(etree.Comment('comment 2'))
        gen.set_comment_to_obj(obj, root)
        self.assertEqual(obj._comment, 'comment 2\ncomment 1')

    def test_generate_obj(self):
        root = etree.fromstring(MOVIE_XML_TITANIC)
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        obj = gen.generate_obj(root)
        self.assertEqual(obj.sourceline, 3)
        self.assertEqual(obj.name.value, 'Titanic')
        self.assertEqual(obj.name.sourceline, 4)
        self.assertEqual(obj.resume.value, '\n     Resume of the movie\n  ')
        self.assertEqual(obj.resume.sourceline, 26)
        self.assertEqual(obj.year.value, '1997')
        self.assertEqual(obj.year.sourceline, 5)
        self.assertEqual([c.value for c in obj.critique], ['critique1', 'critique2'])
        self.assertEqual(len(obj.actors.actor), 3)
        self.assertEqual(len(obj.directors.director), 1)
        self.assertEqual(obj.actors.actor[0].sourceline, 13)
        self.assertEqual(obj.actors.actor[0].name.value, 'DiCaprio')
        self.assertEqual(obj.actors.actor[0].name.sourceline, 14)
        self.assertEqual(obj.actors.actor[0].firstname.value, 'Leonardo')
        self.assertEqual(obj.actors.actor[1].name.value, 'Winslet')
        self.assertEqual(obj.actors.actor[1].firstname.value, 'Kate')
        self.assertEqual(obj.actors.actor[2].name.value, 'Zane')
        self.assertEqual(obj.actors.actor[2].firstname.value, 'Billy')
        self.assertEqual(obj.directors.director[0].name.value, 'Cameron')
        self.assertEqual(obj.directors.director[0].firstname.value, 'James')

    def test_generate_obj_comments(self):
        root = etree.fromstring(MOVIE_XML_TITANIC_COMMENTS)
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        obj = gen.generate_obj(root)
        self.assertEqual(obj.sourceline, 4)
        self.assertEqual(obj.name.value, 'Titanic')
        self.assertEqual(obj.name._comment, ' name comment ')
        self.assertEqual(obj.name.sourceline, 6)
        self.assertEqual(obj.resume.value, '\n     Resume of the movie\n  ')
        self.assertEqual(obj.resume._comment, ' resume comment ')
        self.assertEqual(obj.resume.sourceline, 44)
        self.assertEqual(obj.year.value, '1997')
        self.assertEqual(obj.year._comment, ' year comment ')
        self.assertEqual(obj.year.sourceline, 8)
        self.assertEqual([c.value for c in obj.critique], ['critique1', 'critique2'])
        self.assertEqual(obj.critique[0]._comment, ' critique 1 comment ')
        self.assertEqual(obj.critique[1]._comment, ' critique 2 comment ')
        self.assertEqual(len(obj.actors.actor), 3)
        self.assertEqual(len(obj.directors.director), 1)
        self.assertEqual(obj.actors._comment, ' actors comment ')
        self.assertEqual(obj.actors.actor[0].sourceline, 22)
        self.assertEqual(obj.actors.actor[0]._comment, ' actor 1 comment ')
        self.assertEqual(obj.actors.actor[0].name.value, 'DiCaprio')
        self.assertEqual(obj.actors.actor[0].name._comment,
                         ' actor 1 name comment ')
        self.assertEqual(obj.actors.actor[0].name.sourceline, 24)
        self.assertEqual(obj.actors.actor[0].firstname.value, 'Leonardo')
        self.assertEqual(obj.actors.actor[0].firstname._comment,
                         ' actor 1 firstname comment ')
        self.assertEqual(obj.actors.actor[1].name.value, 'Winslet')
        self.assertEqual(obj.actors.actor[1].name._comment,
                         ' actor 2 name comment ')
        self.assertEqual(obj.actors.actor[1].firstname.value, 'Kate')
        self.assertEqual(obj.actors.actor[1].firstname._comment,
                         ' actor 2 firstname comment ')
        self.assertEqual(obj.actors.actor[2].name.value, 'Zane')
        self.assertEqual(obj.actors.actor[2].name._comment,
                         ' actor 3 name comment ')
        self.assertEqual(obj.actors.actor[2].firstname.value, 'Billy')
        self.assertEqual(obj.actors.actor[2].firstname._comment,
                         ' actor 3 firstname comment ')
        self.assertEqual(obj.directors._comment, ' directors comment ')
        self.assertEqual(obj.directors.director[0].name.value, 'Cameron')
        self.assertEqual(obj.directors.director[0].name._comment,
                         ' director name comment ')
        self.assertEqual(obj.directors.director[0].firstname.value, 'James')
        self.assertEqual(obj.directors.director[0].firstname._comment,
                         ' director firstname comment ')

    def test_get_key_from_obj(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        text = 'actor+'
        elt = dtd_parser.SubElement(text)
        key = gen.get_key_from_obj(elt, None)
        self.assertEqual(key, 'actor')

        text = '(qcm|mqm)'
        elt = dtd_parser.SubElement(text)
        class FakeObject(object): pass
        o = FakeObject()
        key = gen.get_key_from_obj(elt, o)
        self.assertEqual(key, None)
        o.qcm = 'qcm'
        key = gen.get_key_from_obj(elt, o)
        self.assertEqual(key, 'qcm')

        text = '(qcm|mqm)*'
        elt = dtd_parser.SubElement(text)
        class FakeObject(object): pass
        o = FakeObject()
        key = gen.get_key_from_obj(elt, o)
        self.assertEqual(key, '_qcm_mqm')

    def test_set_attrs_to_xml(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        text = 'actor+'
        elt = dtd_parser.SubElement(text)
        root = etree.Element('root')
        gen.set_attrs_to_xml(elt, root)
        self.assertEqual(root.attrib, {})

        elt.attrs = {'id': '1'}
        root = etree.Element('root')
        gen.set_attrs_to_xml(elt, root)
        self.assertEqual(root.attrib, elt.attrs)

    def test_obj_to_xml(self):
        root = etree.fromstring(MOVIE_XML_TITANIC)
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        obj = gen.generate_obj(root)
        xml = gen.obj_to_xml(obj)
        docinfo = root.getroottree().docinfo
        s = etree.tostring(
                xml,
                pretty_print=True,
                xml_declaration=True,
                encoding=docinfo.encoding,
                doctype=docinfo.doctype)
        self.assertEqual(MOVIE_XML_TITANIC, s)

    def test_obj_to_xml_comments(self):
        root = etree.fromstring(MOVIE_XML_TITANIC_COMMENTS)
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        obj = gen.generate_obj(root)
        xml = gen.obj_to_xml(obj)
        docinfo = root.getroottree().docinfo
        s = etree.tostring(
                xml.getroottree(),
                pretty_print=True,
                xml_declaration=True,
                encoding=docinfo.encoding,
                doctype=docinfo.doctype)
        self.assertEqual(MOVIE_XML_TITANIC_COMMENTS, s)

    def test_obj_to_xml_with_empty(self):
        root = etree.fromstring(MOVIE_XML_TITANIC)
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        obj = gen.generate_obj(root)
        is_publish = gen.dtd_classes['is-publish']()
        is_publish.value = "don't care"
        obj['is-publish'] = is_publish
        xml = gen.obj_to_xml(obj)
        s = etree.tostring(xml, pretty_print=True, xml_declaration=True)
        docinfo = root.getroottree().docinfo
        s = etree.tostring(
                xml,
                pretty_print=True,
                xml_declaration=True,
                encoding=docinfo.encoding,
                doctype=docinfo.doctype)
        expected = '''
<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Movie SYSTEM "test.dtd">
<Movie>
  <is-publish />
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
        tw2test.assert_eq_xml(s, expected)

    def test_obj_to_jstree_dict(self):
        root = etree.fromstring(MOVIE_XML_TITANIC)
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        obj = gen.generate_obj(root)
        dic = gen.obj_to_jstree_dict(obj)
        expected = {'attr': {'class': 'tree_Movie', 'id': 'tree_Movie'},
 'children': [{'attr': {'class': 'tree_Movie:name', 'id': 'tree_Movie:name'},
               'data': 'name <span class="_tree_text">(Titanic)</span>',
               'metadata': {
                   'id': 'Movie:name',
                   'replace_id': 'Movie:name'
               }},
              {'attr': {'class': 'tree_Movie:year', 'id': 'tree_Movie:year'},
               'data': 'year <span class="_tree_text">(1997)</span>',
               'metadata': {
                   'id': 'Movie:year',
                   'replace_id': 'Movie:year'
               }},
              {'attr': {'class': 'tree_Movie:directors',
                        'id': 'tree_Movie:directors'},
               'children': [{'attr': {'class': 'tree_Movie:directors:director',
                                      'id': 'tree_Movie:directors:director:1'},
                             'children': [{'attr': {'class': 'tree_Movie:directors:director:1:name',
                                                    'id': 'tree_Movie:directors:director:1:name'},
                                           'data': 'name <span class="_tree_text">(Cameron)</span>',
                                           'metadata': {
                                               'id': 'Movie:directors:director:1:name',
                                               'replace_id': 'Movie:directors:director:1:name'
                                           }},
                                          {'attr': {'class': 'tree_Movie:directors:director:1:firstname',
                                                    'id': 'tree_Movie:directors:director:1:firstname'},
                                           'data': 'firstname <span class="_tree_text">(James)</span>',
                                           'metadata': {
                                               'id': 'Movie:directors:director:1:firstname',
                                               'replace_id': 'Movie:directors:director:1:firstname'
                                           }}],
                             'data': 'director',
                             'metadata': {
                                 'id': 'Movie:directors:director:1',
                                 'replace_id': 'Movie:directors:director:1'
                             }}],
               'data': 'directors',
               'metadata': {
                   'id': 'Movie:directors',
                   'replace_id': 'Movie:directors'
               }},
              {'attr': {'class': 'tree_Movie:actors',
                        'id': 'tree_Movie:actors'},
               'children': [{'attr': {'class': 'tree_Movie:actors:actor',
                                      'id': 'tree_Movie:actors:actor:1'},
                             'children': [{'attr': {'class': 'tree_Movie:actors:actor:1:name',
                                                    'id': 'tree_Movie:actors:actor:1:name'},
                                           'data': 'name <span class="_tree_text">(DiCaprio)</span>',
                                           'metadata': {
                                               'id': 'Movie:actors:actor:1:name',
                                               'replace_id': 'Movie:actors:actor:1:name'
                                           }},
                                          {'attr': {'class': 'tree_Movie:actors:actor:1:firstname',
                                                    'id': 'tree_Movie:actors:actor:1:firstname'},
                                           'data': 'firstname <span class="_tree_text">(Leonardo)</span>',
                                           'metadata': {
                                               'id': 'Movie:actors:actor:1:firstname',
                                               'replace_id': 'Movie:actors:actor:1:firstname'
                                           }}],
                             'data': 'actor',
                             'metadata': {
                                 'id': 'Movie:actors:actor:1',
                                 'replace_id': 'Movie:actors:actor:1'
                             }},
                            {'attr': {'class': 'tree_Movie:actors:actor',
                                      'id': 'tree_Movie:actors:actor:2'},
                             'children': [{'attr': {'class': 'tree_Movie:actors:actor:2:name',
                                                    'id': 'tree_Movie:actors:actor:2:name'},
                                           'data': 'name <span class="_tree_text">(Winslet)</span>',
                                           'metadata': {
                                               'id': 'Movie:actors:actor:2:name',
                                               'replace_id': 'Movie:actors:actor:2:name'
                                           }},
                                          {'attr': {'class': 'tree_Movie:actors:actor:2:firstname',
                                                    'id': 'tree_Movie:actors:actor:2:firstname'},
                                           'data': 'firstname <span class="_tree_text">(Kate)</span>',
                                           'metadata': {
                                               'id': 'Movie:actors:actor:2:firstname',
                                               'replace_id': 'Movie:actors:actor:2:firstname'
                                           }}],
                             'data': 'actor',
                             'metadata': {
                                 'id': 'Movie:actors:actor:2',
                                 'replace_id': 'Movie:actors:actor:2'
                             }},
                            {'attr': {'class': 'tree_Movie:actors:actor',
                                      'id': 'tree_Movie:actors:actor:3'},
                             'children': [{'attr': {'class': 'tree_Movie:actors:actor:3:name',
                                                    'id': 'tree_Movie:actors:actor:3:name'},
                                           'data': 'name <span class="_tree_text">(Zane)</span>',
                                           'metadata': {
                                               'id': 'Movie:actors:actor:3:name',
                                               'replace_id': 'Movie:actors:actor:3:name'
                                           }},
                                          {'attr': {'class': 'tree_Movie:actors:actor:3:firstname',
                                                    'id': 'tree_Movie:actors:actor:3:firstname'},
                                           'data': 'firstname <span class="_tree_text">(Billy)</span>',
                                           'metadata': {
                                               'id': 'Movie:actors:actor:3:firstname',
                                               'replace_id': 'Movie:actors:actor:3:firstname'
                                           }}],
                             'data': 'actor',
                             'metadata': {
                                 'id': 'Movie:actors:actor:3',
                                 'replace_id': 'Movie:actors:actor:3'
                             }}],
               'data': 'actors',
               'metadata': {
                   'id': 'Movie:actors',
                   'replace_id': 'Movie:actors'
               }},
              {'attr': {'class': 'tree_Movie:resume',
                        'id': 'tree_Movie:resume'},
               'data': 'resume <span class="_tree_text">(\n     Resume of the movie\n  )</span>',
               'metadata': {
                   'id': 'Movie:resume',
                   'replace_id': 'Movie:resume'
               }},
              {'attr': {'class': 'tree_Movie:critique',
                        'id': 'tree_Movie:critique:1'},
               'data': 'critique <span class="_tree_text">(critique1)</span>',
               'metadata': {
                   'id': 'Movie:critique:1',
                   'replace_id': 'Movie:critique:1'
               }},
              {'attr': {'class': 'tree_Movie:critique',
                        'id': 'tree_Movie:critique:2'},
               'data': 'critique <span class="_tree_text">(critique2)</span>',
               'metadata': {
                   'id': 'Movie:critique:2',
                   'replace_id': 'Movie:critique:2'
               }}],
 'data': 'Movie',
 'metadata': {
     'id': 'Movie',
     'replace_id': 'Movie'
 }}
        self.assertEqual(dic, expected)


class TestGenerator2(TestCase):

    def test_dtd_classes(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD)
        self.assertEqual(len(gen.dtd_classes), 6)
        for key in ['question', 'choice']:
            self.assertTrue(issubclass(gen.dtd_classes[key],
                dtd_parser.TextElement))
        for (key, nb_elements) in [('Exercise', 2),
                                ('test', 1),
                                ('qcm', 1),
                                ('mqm', 1)]:
            cls = gen.dtd_classes[key]
            self.assertEqual(len(cls._sub_elements), nb_elements)
        cls = gen.dtd_classes['test']
        self.assertEqual(len(cls._sub_elements[0].conditional_sub_elements), 2)

    def test_generate_obj(self):
        root = etree.fromstring(EXERCISE_XML)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD)
        obj = gen.generate_obj(root)
        self.assertEqual(obj.question.value, 'What is your favorite color?')
        self.assertTrue(isinstance(obj.test, gen.dtd_classes['test']))
        self.assertTrue(isinstance(obj.test.mqm, gen.dtd_classes['mqm']))
        self.assertEqual(len(obj.test.mqm.choice), 3)
        self.assertEqual(obj.test.mqm.choice[0].value, 'blue')
        self.assertEqual(obj.test.mqm.choice[1].value, 'red')
        self.assertEqual(obj.test.mqm.choice[2].value, 'black')

    def test_obj_to_xml(self):
        root = etree.fromstring(EXERCISE_XML)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD)
        obj = gen.generate_obj(root)
        xml = gen.obj_to_xml(obj)
        s = etree.tostring(xml, pretty_print=True, xml_declaration=True)
        docinfo = root.getroottree().docinfo
        s = etree.tostring(
                xml, 
                pretty_print=True,
                xml_declaration=True,
                encoding=docinfo.encoding,
                doctype=docinfo.doctype)
        self.assertEqual(EXERCISE_XML, s)

    def test_obj_to_jstree_dict(self):
        root = etree.fromstring(EXERCISE_XML)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD)
        obj = gen.generate_obj(root)
        dic = gen.obj_to_jstree_dict(obj)
        expected = {'attr': {'class': 'tree_Exercise', 'id': 'tree_Exercise'},
 'children': [{'attr': {'id': 'tree_Exercise:question',
                        'class': 'tree_Exercise:question',
                       },
               'data': 'question <span class="_tree_text">(What is your favorite color?)</span>',
               'metadata': {
                   'id': 'Exercise:question',
                   'replace_id': 'Exercise:question'
               }},
              {'attr': {'class': 'tree_Exercise:test',
                        'id': 'tree_Exercise:test'},
               'children': [{'attr': {'class': 'tree_Exercise:test:mqm',
                                      'id': 'tree_Exercise:test:mqm'},
                             'children': [{'attr': {
                                 'id': 'tree_Exercise:test:mqm:choice:1',
                                 'class': 'tree_Exercise:test:mqm:choice',
                             },
                                           'data': 'choice <span class="_tree_text">(blue)</span>',
                                           'metadata': {
                                               'id': 'Exercise:test:mqm:choice:1',
                                               'replace_id': 'Exercise:test:mqm:choice:1'
                                           }},
                                          {'attr': {
                                              'id': 'tree_Exercise:test:mqm:choice:2',
                                              'class': 'tree_Exercise:test:mqm:choice',
                                          },
                                           'data': 'choice <span class="_tree_text">(red)</span>',
                                           'metadata': {
                                               'id': 'Exercise:test:mqm:choice:2',
                                               'replace_id': 'Exercise:test:mqm:choice:2'
                                           }},
                                          {'attr': {
                                              'id': 'tree_Exercise:test:mqm:choice:3',
                                              'class': 'tree_Exercise:test:mqm:choice',
                                          },
                                           'data': 'choice <span class="_tree_text">(black)</span>',
                                           'metadata': {
                                               'id': 'Exercise:test:mqm:choice:3',
                                               'replace_id': 'Exercise:test:mqm:choice:3'
                                           }}],
                             'data': 'mqm',
                             'metadata': {
                                 'id': 'Exercise:test:mqm',
                                 'replace_id': 'Exercise:test:mqm'
                             }}],
               'data': 'test',
               'metadata': {
                   'id': 'Exercise:test',
                   'replace_id': 'Exercise:test'
               }}],
 'data': 'Exercise',
 'metadata': {
     'id': 'Exercise',
     'replace_id': 'Exercise'
 }}
        self.assertEqual(dic, expected)

    def test_obj_to_jstree_json(self):
        root = etree.fromstring(EXERCISE_XML)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD)
        obj = gen.generate_obj(root)
        dict_result = gen.obj_to_jstree_dict(obj)
        json_result = gen.obj_to_jstree_json(obj)
        self.assertEqual(json_result, json.dumps(dict_result))


class TestGenerator3(TestCase):

    def test_dtd_classes(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        self.assertEqual(len(gen.dtd_classes), 9)
        for key in ['question', 'choice', 'comment', 'number']:
            self.assertTrue(issubclass(gen.dtd_classes[key],
                dtd_parser.TextElement))
        for (key, nb_elements) in [('Exercise', 2),
                                   ('test', 3), 
                                   ('qcm', 1), 
                                   ('mqm', 1),
                                   ('comments', 1)]:
            cls = gen.dtd_classes[key]
            self.assertEqual(len(cls._sub_elements), nb_elements)
        cls = gen.dtd_classes['test']
        self.assertEqual(len(cls._sub_elements[1].conditional_sub_elements), 2)

    def test_dtd_attrs(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        expected = {
            'comment': [('idcomment', 'ID', '#IMPLIED')], 
            'question': [('idquestion', 'ID', '#IMPLIED')], 
            'mqm': [('idmqm', 'ID', '#IMPLIED')],
            'comments': [('idcomments', 'ID', '#IMPLIED')],
            'choice': [('idchoice', 'ID', '#IMPLIED')],
            'Exercise': [('idexercise', 'ID', '#IMPLIED')],
            'test': [('idtest', 'ID', '#IMPLIED'),
                     ('name', 'PCDATA', '#IMPLIED')],
            'qcm': [('idqcm', 'ID', '#IMPLIED')]}
        self.assertEqual(expected, gen.dtd_attrs)

    def test_generate_obj(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)
        self.assertEqual(obj.attrs, {'idexercise': '1'})
        self.assertEqual(obj.number.value, '1')
        self.assertEqual(len(obj.test), 2)

        test1, test2 = obj.test
        self.assertEqual(test1.attrs, {'idtest': '1', 'name': 'color'})
        self.assertEqual(test1.question.attrs, {'idquestion': '1'})
        self.assertEqual(test1.question.value, 'What is your favorite color?')
        self.assertTrue(isinstance(test1, gen.dtd_classes['test']))
        self.assertEqual(len(test1._qcm_mqm), 2)
        mqm1, mqm2 = test1._qcm_mqm
        self.assertTrue(isinstance(mqm1, gen.dtd_classes['mqm']))
        self.assertTrue(isinstance(mqm2, gen.dtd_classes['mqm']))
        self.assertEqual(mqm1.attrs, {'idmqm': '1'})
        self.assertEqual(len(mqm1.choice), 3)
        self.assertEqual(mqm1.choice[0].attrs, {'idchoice': '1'})
        self.assertEqual(mqm1.choice[0].value, 'blue')
        self.assertEqual(mqm1.choice[1].attrs, {'idchoice': '2'})
        self.assertEqual(mqm1.choice[1].value, 'red')
        self.assertEqual(mqm1.choice[2].attrs, {'idchoice': '3'})
        self.assertEqual(mqm1.choice[2].value, 'black')
        self.assertEqual(mqm2.attrs, {'idmqm': '2'})
        self.assertEqual(len(mqm2.choice), 3)
        self.assertEqual(mqm2.choice[0].attrs, {'idchoice': '4'})
        self.assertEqual(mqm2.choice[0].value, 'magenta')
        self.assertEqual(mqm2.choice[1].attrs, {'idchoice': '5'})
        self.assertEqual(mqm2.choice[1].value, 'orange')
        self.assertEqual(mqm2.choice[2].attrs, {'idchoice': '6'})
        self.assertEqual(mqm2.choice[2].value, 'yellow')
        self.assertEqual(test1.comments, None)

        self.assertEqual(test2.attrs, {'idtest': '2'})
        self.assertEqual(test2.question.attrs, {'idquestion': '2'})
        self.assertEqual(test2.question.value, 'Have you got a pet?')
        self.assertTrue(isinstance(test2, gen.dtd_classes['test']))
        self.assertEqual(len(test2._qcm_mqm), 2)
        qcm1, qcm2 = test2._qcm_mqm
        self.assertTrue(isinstance(qcm1, gen.dtd_classes['qcm']))
        self.assertTrue(isinstance(qcm2, gen.dtd_classes['qcm']))
        self.assertEqual(len(qcm1.choice), 2)
        self.assertEqual(qcm1.choice[0].attrs, {'idchoice': '7'})
        self.assertEqual(qcm1.choice[0].value, 'yes')
        self.assertEqual(qcm1.choice[1].attrs, {'idchoice': '8'})
        self.assertEqual(qcm1.choice[1].value, 'no')
        self.assertEqual(len(qcm2.choice), 2)
        self.assertEqual(qcm2.choice[0].attrs, {'idchoice': '9'})
        self.assertEqual(qcm2.choice[0].value, 'yes')
        self.assertEqual(qcm2.choice[1].attrs, {'idchoice': '10'})
        self.assertEqual(qcm2.choice[1].value, 'no')

        self.assertTrue(isinstance(test2.comments, gen.dtd_classes['comments']))
        self.assertEqual(len(test2.comments.comment), 2)
        self.assertEqual(test2.comments.attrs, {'idcomments': '1'})
        comment1, comment2 = test2.comments.comment
        self.assertEqual(comment1.attrs, {'idcomment': '1'})
        self.assertEqual(comment1.value, 'My comment 1')
        self.assertEqual(comment2.attrs, {'idcomment': '2'})
        self.assertEqual(comment2.value, 'My comment 2')

    def test_obj_to_xml(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)
        xml = gen.obj_to_xml(obj)
        s = etree.tostring(xml, pretty_print=True, xml_declaration=True)
        docinfo = root.getroottree().docinfo
        s = etree.tostring(
                xml,
                pretty_print=True,
                xml_declaration=True,
                encoding=docinfo.encoding,
                doctype=docinfo.doctype)
        self.assertEqual(EXERCISE_XML_2, s)

    def test_obj_to_xml_non_existing_list(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)
        del obj.test[0]._qcm_mqm[0].choice
        xml = gen.obj_to_xml(obj)
        s = etree.tostring(xml.getroottree(), pretty_print=True)
        expected = '''<Exercise idexercise="1">
  <number>1</number>
  <test idtest="1" name="color">
    <question idquestion="1">What is your favorite color?</question>
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
        self.assertEqual(s, expected)

    def test_obj_to_jstree_dict(self):
        root = etree.fromstring(EXERCISE_XML_2)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        obj = gen.generate_obj(root)
        dic = gen.obj_to_jstree_dict(obj)
        expected = {'attr': {'class': 'tree_Exercise', 'id': 'tree_Exercise'},
 'children': [{'attr': {'class': 'tree_Exercise:number',
                        'id': 'tree_Exercise:number'},
               'data': 'number <span class="_tree_text">(1)</span>',
               'metadata': {
                    'id': 'Exercise:number',
                    'replace_id': 'Exercise:number'
              }},
              {'attr': {'class': 'tree_Exercise:test',
                        'id': 'tree_Exercise:test:1'},
               'children': [{'attr': {'class': 'tree_Exercise:test:1:question',
                                      'id': 'tree_Exercise:test:1:question'},
                             'data': 'question <span class="_tree_text">(What is your favorite color?)</span>',
                             'metadata': {
                                'id': 'Exercise:test:1:question',
                                'replace_id': 'Exercise:test:1:question'
                            }},
                            {'attr': {'class': 'tree_Exercise:test:1:_qcm_mqm',
                                      'id': 'tree_Exercise:test:1:_qcm_mqm:1:mqm'},
                             'children': [{'attr': {'class': 'tree_Exercise:test:1:_qcm_mqm:1:mqm:choice',
                                                    'id': 'tree_Exercise:test:1:_qcm_mqm:1:mqm:choice:1'},
                                           'data': 'choice <span class="_tree_text">(blue)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:1:_qcm_mqm:1:mqm:choice:1',
                                                'replace_id': 'Exercise:test:1:_qcm_mqm:1:mqm:choice:1'
                                            }},
                                          {'attr': {'class': 'tree_Exercise:test:1:_qcm_mqm:1:mqm:choice',
                                                    'id': 'tree_Exercise:test:1:_qcm_mqm:1:mqm:choice:2'},
                                           'data': 'choice <span class="_tree_text">(red)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:1:_qcm_mqm:1:mqm:choice:2',
                                                'replace_id': 'Exercise:test:1:_qcm_mqm:1:mqm:choice:2'
                                            }},
                                          {'attr': {'class': 'tree_Exercise:test:1:_qcm_mqm:1:mqm:choice',
                                                    'id': 'tree_Exercise:test:1:_qcm_mqm:1:mqm:choice:3'},
                                           'data': 'choice <span class="_tree_text">(black)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:1:_qcm_mqm:1:mqm:choice:3',
                                                'replace_id': 'Exercise:test:1:_qcm_mqm:1:mqm:choice:3'
                                            }}],
                             'data': 'mqm',
                             'metadata': {
                                'id': 'Exercise:test:1:_qcm_mqm:1:mqm',
                                'replace_id': 'Exercise:test:1:_qcm_mqm:1'
                            }},
                            {'attr': {'class': 'tree_Exercise:test:1:_qcm_mqm',
                                      'id': 'tree_Exercise:test:1:_qcm_mqm:2:mqm'},
                             'children': [{'attr': {'class': 'tree_Exercise:test:1:_qcm_mqm:2:mqm:choice',
                                                    'id': 'tree_Exercise:test:1:_qcm_mqm:2:mqm:choice:1'},
                                           'data': 'choice <span class="_tree_text">(magenta)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:1:_qcm_mqm:2:mqm:choice:1',
                                                'replace_id': 'Exercise:test:1:_qcm_mqm:2:mqm:choice:1'
                                            }},
                                          {'attr': {'class': 'tree_Exercise:test:1:_qcm_mqm:2:mqm:choice',
                                                    'id': 'tree_Exercise:test:1:_qcm_mqm:2:mqm:choice:2'},
                                           'data': 'choice <span class="_tree_text">(orange)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:1:_qcm_mqm:2:mqm:choice:2',
                                                'replace_id': 'Exercise:test:1:_qcm_mqm:2:mqm:choice:2'
                                           }},
                                          {'attr': {'class': 'tree_Exercise:test:1:_qcm_mqm:2:mqm:choice',
                                                    'id': 'tree_Exercise:test:1:_qcm_mqm:2:mqm:choice:3'},
                                           'data': 'choice <span class="_tree_text">(yellow)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:1:_qcm_mqm:2:mqm:choice:3',
                                                'replace_id': 'Exercise:test:1:_qcm_mqm:2:mqm:choice:3'
                                            }}],
                             'data': 'mqm',
                             'metadata': {
                                'id': 'Exercise:test:1:_qcm_mqm:2:mqm',
                                'replace_id': 'Exercise:test:1:_qcm_mqm:2'
                            }}],
               'data': 'test',
               'metadata': {
                    'id': 'Exercise:test:1',
                    'replace_id': 'Exercise:test:1'
                }},
              {'attr': {'class': 'tree_Exercise:test',
                        'id': 'tree_Exercise:test:2'},
               'children': [{'attr': {'class': 'tree_Exercise:test:2:question',
                                      'id': 'tree_Exercise:test:2:question'},
                             'data': 'question <span class="_tree_text">(Have you got a pet?)</span>',
                             'metadata': {
                                'id': 'Exercise:test:2:question',
                                'replace_id': 'Exercise:test:2:question',
                            }},
                            {'attr': {'class': 'tree_Exercise:test:2:_qcm_mqm',
                                      'id': 'tree_Exercise:test:2:_qcm_mqm:1:qcm'},
                             'children': [{'attr': {'class': 'tree_Exercise:test:2:_qcm_mqm:1:qcm:choice',
                                                    'id': 'tree_Exercise:test:2:_qcm_mqm:1:qcm:choice:1'},
                                           'data': 'choice <span class="_tree_text">(yes)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:2:_qcm_mqm:1:qcm:choice:1',
                                                'replace_id': 'Exercise:test:2:_qcm_mqm:1:qcm:choice:1'
                                          }},
                                          {'attr': {'class': 'tree_Exercise:test:2:_qcm_mqm:1:qcm:choice',
                                                    'id': 'tree_Exercise:test:2:_qcm_mqm:1:qcm:choice:2'},
                                           'data': 'choice <span class="_tree_text">(no)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:2:_qcm_mqm:1:qcm:choice:2',
                                                'replace_id': 'Exercise:test:2:_qcm_mqm:1:qcm:choice:2'
                                            }}],
                             'data': 'qcm',
                             'metadata': {
                                'id': 'Exercise:test:2:_qcm_mqm:1:qcm',
                                'replace_id': 'Exercise:test:2:_qcm_mqm:1'
                            }},
                            {'attr': {'class': 'tree_Exercise:test:2:_qcm_mqm',
                                      'id': 'tree_Exercise:test:2:_qcm_mqm:2:qcm'},
                             'children': [{'attr': {'class': 'tree_Exercise:test:2:_qcm_mqm:2:qcm:choice',
                                                    'id': 'tree_Exercise:test:2:_qcm_mqm:2:qcm:choice:1'},
                                           'data': 'choice <span class="_tree_text">(yes)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:2:_qcm_mqm:2:qcm:choice:1',
                                                'replace_id': 'Exercise:test:2:_qcm_mqm:2:qcm:choice:1'
                                            }},
                                          {'attr': {'class': 'tree_Exercise:test:2:_qcm_mqm:2:qcm:choice',
                                                    'id': 'tree_Exercise:test:2:_qcm_mqm:2:qcm:choice:2'},
                                           'data': 'choice <span class="_tree_text">(no)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:2:_qcm_mqm:2:qcm:choice:2',
                                                'replace_id': 'Exercise:test:2:_qcm_mqm:2:qcm:choice:2'
                                            }}],
                             'data': 'qcm',
                             'metadata': {
                                'id': 'Exercise:test:2:_qcm_mqm:2:qcm',
                                'replace_id': 'Exercise:test:2:_qcm_mqm:2'
                                }},
                            {'attr': {'class': 'tree_Exercise:test:2:comments',
                                      'id': 'tree_Exercise:test:2:comments'},
                             'children': [{'attr': {'class': 'tree_Exercise:test:2:comments:comment',
                                                    'id': 'tree_Exercise:test:2:comments:comment:1'},
                                           'data': 'comment <span class="_tree_text">(My comment 1)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:2:comments:comment:1',
                                                'replace_id': 'Exercise:test:2:comments:comment:1'
                                            }},
                                          {'attr': {'class': 'tree_Exercise:test:2:comments:comment',
                                                    'id': 'tree_Exercise:test:2:comments:comment:2'},
                                           'data': 'comment <span class="_tree_text">(My comment 2)</span>',
                                           'metadata': {
                                                'id': 'Exercise:test:2:comments:comment:2',
                                                'replace_id': 'Exercise:test:2:comments:comment:2'
                                            }}],
                             'data': 'comments',
                             'metadata': {
                                'id': 'Exercise:test:2:comments',
                                'replace_id': 'Exercise:test:2:comments'
                            }}],
               'data': 'test',
               'metadata': {
                    'id': 'Exercise:test:2',
                    'replace_id': 'Exercise:test:2'
                    }}],
 'data': 'Exercise',
 'metadata': {
    'id': 'Exercise',
    'replace_id': 'Exercise'
}}
        self.assertEqual(dic, expected)

    def test_generate_form_child_conditional(self):
        text = '(qcm|mqm)*'
        elt = dtd_parser.SubElement(text)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_child(elt, parent=None)
        self.assertTrue(isinstance(field, forms.GrowingContainer))
        self.assertTrue(isinstance(field.child, forms.ConditionalContainer))
        self.assertEqual(len(field.child.possible_children), 2)
        for child in field.child.possible_children:
            self.assertTrue(isinstance(child, forms.Fieldset))

    def test_generate_form_child_no_list_text(self):
        text = 'comment'
        elt = dtd_parser.SubElement(text)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_child(elt, parent=None)
        self.assertTrue(isinstance(field, forms.TextAreaField))

    def test_generate_form_child_no_list_no_text(self):
        text = 'comments'
        elt = dtd_parser.SubElement(text)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_child(elt, parent=None)
        self.assertTrue(isinstance(field, forms.Fieldset))
        self.assertEqual(field.key, 'comments')
        self.assertEqual(field.name, 'comments')
        self.assertEqual(field.legend, 'comments')
        self.assertEqual(len(field.children), 1)

    def test_generate_form_child_list_text(self):
        text = 'comment*'
        elt = dtd_parser.SubElement(text)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_child(elt, parent=None)
        self.assertTrue(isinstance(field, forms.GrowingContainer))
        self.assertTrue(isinstance(field.child, forms.TextAreaField))
        self.assertEqual(field.key, 'comment')
        self.assertEqual(field.name, None)
        self.assertEqual(field.child.key, 'comment')
        self.assertEqual(field.child.name, 'comment')
        self.assertEqual(field.child.parent, field)

    def test_generate_form_child_list_no_text(self):
        text = 'test*'
        elt = dtd_parser.SubElement(text)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_child(elt, parent=None)
        self.assertTrue(isinstance(field, forms.GrowingContainer))
        self.assertTrue(isinstance(field.child, forms.Fieldset))
        self.assertEqual(field.key, 'test')
        self.assertEqual(field.name, None)
        self.assertEqual(field.child.key, 'test')
        self.assertEqual(field.child.name, 'test')
        self.assertEqual(field.child.legend, 'test')
        self.assertEqual(field.child.parent, field)
        self.assertEqual(len(field.child.children), 3)

    def test_generate_form_children_text(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        element = dtd_parser.SubElement('text')
        field = gen.generate_form_children(gen.dtd_classes['choice'],
                                           parent=None,
                                           element=element)

        self.assertTrue(isinstance(field, forms.TextAreaField))
        self.assertEqual(field.key, 'choice')
        self.assertEqual(field.name, 'choice')

    def test_generate_form_children_no_text(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_children(gen.dtd_classes['qcm'],
                                           parent=None,
                                           element=None)

        self.assertEqual(len(field), 1)
        self.assertTrue(isinstance(field[0], forms.GrowingContainer))
        self.assertEqual(field[0].key, 'choice')
        self.assertEqual(field[0].name, None)

    def test_generate_form(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        form = gen.generate_form('Exercise')
        self.assertTrue(isinstance(form, forms.FormField))
        self.assertEqual(form.legend, 'Exercise')
        self.assertEqual(len(form.children), 2)

    def test_dict_to_obj(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        dic = {}
        obj = gen.dict_to_obj('Exercise', dic)
        self.assertEqual(obj, None)

        dic = {'empty': 'empty'}
        obj = gen.dict_to_obj('choice', dic)
        self.assertTrue(isinstance(obj, gen.dtd_classes['choice']))
        self.assertEqual(obj.value, None)

        dic = {
            'value': 'choice value',
            'attrs': {'id': '1'},
            '_comment': 'My comment',
        }
        obj = gen.dict_to_obj('choice', dic)
        self.assertTrue(isinstance(obj, gen.dtd_classes['choice']))
        self.assertEqual(obj.value, 'choice value')
        # Bad attribute name
        self.assertEqual(obj.attrs, {})
        self.assertEqual(obj._comment, 'My comment')

        dic = {'choice': [{'value': 'choice1',
                           'attrs': {'idchoice': '1'}},
                          {'value': 'choice2',
                           'attrs': {'idchoice': '2'}},
                         ],
               'attrs': {'idmqm': '1'}
              }
        obj = gen.dict_to_obj('mqm', dic)
        self.assertTrue(isinstance(obj, gen.dtd_classes['mqm']))
        self.assertEqual(obj.attrs, {'idmqm': '1'})
        self.assertEqual(len(obj.choice), 2)
        self.assertEqual(obj.choice[0].value, 'choice1')
        self.assertEqual(obj.choice[0].attrs, {'idchoice': '1'})
        self.assertEqual(obj.choice[1].value, 'choice2')
        self.assertEqual(obj.choice[1].attrs, {'idchoice': '2'})

        dic = {'question': {'value': 'test question',
                            'attrs': {'idquestion': '1'}},
               'attrs': {'idtest': '1'}
        }
        obj = gen.dict_to_obj('test', dic)
        self.assertTrue(isinstance(obj, gen.dtd_classes['test']))
        self.assertEqual(obj.attrs, {'idtest': '1'})
        self.assertEqual(obj.question.value, 'test question')
        self.assertEqual(obj.question.attrs, {'idquestion': '1'})

        dic = {'choice': []}
        obj = gen.dict_to_obj('mqm', dic)
        self.assertTrue(isinstance(obj, gen.dtd_classes['mqm']))
        self.assertEqual(obj.choice, [])

        dic = {'question': None}
        obj = gen.dict_to_obj('test', dic)
        self.assertEqual(obj.question, None)
        self.assertEqual(obj.attrs, {})

        dic = {'value': ''}
        obj = gen.dict_to_obj('question', dic)
        self.assertEqual(obj.value, dtd_parser.UNDEFINED)
        self.assertEqual(obj.attrs, {})

        dic = {'value': None}
        obj = gen.dict_to_obj('question', dic)
        self.assertEqual(obj.value, None)
        self.assertEqual(obj.attrs, {})

    def test_split_id(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        cls, ident, parent_id = gen.split_id('test')
        self.assertEqual(cls.__name__, 'test')
        self.assertEqual(ident, None)
        self.assertEqual(parent_id, '')

        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        cls, ident, parent_id = gen.split_id('Exercise:test:qcm:0')
        self.assertEqual(cls.__name__, 'qcm')
        self.assertEqual(ident, 0)
        self.assertEqual(parent_id, 'Exercise:test')

        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        cls, ident, parent_id = gen.split_id('Exercise:test:qcm:0:choice:1')
        self.assertEqual(cls.__name__, 'choice')
        self.assertEqual(ident, 1)
        self.assertEqual(parent_id, 'Exercise:test:qcm:0')

    def test_split_id_v2(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        res = gen.split_id_v2('Exercise:test:_qcm_mqm:0:qcm')
        self.assertEqual(len(res), 4)
        self.assertEqual(res[0]['index'], None)
        self.assertEqual(res[0]['id'], 'Exercise')
        self.assertEqual(res[0]['elt'].tagname, 'Exercise')

        self.assertEqual(res[1]['index'], None)
        self.assertEqual(res[1]['id'], 'Exercise:test')
        self.assertEqual(res[1]['elt'].tagname, 'test')

        self.assertEqual(res[2]['index'], 0)
        self.assertEqual(res[2]['id'], 'Exercise:test:_qcm_mqm')
        self.assertEqual(res[2]['elt'].tagname, '_qcm_mqm')

        self.assertEqual(res[3]['index'], None)
        self.assertEqual(res[3]['id'], 'Exercise:test:_qcm_mqm:0:qcm')
        self.assertEqual(res[3]['elt'].tagname, 'qcm')
        
    def test_split_id_v2_dtd_3(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_3)
        res = gen.split_id_v2('Exercise:test:0:qcm')
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0]['index'], None)
        self.assertEqual(res[0]['id'], 'Exercise')
        self.assertEqual(res[0]['elt'].tagname, 'Exercise')

        self.assertEqual(res[1]['index'], 0)
        self.assertEqual(res[1]['id'], 'Exercise:test')
        self.assertEqual(res[1]['elt'].tagname, 'test')

        self.assertEqual(res[2]['index'], None)
        self.assertEqual(res[2]['id'], 'Exercise:test:0:qcm')
        self.assertEqual(res[2]['elt'].tagname, 'qcm')

    def test_split_id_not_valid(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        try:
            cls, ident, parent_id = gen.split_id('plop')
            assert False
        except Exception, e:
            self.assertEqual(str(e), 'plop is not a valid element')

    def test_get_previous_element_for_jstree(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        expected = [('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:question')
        self.assertEqual(result, expected)

        expected = [('#tree_Exercise:test:0:question', 'after'),
                    ('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:_qcm_mqm:1:qcm')
        self.assertEqual(result, expected)
        
        expected = [('#tree_Exercise:test:0:_qcm_mqm:1:qcm', 'after'),
                    ('#tree_Exercise:test:0:_qcm_mqm:1:mqm', 'after'),
                    ('#tree_Exercise:test:0:question', 'after'),
                    ('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:_qcm_mqm:2:qcm')
        self.assertEqual(result, expected)

        expected = [('.tree_Exercise:test:0:_qcm_mqm', 'after'),
                    ('#tree_Exercise:test:0:question', 'after'),
                    ('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:comments')
        self.assertEqual(result, expected)

        expected = [('#tree_Exercise:test:0:comments', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:comments:comment:1')
        self.assertEqual(result, expected)

        expected = [('#tree_Exercise:test:0:comments:comment:1', 'after'),
                    ('#tree_Exercise:test:0:comments', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:comments:comment:2')
        self.assertEqual(result, expected)

    def test_get_previous_element_for_jstree_dtd_3(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_3)
        expected = [('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:question')
        self.assertEqual(result, expected)

        expected = [('#tree_Exercise:test:0:question', 'after'),
                    ('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:qcm')
        self.assertEqual(result, expected)

        expected = [
                    ('#tree_Exercise:test:0:mqm', 'after'),
                    ('#tree_Exercise:test:0:qcm', 'after'),
                    ('#tree_Exercise:test:0:question', 'after'),
                    ('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:comments')
        self.assertEqual(result, expected)

        expected = [('#tree_Exercise:test:0:comments', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:comments:comment:1')
        self.assertEqual(result, expected)

        expected = [('#tree_Exercise:test:0:comments:comment:1', 'after'),
                    ('#tree_Exercise:test:0:comments', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:comments:comment:2')
        self.assertEqual(result, expected)

    def test_get_previous_element_for_jstree_dtd_4(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_4)
        expected = [('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:question')
        self.assertEqual(result, expected)

        expected = [('#tree_Exercise:test:0:question', 'after'),
                    ('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:qcm')
        self.assertEqual(result, expected)

        expected = [
                    ('#tree_Exercise:test:0:mqm', 'after'),
                    ('#tree_Exercise:test:0:qcm', 'after'),
                    ('#tree_Exercise:test:0:question', 'after'),
                    ('#tree_Exercise:test:0', 'inside')]
        result = gen.get_previous_element_for_jstree(
            'Exercise:test:0:_positive-comments_negative-comments:1:comment')
        self.assertEqual(result, expected)
