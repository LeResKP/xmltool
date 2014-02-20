
def attrs_to_str(attrs):
    """Create string from the given attrs

    :param attrs: The attributes to put on HTML element.
    :type attrs: List of tuple
    :return: The givens attrs as string like: 'name="myname"'
    :rtype: str
    """
    attr = ' '.join(['%s="%s"' % (attrname, value)
                     for attrname, value in attrs])
    if not attr:
        return attr

    return ' ' + attr


class Render(object):
    """Default render.
    """

    def add_add_button(self):
        return True

    def add_delete_button(self):
        return True

    def add_comment(self):
        return True

    def text_element_to_html(self, obj, attrs, value):
        return (
            u'<textarea class="form-control"{attrs}>{value}'
            u'</textarea>').format(attrs=attrs_to_str(attrs), value=value)


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
