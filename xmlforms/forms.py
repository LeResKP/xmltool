#!/usr/bin/env python

import dtd_parser


def clone_obj(obj):

    dic = vars(obj).copy()
    for key in [
        'attrs_children',
        'css_classes',
        'container_css_classes']:
        dic.pop(key)

    newobj = obj.__class__(**dic)

    children = getattr(obj, 'children', None)
    if children:
        newobj.children = []
        for child in children:
            c = clone_obj(child)
            c.parent = newobj
            newobj.children.append(c)

    children = getattr(obj, 'possible_children', None)
    if children:
        newobj.possible_children = []
        for child in children:
            c = clone_obj(child)
            c.parent = newobj
            newobj.possible_children.append(c)

    child = getattr(obj, 'child', None)
    if child:
        newobj.child = clone_obj(newobj.child)
        newobj.child.parent = newobj

    return newobj


class Field(object):
    attrs = []
    html_attrs = []
    display_container = False

    def __init__(self, **kwargs):

        dic = {
            'key': None,
            'name': None,
            'value': None,
            'parent': None,
            'required': None,
            'empty': False,
            'add_value_str': True,
            'attrs_children': [],
            'css_classes': [],
            'container_css_classes': ['container'],
            'container_id': '',
            '_name': None,
        }

        for attr in self.html_attrs + self.attrs:
            dic[attr] = None

        dic.update(kwargs)
        self.__dict__.update(dic)
        self._init_css_classes()

    def _init_css_classes(self):
        if self.key and not isinstance(self, GrowingContainer):
            if self.key not in self.css_classes:
                self.css_classes += [self.key]

    def _get_name(self):
        if not self._name:
            lis = []
            if self.parent:
                name = self.parent._get_name()
                if name:
                    lis.append(name)
            if self.name:
                lis.append(self.name)
            self._name = ':'.join(lis)
        return self._name

    def get_id(self):
        return self._get_name()

    def get_name(self):
        s = self._get_name()
        if not s:
            return ''
        if self.add_value_str:
            s += ':value'
        return s

    def set_value(self, value):
        if value and (self.key or type(self) is FormField):
            if type(value) != list:
                for k, v in value.attrs.items():
                    self.attrs_children += [InputField(
                        key=k,
                        name='attrs:%s' % k,
                        parent=self,
                        add_value_str=False,
                        css_classes=['attr'],
                        value=v)]
        self._set_value(value)

    def _set_value(self, value):
        if value and hasattr(value, 'value'):
            value = value.value
        if value == dtd_parser.UNDEFINED:
            self.empty = True
            value = None
        self.value = value

    def get_value(self):
        return self.value or ''

    def get_attrs(self):
        attrs = []
        name = self.get_name()
        if name and not isinstance(self, MultipleField):
            attrs += ['name="%s"' % name]
        id_ = self.get_id()
        if id_ and not isinstance(self, FormField):
            attrs += ['id="%s"' % id_]
        css_classes = ' '.join(self.css_classes)
        if css_classes:
            attrs += ['class="%s"' % css_classes ]
        for attr in self.html_attrs:
            v = getattr(self, attr, None)
            if v:
                attrs += ['%s="%s"' % (attr, v)]
        s = ' '.join(attrs)
        if s:
            return ' %s' % s
        return ''

    def _display(self):
        raise NotImplementedError

    def display(self):
        html = []
        for child in self.attrs_children:
            html += [child.display()]
        html += [self._display()]
        if not filter(bool, html):
            return ''

        if self.display_container:
            attrs = []
            attrs += ['class="%s"' % ' '.join(self.container_css_classes)]
            if self.container_id:
                attrs += ['id="%s"' % self.container_id]
            return '<div %s>%s</div>' % (
                ' '.join(attrs),
                ''.join(html))
        return ''.join(html)


class InputField(Field):

    def _display(self):
        return '<input type="text" value="%s"%s>' % (self.get_value(),
                                                    self.get_attrs())

class ButtonField(Field):

    def display(self):
        return '<input type="button" value="%s"%s>' % (self.get_value(),
                                                       self.get_attrs())

class TextAreaField(Field):
    attrs = ['label']
    html_attrs = ['rows']
    display_container = True

    def _set_value(self, value):
        super(TextAreaField, self)._set_value(value)
        num = self.value and self.value.count('\n') or 0
        self.rows = max(num + 1, 2)

    def _display(self):
        html = []
        show_container = True
        if not self.required:
            if not self.value and not self.empty:
                show_container = False

        parent_is_growing = isinstance(self.parent, GrowingContainer)
        if not self.required:
            if not parent_is_growing:
                add_button_css_classes = ['add-button']
                if show_container:
                    add_button_css_classes += ['hidden']
                add_button = ButtonField(value='Add %s' % self.key,
                                         css_classes=add_button_css_classes)
                html += [add_button.display()]
                if show_container:
                    html += ['<div>']
                else:
                    html += ['<div class="deleted">']
        html += ['<label>%s</label>' % self.label]
        if not self.required or parent_is_growing:
            css_classes=['delete-button']
            if parent_is_growing:
                css_classes=['growing-delete-button']
            delete_button = ButtonField(value='Delete %s' % self.key,
                                        css_classes=css_classes)
            html += [delete_button.display()]
        html += ['<textarea%s>%s</textarea>' % (self.get_attrs(), self.get_value())]
        if not self.required and not parent_is_growing:
            html += ['</div>']
        if parent_is_growing:
            add_button = ButtonField(value="New %s" % self.parent.key,
                                     css_classes=['growing-add-button'])
            html += [add_button.display()]
        return ''.join(html)


