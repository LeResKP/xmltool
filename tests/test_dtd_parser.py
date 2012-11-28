from unittest import TestCase
import xmltools.dtd_parser as dtd_parser
import xmltools.forms as forms
from lxml import etree
import __builtin__
import os


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


class test_DtdSubElement(TestCase):

    def test_init(self):
        text = 'actor'
        elt = dtd_parser.DtdSubElement(text)
        self.assertEqual(elt.name, 'actor')
        self.assertTrue(elt.required)
        self.assertFalse(elt.islist)

    def test_init_no_required(self):
        text = 'actor?'
        elt = dtd_parser.DtdSubElement(text)
        self.assertEqual(elt.name, 'actor')
        self.assertFalse(elt.required)
        self.assertFalse(elt.islist)

    def test_init_list(self):
        text = 'actor*'
        elt = dtd_parser.DtdSubElement(text)
        self.assertEqual(elt.name, 'actor')
        self.assertFalse(elt.required)
        self.assertTrue(elt.islist)

    def test_init_list_required(self):
        text = 'actor+'
        elt = dtd_parser.DtdSubElement(text)
        self.assertEqual(elt.name, 'actor')
        self.assertTrue(elt.required)
        self.assertTrue(elt.islist)

    def test_init_conditional(self):
        text = '(qcm|mqm)*'
        elt = dtd_parser.DtdSubElement(text)
        self.assertEqual(elt.name, '(qcm|mqm)')
        self.assertFalse(elt.required)
        self.assertTrue(elt.islist)
        qcm, mqm = elt.conditional_names
        self.assertEqual(qcm.name, 'qcm')
        self.assertTrue(qcm.required)
        self.assertTrue(qcm.islist)
        self.assertEqual(mqm.name, 'mqm')
        self.assertTrue(mqm.required)
        self.assertTrue(mqm.islist)

    def test_repr(self):
        text = 'actor*'
        elt = dtd_parser.DtdSubElement(text)
        self.assertTrue(repr(elt))


