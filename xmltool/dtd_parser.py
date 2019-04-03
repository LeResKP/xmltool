from future.utils import native_str

import re
from .elements import (
    ContainerElement,
    TextElement,
    ListElement,
    ChoiceListElement,
    ChoiceElement,
    InListMixin,
    InChoiceMixin,
)
from dogpile.cache.api import NO_VALUE


comment_regex_compile = re.compile(r'<!--(.*?)-->', re.DOTALL)
tag_regex_compile = re.compile(r'<!(?P<type>[A-Z]+)(.*?)>', re.DOTALL)
element_regex_compile = re.compile(r' *(?P<name>[^( ]+) *\((?P<elements>.+)\)')
empty_element_regex_compile = re.compile(r' *(?P<name>[^( ]+) *(?P<elements>.+)')
entity_regex_compile = re.compile(r' *(?P<name>% *[^" ]+?) *"(?P<elements>.+)"')


def cleanup(value):
    for c in ['\n', '\r']:
        value = value.replace(c, '')
    return value


def parse_element(value):
    matchobj = element_regex_compile.match(value)
    if not matchobj:
        matchobj = empty_element_regex_compile.match(value)
    if not matchobj:
        raise Exception('Error parsing element %s' % value)
    name, elements = matchobj.groups()
    if elements.count(')') != elements.count('('):
        raise Exception('Unbalanced parenthesis %s' % value)
    return name, elements.replace(' ', '')


def parse_entity(value):
    matchobj = entity_regex_compile.match(value)
    if not matchobj:
        raise Exception('Error parsing entity %s' % value)
    name, elements = matchobj.groups()
    return name.replace(' ', ''), elements.replace(' ', '')


def split_list(lis, cols):
    return [lis[i:i+cols] for i in range(0, len(lis), cols)]


def parse_attribute(value):
    for c in ['\n', '\r']:
        value = value.replace(c, '')
    lis = value.split(' ')
    lis = list(filter(bool, lis))
    assert (len(lis) - 1) % 3 == 0
    name = lis[0].strip()
    attributes = []
    for (attr_name, attr_type, require) in split_list(lis[1:], 3):
        attributes += [(attr_name.strip(), attr_type.strip(), require.strip())]
    return name, attributes


def dtd_to_dict_v2(dtd):
    dtd_entities = {}
    dtd_attributes = {}
    dtd_elements = {}
    # Removed the comments
    res = comment_regex_compile.sub('', dtd)
    tags = tag_regex_compile.findall(res)
    for element, value in tags:
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
            raise Exception('%s is not supported' % element)

    dic = {}
    for tagname, elements in dtd_elements.items():
        for key, value in dtd_entities.items():
            elements = elements.replace('%s;' % key, value)
        dic[tagname] = {
            'elts':  elements,
            'attrs': dtd_attributes.get(tagname) or []
        }
    return dic


def _parse_elts(elts):
    splitted = elts.split(',')
    lis = []
    for text in splitted:
        tagname = text
        required = True
        islist = False
        if text.endswith('+'):
            tagname = text[:-1]
            islist = True
        elif text.endswith('*'):
            tagname = text[:-1]
            islist = True
            required = False
        elif text.endswith('?'):
            tagname = text[:-1]
            required = False

        if '|' not in tagname:
            lis += [(tagname, required, islist, [])]
        else:
            tagname = tagname.replace('(', '').replace(')', '')
            tagnames = tagname.split('|')
            sub = []
            for tg in tagnames:
                sub += _parse_elts(tg)
            lis += [('%s' % '_'.join(tagnames), required, islist, sub)]
    return lis


def _create_new_class(class_dict, name, required, islist, conditionals,
                      inlist=False, inchoice=False):
    base_cls = class_dict.get(name)
    if base_cls is None and not conditionals:
        raise ValueError('You should provide a base_cls or conditionals for %s' % name)
    cls = base_cls

    if conditionals:
        assert name
        if not islist:
            parent_cls = type(native_str('%sChoice' % name), (ChoiceElement,), {
                '_choice_classes': [],
                'tagname': 'choice__%s' % name,
                '_required': required
            })
        else:
            parent_cls = type(native_str('%sChoiceList' % name), (ChoiceListElement,), {
                '_choice_classes': [],
                'tagname': 'list__%s' % name,
                '_required': required,
            })

        for (subname, subrequired, subislist, subconditionals) in conditionals:
            assert not subconditionals, subconditionals
            assert not subislist
            sub_cls = _create_new_class(class_dict, subname, subrequired,
                                        subislist, subconditionals,
                                        inlist=islist, inchoice=(not islist))
            sub_cls._parent_cls = parent_cls
            parent_cls._choice_classes += [sub_cls]
        return parent_cls

    if not islist:
        classes = ()
        if inlist or inchoice:
            assert(inlist != inchoice)
        if inlist:
            classes = (InListMixin,)
        if inchoice:
            classes = (InChoiceMixin,)
        return type(cls.__name__, classes + (cls,), {
            '_required': required})

    # Always create a new cls to make sure _required is well defined
    newcls = type(cls.__name__, (InListMixin, cls, ), {'_required': required})

    listcls = type('%sList' % cls.__name__, (ListElement, ), {
        '_children_class': newcls,
        '_required': required,
        'tagname': 'list__%s' % name
    })
    newcls._parent_cls = listcls
    return listcls


def _create_class_dict(dtd_dict):
    class_dict = {}
    for tagname, dic in dtd_dict.items():
        is_empty = False
        lis = _parse_elts(dic['elts'])
        if dic['elts'] in ['#PCDATA', 'EMPTY']:
            c = TextElement
            if dic['elts'] == 'EMPTY':
                is_empty = True
        elif (lis[0][3] and
              lis[0][3][0][0] in ['#PCDATA', 'EMPTY']):
            # Special case with mixed content
            c = TextElement
            if lis[0][3][0][0] == 'EMPTY':
                is_empty = True
            # TODO: find a better way to handle the mixed content
            # 
            # Make some replacements to have the same dtd than for the children
            # like this 'sub1, sub2'. Not sure we can have list of elements in,
            # but it is sure it is not supported!
            dic['elts'] = dic['elts'].replace('#PCDATA|', '')
            dic['elts'] = dic['elts'].replace('EMPTY|', '')
            dic['elts'] = dic['elts'].replace('|', '?,')
            dic['elts'] = dic['elts'][1:-2] + '?' # Remove the '*' at the end
        else:
            c = ContainerElement
        cls = type(native_str(tagname), (c,), {
            'tagname': tagname,
            '_attribute_names': [tple[0] for tple in dic['attrs']],
            'children_classes': [],
            '_is_empty': is_empty,
        })
        class_dict[tagname] = cls
    return class_dict


def _create_classes(dtd_dict):
    class_dict = _create_class_dict(dtd_dict)
    for tagname, dic in dtd_dict.items():
        cls = class_dict[tagname]
        lis = _parse_elts(dic['elts'])
        for (name, required, islist, conditionals) in lis:
            if name in ['#PCDATA', 'EMPTY']:
                # Text with no sub elements
                continue
            sub_cls = _create_new_class(
                class_dict, name, required, islist, conditionals)
            sub_cls._parent_cls = cls
            cls.children_classes += [sub_cls]

    return class_dict