class MultipleField(Field):

    def __init__(self, **kwargs):
        super(MultipleField, self).__init__(**kwargs)
        self.children = []

    def _set_value(self, value):
        self.value = value
        for child in self.children:
            v = value
            if child.key and hasattr(value, child.key):
                v = getattr(value, child.key)
            child.set_value(v)

    def get_value(self):
        return self.value or []

    def get_children(self):
        return self.children


class Fieldset(MultipleField):
    attrs = ['legend']
    display_container = True

    def _display(self):
        child_html = []
        for child in self.get_children():
            content = child.display()
            child_html += [content]

        if not filter(bool, child_html):
            return ''

        html = []
        show_container = True
        if not self.required:
            if not self.value and not self.empty:
                show_container = False

        legend = self.legend
        parent_is_growing = isinstance(self.parent, GrowingContainer)
        if not self.required or parent_is_growing:
            css_classes=['fieldset-delete-button']
            if parent_is_growing:
                css_classes=['growing-fieldset-delete-button']
            delete_button = ButtonField(value='Delete %s' % self.key,
                                        css_classes=css_classes)
            legend += delete_button.display()
            if not parent_is_growing:
                add_button_css_classes = ['add-button']
                if show_container:
                    add_button_css_classes += ['hidden']
                add_button = ButtonField(value='Add %s' % self.key,
                                         css_classes=add_button_css_classes)
                html += [add_button.display()]

        if not show_container:
            self.css_classes += ['deleted']
        html += ['<fieldset%s>' % self.get_attrs()]
        html += ['<legend>%s</legend>' % legend]

        html.extend(child_html)
        html += ['</fieldset>']

        if parent_is_growing:
            add_button = ButtonField(value="New %s" % self.parent.key,
                                    css_classes=['growing-add-button'])
            html += [add_button.display()]
        return ''.join(html)


class FormField(Fieldset):

    html_attrs = ['action']
    display_container = False

    def __init__(self, **kwargs):
        super(FormField, self).__init__(**kwargs)
        self.extra_children = [
            InputField(
                key='_dtd_url',
                name='_dtd_url',
                parent=self,
                add_value_str=False,
                value=kwargs.get('_dtd_url')
            ),
            InputField(
                key='_encoding',
                name='_encoding',
                parent=self,
                add_value_str=False,
                value=kwargs.get('_encoding')
            ),
            InputField(
                key='_root_tag',
                name='_root_tag',
                parent=self,
                add_value_str=False,
                value=self.legend
            )
        ]

    def display(self):
        self.required = True # No delete nor add button on the form
        children_html = super(FormField, self).display()
        if not children_html:
            return ''
        extra_children_html = []
        for child in self.extra_children:
            extra_children_html.append(child.display())

        html = []
        html += ['<form%s method="POST">' % self.get_attrs()]
        html += [''.join(extra_children_html)]
        html += [children_html]
        html += ['<input type="submit" />']
        html += ['</form>']
        return ''.join(html)


class ConditionalContainer(Field):
    def __init__(self, **kwargs):
        self.possible_children = []
        super(ConditionalContainer, self).__init__(**kwargs)

    def get_children(self):
        for c in self.possible_children:
            if hasattr(self.value, c.key):
                c.set_value(getattr(self.value, c.key, None))
                return [c]
        return []

    def get_child(self):
        for c in self.possible_children:
            if hasattr(self.value, c.key):
                c.set_value(getattr(self.value, c.key, None))
                return c
        return None

    def _display(self):
        if not self.possible_children:
            return ''

        child = self.get_child()
        html = ['<div class="conditional-container">']
        if child:
            html += ['<select class="hidden conditional">']
        else:
            html += ['<select class="conditional">']
        html += ['<option value="">Add new</option>']
        children_html = []
        for index, c in enumerate(self.possible_children):
            lis = c.css_classes
            if isinstance(c, TextAreaField):
                c.required = False
                lis = c.container_css_classes
            if child:
                if c != child:
                    lis += ['deleted']
            else:
                lis += ['deleted']
            option = '%s:option:%i' % (c._get_name(), index)
            lis += ['conditional-option']
            lis += [option]
            children_html += [c.display()]
            html += ['<option value="%s">%s</option>' % (option, c.key)]
        html += ['</select>']
        html += children_html
        html += ['</div>']
        return '\n'.join(html)


class GrowingContainer(MultipleField):
    attrs = ['child']
    repetitions = 1

    def _init_css_classes(self):
        pass

    def _set_value(self, value):
        Field._set_value(self, value)

    def get_children(self):
        if not self.child:
            return []

        values = []
        if self.value:
            values = [None] + self.value
            repetitions = len(values)
        else:
            repetitions = self.repetitions

        children = []
        for i in range(repetitions):
            v = None
            if values and len(values) > i:
                v = values[i]
            obj = clone_obj(self.child)
            if i == 0:
                obj.container_css_classes += ['growing-source']
                obj.container_id = obj._get_name()
                obj.required = True
            elif i > 1:
                obj.required = False
            obj.name += ':%i' % i
            # Removed the cache since we already had called _get_name() for the
            # container_id
            obj._name = None
            obj.set_value(v)
            children += [obj]

        return children

    def _display(self):
        html = []
        for child in self.get_children():
            html += [child.display()]

        if not filter(bool, html):
            return ''
        self.css_classes += ['growing-container']
        if self.required:
            self.css_classes += ['required']
        return '<div class="%s">%s</div>' % (' '.join(self.css_classes),
                                             '\n'.join(html))

