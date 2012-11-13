from unittest import TestCase
import xmlforms.forms as forms
import xmlforms.dtd_parser as dtd_parser
import tw2.core.testbase as tw2test

# Set to True to print the html used in the javascript test
generate_javascript = False


class cls(object):
    attrs = {}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


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
        field._name = None
        field.add_value_str = False
        self.assertEqual(field.get_name(), 'test')
        field._name = None
        field.add_value_str = True
        field.parent = forms.Field(name='parent1')
        self.assertEqual(field.get_name(), 'parent1:test:value')
        field._name = None
        field.parent.add_value_str = False
        field.add_value_str = False
        self.assertEqual(field.get_name(), 'parent1:test')
        field._name = None
        field.add_value_str = True
        field.parent.add_value_str = True
        field.parent.name = None
        field.parent._name = None
        self.assertEqual(field.get_name(), 'test:value')
        field._name = None
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

    def test_display(self):
        field = forms.Field(name='test')
        self.failUnlessRaises(NotImplementedError, field.display)


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

    def test_display_with_attrs(self):
        field = forms.TextAreaField(name='test', key='test')
        o = cls()
        o.value = 'Hello'
        o.attrs = {'id': 1}
        field.set_value(o)
        expected = '''
        <div class="container">
          <input type="text" value="1" name="test:attrs:id" id="test:attrs:id" class="attr id">
          <input type="button" value="Add test" class="add-button hidden">
          <div>
            <label>None</label>
            <input type="button" value="Delete test" class="delete-button">
            <textarea name="test:value" id="test" class="test" rows="2">Hello</textarea>
           </div>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_more_lines(self):
        field = forms.TextAreaField(name='test', key='test')
        o = cls()
        o.value = 'Hello\nWorld\n!'
        o.attrs = {'id': 1}
        field.set_value(o)
        expected = '''
        <div class="container">
          <input type="text" value="1" name="test:attrs:id" id="test:attrs:id" class="attr id">
          <input type="button" value="Add test" class="add-button hidden">
          <div>
            <label>None</label>
            <input type="button" value="Delete test" class="delete-button">
            <textarea name="test:value" id="test" class="test" rows="3">Hello\nWorld\n!</textarea>
          </div>
        </div>
        '''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_empty_non_required(self):
        field = forms.TextAreaField(name='test', key='test', label='test')
        expected = '''
        <div class="container">
          <input type="button" value="Add test" class="add-button">
          <div class="deleted">
            <label>test</label>
            <input type="button" value="Delete test" class="delete-button">
            <textarea name="test:value" id="test" class="test"></textarea>
          </div>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_non_empty_non_required(self):
        field = forms.TextAreaField(name='test', key='test', label='test')
        o = cls(value=dtd_parser.UNDEFINED, attrs={})
        field.set_value(o)
        expected = '''
        <div class="container">
          <input type="button" value="Add test" class="add-button hidden">
          <div>
            <label>test</label>
            <input type="button" value="Delete test" class="delete-button">
            <textarea name="test:value" id="test" class="test" rows="2">
            </textarea>
          </div>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_empty_required(self):
        field = forms.TextAreaField(name='test', key='test', label='test',
                                    required=True)
        expected = '''
        <div class="container">
          <label>test</label>
          <textarea name="test:value" id="test" class="test">
          </textarea>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_non_empty_required(self):
        field = forms.TextAreaField(name='test', key='test', label='test',
                                    required=True)
        o = cls(value='Hello World', attrs={})
        field.set_value(o)
        expected = '''
        <div class="container">
          <label>test</label>
          <textarea name="test:value" id="test" class="test" rows="2">Hello World</textarea>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_growing_parent(self):
        parent = forms.GrowingContainer(key='test')
        field = forms.TextAreaField(name='test', key='test', label='test',
                                    parent=parent)
        expected = '''
        <div class="container">
          <label>test</label>
          <input type="button" value="Delete test" class="growing-delete-button">
          <textarea name="test:value" id="test" class="test"></textarea>
          <input type="button" value="New test" class="growing-add-button">
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)


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
        field = forms.Fieldset(name='test', key='test', legend='test')
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
        expected = '''
        <div class="container">
          <input type="text" value="idfieldset" name="test:attrs:id" id="test:attrs:id" class="attr id">
          <input type="button" value="Add test" class="add-button hidden">
          <fieldset id="test" class="test">
            <legend>test<input type="button" value="Delete test" class="fieldset-delete-button">
            </legend>
            <div class="container">
              <input type="text" value="1" name="test:sub1:attrs:id" id="test:sub1:attrs:id" class="attr id">
              <input type="button" value="Add sub1" class="add-button hidden">
              <div>
                <label>None</label>
                <input type="button" value="Delete sub1" class="delete-button">
                <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">textarea 1</textarea>
              </div>
            </div>
            <div class="container">
              <input type="text" value="2" name="test:sub2:attrs:id" id="test:sub2:attrs:id" class="attr id">
              <input type="button" value="Add sub2" class="add-button hidden">
              <div>
                <label>None</label>
                <input type="button" value="Delete sub2" class="delete-button">
                <textarea name="test:sub2:value" id="test:sub2" class="sub2" rows="2">textarea 2</textarea>
              </div>
            </div>
          </fieldset>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_not_required(self):
        field = forms.Fieldset(name='test', key='test', legend='test')
        self.assertEqual(field.display(), '')
        sub1 = forms.TextAreaField(name='sub1', key='sub1', value='textarea 1',
                                  parent=field)
        field.children = [sub1]
        expected = '''
        <div class="container">
          <input type="button" value="Add test" class="add-button">
          <fieldset id="test" class="test deleted">
            <legend>test<input type="button" value="Delete test" class="fieldset-delete-button">
            </legend>
            <div class="container">
              <input type="button" value="Add sub1" class="add-button hidden">
              <div>
                <label>None</label>
                <input type="button" value="Delete sub1" class="delete-button">
                <textarea name="test:sub1:value" id="test:sub1" class="sub1">textarea 1</textarea>
              </div>
            </div>
          </fieldset>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_required(self):
        field = forms.Fieldset(name='test', key='test', legend='test',
                               required=True)
        sub1 = forms.TextAreaField(name='sub1', key='sub1', value='textarea 1',
                                  parent=field)
        field.children = [sub1]
        expected = '''
        <div class="container">
          <fieldset id="test" class="test">
            <legend>test</legend>
            <div class="container">
              <input type="button" value="Add sub1" class="add-button hidden">
              <div>
                <label>None</label>
                <input type="button" value="Delete sub1" class="delete-button">
                <textarea name="test:sub1:value" id="test:sub1" class="sub1">textarea 1</textarea>
              </div>
            </div>
          </fieldset>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_growing_parent(self):
        parent = forms.GrowingContainer(key='test')
        field = forms.Fieldset(name='test', key='test', legend='test',
                               required=True, parent=parent)
        parent.child = field
        sub1 = forms.TextAreaField(name='sub1', key='sub1', value='textarea 1',
                                  parent=field)
        field.children = [sub1]
        expected = '''
        <div class="container">
          <fieldset id="test" class="test">
            <legend>test<input type="button" value="Delete test" class="growing-fieldset-delete-button">
            </legend>
            <div class="container">
              <input type="button" value="Add sub1" class="add-button hidden">
              <div>
                <label>None</label>
                <input type="button" value="Delete sub1" class="delete-button">
                <textarea name="test:sub1:value" id="test:sub1" class="sub1">textarea 1</textarea>
              </div>
            </div>
          </fieldset>
          <input type="button" value="New test" class="growing-add-button">
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)


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
        expected = '''
        <form method="POST">
          <fieldset>
            <legend>None</legend>
            <div class="container">
              <input type="button" value="Add sub1" class="add-button hidden">
              <div>
                <label>None</label>
                <input type="button" value="Delete sub1" class="delete-button">
                <textarea name="form:sub1:value" id="form:sub1" class="sub1">textarea 1</textarea>
              </div>
            </div>
            <div class="container">
              <input type="button" value="Add sub2" class="add-button hidden">
              <div>
                <label>None</label>
                <input type="button" value="Delete sub2" class="delete-button">
                <textarea name="form:sub2:value" id="form:sub2" class="sub2">textarea 2</textarea>
              </div>
            </div>
          </fieldset>
          <input type="submit" />
        </form>'''
        tw2test.assert_eq_xml(form.display(), expected)


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

    def test_display_textareas(self):
        field = forms.ConditionalContainer(name='test')
        self.assertEqual(field.display(), '')

        sub1 = forms.TextAreaField(name='sub1', key='sub1', parent=field)
        sub2 = forms.TextAreaField(name='sub2', key='sub2', parent=field)
        field.possible_children = [sub1, sub2]

        o = cls()
        o.sub1 = cls()
        o.sub1.value = 'first textarea'
        field.set_value(o)
        expected = '''
        <div class="conditional-container">
          <select class="hidden conditional">
            <option value="">Add new</option>
            <option value="test:sub1:option:0">sub1</option>
            <option value="test:sub2:option:1">sub2</option>
          </select>
          <div class="container conditional-option test:sub1:option:0">
            <input type="button" value="Add sub1" class="add-button hidden">
            <div>
              <label>None</label>
              <input type="button" value="Delete sub1" class="delete-button">
              <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>
            </div>
          </div>
          <div class="container deleted conditional-option test:sub2:option:1">
            <input type="button" value="Add sub2" class="add-button">
            <div class="deleted">
              <label>None</label>
              <input type="button" value="Delete sub2" class="delete-button">
              <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>
            </div>
          </div>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_textareas_no_value(self):
        field = forms.ConditionalContainer(name='test')
        self.assertEqual(field.display(), '')

        sub1 = forms.TextAreaField(name='sub1', key='sub1', parent=field)
        sub2 = forms.TextAreaField(name='sub2', key='sub2', parent=field)
        field.possible_children = [sub1, sub2]

        expected = '''
        <div class="conditional-container">
          <select class="conditional">
            <option value="">Add new</option>
            <option value="test:sub1:option:0">sub1</option>
            <option value="test:sub2:option:1">sub2</option>
          </select>
          <div class="container deleted conditional-option test:sub1:option:0">
            <input type="button" value="Add sub1" class="add-button">
            <div class="deleted">
              <label>None</label>
              <input type="button" value="Delete sub1" class="delete-button">
              <textarea name="test:sub1:value" id="test:sub1" class="sub1"></textarea>
            </div>
          </div>
          <div class="container deleted conditional-option test:sub2:option:1">
            <input type="button" value="Add sub2" class="add-button">
            <div class="deleted">
              <label>None</label>
              <input type="button" value="Delete sub2" class="delete-button">
              <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>
            </div>
          </div>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)

    def test_display_growing(self):
        field = forms.ConditionalContainer(name='test')
        growing1 = forms.GrowingContainer(key='growing1', name='growing1')
        child1 = forms.TextAreaField(name='textarea_child1', parent=growing1)
        growing1.child = child1
        growing2 = forms.GrowingContainer(key='growing2', name='growing2')
        child2 = forms.TextAreaField(name='textarea_child2', parent=growing2)
        growing2.child = child2
        field.possible_children = [growing1, growing2]

        expected = '''
        <div class="conditional-container">
          <select class="conditional">
            <option value="">Add new</option>
            <option value="growing1:option:0">growing1</option>
            <option value="growing2:option:1">growing2</option>
          </select>
          <div class="deleted conditional-option growing1:option:0 growing-container">
            <div class="container growing-source" id="growing1:textarea_child1">
              <label>None</label>
              <input type="button" value="Delete None" class="growing-delete-button">
              <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>
              <input type="button" value="New growing1" class="growing-add-button">
            </div>
          </div>
          <div class="deleted conditional-option growing2:option:1 growing-container">
            <div class="container growing-source" id="growing2:textarea_child2">
              <label>None</label>
              <input type="button" value="Delete None" class="growing-delete-button">
              <textarea name="growing2:textarea_child2:0:value" id="growing2:textarea_child2:0" rows="2"></textarea>
              <input type="button" value="New growing2" class="growing-add-button">
            </div>
          </div>
        </div>'''
        tw2test.assert_eq_xml(field.display(), expected)


