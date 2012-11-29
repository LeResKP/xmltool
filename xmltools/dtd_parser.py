import re
from lxml import etree
import forms
import utils
from elements import Element, SubElement, TextElement


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
    for (att_name, type_, require) in split_list(lis[1:], 3):
        attributes += [(att_name.strip(), type_.strip(), require.strip())]
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
            name, elements = parse_element(clean_value)
            dtd_elements[name] = elements
        elif element == 'ENTITY':
            name, elements = parse_entity(clean_value)
            dtd_entities[name] = elements
        elif element == 'ATTLIST':
            name, attributes = parse_attribute(value)
            dtd_attributes.setdefault(name, []).extend(attributes)
        else:
            raise Exception, '%s is not supported' % element

    for name, elements in dtd_elements.items():
        for key, value in dtd_entities.items():
            elements = elements.replace('%s;' % key, value)
        dtd_elements[name] = elements

    return dtd_elements, dtd_attributes


def get_child(name, xml):
    for child in xml:
        if child.tag == name:
            return child
    return None


def get_children(name, xml):
    lis = []
    for child in xml:
        if child.tag == name:
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
        for name, elements in self.dtd.items():
            attrs = self.dtd_attrs.get(name) or []
            if elements in ['#PCDATA', 'EMPTY']:
                cls = type(name, (TextElement,), {'_attrs': attrs,
                                                     'name': name,
                                                     '_generator': self})
                cls.__name__ = name
                self.dtd_classes[name] = cls
                continue
            splitted = elements.split(',')
            lis = [SubElement(element) for element in splitted]
            cls = type(name, (Element,), {'_elements': lis,
                                             '_attrs': attrs,
                                             'name': name,
                                             '_generator': self})
            cls.__name__ = name
            self.dtd_classes[name] = cls

    def get_key_from_xml(self, element, obj):
        if not element.conditional_names:
            return element.name

        for elt in element.conditional_names:
            name = elt.name
            if get_children(name, obj):
                return name
        return None

    def set_attrs_to_obj(self, obj, xml):
        for (attr_name, type_, require) in obj._attrs:
            value = xml.attrib.get(attr_name)
            if value:
                obj.attrs[attr_name] = value

    def generate_obj(self, xml):
        obj = self.dtd_classes[xml.tag]()
        self.set_attrs_to_obj(obj, xml)

        if isinstance(obj, TextElement):
            text = None
            if xml is not None:
                text = xml.text or UNDEFINED
            obj.value = text
            return obj

        for element in obj._elements:
            key = self.get_key_from_xml(element, xml)
            if not key:
                continue
            if element.islist:
                children = get_children(key, xml)
                lis = [self.generate_obj(c) for c in children]
                setattr(obj, key, lis)
            else:
                child = get_child(key, xml)
                value = (child is not None) and self.generate_obj(child) or None
                setattr(obj, key, value)

        return obj

    def get_key_from_obj(self, element, obj):
        if not element.conditional_names:
            return element.name

        for elt in element.conditional_names:
            name = elt.name
            if getattr(obj, name, None):
                return name
        return None

    def set_attrs_to_xml(self, obj, xml):
        for attr_name, value in obj.attrs.items():
            xml.attrib[attr_name] = value

    def obj_to_xml(self, obj, xml=None):
        if not obj:
            return None

        if xml is None:
            # Create the root node
            name = obj.__class__.__name__
            xml = etree.Element(name)

        self.set_attrs_to_xml(obj, xml)

        if isinstance(obj, TextElement):
            xml.text = obj.value
            return xml

        for element in obj._elements:
            key = self.get_key_from_obj(element, obj)
            if not key:
                continue
            if element.islist:
                value = getattr(obj, key, [])
                for v in value:
                    e = etree.Element(key)
                    self.obj_to_xml(v, e)
                    if len(e) or e.text or element.required:
                        if e.text:
                            e.text = clear_value(e.text)
                        xml.append(e)
            else:
                value = getattr(obj, key, None)
                e = etree.Element(key)
                self.obj_to_xml(value, e)
                if len(e) or e.text or element.required:
                    if e.text:
                        e.text = clear_value(e.text)
                    xml.append(e)

        return xml

    def generate_form_child(self, element, parent):
        if element.conditional_names:
            field = forms.ConditionalContainer(parent=parent,
                                               required=element.required)
            for elt in element.conditional_names:
                field.possible_children += [self.generate_form_child(elt,
                                                                     field)]
            return field

        key = element.name
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
            key = cls.name
            return forms.TextAreaField(
                key=key,
                name=key,
                label=key,
                parent=parent,
                required=element.required,
                )
        children = []
        for elt in cls._elements:
            children += [self.generate_form_child(elt, parent)]

        return children

    def generate_form(self, root_tag, encoding='UTF-8', **kwargs):
        cls = self.dtd_classes[root_tag]
        kwargs['_dtd_url'] = self._dtd_url
        kwargs['_encoding'] = self._encoding
        parent = forms.FormField(legend=cls.name, **kwargs)
        parent.children += self.generate_form_children(cls, parent, None)
        return parent

    def get_key_from_dict(self, element, dic):
        if not element.conditional_names:
            return element.name

        for elt in element.conditional_names:
            name = elt.name
            if name in dic:
                return name
        return None

    def dict_to_obj(self, root_tag, dic, required=True):
        if not dic:
            return None

        obj = self.dtd_classes[root_tag]()
        attrs = dic.get('attrs') or {}
        for (attr_name, type_, require) in obj._attrs:
            if attr_name in attrs:
                obj.attrs[attr_name] = attrs[attr_name]

        if isinstance(obj, TextElement):
            value = dic.get('value')
            if value == '':
                # We want to make sure we will display the tags added by the
                # user
                value = UNDEFINED
            obj.value = value
            return obj

        isempty = True
        for element in obj._elements:
            key = self.get_key_from_dict(element, dic)
            if not key:
                continue
            value = dic.get(key)
            if element.islist:
                value = value or []
                assert isinstance(value, list)
                lis = []
                for v in value:
                    sub_obj = self.dict_to_obj(key, v, element.required)
                    if sub_obj:
                        lis += [sub_obj]
                setattr(obj, key, lis)
                isempty=False
            else:
                res = self.dict_to_obj(key, value, element.required)
                if (element.required and required) or res:
                    setattr(obj, key, res)
                    isempty=False
        if isempty:
            return None
        return obj
