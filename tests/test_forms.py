from unittest import TestCase
import xmlforms.forms as forms
import xmlforms.dtd_parser as dtd_parser
import tw2.core.testbase as tw2test


class cls(object):
    attrs = {}
    pass


def display(field):
    """Since we use xml validation, we need a root element
    """
    return '<div>%s</div>' % field.display()


class TestFunctions(TestCase):

    def test_clone_obj(self):
        field = forms.Field(name='field', test=True)
        cloned_field = forms.clone_obj(field)
        self.assertTrue(field != cloned_field)
        self.assertEqual(field.name, cloned_field.name)
        self.assertEqual(field.test, cloned_field.test)

        field = forms.MultipleField(name='test')
        sub1 = forms.Field(name='sub1', key='sub1')
        sub2 = forms.Field(name='sub2', key='sub2')
        field.children = [sub1, sub2]
        cloned_field = forms.clone_obj(field)
        self.assertTrue(field != cloned_field)
        self.assertEqual(field.name, cloned_field.name)
        for index in range(2):
            self.assertTrue(field.children[index] !=
                            cloned_field.children[index])
            self.assertEqual(field.children[index].name,
                             cloned_field.children[index].name)
            self.assertEqual(field.children[index].key,
                             cloned_field.children[index].key)

        field = forms.ConditionalContainer(name='test')
        sub1 = forms.TextAreaField(name='sub1', key='sub1', parent=field)
        sub2 = forms.TextAreaField(name='sub2', key='sub2', parent=field)
        field.possible_children = [sub1, sub2]
        cloned_field = forms.clone_obj(field)
        self.assertTrue(field != cloned_field)
        self.assertEqual(field.name, cloned_field.name)
        for index in range(2):
            self.assertTrue(field.possible_children[index] !=
                            cloned_field.possible_children[index])
            self.assertEqual(field.possible_children[index].name,
                             cloned_field.possible_children[index].name)
            self.assertEqual(field.possible_children[index].key,
                             cloned_field.possible_children[index].key)
            self.assertEqual(cloned_field.possible_children[index].parent,
                             cloned_field)

        field = forms.GrowingContainer(name='test')
        child = forms.TextAreaField(name='textarea_child', parent=field)
        field.child = child
        cloned_field = forms.clone_obj(field)
        self.assertTrue(field != cloned_field)
        self.assertEqual(field.name, cloned_field.name)
        self.assertTrue(field.child != cloned_field.child)
        self.assertEqual(field.child.name, cloned_field.child.name)
        self.assertEqual(cloned_field.child.parent, cloned_field)



class TestField(TestCase):

    def test_init(self):
        field = forms.Field()
        self.assertEqual(field.key, None)
        self.assertEqual(field.name, None)
        self.assertEqual(field.value, None)
        self.assertEqual(field.parent, None)
        self.assertEqual(field.required, None)
        self.assertEqual(field.empty, False)

        field = forms.Field(toto='plop', key='key', name='name')
        self.assertEqual(field.key, 'key')
        self.assertEqual(field.name, 'name')
        self.assertEqual(field.value, None)
        self.assertEqual(field.parent, None)
        self.assertEqual(field.required, None)
        self.assertEqual(field.empty, False)
        self.assertEqual(field.toto, 'plop')

    def test_get_name(self):
        field = forms.Field(name='test')
        self.assertEqual(field.get_name(), 'test:value')
        field.add_value_str = False
        self.assertEqual(field.get_name(), 'test')
        field.add_value_str = True
        field.parent = forms.Field(name='parent1')
        self.assertEqual(field.get_name(), 'parent1:test:value')
        field.parent.add_value_str = False
        field.add_value_str = False
        self.assertEqual(field.get_name(), 'parent1:test')
        field.add_value_str = True
        field.parent.add_value_str = True
        field.parent.name = None
        self.assertEqual(field.get_name(), 'test:value')
        field.add_value_str = False
        self.assertEqual(field.get_name(), 'test')

    def test_set_value(self):
        field = forms.Field(name='test')
        self.assertEqual(field.value, None)
        self.assertEqual(field.empty, False)
        field.set_value(None)
        self.assertEqual(field.value, None)
        self.assertEqual(field.empty, False)
        field.set_value('my value')
        self.assertEqual(field.value, 'my value')
        self.assertEqual(field.empty, False)
        field.set_value(dtd_parser.UNDEFINED)
        self.assertEqual(field.value, None)
        self.assertEqual(field.empty, True)
        o = cls()
        o.value = 'my value'
        field = forms.Field(name='test')
        field.set_value(o)
        self.assertEqual(field.value, 'my value')
        self.assertEqual(field.empty, False)

    def test_get_value(self):
        field = forms.Field(name='test')
        self.assertEqual(field.get_value(), '')
        field.value = 'my value'
        self.assertEqual(field.get_value(), 'my value')

