#!/usr/bin/env python

from io import StringIO
from unittest import TestCase
from xmltool.testbase import BaseTest
import json
from lxml import etree, html
from xmltool import dtd_parser, dtd
from xmltool.elements import (
    EmptyElement,
    escape_attr,
)
from xmltool.utils import unflatten_params
from ..test_dtd_parser import (
    MOVIE_DTD,
    MOVIE_XML_TITANIC_COMMENTS,
)

_marker = object()


class ElementTester(BaseTest):
    # Should be defined in the inheritance classes
    dtd_str = None
    xml = None
    expected_xml = None
    submit_data = None

    def test_to_xml(self):
        if self.__class__ == ElementTester:
            return
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        tree = obj.to_xml()
        xml_str = etree.tostring(
            tree.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8',
        )
        if self.expected_xml:
            self.assertEqual(xml_str, self.expected_xml)
        else:
            self.assertEqual(xml_str, self.xml)

    def test_load_from_dict(self):
        if self.__class__ == ElementTester:
            return
        data = unflatten_params(self.submit_data)
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_dict(data)
        tree = obj.to_xml()
        xml_str = etree.tostring(
            tree.getroottree(),
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8',
        )
        if self.expected_xml:
            self.assertEqual(xml_str, self.expected_xml)
        else:
            self.assertEqual(xml_str, self.xml)


