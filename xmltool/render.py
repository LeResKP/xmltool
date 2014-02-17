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
            u'</textarea>').format(attrs=attrs, value=value)


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
        return u'<div>%s</div>' % value
