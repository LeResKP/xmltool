QUnit.module('Test functions');

test("xmltools.replace_id", function() {
    expect(3);
    var html = '<div id="test:0:qcm:1">Hello world</div>'
    var expected = '<div id="test:0:qcm:1">Hello world</div>'
    obj = $(html);
    xmltools.replace_id(obj, 1, 'test:0:qcm');
    equal(obj.html(), $(expected).html(), 'Replacement');

    var html = ['<div id="test:0:qcm">',
        '<div id="test:0:qcm:0:container">',
        '  <input id="test:0:qcm:0:id" name="test:0:qcm:0:name" />',
        '  <input id="test:0:qcm:0:value" />',
        '  <div id="test:0:qcm:0:container:0:subcontainer">',
            '  <textarea id="test:0:qcm:0:container:0:subcontainer:id" name="test:0:qcm:0:container:0:subcontainer:name"></textarea>',
            '  <textarea name="test:0:qcm:0:container:0:subcontainer:value"></textarea>',
        '  </div>',
        '</div>',
        '</div>'
    ].join('\n')
    var expected = ['<div id="test:0:qcm">',
        '<div id="test:0:qcm:11:container">',
        '  <input id="test:0:qcm:11:id" name="test:0:qcm:11:name" />',
        '  <input id="test:0:qcm:11:value"/>',
        '  <div id="test:0:qcm:11:container:0:subcontainer">',
            '  <textarea id="test:0:qcm:11:container:0:subcontainer:id" name="test:0:qcm:11:container:0:subcontainer:name"></textarea>',
            '  <textarea name="test:0:qcm:11:container:0:subcontainer:value"></textarea>',
        '  </div>',
        '</div>',
        '</div>'
    ].join('\n')

    var obj = $(html);
    xmltools.replace_id(obj, 11);
    equal(obj.html(), $(expected).html(), 'With no container_id given');

    var expected = ['<div id="test:0:qcm">',
        '<div id="test:11:qcm:0:container">',
        '  <input id="test:11:qcm:0:id" name="test:11:qcm:0:name" />',
        '  <input id="test:11:qcm:0:value" />',
        '  <div id="test:11:qcm:0:container:0:subcontainer">',
            '  <textarea id="test:11:qcm:0:container:0:subcontainer:id" name="test:11:qcm:0:container:0:subcontainer:name"></textarea>',
            '  <textarea name="test:11:qcm:0:container:0:subcontainer:value"></textarea>',
        '  </div>',
        '</div>',
        '</div>'
    ].join('\n')
    var obj = $(html);
    xmltools.replace_id(obj, 11, 'test');
    equal(obj.html(), $(expected).html(), 'With container_id given');
});