class TestElementPCDATA(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Hello world</text>
</texts>
'''
    submit_data = {'texts:text:_value': 'Hello world'}


    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['text'].text, 'Hello world')
        self.assertEqual(obj['text'].sourceline, 3)

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)

        cls = classes['texts']
        obj = cls()
        text = obj.add('text')
        self.assertEqual(text.tagname, 'text')
        self.assertEqual(obj['text'], text)

    def test_add_bad_child(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        try:
            obj.add('unexisiting')
            assert 0
        except Exception as e:
            self.assertEqual(str(e), 'Invalid child unexisiting')


class TestElementPCDATAEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''
    submit_data = {}


class TestElementPCDATANotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Hello world</text>
</texts>
'''

    submit_data = {'texts:text:_value': 'Hello world'}


class TestElementPCDATAEmptyNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    submit_data = {}


class TestElementPCDATAEmptyNotRequiredDefined(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text?)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''

    submit_data = {'texts:text:_value': ''}


class TestListElement(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Tag 1</text>
  <text>Tag 2</text>
</texts>
'''

    submit_data = {
        'texts:list__text:0:text:_value': 'Tag 1',
        'texts:list__text:1:text:_value': 'Tag 2',
    }

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        text1 = obj.add('text')
        self.assertEqual(text1.tagname, 'text')
        self.assertEqual(len(obj['text']), 1)
        self.assertEqual(obj['text'][0], text1)

        text2 = obj.add('text')
        self.assertEqual(text2.tagname, 'text')
        self.assertEqual(len(obj['text']), 2)
        self.assertEqual(obj['text'][1], text2)

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['text'][0].text, 'Tag 1')
        self.assertEqual(obj['text'][0].sourceline, 3)
        self.assertEqual(obj['text'][1].text, 'Tag 2')
        self.assertEqual(obj['text'][1].sourceline, 4)


class TestListElementEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text></text>
</texts>
'''

    submit_data = {}


class TestListElementNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>Tag 1</text>
  <text>Tag 2</text>
</texts>
'''

    submit_data = {
        'texts:list__text:0:text:_value': 'Tag 1',
        'texts:list__text:1:text:_value': 'Tag 2',
    }


class TestListElementEmptyNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text*)>
        <!ELEMENT text (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''

    submit_data = {}


class TestListElementElementEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text+)>
        <!ELEMENT text (subtext)>
        <!ELEMENT subtext (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''
    expected_xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>
    <subtext></subtext>
  </text>
</texts>
'''

    submit_data = {}


choice_str_to_html = [
    ('texts',
     '<div class="panel panel-default texts" id="texts">'
     '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
     '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
     '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
     '<select class="btn-add">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:text2">text2</option>'
     '</select>'
     '</div></div>'
    ),
    ('texts:text1',
     '<div id="texts:text1" class="xt-container-text1">'
     '<label>text1</label>'
     '<span class="btn-external-editor" '
     'ng-click="externalEditor(this)"></span>'
     '<select class="btn-add hidden">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:text2">text2</option>'
     '</select>'
     '<a class="btn-delete" data-target="#texts:text1" title="Delete"></a>'
     '<a data-comment-name="texts:text1:_comment" class="btn-comment" '
     'title="Add comment"></a>'
     '<textarea class="form-control text1" name="texts:text1:_value" rows="1"></textarea>'
     '</div>'
    )
]

choice_js_selector = [
        [],
        [('inside', '#tree_texts')],
    ]


class TestElementChoice(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1|text2)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
</texts>
'''

    submit_data = {
        'texts:text1:_value': 'Tag 1',
    }

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        text1 = obj.add('text1')
        self.assertEqual(text1.tagname, 'text1')
        self.assertEqual(obj['text1'], text1)

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['text1'].text, 'Tag 1')
        self.assertEqual(obj['text1'].sourceline, 3)
        self.assertFalse(hasattr(obj, 'text2'))

        xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text2>Tag 2</text2>
</texts>'''
        root = etree.fromstring(xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['text2'].text, 'Tag 2')
        self.assertEqual(obj['text2'].sourceline, 3)
        self.assertFalse(hasattr(obj, 'text1'))


class TestElementChoiceEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1|text2)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''

    submit_data = {}


class TestElementChoiceNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1|text2)?>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
</texts>
'''

    submit_data = {
        'texts:text1:_value': 'Tag 1',
    }


class TestElementChoiceEmptyNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1|text2)?>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''

    submit_data = {}


choicelist_str_to_html = [
    ('texts',
     '<div class="panel panel-default texts" id="texts">'
     '<div class="panel-heading"><span data-toggle="collapse" href="#collapse-texts">texts'
     '<a data-comment-name="texts:_comment" class="btn-comment" title="Add comment"></a>'
     '</span></div><div class="panel-body panel-collapse collapse in" id="collapse-texts">'
     '<div class="list-container">'
     '<select class="btn-add btn-list">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:list__text1_text2:0:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:list__text1_text2:0:text2">text2</option>'
     '</select>'
     '</div>'
     '</div></div>'
    ),
    ('texts:list__text1_text2:0:text1',
     '<select class="btn-add btn-list">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:list__text1_text2:0:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:list__text1_text2:0:text2">text2</option>'
     '</select>'
     '<div id="texts:list__text1_text2:0:text1" class="xt-container-text1">'
     '<label>text1</label>'
     '<span class="btn-external-editor" '
     'ng-click="externalEditor(this)"></span>'
     '<a class="btn-delete btn-list" '
     'data-target="#texts:list__text1_text2:0:text1" title="Delete"></a>'
     '<a data-comment-name="texts:list__text1_text2:0:text1:_comment" '
     'class="btn-comment" title="Add comment"></a>'
     '<textarea class="form-control text1" name="texts:list__text1_text2:0:text1:_value" '
     'rows="1"></textarea>'
     '</div>'
    ),
    ('texts:list__text1_text2:10:text1',
     '<select class="btn-add btn-list">'
     '<option>New text1/text2</option>'
     '<option class="xt-option-text1" value="texts:list__text1_text2:10:text1">text1</option>'
     '<option class="xt-option-text2" value="texts:list__text1_text2:10:text2">text2</option>'
     '</select>'
     '<div id="texts:list__text1_text2:10:text1" class="xt-container-text1">'
     '<label>text1</label>'
     '<span class="btn-external-editor" '
     'ng-click="externalEditor(this)"></span>'
     '<a class="btn-delete btn-list" '
     'data-target="#texts:list__text1_text2:10:text1" title="Delete"></a>'
     '<a data-comment-name="texts:list__text1_text2:10:text1:_comment" '
     'class="btn-comment" title="Add comment"></a>'
     '<textarea class="form-control text1" name="texts:list__text1_text2:10:text1:_value" '
     'rows="1"></textarea>'
     '</div>'
    )
]

choice_list_js_selector = [
        [],
        [('inside', '#tree_texts')],
    ]

class TestElementChoiceList(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
  <text2>Tag 2</text2>
  <text1>Tag 3</text1>
</texts>
'''

    submit_data = {
        'texts:list__text1_text2:0:text1:_value': 'Tag 1',
        'texts:list__text1_text2:1:text2:_value': 'Tag 2',
        'texts:list__text1_text2:2:text1:_value': 'Tag 3',
    }

    def test_add(self):
        dtd_dict = dtd_parser.dtd_to_dict_v2(self.dtd_str)
        classes = dtd_parser._create_classes(dtd_dict)
        cls = classes['texts']
        obj = cls()
        text1 = obj.add('text1')
        self.assertEqual(obj['list__text1_text2'], [text1])
        text2 = obj.add('text2')
        self.assertEqual(obj['list__text1_text2'], [text1, text2])

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.tagname, 'texts')
        self.assertEqual(obj.sourceline, 2)
        self.assertEqual(obj['list__text1_text2'][0].text, 'Tag 1')
        self.assertEqual(obj['list__text1_text2'][0].sourceline, 3)
        self.assertEqual(obj['list__text1_text2'][1].text, 'Tag 2')
        self.assertEqual(obj['list__text1_text2'][1].sourceline, 4)
        self.assertEqual(obj['list__text1_text2'][2].text, 'Tag 3')
        self.assertEqual(obj['list__text1_text2'][2].sourceline, 5)


