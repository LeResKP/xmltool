import re
from lxml import etree
import forms
import utils
from elements import (
    Element,
    SubElement,
    TextElement,
    ElementList,
    generate_id,
    MultipleElementList
)
import simplejson as json


comment_regex_compile = re.compile(r'<!--(.*?)-->', re.DOTALL)
tag_regex_compile = re.compile(r'<!(?P<type>[A-Z]+)(.*?)>', re.DOTALL)
element_regex_compile = re.compile(r' *(?P<name>[^( ]+) *\((?P<elements>.+)\)')
empty_element_regex_compile = re.compile(r' *(?P<name>[^( ]+) *(?P<elements>.+)')
entity_regex_compile = re.compile(r' *(?P<name>% *[^" ]+?) *"(?P<elements>.+)"')

UNDEFINED = '__undefined__'

def clear_value(value):
    """Clear the given value

    :param value: string to clean

    >>> clear_value('')
    ''
    >>> clear_value([])
    ''
    >>> clear_value('__undefined__')
    ''
    """
    if value == UNDEFINED:
        return ''
    return value or ''


def cleanup(value):
    for c in ['\n', '\r']:
        value = value.replace(c, '')
    return value


def parse_element(value):
    matchobj = element_regex_compile.match(value)
    if not matchobj:
        matchobj = empty_element_regex_compile.match(value)
    if not matchobj:
        raise Exception, 'Error parsing element %s' % value
    name, elements = matchobj.groups()
    if elements.count(')') != elements.count('('):
        raise Exception, 'Unbalanced parenthesis %s' % value
    return name, elements.replace(' ', '')


def parse_entity(value):
    matchobj = entity_regex_compile.match(value)
    if not matchobj:
        raise Exception, 'Error parsing entity %s' % value
    name, elements = matchobj.groups()
    return name.replace(' ', ''), elements.replace(' ', '')


def split_list(lis, cols):
    return [lis[i:i+cols] for i in range(0, len(lis), cols)]


def parse_attribute(value):
    for c in ['\n', '\r']:
        value = value.replace(c, '')
    lis = value.split(' ')
    lis = filter(bool, lis)
    assert (len(lis) - 1) % 3 == 0
    name = lis[0].strip()
    attributes = []
    for (attr_name, attr_type, require) in split_list(lis[1:], 3):
        attributes += [(attr_name.strip(), attr_type.strip(), require.strip())]
    return name, attributes


def dtd_to_dict(dtd):
    dtd_elements = {}
    dtd_entities = {}
    dtd_attributes = {}
    # Removed the comments
    res = comment_regex_compile.sub('', dtd)
    res = tag_regex_compile.findall(res)
    for element, value in res:
        clean_value = cleanup(value)
        if element == 'ELEMENT':
            tagname, elements = parse_element(clean_value)
            dtd_elements[tagname] = elements
        elif element == 'ENTITY':
            tagname, elements = parse_entity(clean_value)
            dtd_entities[tagname] = elements
        elif element == 'ATTLIST':
            tagname, attributes = parse_attribute(value)
            dtd_attributes.setdefault(tagname, []).extend(attributes)
        else:
            raise Exception, '%s is not supported' % element

    for tagname, elements in dtd_elements.items():
        for key, value in dtd_entities.items():
            elements = elements.replace('%s;' % key, value)
        dtd_elements[tagname] = elements

    return dtd_elements, dtd_attributes


def get_child(tagname, xml):
    for child in xml:
        if child.tag == tagname:
            return child
    return None


def get_children(tagname, xml):
    lis = []
    for child in xml:
        if child.tag == tagname:
            lis += [child]
    return lis


