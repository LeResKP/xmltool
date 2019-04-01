from .utils import prefixes_to_str

def attrs_to_str(attrs):
    """Create string from the given attrs

    :param attrs: The attributes to put on HTML element.
    :type attrs: List of tuple
    :return: The givens attrs as string like: 'name="myname"'
    :rtype: str
    """
    dic = {}
    for k, v in attrs:
        dic.setdefault(k, []).append(str(v))

    lis = []
    for k, v in attrs:
        l = dic.pop(k, None)
        if not l:
            continue
        lis += ['%s="%s"' % (k, ' '.join(l))]

    if not lis:
        return ''

    return ' ' + ' '.join(lis)


class Render(object):
    """Default render.
    """

    def __init__(self, extra_attrs_func=None):
        self.extra_attrs_func = extra_attrs_func

    def add_add_button(self):
        return True

    def add_delete_button(self):
        return True

    def add_comment(self):
        return True

    def text_element_to_html(self, obj, attrs, value):
        return (
            u'<textarea{attrs}>{value}'
            u'</textarea>').format(
            attrs=attrs_to_str([('class', 'form-control')] + attrs),
            value=value)


class ContenteditableRender(Render):
    """Default render.
    """

    def __init__(self, extra_attrs_func=None, extra_div_attrs_func=None):
        self.extra_attrs_func = extra_attrs_func
        self.extra_div_attrs_func = extra_div_attrs_func

    def cleanup_value(self, value):
        return value.replace('\n', '<br />')

    def text_element_to_html(self, obj, attrs, value):

        ident = prefixes_to_str(obj.prefixes_no_cache + ['_contenteditable'])

        div_attrs = [
            ('class', 'contenteditable'),
            ('class', 'form-control'),
            ('class', obj.tagname),
            ('contenteditable', 'true'),
            ('spellcheck', 'false'),
            ('id', ident),
        ]
        if self.extra_div_attrs_func:
            div_attrs += self.extra_div_attrs_func(obj)

        return (
            u'<textarea{attrs}>{value}'
            u'</textarea>'
            u'<div{divattrs}>{htmlvalue}</div>'
        ).format(
            attrs=attrs_to_str([('class', 'form-control'),
                                ('class', 'hidden')] + attrs),
            value=value,
            htmlvalue=self.cleanup_value(value),
            divattrs=attrs_to_str(div_attrs),
        )


class CKeditorRender(ContenteditableRender):

    def cleanup_value(self, value):
        value = super(CKeditorRender, self).cleanup_value(value)
        # Add the non breaking spaces like CKeditor do when it adds spaces.
        return value.replace('  ', ' &nbsp;')


class ReadonlyRender(Render):
    """Readonly render: we don't add any button, comment nor HTML form.
    """

    def add_add_button(self):
        return False

    def add_delete_button(self):
        return False

    def add_comment(self):
        return False

    def text_element_to_html(self, obj, attrs, value):
        return super(ReadonlyRender, self).text_element_to_html(
            obj, attrs + [('readonly', 'readonly')], value)