class test_DtdElement(TestCase):

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
            self.assertEqual(str(e), "Can't set value to non DtdTextElement")

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
            self.assertTrue(issubclass(gen.dtd_classes[key],
                dtd_parser.DtdTextElement))
        cls = gen.dtd_classes['Movie']
        self.assertEqual(cls.__name__, 'Movie')
        self.assertEqual(len(cls._elements), 7)
        for (key, expected) in [('directors', 1), 
                                ('actors', 1), 
                                ('director', 2),
                                ('actor', 2)]:
            cls = gen.dtd_classes[key]
            self.assertEqual(len(cls._elements), expected)

    def test_get_key_from_xml(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        text = 'actor+'
        elt = dtd_parser.DtdSubElement(text)
        key = gen.get_key_from_xml(elt, None)
        self.assertEqual(key, 'actor')

        text = '(qcm|mqm)*'
        elt = dtd_parser.DtdSubElement(text)
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
        elt = dtd_parser.DtdSubElement(text)
        root = etree.Element('root')
        root.attrib['id'] = '1'
        gen.set_attrs_to_obj(elt, root)
        self.assertEqual(elt.attrs, {})

        elt._attrs = [('id', 'ID', '#IMPLIED'),
                      ('name', 'ID', '#IMPLIED'),
                      ]
        gen.set_attrs_to_obj(elt, root)
        self.assertEqual(elt.attrs, root.attrib)

    def test_generate_obj(self):
        root = etree.fromstring(MOVIE_XML_TITANIC)
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        obj = gen.generate_obj(root)
        self.assertEqual(obj.name.value, 'Titanic')
        self.assertEqual(obj.resume.value, '\n     Resume of the movie\n  ')
        self.assertEqual(obj.year.value, '1997')
        self.assertEqual([c.value for c in obj.critique], ['critique1', 'critique2'])
        self.assertEqual(len(obj.actors.actor), 3)
        self.assertEqual(len(obj.directors.director), 1)
        self.assertEqual(obj.actors.actor[0].name.value, 'DiCaprio')
        self.assertEqual(obj.actors.actor[0].firstname.value, 'Leonardo')
        self.assertEqual(obj.actors.actor[1].name.value, 'Winslet')
        self.assertEqual(obj.actors.actor[1].firstname.value, 'Kate')
        self.assertEqual(obj.actors.actor[2].name.value, 'Zane')
        self.assertEqual(obj.actors.actor[2].firstname.value, 'Billy')
        self.assertEqual(obj.directors.director[0].name.value, 'Cameron')
        self.assertEqual(obj.directors.director[0].firstname.value, 'James')

    def test_get_key_from_obj(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        text = 'actor+'
        elt = dtd_parser.DtdSubElement(text)
        key = gen.get_key_from_obj(elt, None)
        self.assertEqual(key, 'actor')

        text = '(qcm|mqm)*'
        elt = dtd_parser.DtdSubElement(text)
        class FakeObject(object): pass
        o = FakeObject()
        key = gen.get_key_from_obj(elt, o)
        self.assertEqual(key, None)
        o.qcm = 'qcm'
        key = gen.get_key_from_obj(elt, o)
        self.assertEqual(key, 'qcm')

    def test_set_attrs_to_xml(self):
        gen = dtd_parser.Generator(dtd_str=MOVIE_DTD)
        text = 'actor+'
        elt = dtd_parser.DtdSubElement(text)
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
        s = etree.tostring(xml, pretty_print=True, xml_declaration=True)
        docinfo = root.getroottree().docinfo
        s = etree.tostring(
                xml, 
                pretty_print=True,
                xml_declaration=True,
                encoding=docinfo.encoding,
                doctype=docinfo.doctype)
        self.assertEqual(MOVIE_XML_TITANIC, s)


class TestGenerator2(TestCase):

    def test_dtd_classes(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD)
        self.assertEqual(len(gen.dtd_classes), 6)
        for key in ['question', 'choice']:
            self.assertTrue(issubclass(gen.dtd_classes[key],
                dtd_parser.DtdTextElement))
        for (key, nb_elements) in [('Exercise', 2),
                                ('test', 1), 
                                ('qcm', 1), 
                                ('mqm', 1)]:
            cls = gen.dtd_classes[key]
            self.assertEqual(len(cls._elements), nb_elements)
        cls = gen.dtd_classes['test']
        self.assertEqual(len(cls._elements[0].conditional_names), 2)

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


class TestGenerator3(TestCase):

    def test_dtd_classes(self):
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        self.assertEqual(len(gen.dtd_classes), 9)
        for key in ['question', 'choice', 'comment', 'number']:
            self.assertTrue(issubclass(gen.dtd_classes[key],
                dtd_parser.DtdTextElement))
        for (key, nb_elements) in [('Exercise', 2),
                                   ('test', 3), 
                                   ('qcm', 1), 
                                   ('mqm', 1),
                                   ('comments', 1)]:
            cls = gen.dtd_classes[key]
            self.assertEqual(len(cls._elements), nb_elements)
        cls = gen.dtd_classes['test']
        self.assertEqual(len(cls._elements[1].conditional_names), 2)

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
        self.assertEqual(len(test1.mqm), 2)
        self.assertEqual(getattr(test1, 'qcm', None), None)
        mqm1, mqm2 = test1.mqm
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
        self.assertEqual(len(test2.qcm), 2)
        self.assertEqual(getattr(test2, 'mqm', None), None)
        qcm1, qcm2 = test2.qcm
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
        del obj.test[0].mqm[0].choice
        xml = gen.obj_to_xml(obj)
        s = etree.tostring(xml, pretty_print=True)
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

    def test_generate_form_child_conditional(self):
        text = '(qcm|mqm)*'
        elt = dtd_parser.DtdSubElement(text)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_child(elt, parent=None)
        self.assertTrue(isinstance(field, forms.ConditionalContainer))
        self.assertEqual(len(field.possible_children), 2)
        for child in field.possible_children:
            self.assertTrue(isinstance(child, forms.GrowingContainer))

    def test_generate_form_child_no_list_text(self):
        text = 'comment'
        elt = dtd_parser.DtdSubElement(text)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_child(elt, parent=None)
        self.assertTrue(isinstance(field, forms.TextAreaField))

    def test_generate_form_child_no_list_no_text(self):
        text = 'comments'
        elt = dtd_parser.DtdSubElement(text)
        gen = dtd_parser.Generator(dtd_str=EXERCISE_DTD_2)
        field = gen.generate_form_child(elt, parent=None)
        self.assertTrue(isinstance(field, forms.Fieldset))
        self.assertEqual(field.key, 'comments')
        self.assertEqual(field.name, 'comments')
        self.assertEqual(field.legend, 'comments')
        self.assertEqual(len(field.children), 1)

    def test_generate_form_child_list_text(self):
        text = 'comment*'
        elt = dtd_parser.DtdSubElement(text)
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
        elt = dtd_parser.DtdSubElement(text)
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
        element = dtd_parser.DtdSubElement('text')
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
            'attrs': {'id': '1'}
        }
        obj = gen.dict_to_obj('choice', dic)
        self.assertTrue(isinstance(obj, gen.dtd_classes['choice']))
        self.assertEqual(obj.value, 'choice value')
        # Bad attribute name
        self.assertEqual(obj.attrs, {})

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


class TestHelperFunctions(TestCase):

    def test_is_http_url(self):
        url = 'file.txt'
        self.assertFalse(dtd_parser.is_http_url(url))
        url = 'http://file.txt'
        self.assertTrue(dtd_parser.is_http_url(url))
        url = 'https://file.txt'
        self.assertTrue(dtd_parser.is_http_url(url))

    def test_get_dtd_content(self):
        url = 'http://xml-tools.lereskp.fr/static/exercise.dtd'
        http_content = dtd_parser._get_dtd_content(url)
        url = 'tests/exercise.dtd'
        fs_content = dtd_parser._get_dtd_content(url)
        self.assertEqual(http_content, fs_content)

    def test_validate_xml(self):
        root = etree.fromstring(EXERCISE_XML)
        dtd_parser._validate_xml(root, EXERCISE_DTD)
        try:
            root = etree.fromstring(INVALID_EXERCISE_XML)
            dtd_parser._validate_xml(root, EXERCISE_DTD)
            assert 0
        except etree.DocumentInvalid:
            pass

    def test_get_obj(self):
        obj = dtd_parser.get_obj('tests/exercise.xml')
        self.assertEqual(obj.name, 'Exercise')
        try:
            obj = dtd_parser.get_obj('tests/exercise-notvalid.xml')
            assert 0
        except etree.DocumentInvalid:
            pass

        obj = dtd_parser.get_obj('tests/exercise-notvalid.xml',
                                 validate_xml=False)
        self.assertEqual(obj.name, 'Exercise')

    def test_write_obj(self):
        def FakeValidate(*args, **kwargs):
            raise etree.DocumentInvalid('Error')

        filename = 'tests/test.xml'
        self.assertFalse(os.path.isfile(filename))
        old_validate = dtd_parser._validate_xml
        try:
            obj = dtd_parser.get_obj('tests/exercise.xml')
            dtd_parser.write_obj(filename, obj)
            new_content = open(filename, 'r').read()
            old_content = open('tests/exercise.xml', 'r').read()
            self.assertEqual(new_content, old_content)

            dtd_parser._validate_xml = FakeValidate
            try:
                dtd_parser.write_obj(filename, obj)
                assert 0
            except etree.DocumentInvalid:
                pass
            dtd_parser.write_obj(filename, obj, validate_xml=False)
        finally:
            dtd_parser._validate_xml = old_validate
            if os.path.isfile(filename):
                os.remove(filename)

    def test_generate_form(self):
        html = dtd_parser.generate_form('tests/exercise.xml')
        self.assertTrue('<form method="POST">' in html)

        html = dtd_parser.generate_form('tests/exercise.xml',
                                        form_action='/action/submit')
        self.assertTrue('<form action="/action/submit" method="POST">' in html)

    def test_update_xml_file(self):
        filename = 'tests/test.xml'
        self.assertFalse(os.path.isfile(filename))
        try:
            data = {
                '_encoding': 'UTF-8',
                '_dtd_url': 'http://xml-tools.lereskp.fr/static/exercise.dtd',
                '_root_tag': 'Exercise',
                'Exercise.question': 'How are you?',
            }
            obj = dtd_parser.update_xml_file(filename, data)
            self.assertTrue(obj)
            result = open(filename, 'r').read()
            expected = '''<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Exercise PUBLIC "http://xml-tools.lereskp.fr/static/exercise.dtd" "http://xml-tools.lereskp.fr/static/exercise.dtd">
<Exercise>
  <number/>
</Exercise>
'''
            self.assertEqual(result, expected)
        finally:
            if os.path.isfile(filename):
                os.remove(filename)

