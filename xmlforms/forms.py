#!/usr/bin/env python

import dtd_parser


def clone_obj(obj):
    newobj = obj.__class__(**vars(obj))

    if hasattr(obj, 'children') and obj.children:
        children = []
        for child in obj.children:
            c = clone_obj(child)
            c.parent = newobj
            children += [c]
        newobj.children = children

    if hasattr(obj, 'possible_children') and obj.possible_children:
        children = []
        for child in obj.possible_children:
            c = clone_obj(child)
            c.parent = newobj
            children += [c]
        newobj.possible_children = children

    if hasattr(obj, 'child') and obj.child:
        newobj.child = clone_obj(newobj.child)
        newobj.child.parent = newobj

    return newobj


class Field(object):
    attrs = []
    html_attrs = []

    def __init__(self, **kwargs):
        self.key = None
        self.name = None
        self.value = None
        self.parent = None
        self.required = None
        self.empty = False
        self.add_value_str = True
        self.attrs_children = []
        self.css_classes = []

        for attr in self.html_attrs + self.attrs:
            setattr(self, attr, None)
        for k, v in kwargs.iteritems():
            if type(v) is list:
                v = list(v)
            setattr(self, k, v)

        if self.key and self.key not in self.css_classes:
            self.css_classes += [self.key]

    def get_name(self):
        lis = []
        parent = self
        while parent:
            name = getattr(parent, 'name', None)
            lis += [name]
            parent = parent.parent
        lis.reverse()
        s = ':'.join(filter(bool, lis))
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
        attrs += [' name="%s"' % self.get_name()]
        css_classes = ' '.join(self.css_classes)
        if css_classes:
            attrs += [' class="%s"' % css_classes ]
        for attr in self.html_attrs:
            v = getattr(self, attr, None)
            if v:
                attrs += ['%s="%s"' % (attr, v)]
        return ' '.join(attrs)

    def display(self):
        html = []
        for child in self.attrs_children:
            html += [child.display()]
        html += [self._display()]
        return ''.join(html)

    def _display(self):
        raise NotImplementedError


class InputField(Field):

    def _display(self):
        return '<input type="text" value="%s"%s>' % (self.get_value(),
                                                    self.get_attrs())


class TextAreaField(Field):
    attrs = ['label']
    html_attrs = ['rows']

    def _set_value(self, value):
        super(TextAreaField, self)._set_value(value)
        num = self.value and self.value.count('\n') or 0
        self.rows = max(num + 1, 2)

    def _display(self):
        html = []
        if not self.empty and not self.value and not self.required:
            # For now, we don't want to add the empty field
            return ''
        if self.label:
            html += ['<label>%s</label>' % self.label]
        html += ['<textarea%s>%s</textarea>' % (self.get_attrs(), self.get_value())]
        return '<div>%s</div>' % ''.join(html)


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

    def _display(self):
        html = []
        html += ['<fieldset%s>' % self.get_attrs()]
        if self.legend:
            html += ['<legend>%s</legend>' % self.legend]

        child_html = []
        for child in self.get_children():
            content = child.display()
            child_html += [content]

        if not filter(bool, child_html):
            return ''

        html.extend(child_html)
        html += ['</fieldset>']
        return '\n'.join(html)


class FormField(Fieldset):

    html_attrs = ['action']

    def display(self):
        children_html = super(FormField, self).display()
        if not children_html:
            return ''
        html = []
        html += ['<form%s method="POST">' % self.get_attrs()]
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

    def _display(self):
        html = []
        for child in self.get_children():
	        html += ['<div>%s</div>' % child.display()]
        return '\n'.join(html)


class GrowingContainer(Fieldset):
    attrs = ['legend', 'child']
    repetitions = 0

    def _set_value(self, value):
        Field._set_value(self, value)

    def get_children(self):
        values = []
        if self.value:
            values = self.value
            repetitions = len(values)
        else:
            repetitions = self.repetitions

        children = []
        for i in range(repetitions):
            v = None
            if values and len(values) > i:
                v = values[i]
            obj = clone_obj(self.child)
            obj.name += ':%i' % i
            obj.set_value(v)
            children += [obj]

        return children