class TestGrowingContainer(TestCase):

    def test_init(self):
        field = forms.GrowingContainer(name='test')
        field.child = None
        field.legend = 'None'

    def test_get_children(self):
        field = forms.GrowingContainer(name='test')
        child = forms.TextAreaField(name='textarea_child', parent=field)
        field.child = child
        child1, = field.get_children()
        self.assertTrue(child1 != child)
        self.assertEqual(child1.name, 'textarea_child:0')
        self.assertEqual(child1.parent, field)
        self.assertEqual(child1.required, True)
        self.assertTrue('growing-source' in child1.container_css_classes)

        child.required = True
        o = cls()
        o.value = ['hello', 'world']
        field.set_value(o)
        child1, child2, child3 = field.get_children()
        self.assertTrue(child1 != child)
        self.assertTrue(child2 != child)
        self.assertTrue(child3 != child)
        self.assertEqual(child1.name, 'textarea_child:0')
        self.assertEqual(child1.parent, field)
        self.assertEqual(child1.required, True)
        self.assertEqual(child1.value, None)
        self.assertEqual(child2.name, 'textarea_child:1')
        self.assertEqual(child2.parent, field)
        self.assertEqual(child2.required, True)
        self.assertEqual(child2.value, 'hello')
        self.assertEqual(child3.name, 'textarea_child:2')
        self.assertEqual(child3.parent, field)
        self.assertEqual(child3.required, False)
        self.assertEqual(child3.value, 'world')

    def test_display(self):
        field = forms.GrowingContainer(key='test', name='test')
        self.assertEqual(field.display(), '')
        child = forms.TextAreaField(key='test', name='textarea_child', parent=field)
        field.child = child
        expected = '''
        <div class="growing-container">
          <div class="container growing-source" id="test:textarea_child">
            <label>None</label>
            <input type="button" value="Delete test" class="growing-delete-button">
            <textarea name="test:textarea_child:0:value" id="test:textarea_child:0" class="test" rows="2"></textarea>
            <input type="button" value="New test" class="growing-add-button">
          </div>
        </div>
        '''
        tw2test.assert_eq_xml(field.display(), expected)

        field = forms.GrowingContainer(key='test', name='test', required=True,
                                      child=child)
        values = []
        for index, s in enumerate(['hello', 'world']):
            o = cls()
            o.value = s
            o.attrs = {'idtest': 'test%i' % index}
            values += [o]
        field.set_value(values)
        expected = '''
        <div class="growing-container required">
          <div class="container growing-source" id="test:textarea_child">
            <label>None</label>
            <input type="button" value="Delete test" class="growing-delete-button">
            <textarea name="test:textarea_child:0:value" id="test:textarea_child:0" class="test" rows="2"></textarea>
            <input type="button" value="New test" class="growing-add-button">
          </div>
          <div class="container">
            <input type="text" value="test0" name="test:textarea_child:1:attrs:idtest" id="test:textarea_child:1:attrs:idtest" class="attr idtest">
            <label>None</label>
            <input type="button" value="Delete test" class="growing-delete-button">
            <textarea name="test:textarea_child:1:value" id="test:textarea_child:1" class="test" rows="2">hello</textarea>
            <input type="button" value="New test" class="growing-add-button">
          </div>
          <div class="container">
            <input type="text" value="test1" name="test:textarea_child:2:attrs:idtest" id="test:textarea_child:2:attrs:idtest" class="attr idtest">
            <label>None</label>
            <input type="button" value="Delete test" class="growing-delete-button">
            <textarea name="test:textarea_child:2:value" id="test:textarea_child:2" class="test" rows="2">world</textarea>
            <input type="button" value="New test" class="growing-add-button">
          </div>
        </div>'''

        '''
        <div class="growing-container growing-container required">
          <div class="container growing-source" id="test:textarea_child">
          <label>None</label>
          <input type="button" value="Delete test" class="growing-delete-button"><textarea name="test:textarea_child:0:value" id="test:textarea_child:0" class="test" rows="2"></textarea><input type="button" value="New test" class="growing-add-button"></div>
<div class="container"><input type="text" value="test0" name="test:textarea_child:1:attrs:idtest" id="test:textarea_child:1:attrs:idtest" class="attr idtest"><label>None</label><input type="button" value="Delete test" class="growing-delete-button"><textarea name="test:textarea_child:1:value" id="test:textarea_child:1" class="test" rows="2">hello</textarea><input type="button" value="New test" class="growing-add-button"></div>
<div class="container"><input type="text" value="test1" name="test:textarea_child:2:attrs:idtest" id="test:textarea_child:2:attrs:idtest" class="attr idtest"><label>None</label><input type="button" value="Delete test" class="growing-delete-button"><textarea name="test:textarea_child:2:value" id="test:textarea_child:2" class="test" rows="2">world</textarea><input type="button" value="New test" class="growing-add-button"></div></div> 

        '''
        tw2test.assert_eq_xml(field.display(), expected)