class Generator(object):
    """Helper class to manipulate the xml files.

    One of the following parameters should be given:
    :param dtd_str: dtd string
    :param dtd_dict: dtd already parsed in a dict
    :param dtd_file: dtd file
    """

    def __init__(self, dtd_str=None, dtd_url=None, encoding='UTF-8'):
        dtd_attrs = {}
        self._dtd_url = dtd_url
        self._encoding = encoding
        if dtd_url:
            dtd_str = utils.get_dtd_content(dtd_url)

        if dtd_str:
            dtd_dict, dtd_attrs = dtd_to_dict(dtd_str)
        else:
            raise ValueError, ('Make sure you only pass one of the following '
        'parameters: dtd_str, dtd_url')

        assert dtd_dict # We should have a non empty dtd_dict
        self.dtd = dtd_dict # The dtd as dict
        self.dtd_attrs = dtd_attrs # The dtd attributes as dict
        self.dtd_classes = {}
        self._create_classes()

    def _create_classes(self):
        """Populate self.dtd_classes with the classes corresponding to the dtd
        elements.
        The generated classes inherit from :class:`Element`
        """
        for tagname, elements in self.dtd.items():
            attrs = self.dtd_attrs.get(tagname) or []
            if elements in ['#PCDATA', 'EMPTY']:
                cls = type(tagname, (TextElement,), {
                    '_attrs': attrs,
                    'tagname': tagname,
                    'empty': (elements == 'EMPTY'),
                    '_generator': self})
                cls.__name__ = tagname
                self.dtd_classes[tagname] = cls
                continue
            splitted = elements.split(',')
            lis = [SubElement(element) for element in splitted]
            child_tagnames = []
            for elt in lis:
                if elt._conditional_names and not elt.islist:
                    child_tagnames += elt._conditional_names
                else:
                    child_tagnames += [elt.tagname]
            cls = type(tagname, (Element,), {
                '_sub_elements': lis,
                'child_tagnames': child_tagnames,
                '_attrs': attrs,
                'tagname': tagname,
                '_generator': self})
            cls.__name__ = tagname
            self.dtd_classes[tagname] = cls

    def create_obj(self, tagname):
        """Create the object correspoding to the given tagname

        :param tagname: the XML tag name
        :type tagname: str
        :return: The created object
        :rtype: :class: `Element` or :class: `TextElement`
        """
        if tagname not in self.dtd_classes:
            raise Exception("Tagname %s doesn't exist" % tagname)
        return self.dtd_classes[tagname]()

    def get_key_from_xml(self, element, obj):
        if not element._conditional_names:
            return element.tagname

        for tagname in element._conditional_names:
            if get_children(tagname, obj):
                return tagname
        return None

    def set_attrs_to_obj(self, obj, xml):
        for (attr_name, type_, require) in obj._attrs:
            value = xml.attrib.get(attr_name)
            if value:
                obj.attrs[attr_name] = value

    def set_comment_to_obj(self, obj, xml):
        comments = []
        previous = xml
        while True:
            previous = previous.getprevious()
            if previous is None:
                break
            if not isinstance(previous, etree._Comment):
                break
            comments += [previous.text]
        obj._comment = '\n'.join(comments) or None

    def get_sub_element(self, obj, xml):
        for element in obj._sub_elements:
            if not element._conditional_names:
                if element.tagname == xml.tag:
                    return element
            else:
                for tagname in element._conditional_names:
                    if tagname == xml.tag:
                        return element
        
    def generate_obj(self, xml):
        obj = self.create_obj(xml.tag)
        self.set_attrs_to_obj(obj, xml)
        self.set_comment_to_obj(obj, xml)
        obj.sourceline = xml.sourceline

        if isinstance(obj, TextElement):
            text = None
            if xml is not None:
                text = xml.text or UNDEFINED
            obj.value = text
            return obj

        for child in xml:
            element = self.get_sub_element(obj, child)
            if not element:
                # When it can arrived?
                continue
            if element.islist:
                newo = getattr(obj, element.tagname, None)
                if newo is None:
                    if element._conditional_names:
                        classes = [self.dtd_classes[name]
                                   for name in element._conditional_names]
                        newo = MultipleElementList(classes)
                    else:
                        newo = ElementList(self.dtd_classes[element.tagname])
                    setattr(obj, element.tagname, newo)
                newo.append(self.generate_obj(child))
            else:
                value = self.generate_obj(child)
                setattr(obj, child.tag, value)

        _marker = object()
        # Make sure all the property are defined.
        for element in obj._sub_elements:
            tagname = element.tagname
            if getattr(obj, tagname, _marker) == _marker:
                if element.islist:
                    if element._conditional_names:
                        classes = [self.dtd_classes[name]
                                   for name in element._conditional_names]
                        lis = MultipleElementList(classes)
                    else:
                        lis = ElementList(self.dtd_classes[tagname])

                    setattr(obj, tagname, lis)
                else:
                    if not element._conditional_names:
                        setattr(obj, tagname, None)
                    
        return obj

    def get_key_from_obj(self, element, obj):
        if not element._conditional_names or element.islist:
            return element.tagname

        for tagname in element._conditional_names:
            if getattr(obj, tagname, None):
                return tagname
        return None

    def set_attrs_to_xml(self, obj, xml):
        for attr_name, value in obj.attrs.items():
            xml.attrib[attr_name] = value

    def obj_to_xml(self, obj, xml=None):
        if not obj:
            return None

        if xml is None:
            # Create the root node
            tagname = obj.__class__.__name__
            xml = etree.Element(tagname)

        self.set_attrs_to_xml(obj, xml)

        if isinstance(obj, TextElement):
            if not obj.empty:
                xml.text = obj.value
            return xml

        for element in obj._sub_elements:
            key = self.get_key_from_obj(element, obj)
            if not key:
                continue
            if element.islist:
                value = getattr(obj, key, [])
                for v in value:
                    e = etree.Element(v.tagname)
                    self.obj_to_xml(v, e)
                    if len(e) or e.text or element.required:
                        if e.text:
                            e.text = clear_value(e.text)
                        if v._comment:
                            xml.append(etree.Comment(v._comment))
                        xml.append(e)
            else:
                value = getattr(obj, key, None)
                e = etree.Element(key)
                self.obj_to_xml(value, e)
                empty_elt = getattr(value, 'empty', False)
                if len(e) or e.text or element.required or empty_elt:
                    if e.text:
                        e.text = clear_value(e.text)
                    if value and value._comment:
                        xml.append(etree.Comment(value._comment))
                    xml.append(e)

        if obj._comment:
            xml.addprevious(etree.Comment(obj._comment))
        return xml

    def obj_to_jstree_dict(self, obj, prefix_id=None, index=None):
        """Generate a python dic from the given object which can be jsonified
        and can be used with jstree.
        """
        if not obj:
            return {}

        if isinstance(obj, TextElement):
            return obj.to_jstree_dict(clear_value(obj.value), prefix_id, index)

        dic =  obj.to_jstree_dict(prefix_id, index, skip_children=True)
        ident = dic['metadata']['id']
        children = []
        for element in obj._sub_elements:
            key = self.get_key_from_obj(element, obj)
            if not key:
                continue
            if element.islist:
                value = getattr(obj, key, [])
                if element._conditional_names:
                    tmp_ident = '%s:%s' % (ident, key)
                    for i, v in enumerate(value):
                        d = self.obj_to_jstree_dict(v, '%s:%i' % (tmp_ident, i+1))
                        if d:
                            children += [d]
                else:
                    for i, v in enumerate(value):
                        d = self.obj_to_jstree_dict(v, ident, (i + 1))
                        if d:
                            children += [d]
            else:
                value = getattr(obj, key, None)
                d = self.obj_to_jstree_dict(value, ident)
                if d:
                    children += [d]

        dic.update({'children': children})
        return dic

    def obj_to_jstree_json(self, *args, **kw):
        return json.dumps(self.obj_to_jstree_dict(*args, **kw))

    def generate_form_child(self, element, parent):
        if element._conditional_names:
            key=None
            if element.islist:
                key = element.tagname
                parent = forms.GrowingContainer(
                        key=key,
                        parent=parent,
                        required=element.required,
                        )
            field = forms.ConditionalContainer(name=key,
                                               parent=parent,
                                               required=element.required)
            for elt in element.conditional_sub_elements:
                field.possible_children += [self.generate_form_child(elt,
                                                                     field)]
            if element.islist:
                parent.child = field
                return parent
            return field

        key = element.tagname
        sub_cls = self.dtd_classes[key]
        if element.islist:
            field = forms.GrowingContainer(
                    key=key,
                    parent=parent,
                    required=element.required,
                    )
            sub_field = forms.Fieldset(
                    key=key,
                    name=key,
                    parent=field,
                    legend=key,
                    required=element.required)

            result = self.generate_form_children(sub_cls, sub_field, element)
            if result:
                if type(result) != list:
                    field.child = result
                    result.parent = field
                    return field
                sub_field.children = result
            field.child = sub_field
        else:
            if issubclass(sub_cls, TextElement):
                return self.generate_form_children(sub_cls, parent, element)

            field = forms.Fieldset(
                    key=key,
                    name=key,
                    legend=key,
                    parent=parent,
                    required=element.required)
            result = self.generate_form_children(sub_cls, field, element)
            assert type(result) == list
            if result:
                field.children = result
        return field

    def generate_form_children(self, cls, parent, element):
        if issubclass(cls, TextElement):
            key = cls.tagname
            return forms.TextAreaField(
                key=key,
                name=key,
                label=key,
                parent=parent,
                required=element.required,
                )
        children = []
        for elt in cls._sub_elements:
            children += [self.generate_form_child(elt, parent)]

        return children

    def generate_form(self, root_tag, encoding='UTF-8', **kwargs):
        """Generate the HTML form for the given xml_filename.

        :param root_tag: the root tag of the form
        :type root_tag: str
        :param encoding: the encoding to use
        :type encoding: str
        :param kwargs: Some extra values passed to the form object.
        :type kwargs: dict
        """
        cls = self.dtd_classes[root_tag]
        kwargs['_dtd_url'] = self._dtd_url
        kwargs['_encoding'] = self._encoding
        parent = forms.FormField(
            legend=cls.tagname, name=cls.tagname,  **kwargs)
        parent.children += self.generate_form_children(cls, parent, None)
        return parent

    def get_key_from_dict(self, element, dic):
        if not element._conditional_names or element.islist:
            return element.tagname

        for tagname in element._conditional_names:
            if tagname in dic:
                return tagname
        return None

    def dict_to_obj(self, root_tag, dic, required=True):
        if not dic:
            return None

        obj = self.create_obj(root_tag)
        attrs = dic.get('attrs') or {}
        for (attr_name, type_, require) in obj._attrs:
            if attr_name in attrs:
                obj.attrs[attr_name] = attrs[attr_name]

        obj._comment = dic.get('_comment') or None

        if isinstance(obj, TextElement):
            value = dic.get('value')
            if value == '':
                # We want to make sure we will keep the empty tags added by the
                # user
                value = UNDEFINED
            obj.value = value
            return obj

        isempty = True
        for element in obj._sub_elements:
            key = self.get_key_from_dict(element, dic)
            if not key:
                continue
            value = dic.get(key)
            if element.islist:
                value = value or []
                assert isinstance(value, list)
                if element._conditional_names:
                    classes = [self.dtd_classes[name]
                               for name in element._conditional_names]
                    lis = MultipleElementList(classes)
                    for v in value:
                        ks = v.keys()
                        assert len(ks) == 1, ks
                        k = ks[0]
                        subv = v[k]
                        sub_obj = self.dict_to_obj(k, subv, element.required)
                        if sub_obj:
                            lis += [sub_obj]
                    setattr(obj, key, lis)
                else:
                    lis = ElementList(self.dtd_classes[key])
                    for v in value:
                        sub_obj = self.dict_to_obj(key, v, element.required)
                        if sub_obj:
                            lis += [sub_obj]
                    setattr(obj, key, lis)
                isempty = False
            else:
                res = self.dict_to_obj(key, value, element.required)
                if (element.required and required) or res:
                    setattr(obj, key, res)
                    isempty=False
        if isempty:
            return None
        return obj

    def split_id(self, ident):
        """Split the given ident to find the right class, the index (may be
        None) and the parent id.

        :param ident: HTML identifier like (Excercise:test:choice:1)
        :type ident: str
        :return: cls, index, parent_id
        :rtype: tuple
        """
        splitted = ident.split(':')
        eltname = splitted.pop()
        index = utils.to_int(eltname)
        if index is not None:
            eltname = splitted.pop()

        if eltname not in self.dtd_classes:
            raise Exception('%s is not a valid element' % eltname)

        cls = self.dtd_classes[eltname]
        return cls, index, ':'.join(splitted)

    def split_id_v2(self, ident):
        splitted = ident.split(':')
        # splitted.reverse()
        root_elt = self.dtd_classes[splitted.pop(0)]
        res = [{
            'elt': root_elt,
            'index': None,
        }]
        for eltname in splitted:
            last_elt = res[-1]['elt']
            index = utils.to_int(eltname)
            if index is not None:
                res[-1]['index'] = index
                continue
            if isinstance(last_elt, SubElement):
                elts = last_elt.conditional_sub_elements
            else:
                elts = last_elt._sub_elements
            for elt in elts:
                eltnames = []
                if elt._conditional_names:
                    eltnames = elt._conditional_names
                if eltname == elt.tagname or eltname in eltnames:
                    if eltname in self.dtd_classes:
                        res += [{
                            'elt': self.dtd_classes[eltname],
                            'index': None,
                        }]
                    else:
                        res += [{
                            'elt': elt,
                            'index': None,
                        }]
                    break

        parent_id = ''
        for dic in res:
            if parent_id != '':
                parent_id += ':'
            parent_id += dic['elt'].tagname
            dic['id'] = parent_id
            dic['id_with_index'] = parent_id
            if dic['index'] is not None:
                dic['id_with_index'] = '%s:%i' % (parent_id, dic['index'])
                parent_id += ':%i' % dic['index']
        return res

    def get_previous_element_for_jstree(self, ident):
        """Find the previous element from the given ident. We also get the
        position where this element should be inserted in the tree.

        :param ident: HTML identifier like (Excercise:test:choice:1)
        :type ident: str
        :return: the list of the previous elements and the position
        :rtype: list of tuple
        """
        splitted = self.split_id_v2(ident)
        lis = []
        current = splitted.pop()
        cls = current['elt']

        parent = splitted.pop()
        parent_cls = parent['elt']

        if isinstance(parent_cls, SubElement):
            if parent_cls.islist and parent['index'] is not None and parent['index'] > 1:
                for i in range(parent['index'] -1, 0, -1):
                    new_ident = '#tree_%s' % parent['id']
                    new_ident += ':%i' % i
                    for e in parent_cls._conditional_names:
                        lis += [(new_ident + ':%s' % e, 'after')]

            current = parent
            cls = current['elt']
            parent = splitted.pop()
            parent_cls = parent['elt']

        tmp_list = []
        for elt in parent_cls._sub_elements:
            if elt._conditional_names:
                if cls.tagname in elt._conditional_names:
                    break
            if elt.tagname  == cls.tagname and not elt.islist:
                break

            if elt.islist:
                if elt.tagname == cls.tagname:
                    if not elt._conditional_names and current['index'] is not None and current['index'] > 1:
                        for i in range(1, current['index']):
                            new_ident = '#tree_%s' % current['id']
                            new_ident += ':%i' % i
                            tmp_list += [(new_ident, 'after')]
                else:
                    if elt._conditional_names and not elt.islist:
                        for tagname in elt._conditional_names:
                            new_ident = '.tree_%s' % parent['id']
                            if parent['index'] is not None:
                                new_ident += ':%i' % parent['index']
                            new_ident += ':%s' % tagname
                            tmp_list += [(new_ident, 'after')]
                    else:
                        new_ident = '.tree_%s' % parent['id']
                        if parent['index'] is not None:
                            new_ident += ':%i' % parent['index']
                        new_ident += ':%s' % elt.tagname
                        tmp_list += [(new_ident, 'after')]
            else:
                if not elt._conditional_names:
                    new_ident = '#tree_%s' % parent['id']
                    if parent['index'] is not None:
                        new_ident += ':%i' % parent['index']
                    new_ident += ':%s' % elt.tagname
                    tmp_list += [(new_ident, 'after')]
                else:
                    for tagname in elt._conditional_names:
                        new_ident = '#tree_%s' % parent['id']
                        if parent['index'] is not None:
                            new_ident += ':%i' % parent['index']
                        new_ident += ':%s' % tagname
                        tmp_list += [(new_ident, 'after')]

            if elt.tagname  == cls.tagname:
                break

        tmp_list.reverse()
        lis.extend(tmp_list)
        
        new_ident = '#tree_%s' % parent['id']
        if parent['index'] is not None:
            new_ident += ':%i' % parent['index']
        lis += [(new_ident, 'inside')]
        
        return lis