class TestElementChoiceListEmpty(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''

    submit_data = {}


class TestElementChoiceListNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts ((text1|text2)+)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>Tag 1</text1>
  <text2>Tag 2</text2>
  <text1>Tag 3</text1>
</texts>
'''

    submit_data = {
        'texts:list__text1_text2:0:text1:_value': 'Tag 1',
        'texts:list__text1_text2:1:text2:_value': 'Tag 2',
        'texts:list__text1_text2:2:text1:_value': 'Tag 3',
    }


class TestElementChoiceListEmptyNotRequired(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts ((text1|text2)*)>
        <!ELEMENT text1 (#PCDATA)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts/>
'''

    submit_data = {}


class TestListElementOfList(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text1*)>
        <!ELEMENT text1 (text2+)>
        <!ELEMENT text2 (#PCDATA)>
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text1>
    <text2>text2-1</text2>
    <text2>text2-2</text2>
  </text1>
  <text1>
    <text2>text2-3</text2>
  </text1>
</texts>
'''

    submit_data = {
        'texts:list__text1:0:text1:list__text2:0:text2:_value': 'text2-1',
        'texts:list__text1:0:text1:list__text2:1:text2:_value': 'text2-2',
        'texts:list__text1:1:text1:list__text2:0:text2:_value': 'text2-3',
    }


class TestElementWithAttributes(ElementTester):
    dtd_str = u'''
        <!ELEMENT texts (text, text1*)>
        <!ELEMENT text (#PCDATA)>
        <!ELEMENT text1 (#PCDATA)>

        <!ATTLIST texts idtexts ID #IMPLIED>
        <!ATTLIST texts name CDATA "">
        <!ATTLIST text idtext ID #IMPLIED>
        <!ATTLIST text1 idtext1 CDATA "">
        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts idtexts="id_texts" name="my texts">
  <text idtext="id_text">Hello world</text>
  <text1 idtext1="id_text1_1">My text 1</text1>
  <text1>My text 2</text1>
</texts>
'''

    submit_data = {
        'texts:_attrs:idtexts': 'id_texts',
        'texts:_attrs:name': 'my texts',
        'texts:text:_value': 'Hello world',
        'texts:text:_attrs:idtext': 'id_text',
        'texts:list__text1:0:text1:_value': 'My text 1',
        'texts:list__text1:0:text1:_attrs:idtext1': 'id_text1_1',
        'texts:list__text1:1:text1:_value': 'My text 2',
    }

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj._attribute_names, ['idtexts', 'name'])
        self.assertEqual(obj.attributes, {
            'idtexts': 'id_texts',
            'name': 'my texts',
        })
        self.assertEqual(obj['text']._attribute_names, ['idtext'])
        self.assertEqual(obj['text'].attributes, {
            'idtext': 'id_text',
        })
        self.assertEqual(obj['text1'][0]._attribute_names, ['idtext1'])
        self.assertEqual(obj['text1'][0].attributes, {
            'idtext1': 'id_text1_1',
        })
        self.assertEqual(obj['text1'][1]._attribute_names, ['idtext1'])
        self.assertEqual(obj['text1'][1].attributes, None)

    def test_walk(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = [e for e in obj.walk()]
        expected = [obj['text']] + obj['text1']
        self.assertEqual(lis, expected)


class TestElementComments(ElementTester):
    dtd_str = MOVIE_DTD
    xml = MOVIE_XML_TITANIC_COMMENTS

    submit_data = {
        'Movie:_comment': ' Movie comment ',
        'Movie:name:_value': 'Titanic',
        'Movie:name:_comment': ' name comment ',
        'Movie:year:_value': '1997',
        'Movie:year:_comment': ' year comment ',
        'Movie:directors:_comment': ' directors comment ',
        'Movie:directors:list__director:0:director:_comment': ' director comment ',
        'Movie:directors:list__director:0:director:name:_value': 'Cameron',
        'Movie:directors:list__director:0:director:name:_comment': ' director name comment ',
        'Movie:directors:list__director:0:director:firstname:_value': 'James',
        'Movie:directors:list__director:0:director:firstname:_comment': ' director firstname comment ',
        'Movie:actors:_comment': ' actors comment ',
        'Movie:actors:list__actor:0:actor:_comment': ' actor 1 comment ',
        'Movie:actors:list__actor:0:actor:name:_value': 'DiCaprio',
        'Movie:actors:list__actor:0:actor:name:_comment': ' actor 1 name comment ',
        'Movie:actors:list__actor:0:actor:firstname:_value': 'Leonardo',
        'Movie:actors:list__actor:0:actor:firstname:_comment': ' actor 1 firstname comment ',
        'Movie:actors:list__actor:1:actor:_comment': ' actor 2 comment ',
        'Movie:actors:list__actor:1:actor:name:_value': 'Winslet',
        'Movie:actors:list__actor:1:actor:name:_comment': ' actor 2 name comment ',
        'Movie:actors:list__actor:1:actor:firstname:_value': 'Kate',
        'Movie:actors:list__actor:1:actor:firstname:_comment': ' actor 2 firstname comment ',
        'Movie:actors:list__actor:2:actor:_comment': ' actor 3 comment ',
        'Movie:actors:list__actor:2:actor:name:_value': 'Zane',
        'Movie:actors:list__actor:2:actor:name:_comment': ' actor 3 name comment ',
        'Movie:actors:list__actor:2:actor:firstname:_value': 'Billy',
        'Movie:actors:list__actor:2:actor:firstname:_comment': ' actor 3 firstname comment ',
        'Movie:resume:_comment': ' resume comment ',
        'Movie:resume:_value': '\n     Resume of the movie\n  ',
        'Movie:list__critique:0:critique:_comment': ' critique 1 comment ',
        'Movie:list__critique:0:critique:_value': 'critique1',
        'Movie:list__critique:1:critique:_comment': ' critique 2 comment ',
        'Movie:list__critique:1:critique:_value': 'critique2',
    }

    def test_load_from_xml(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        self.assertEqual(obj.sourceline, 3)
        self.assertEqual(obj['name'].text, 'Titanic')
        self.assertEqual(obj['name'].comment, ' name comment ')
        self.assertEqual(obj['name'].sourceline, 5)
        self.assertEqual(obj['resume'].text, '\n     Resume of the movie\n  ')
        self.assertEqual(obj['resume'].comment, ' resume comment ')
        self.assertEqual(obj['resume'].sourceline, 43)
        self.assertEqual(obj['year'].text, '1997')
        self.assertEqual(obj['year'].comment, ' year comment ')
        self.assertEqual(obj['year'].sourceline, 7)
        self.assertEqual([c.text for c in obj['critique']], ['critique1', 'critique2'])
        self.assertEqual(obj['critique'][0].comment, ' critique 1 comment ')
        self.assertEqual(obj['critique'][1].comment, ' critique 2 comment ')
        self.assertEqual(len(obj['actors']['actor']), 3)
        self.assertEqual(len(obj['directors']['director']), 1)
        self.assertEqual(obj['actors'].comment, ' actors comment ')
        self.assertEqual(obj['actors']['actor'][0].sourceline, 21)
        self.assertEqual(obj['actors']['actor'][0].comment, ' actor 1 comment ')
        self.assertEqual(obj['actors']['actor'][0]['name'].text, 'DiCaprio')
        self.assertEqual(obj['actors']['actor'][0]['name'].comment,
                         ' actor 1 name comment ')
        self.assertEqual(obj['actors']['actor'][0]['name'].sourceline, 23)
        self.assertEqual(obj['actors']['actor'][0]['firstname'].text, 'Leonardo')
        self.assertEqual(obj['actors']['actor'][0]['firstname'].comment,
                         ' actor 1 firstname comment ')
        self.assertEqual(obj['actors']['actor'][1].comment, ' actor 2 comment ')
        self.assertEqual(obj['actors']['actor'][1]['name'].text, 'Winslet')
        self.assertEqual(obj['actors']['actor'][1]['name'].comment,
                         ' actor 2 name comment ')
        self.assertEqual(obj['actors']['actor'][1]['firstname'].text, 'Kate')
        self.assertEqual(obj['actors']['actor'][1]['firstname'].comment,
                         ' actor 2 firstname comment ')
        self.assertEqual(obj['actors']['actor'][2].comment,
                         ' actor 3 comment ')
        self.assertEqual(obj['actors']['actor'][2]['name'].text, 'Zane')
        self.assertEqual(obj['actors']['actor'][2]['name'].comment,
                         ' actor 3 name comment ')
        self.assertEqual(obj['actors']['actor'][2]['firstname'].text, 'Billy')
        self.assertEqual(obj['actors']['actor'][2]['firstname'].comment,
                         ' actor 3 firstname comment ')
        self.assertEqual(obj['directors'].comment, ' directors comment ')
        self.assertEqual(obj['directors']['director'][0]['name'].text, 'Cameron')
        self.assertEqual(obj['directors']['director'][0]['name'].comment,
                         ' director name comment ')
        self.assertEqual(obj['directors']['director'][0]['firstname'].text, 'James')
        self.assertEqual(obj['directors']['director'][0]['firstname'].comment,
                         ' director firstname comment ')


class TestWalk(TestCase):
    dtd_str = u'''
        <!ELEMENT texts (text, text1*)>
        <!ELEMENT text (t1|t2)>
        <!ELEMENT text1 (text11, text)>
        <!ELEMENT t1 (#PCDATA)>
        <!ELEMENT t2 (#PCDATA)>
        <!ELEMENT text11 (#PCDATA)>

        '''
    xml = b'''<?xml version='1.0' encoding='UTF-8'?>
<texts>
  <text>
    <t1>t1</t1>
  </text>
  <text1>
    <text11>My text 1</text11>
    <text>
      <t1>t11</t1>
    </text>
  </text1>
  <text1>
    <text11>My text 2</text11>
    <text>
      <t2>t11</t2>
    </text>
  </text1>
</texts>
'''

    def test_walk(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = [e for e in obj.walk()]
        expected = [
            obj['text'],
            obj['text']['t1'],
            obj['text1'][0],
            obj['text1'][0]['text11'],
            obj['text1'][0]['text'],
            obj['text1'][0]['text']['t1'],
            obj['text1'][1],
            obj['text1'][1]['text11'],
            obj['text1'][1]['text'],
            obj['text1'][1]['text']['t2'],
        ]
        self.assertEqual(lis, expected)

    def test_findall(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()
        obj.load_from_xml(root)
        lis = obj.findall('text11')
        expected = [
            obj['text1'][0]['text11'],
            obj['text1'][1]['text11'],
        ]
        self.assertEqual(lis, expected)

        lis = obj.findall('t1')
        expected = [
            obj['text']['t1'],
            obj['text1'][0]['text']['t1'],
        ]
        self.assertEqual(lis, expected)

        lis = obj['text1'].findall('text11')
        expected = [
            obj['text1'][0]['text11'],
            obj['text1'][1]['text11'],
        ]
        self.assertEqual(lis, expected)


class TestXPath(TestCase):
    dtd_str = MOVIE_DTD
    xml = MOVIE_XML_TITANIC_COMMENTS

    def test_xpath(self):
        root = etree.fromstring(self.xml)
        dic = dtd.DTD(StringIO(self.dtd_str)).parse()
        obj = dic[root.tag]()

        try:
            res = obj.xpath('Movie')
            assert(False)
        except Exception as e:
            self.assertEqual(
                str(e),
                'The xpath is only supported '
                'when the object is loaded from XML')

        obj.load_from_xml(root)
        # Since obj is Movie it didn't match
        res = obj.xpath('Movie')
        self.assertEqual(len(res), 0)

        res = obj.xpath('/Movie')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], obj)

        res = obj.xpath('directors')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], obj['directors'])
        res = obj.xpath('//actors/actor')
        self.assertEqual(len(res), 3)
        self.assertEqual(res, obj['actors']['actor'])

        actor_obj = obj['actors']['actor'][0]
        res = actor_obj.xpath('/Movie')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], obj)

        res = actor_obj.xpath('..')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], actor_obj._parent_obj._parent_obj)