class JavascriptTestGenerator(TestCase):

    def test_print(self):

        if generate_javascript:
            # We want to generate the html needed for the javascript tests
            print 'Delete button'
            field = forms.TextAreaField(name='test', key='test')
            o = cls()
            o.value = 'Hello'
            o.attrs = {'id': 1}
            field.set_value(o)
            print '<div>%s</div>' % field.display()

            print 'Growing delete button'
            field = forms.GrowingContainer(key='test')
            child = forms.TextAreaField(name='test', key='test', label='test',
                                        parent=field)
            field.child = child
            print '<div>%s</div>' % field.display()

            print 'Fieldset delete button'
            field = forms.Fieldset(name='test', key='test', legend='test')
            sub1 = forms.TextAreaField(name='sub1', key='sub1',
                                       value='textarea 1', parent=field)
            field.children = [sub1]
            o = cls()
            o.sub1 = cls()
            o.sub1.value = 'textarea 1'
            field.set_value(o)
            print '<div>%s</div>' % field.display()

            print 'Growing fieldset delete button'
            parent = forms.GrowingContainer(key='test')
            field = forms.Fieldset(name='test', key='test', legend='test',
                                   required=True, parent=parent)
            parent.child = field
            sub1 = forms.TextAreaField(name='sub1', key='sub1',
                                       value='textarea 1', parent=field)
            field.children = [sub1]
            print '<div>%s</div>' % parent.display()

            print 'Conditional container'
            field = forms.ConditionalContainer(name='test')
            sub1 = forms.TextAreaField(name='sub1', key='sub1', parent=field)
            sub2 = forms.TextAreaField(name='sub2', key='sub2', parent=field)
            field.possible_children = [sub1, sub2]
            o = cls()
            o.sub1 = cls()
            o.sub1.value = 'first textarea'
            field.set_value(o)
            print '<div>%s</div>' % field.display()

            print 'Conditional container with Growing'
            field = forms.ConditionalContainer(name='test')
            growing1 = forms.GrowingContainer(key='growing1', name='growing1')
            child1 = forms.TextAreaField(
                name='textarea_child1', parent=growing1)
            growing1.child = child1
            growing2 = forms.GrowingContainer(key='growing2', name='growing2')
            child2 = forms.TextAreaField(
                name='textarea_child2', parent=growing2)
            growing2.child = child2
            field.possible_children = [growing1, growing2]
            print '<div>%s</div>' % field.display()