class TestTextAreaField(TestCase):

    def test_set_value(self):
        field = forms.TextAreaField()
        self.assertEqual(field.value, None)
        self.assertEqual(field.rows, None)
        field.set_value(u'Hello')
        self.assertEqual(field.value, u'Hello')
        self.assertEqual(field.rows, 2)
        field.set_value(u'Hello\nWorld\n!')
        self.assertEqual(field.value, u'Hello\nWorld\n!')
        self.assertEqual(field.rows, 3)

    def test_display(self):
        field = forms.TextAreaField(name='test', key='test')
        self.assertEqual(field.display(), '')
        o = cls()
        o.value = 'Hello'
        o.attrs = {'id': 1}
        field = forms.TextAreaField(name='test', key='test')
        field.set_value(o)
        tw2test.assert_eq_xml(display(field), """
          <div>
            <input type="text" value="1" name="test:attrs:id" class="attr id">
            <div>
              <textarea name="test:value" class="test" rows="2">Hello</textarea>
            </div>
          </div>
        """)
        o.value = 'Hello\nWorld\n!'
        field = forms.TextAreaField(name='test', key='test')
        field.set_value(o)
        tw2test.assert_eq_xml(display(field), """
          <div>
            <input type="text" value="1" name="test:attrs:id" class="attr id">
            <div>
              <textarea name="test:value" class="test" rows="3">Hello\nWorld\n!</textarea>
            </div>
          </div>
        """)
        field = forms.TextAreaField(name='test', key='test')
        field.label = 'my label'
        field.set_value(o)
        tw2test.assert_eq_xml(display(field), """
          <div>
            <input type="text" value="1" name="test:attrs:id" class="attr id">
            <div>
              <label>my label</label>
              <textarea name="test:value" class="test" rows="3">Hello\nWorld\n!</textarea>
            </div>
          </div>
        """)
        o.value = dtd_parser.UNDEFINED
        field = forms.TextAreaField(name='test', key='test')
        field.label = 'my label'
        field.set_value(o)
        tw2test.assert_eq_xml(display(field), """
          <div>
            <input type="text" value="1" name="test:attrs:id" class="attr id">
            <div>
              <label>my label</label>
              <textarea name="test:value" class="test" rows="2"></textarea>
            </div>
          </div>
        """)