test("xmltools.has_field", function() {
    expect(4)
    var container = [
    '<div>',
    '  <div class="container conditional-option test:sub1:option:0">',
    '    <input type="button" value="Add sub1" class="add-button hidden">',
    '    <div>',
    '      <label>None</label>',
    '      <input type="button" value="Delete sub1" class="delete-button">',
    '      <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')
    equal(xmltools.has_field($(container)), true, 'textarea field');

    var container = [
    '<div>',
    '  <div class="container conditional-option test:sub1:option:0">',
    '    <input type="button" value="Add sub1" class="add-button hidden">',
    '    <div class="deleted">',
    '      <label>None</label>',
    '      <input type="button" value="Delete sub1" class="delete-button">',
    '      <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')
    equal(xmltools.has_field($(container)), false, 'deleted textarea field');

    var container = [
    '<div>',
    '  <div class="deleted conditional-option growing1:option:0 growing-container">',
    '    <div class="container growing-source" id="growing1:textarea_child1">',
    '      <label>None</label>',
    '      <input type="button" value="Delete None" class="growing-delete-button">',
    '      <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>',
    '      <input type="button" value="New growing1" class="growing-add-button">',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')
    equal(xmltools.has_field($(container)), false, 'growing field (only growing-source)');

    var container = [
    '<div>',
    '  <div class="deleted conditional-option growing1:option:0 growing-container">',
    '    <div class="container growing-source" id="growing1:textarea_child1">',
    '      <label>None</label>',
    '      <input type="button" value="Delete None" class="growing-delete-button">',
    '      <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>',
    '      <input type="button" value="New growing1" class="growing-add-button">',
    '    </div>',
    '    <div class="container" id="growing1:textarea_child1">',
    '      <label>None</label>',
    '      <input type="button" value="Delete None" class="growing-delete-button">',
    '      <textarea name="growing1:textarea_child1:1:value" id="growing1:textarea_child1:1" rows="2"></textarea>',
    '      <input type="button" value="New growing1" class="growing-add-button">',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')
    equal(xmltools.has_field($(container)), true, 'growing field');
});

test("xmltools.update_conditional_container", function() {
    expect(2);
    var html = [
    '<div>',
    '  <div class="conditional-container">',
    '    <select class="hidden conditional">',
    '      <option value="">Add new</option>',
    '      <option value="test:sub1:option:0">sub1</option>',
    '      <option value="test:sub2:option:1">sub2</option>',
    '    </select>',
    '    <div class="container conditional-option test:sub1:option:0">',
    '      <input type="button" value="Add sub1" class="add-button hidden">',
    '      <div>',
    '        <label>None</label>',
    '        <input type="button" value="Delete sub1" class="delete-button">',
    '        <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '      </div>',
    '    </div>',
    '    <div class="container deleted conditional-option test:sub2:option:1">',
    '      <input type="button" value="Add sub2" class="add-button">',
    '      <div class="deleted">',
    '      <label>None</label>',
    '      <input type="button" value="Delete sub2" class="delete-button">',
    '      <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    var obj = $(html);
    var container = obj.find('.conditional-option:first > div:first');
    xmltools.update_conditional_container(container)
    equal(obj.html(), $(html).html(), 'Nothing has changed')

    var expected = [
    '<div>',
    '  <div class="conditional-container">',
    '    <select class="conditional">',
    '      <option value="">Add new</option>',
    '      <option value="test:sub1:option:0">sub1</option>',
    '      <option value="test:sub2:option:1">sub2</option>',
    '    </select>',
    '    <div class="container conditional-option test:sub1:option:0 deleted">',
    '      <input type="button" value="Add sub1" class="add-button hidden">',
    '      <div class="deleted">',
    '        <label>None</label>',
    '        <input type="button" value="Delete sub1" class="delete-button">',
    '        <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '      </div>',
    '    </div>',
    '    <div class="container deleted conditional-option test:sub2:option:1">',
    '      <input type="button" value="Add sub2" class="add-button">',
    '      <div class="deleted">',
    '      <label>None</label>',
    '      <input type="button" value="Delete sub2" class="delete-button">',
    '      <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    container.addClass('deleted');
    xmltools.update_conditional_container(container)
    equal(obj.html(), $(expected).html(), 'Select is displayed')
})

test("Button", function() {
    expect(2);
    var html = [
        '<div>',
        '  <div class="container">',
        '    <input type="text" value="1" name="test:attrs:id" id="test:attrs:id" class="attr id">',
        '    <input type="button" value="Add test" class="add-button hidden">',
        '    <div>',
        '      <label>None</label>',
        '      <input type="button" value="Delete test" class="delete-button">',
        '      <textarea name="test:value" id="test" class="test" rows="2">Hello</textarea>',
        '    </div>',
        '  </div>',
        '</div>'].join('\n');

    var expected = [
        '<div>',
        '  <div class="container">',
        '    <input type="text" value="1" name="test:attrs:id" id="test:attrs:id" class="attr id" />',
        '    <input type="button" value="Add test" class="add-button" />',
        '    <div class="deleted">',
        '      <label>None</label>',
        '      <input type="button" value="Delete test" class="delete-button" />',
        '      <textarea name="test:value" id="test" class="test" rows="2">Hello</textarea>',
        '    </div>',
        '  </div>',
        '</div>'].join('\n')
    var obj = $(html);
    obj.appendTo($('body'));
    obj.find('.delete-button').trigger('click');
    equal(obj.html(), $(expected).html(), 'delete button');

    $(expected).find('.add-button').trigger('click');
    equal($(expected).html(), obj.html(), 'add button');
    obj.remove();
});

test("Growing button", function() {
    expect(2);
    var html = [
    '<div>',
    '  <div class="growing-container">',
    '    <div class="container growing-source" id="test">',
    '      <label>test</label>',
    '      <input type="button" value="Delete test" class="growing-delete-button">',
    '      <textarea name="test:0:value" id="test:0" class="test" rows="2"></textarea>',
    '      <input type="button" value="New test" class="growing-add-button">',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    var expected = [
    '<div>',
    '  <div class="growing-container">',
    '    <div class="container growing-source" id="test">',
    '      <label>test</label>',
    '      <input type="button" value="Delete test" class="growing-delete-button">',
    '      <textarea name="test:0:value" id="test:0" class="test" rows="2"></textarea>',
    '      <input type="button" value="New test" class="growing-add-button">',
    '    </div><div class="container">',
    '      <label>test</label>',
    '      <input type="button" value="Delete test" class="growing-delete-button">',
    '      <textarea name="test:1:value" id="test:1" class="test" rows="2"></textarea>',
    '      <input type="button" value="New test" class="growing-add-button">',
    '    </div>',
    '  </div>',
    '</div>',
    ].join('\n')
    var obj = $(html);
    obj.appendTo($('body'));
    obj.find('.growing-add-button').trigger('click');
    equal(obj.html(), $(expected).html(), 'add button');

    $(expected).find('.growing-delete-button:last').trigger('click');
    equal($(expected).html(), obj.html(), 'delete button');
    obj.remove();
});

test("Fieldset button", function() {
    expect(2);
    var html = [
    '<div>',
    '  <div class="container">',
    '    <input type="button" value="Add test" class="add-button hidden">',
    '    <fieldset id="test" class="test">',
    '      <legend>',
    '      test<input type="button" value="Delete test" class="fieldset-delete-button">',
    '      </legend>',
    '      <div class="container">',
    '        <input type="button" value="Add sub1" class="add-button hidden">',
    '        <div>',
    '          <label>None</label>',
    '          <input type="button" value="Delete sub1" class="delete-button">',
    '          <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">',
    '          textarea 1</textarea>',
    '        </div>',
    '      </div>',
    '    </fieldset>',
    '  </div>',
    '</div>'
    ].join('\n')

    var expected = [
    '<div>',
    '  <div class="container">',
    '    <input type="button" value="Add test" class="add-button">',
    '    <fieldset id="test" class="test deleted">',
    '      <legend>',
    '      test<input type="button" value="Delete test" class="fieldset-delete-button">',
    '      </legend>',
    '      <div class="container">',
    '        <input type="button" value="Add sub1" class="add-button hidden">',
    '        <div>',
    '          <label>None</label>',
    '          <input type="button" value="Delete sub1" class="delete-button">',
    '          <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">',
    '          textarea 1</textarea>',
    '        </div>',
    '      </div>',
    '    </fieldset>',
    '  </div>',
    '</div>'
    ].join('\n')
    var obj = $(html);
    obj.appendTo($('body'));
    obj.find('.fieldset-delete-button').trigger('click');
    equal(obj.html(), $(expected).html(), 'delete button');

    $(expected).find('.add-button').trigger('click');
    equal($(expected).html(), obj.html(), 'add button');
    obj.remove();
});

test("Growing fieldset button", function() {
    expect(2);
    var html = [
    '<div>',
    '  <div class="growing-container">',
    '    <div class="container growing-source" id="test">',
    '      <fieldset id="test:0" class="test">',
    '        <legend>',
    '        test<input type="button" value="Delete test" class="growing-fieldset-delete-button">',
    '        </legend>',
    '        <div class="container">',
    '          <input type="button" value="Add sub1" class="add-button">',
    '          <div class="deleted">',
    '            <label>None</label>',
    '            <input type="button" value="Delete sub1" class="delete-button">',
    '            <textarea name="test:0:sub1:value" id="test:0:sub1" class="sub1" rows="2"></textarea>',
    '          </div>',
    '        </div>',
    '      </fieldset>',
    '      <input type="button" value="New test" class="growing-add-button">',
    '    </div>',
    '  </div>',
    '</div>',
    ].join('\n')

    var expected = [
    '<div>',
    '  <div class="growing-container">',
    '    <div class="container growing-source" id="test">',
    '      <fieldset id="test:0" class="test">',
    '        <legend>',
    '        test<input type="button" value="Delete test" class="growing-fieldset-delete-button">',
    '        </legend>',
    '        <div class="container">',
    '          <input type="button" value="Add sub1" class="add-button">',
    '          <div class="deleted">',
    '            <label>None</label>',
    '            <input type="button" value="Delete sub1" class="delete-button">',
    '            <textarea name="test:0:sub1:value" id="test:0:sub1" class="sub1" rows="2"></textarea>',
    '          </div>',
    '        </div>',
    '      </fieldset>',
    '      <input type="button" value="New test" class="growing-add-button">',
    '    </div><div class="container">',
    '      <fieldset id="test:1" class="test">',
    '        <legend>',
    '        test<input type="button" value="Delete test" class="growing-fieldset-delete-button">',
    '        </legend>',
    '        <div class="container">',
    '          <input type="button" value="Add sub1" class="add-button">',
    '          <div class="deleted">',
    '            <label>None</label>',
    '            <input type="button" value="Delete sub1" class="delete-button">',
    '            <textarea name="test:1:sub1:value" id="test:1:sub1" class="sub1" rows="2"></textarea>',
    '          </div>',
    '        </div>',
    '      </fieldset>',
    '      <input type="button" value="New test" class="growing-add-button">',
    '    </div>',
    '  </div>',
    '</div>',
    ].join('\n')
    var obj = $(html);
    obj.appendTo($('body'));
    obj.find('.growing-add-button').trigger('click');
    equal(obj.html(), $(expected).html(), 'add button');

    $(expected).find('.growing-fieldset-delete-button:last').trigger('click');
    equal($(expected).html(), obj.html(), 'delete button');
    obj.remove();
});

test("Select on conditional", function() {
    expect(3);

    var html = [
    '<div>',
    '  <div class="conditional-container">',
    '    <select class="conditional">',
    '      <option value="">Add new</option>',
    '      <option value="test:sub1:option:0">sub1</option>',
    '      <option value="test:sub2:option:1">sub2</option>',
    '    </select>',
    '    <div class="container conditional-option test:sub1:option:0 deleted">',
    '      <input type="button" value="Add sub1" class="add-button hidden">',
    '      <div class="deleted">',
    '        <label>None</label>',
    '        <input type="button" value="Delete sub1" class="delete-button">',
    '        <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '      </div>',
    '    </div>',
    '    <div class="container deleted conditional-option test:sub2:option:1">',
    '      <input type="button" value="Add sub2" class="add-button">',
    '      <div class="deleted">',
    '      <label>None</label>',
    '      <input type="button" value="Delete sub2" class="delete-button">',
    '      <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    var obj = $(html);
    var select = obj.find('select');
    obj.appendTo($('body'));
    select.trigger('change');
    equal(obj.html(), $(html).html(), 'Nothing has changed')

    var expected = [
    '<div>',
    '  <div class="conditional-container">',
    '    <select class="conditional hidden">',
    '      <option value="">Add new</option>',
    '      <option value="test:sub1:option:0">sub1</option>',
    '      <option value="test:sub2:option:1">sub2</option>',
    '    </select>',
    '    <div class="container conditional-option test:sub1:option:0 deleted">',
    '      <input type="button" value="Add sub1" class="add-button hidden">',
    '      <div class="deleted">',
    '        <label>None</label>',
    '        <input type="button" value="Delete sub1" class="delete-button">',
    '        <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '      </div>',
    '    </div>',
    '    <div class="container conditional-option test:sub2:option:1">',
    '      <input type="button" value="Add sub2" class="add-button hidden">',
    '      <div>',
    '      <label>None</label>',
    '      <input type="button" value="Delete sub2" class="delete-button">',
    '      <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    select.val(select.find('option:last').val());
    select.trigger('change');
    equal(obj.html(), $(expected).html(), 'Display last option')
    obj.remove();

    var html = [
    '<div>',
    '  <div class="conditional-container">',
    '    <select class="conditional">',
    '      <option value="">Add new</option>',
    '      <option value="growing1:option:0">growing1</option>',
    '      <option value="growing2:option:1">growing2</option>',
    '    </select>',
    '    <div class="deleted conditional-option growing1:option:0 growing-container">',
    '      <div class="container growing-source" id="growing1:textarea_child1">',
    '        <label>None</label>',
    '        <input type="button" value="Delete None" class="growing-delete-button">',
    '        <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>',
    '        <input type="button" value="New growing1" class="growing-add-button">',
    '      </div>',
    '    </div>',
    '    <div class="deleted conditional-option growing2:option:1 growing-container">',
    '      <div class="container growing-source" id="growing2:textarea_child2">',
    '        <label>None</label>',
    '        <input type="button" value="Delete None" class="growing-delete-button">',
    '        <textarea name="growing2:textarea_child2:0:value" id="growing2:textarea_child2:0" rows="2"></textarea>',
    '        <input type="button" value="New growing2" class="growing-add-button">',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    var expected = [
    '<div>',
    '  <div class="conditional-container">',
    '    <select class="conditional hidden">',
    '      <option value="">Add new</option>',
    '      <option value="growing1:option:0">growing1</option>',
    '      <option value="growing2:option:1">growing2</option>',
    '    </select>',
    '    <div class="deleted conditional-option growing1:option:0 growing-container">',
    '      <div class="container growing-source" id="growing1:textarea_child1">',
    '        <label>None</label>',
    '        <input type="button" value="Delete None" class="growing-delete-button">',
    '        <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>',
    '        <input type="button" value="New growing1" class="growing-add-button">',
    '      </div>',
    '    </div>',
    '    <div class="conditional-option growing2:option:1 growing-container">',
    '      <div class="container growing-source" id="growing2:textarea_child2">',
    '        <label>None</label>',
    '        <input type="button" value="Delete None" class="growing-delete-button">',
    '        <textarea name="growing2:textarea_child2:0:value" id="growing2:textarea_child2:0" rows="2"></textarea>',
    '        <input type="button" value="New growing2" class="growing-add-button">',
    '      </div><div class="container">',
    '        <label>None</label>',
    '        <input type="button" value="Delete None" class="growing-delete-button">',
    '        <textarea name="growing2:textarea_child2:1:value" id="growing2:textarea_child2:1" rows="2"></textarea>',
    '        <input type="button" value="New growing2" class="growing-add-button">',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    var obj = $(html);
    var select = obj.find('select');
    select.val(select.find('option:last').val());
    obj.appendTo($('body'));
    select.trigger('change');
    equal(obj.html(), $(expected).html(), 'Conditional container with Growing');
    obj.remove();
});

test("form submit", function() {
    expect(1);

    var html = [
    '<div>',
    '<form action="javascript:">',
    '<input type="text" value="1" name="input1" />',
    '<input type="text" value="2" name="input2" class="deleted" />',
    '<div class="deleted">',
    '  <input type="text" value="3" name="input3" class="deleted" />',
    '</div>',
    '<div>',
    '  <input type="text" value="4" name="input4" class="deleted" />',
    '  <input type="text" value="5" name="input5" />',
    '</div>',
    '<div class="growing-source">',
    '  <input type="text" value="6" name="input6" />',
    '</div>',
    '</form>',
    '</div>',
    ].join('\n');

    var obj = $(html);
    var form = obj.find('form');
    obj.appendTo($('body'));
    form.trigger('submit');
    equal(form.serialize(), 'input1=1&input5=5', 'submit');
    obj.remove();
});

/*
jsdom.env({
  html: "<html><body></body></html>",
  scripts: [
    'http://code.jquery.com/jquery-1.5.min.js'
  ]
}, function (err, window) {
  var $ = window.jQuery;

  $('body').append("<div class='testing'>Hello World</div>");
  console.log($(".testing").text()); // outputs Hello World
});
*/