class TestMultipleField(TestCase):

    def test_init(self):
        field = forms.MultipleField()
        self.assertEqual(field.key, None)
        self.assertEqual(field.name, None)
        self.assertEqual(field.value, None)
        self.assertEqual(field.parent, None)
        self.assertEqual(field.required, None)
        self.assertEqual(field.empty, False)
        self.assertEqual(field.children, [])

    def test_set_value(self):
        field = forms.MultipleField(name='test')
        sub1 = forms.Field(name='sub1', key='sub1')
        sub2 = forms.Field(name='sub2', key='sub2')
        sub3 = forms.MultipleField(name='sub3', key='sub3')
        sub4 = forms.Field(name='sub4', key='sub4')
        sub3.children = [sub4]
        field.children = [sub1, sub2, sub3]
        field.set_value(None)
        self.assertEqual(field.value, None)

        o = cls()
        o.sub1 = cls()
        o.sub1.value = 'sub1 value'
        o.sub2 = cls()
        o.sub2.value = 'sub2 value'
        o.sub3 = cls()
        o.sub3.sub4 = cls()
        o.sub3.sub4.value = 'sub4 value'

        field.set_value(o)
        self.assertEqual(field.value, o)
        self.assertEqual(sub1.value, 'sub1 value')
        self.assertEqual(sub2.value, 'sub2 value')
        self.assertEqual(sub3.value, o.sub3)
        self.assertEqual(sub4.value, 'sub4 value')

    def test_set_value_no_key(self):
        field = forms.MultipleField(name='test')
        sub1 = forms.Field(name='sub1', key='sub1')
        sub2 = forms.Field(name='sub2', key='sub2')
        # No key for the MultipleField
        sub3 = forms.MultipleField(name='sub3')
        sub4 = forms.Field(name='sub4', key='sub4')
        sub3.children = [sub4]
        field.children = [sub1, sub2, sub3]
        field.set_value(None)
        self.assertEqual(field.value, None)

        o = cls()
        o.sub1 = cls()
        o.sub1.value = 'sub1 value'
        o.sub2 = cls()
        o.sub2.value = 'sub2 value'
        o.sub4 = cls()
        o.sub4.value = 'sub4 value'

        field.set_value(o)
        self.assertEqual(field.value, o)
        self.assertEqual(sub1.value, 'sub1 value')
        self.assertEqual(sub2.value, 'sub2 value')
        self.assertEqual(sub3.value, o)
        self.assertEqual(sub4.value, 'sub4 value')

    def test_get_value(self):
        field = forms.MultipleField(name='test')
        self.assertEqual(field.get_value(), [])
        field.value = 'plop'
        self.assertEqual(field.get_value(), 'plop')

    def test_get_children(self):
        field = forms.MultipleField(name='test')
        self.assertEqual(field.get_children(), [])
        child1 = forms.Field(name='child1')
        field.children += [child1]
        self.assertEqual(field.get_children(), [child1])


class TestFieldset(TestCase):

    def test_init(self):
        field = forms.Fieldset(name='test')
        self.assertEqual(field.legend, None)
        field = forms.Fieldset(name='test', legend='my legend')
        self.assertEqual(field.legend, 'my legend')

    def test_display(self):
        field = forms.Fieldset(name='test', key='test')
        self.assertEqual(field.display(), '')
        sub1 = forms.TextAreaField(name='sub1', key='sub1', value='textarea 1',
                                  parent=field)
        sub2 = forms.TextAreaField(name='sub2', key='sub2', value='textarea 2',
                                  parent=field)
        field.children = [sub1, sub2]
        o = cls()
        o.sub1 = cls()
        o.sub1.value = 'textarea 1'
        o.sub1.attrs = {'id': '1'}
        o.sub2 = cls()
        o.sub2.value = 'textarea 2'
        o.sub2.attrs = {'id': '2'}
        o.attrs = {'id': 'idfieldset'}
        field.set_value(o)
        tw2test.assert_eq_xml(display(field), """
        <div>
          <input type="text" value="idfieldset" name="test:attrs:id" class="attr id">
          <fieldset name="test:value" class="test">
            <input type="text" value="1" name="test:sub1:attrs:id" class="attr id">
            <div><textarea name="test:sub1:value" class="sub1" rows="2">textarea 1</textarea></div>
            <input type="text" value="2" name="test:sub2:attrs:id" class="attr id">
            <div><textarea name="test:sub2:value" class="sub2" rows="2">textarea 2</textarea></div>
          </fieldset>
        </div>
        """)

        field.legend = 'my legend'
        tw2test.assert_eq_xml(display(field), """
        <div>
          <input type="text" value="idfieldset" name="test:attrs:id" class="attr id">
          <fieldset name="test:value" class="test">
            <legend>my legend</legend>
            <input type="text" value="1" name="test:sub1:attrs:id" class="attr id">
            <div><textarea name="test:sub1:value" class="sub1" rows="2">textarea 1</textarea></div>
            <input type="text" value="2" name="test:sub2:attrs:id" class="attr id">
            <div><textarea name="test:sub2:value" class="sub2" rows="2">textarea 2</textarea></div>
          </fieldset>
        </div>
        """)


class TestFormField(TestCase):

    def test_display(self):
        form = forms.FormField(name='form')
        # No value
        self.assertEqual(form.display(), '')
        sub1 = forms.TextAreaField(name='sub1', key='sub1', value='textarea 1',
                                  parent=form)
        sub2 = forms.TextAreaField(name='sub2', key='sub2', value='textarea 2',
                                  parent=form)
        form.children = [sub1, sub2]
        tw2test.assert_eq_xml(form.display(), """
          <form name="form:value" method="POST">
            <fieldset name="form:value">
              <div><textarea name="form:sub1:value" class="sub1">textarea 1</textarea></div>
              <div><textarea name="form:sub2:value" class="sub2">textarea 2</textarea></div>
            </fieldset>
            <input type="submit" />
          </form>
        """)


class TestConditionalContainer(TestCase):

    def test_init(self):
        field = forms.ConditionalContainer(name='test')
        self.assertEqual(field.possible_children, [])

    def test_get_children(self):
        field = forms.ConditionalContainer(name='test')
        self.assertEqual(field.get_children(), [])

        sub1 = forms.TextAreaField(name='sub1', key='sub1', parent=field)
        sub2 = forms.TextAreaField(name='sub2', key='sub2', parent=field)
        field.possible_children = [sub1, sub2]
        self.assertEqual(field.get_children(), [])

        o = cls()
        o.sub1 = cls()
        o.sub1.value = 'first textarea'
        field.set_value(o)
        self.assertEqual(field.get_children(), [sub1])

    def test_display(self):
        field = forms.ConditionalContainer(name='test')
        self.assertEqual(field.display(), '')

        sub1 = forms.TextAreaField(name='sub1', key='sub1', parent=field)
        sub2 = forms.TextAreaField(name='sub2', key='sub2', parent=field)
        field.possible_children = [sub1, sub2]

        o = cls()
        o.sub1 = cls()
        o.sub1.value = 'first textarea'
        field.set_value(o)
        tw2test.assert_eq_xml(field.display(), """
          <div>
            <div>
              <textarea name="test:sub1:value" class="sub1" rows="2">first textarea</textarea>
            </div>
          </div>
        """)

class TestGrowingContainer(TestCase):

    def test_init(self):
        field = forms.GrowingContainer(name='test')
        field.child = None
        field.legend = 'None'

    def test_get_children(self):
        field = forms.GrowingContainer(name='test')
        child = forms.TextAreaField(name='textarea_child', parent=field)
        field.child = child
        self.assertEqual(field.get_children(), [])

        o = cls()
        o.value = ['hello world']
        field.set_value(o)
        children = field.get_children()
        self.assertEqual(len(children), 1)
        self.assertTrue(children[0] != child)
        self.assertEqual(child.name + ':0', children[0].name)
        self.assertEqual(child.parent, children[0].parent)

    def test_display(self):
        field = forms.GrowingContainer(name='test')
        self.assertEqual(field.display(), '')
        child = forms.TextAreaField(name='textarea_child', parent=field)
        field.child = child
        self.assertEqual(field.display(), '')

        o = cls()
        o.value = ['hello', 'world']
        field.set_value(o)
        tw2test.assert_eq_xml(field.display(), """
          <fieldset name="test:value">
            <div><textarea name="test:textarea_child:0:value" rows="2">hello</textarea></div>
            <div><textarea name="test:textarea_child:1:value" rows="2">world</textarea></div>
          </fieldset>
        """)

