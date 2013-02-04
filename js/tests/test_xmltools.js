QUnit.module('Test xmltools functions');

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
    '    <a class="add-button hidden">Add sub1</a>',
    '    <div>',
    '      <label>None</label>',
    '      <a class="delete-button">Delete sub1</a>',
    '      <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')
    equal(xmltools.has_field($(container)), true, 'textarea field');

    var container = [
    '<div>',
    '  <div class="container conditional-option test:sub1:option:0">',
    '    <a class="add-button hidden">Add sub1</a>',
    '    <div class="deleted">',
    '      <label>None</label>',
    '      <a class="delete-button">Delete sub1</a>',
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
    '      <a class="growing-delete-button">Delete None</a>',
    '      <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>',
    '      <a class="growing-add-button">New growing1</a>',
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
    '      <a class="growing-delete-button">Delete None</a>',
    '      <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>',
    '      <a class="growing-add-button">New growing1</a>',
    '    </div>',
    '    <div class="container" id="growing1:textarea_child1">',
    '      <label>None</label>',
    '      <a class="growing-delete-button">Delete None</a>',
    '      <textarea name="growing1:textarea_child1:1:value" id="growing1:textarea_child1:1" rows="2"></textarea>',
    '      <a class="growing-add-button">New growing1</a>',
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
    '      <a class="add-button hidden">Add sub1</a>',
    '      <div>',
    '        <label>None</label>',
    '        <a class="delete-button">Delete sub1</a>',
    '        <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '      </div>',
    '    </div>',
    '    <div class="container deleted conditional-option test:sub2:option:1 inline">',
    '      <a class="add-button">Add sub2</a>',
    '      <div class="deleted">',
    '      <label>None</label>',
    '      <a class="delete-button">Delete sub2</a>',
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
    '      <a class="add-button hidden">Add sub1</a>',
    '      <div class="deleted">',
    '        <label>None</label>',
    '        <a class="delete-button">Delete sub1</a>',
    '        <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '      </div>',
    '    </div>',
    '    <div class="container deleted conditional-option test:sub2:option:1 inline">',
    '      <a class="add-button">Add sub2</a>',
    '      <div class="deleted">',
    '      <label>None</label>',
    '      <a class="delete-button">Delete sub2</a>',
    '      <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    container.addClass('deleted');
    xmltools.update_conditional_container(container)
    equal(obj.html(), $(expected).html(), 'Select is displayed')
});

test("xmltools.truncate", function() {
    expect(2);
    var text = 'Short text';
    equal(xmltools.truncate(text, 30), text, 'Short text is not truncated');
    var text = 'This text is very too long and will be truncated';
    var expected = 'This text is very too long and...';
    equal(xmltools.truncate(text, 30), expected, 'Long text is truncated');
});

test("xmltools.get_first_class", function() {
    expect(2);
    var elt = $('<li/>');
    equal(xmltools.get_first_class(elt), '', 'no class');

    var elt = $('<li class="class1 class2"/>');
    equal(xmltools.get_first_class(elt), 'class1', 'ok first class');
});

test("xmltools.escape_id", function() {
    expect(1);
    equal(xmltools.escape_id('bob:1'), 'bob\\:1', 'id escaped');
});

test("Button", function() {
    expect(2);
    var html = [
        '<div>',
        '  <div class="container">',
        '    <input type="text" value="1" name="test:attrs:id" id="test:attrs:id" class="attr id">',
        '    <a class="add-button hidden">Add test</a>',
        '    <div>',
        '      <label>None</label>',
        '      <a class="delete-button">Delete test</a>',
        '      <textarea name="test:value" id="test" class="test" rows="2">Hello</textarea>',
        '    </div>',
        '  </div>',
        '</div>'].join('\n');

    var expected = [
        '<div>',
        '  <div class="container inline">',
        '    <input type="text" value="1" name="test:attrs:id" id="test:attrs:id" class="attr id" />',
        '    <a class="add-button">Add test</a>',
        '    <div class="deleted">',
        '      <label>None</label>',
        '      <a class="delete-button">Delete test</a>',
        '      <textarea name="test:value" id="test" class="test" rows="2">Hello</textarea>',
        '    </div>',
        '  </div>',
        '</div>'].join('\n')
    var obj = $(html);
    obj.xmltools();
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
    '      <a class="growing-delete-button">Delete test</a>',
    '      <textarea name="test:0:value" id="test:0" class="test" rows="2"></textarea>',
    '      <a class="growing-add-button">New test</a>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    var expected = [
    '<div>',
    '  <div class="growing-container">',
    '    <div class="container growing-source" id="test">',
    '      <label>test</label>',
    '      <a class="growing-delete-button">Delete test</a>',
    '      <textarea name="test:0:value" id="test:0" class="test" rows="2"></textarea>',
    '      <a class="growing-add-button">New test</a>',
    '    </div><div class="container">',
    '      <label>test</label>',
    '      <a class="growing-delete-button">Delete test</a>',
    '      <textarea name="test:1:value" id="test:1" class="test" rows="2"></textarea>',
    '      <a class="growing-add-button">New test</a>',
    '    </div>',
    '  </div>',
    '</div>',
    ].join('\n')
    var obj = $(html);
    obj.xmltools();
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
    '    <a class="add-button hidden">Add test</a>',
    '    <fieldset id="test" class="test">',
    '      <legend>',
    '      test<a class="fieldset-delete-button">Delete test</a>',
    '      </legend>',
    '      <div class="container">',
    '        <a class="add-button hidden">Add sub1</a>',
    '        <div>',
    '          <label>None</label>',
    '          <a class="delete-button">Delete sub1</a>',
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
    '  <div class="container inline">',
    '    <a class="add-button">Add test</a>',
    '    <fieldset id="test" class="test deleted">',
    '      <legend>',
    '      test<a class="fieldset-delete-button">Delete test</a>',
    '      </legend>',
    '      <div class="container">',
    '        <a class="add-button hidden">Add sub1</a>',
    '        <div>',
    '          <label>None</label>',
    '          <a class="delete-button">Delete sub1</a>',
    '          <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">',
    '          textarea 1</textarea>',
    '        </div>',
    '      </div>',
    '    </fieldset>',
    '  </div>',
    '</div>'
    ].join('\n')
    var obj = $(html);
    obj.xmltools();
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
    '        test<a class="growing-fieldset-delete-button">Delete test</a>',
    '        </legend>',
    '        <div class="container inline">',
    '          <a class="add-button">Add sub1</a>',
    '          <div class="deleted">',
    '            <label>None</label>',
    '            <a class="delete-button">Delete sub1</a>',
    '            <textarea name="test:0:sub1:value" id="test:0:sub1" class="sub1" rows="2"></textarea>',
    '          </div>',
    '        </div>',
    '      </fieldset>',
    '      <a class="growing-add-button">New test</a>',
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
    '        test<a class="growing-fieldset-delete-button">Delete test</a>',
    '        </legend>',
    '        <div class="container inline">',
    '          <a class="add-button">Add sub1</a>',
    '          <div class="deleted">',
    '            <label>None</label>',
    '            <a class="delete-button">Delete sub1</a>',
    '            <textarea name="test:0:sub1:value" id="test:0:sub1" class="sub1" rows="2"></textarea>',
    '          </div>',
    '        </div>',
    '      </fieldset>',
    '      <a class="growing-add-button">New test</a>',
    '    </div><div class="container">',
    '      <fieldset id="test:1" class="test">',
    '        <legend>',
    '        test<a class="growing-fieldset-delete-button">Delete test</a>',
    '        </legend>',
    '        <div class="container inline">',
    '          <a class="add-button">Add sub1</a>',
    '          <div class="deleted">',
    '            <label>None</label>',
    '            <a class="delete-button">Delete sub1</a>',
    '            <textarea name="test:1:sub1:value" id="test:1:sub1" class="sub1" rows="2"></textarea>',
    '          </div>',
    '        </div>',
    '      </fieldset>',
    '      <a class="growing-add-button">New test</a>',
    '    </div>',
    '  </div>',
    '</div>',
    ].join('\n')
    var obj = $(html);
    obj.xmltools();
    obj.find('.growing-add-button').trigger('click');
    equal(obj.html(), $(expected).html(), 'add button');

    $(expected).find('.growing-fieldset-delete-button:last').trigger('click');
    equal($(expected).html(), obj.html(), 'delete button');
    obj.remove();
});

test("Select on conditional", function() {
    expect(10);
    $('<div id="tree"></div>').appendTo($("body"));
    var counter = 0;
    xmltools.jstree.add_node = function(){
        counter += 1;
    };

    var html = [
    '<div>',
    '  <div class="conditional-container">',
    '    <select class="conditional">',
    '      <option value="">Add new</option>',
    '      <option value="test:sub1:option:0">sub1</option>',
    '      <option value="test:sub2:option:1">sub2</option>',
    '    </select>',
    '    <div class="container conditional-option test:sub1:option:0 deleted">',
    '      <a class="add-button hidden">Add sub1</a>',
    '      <div class="deleted">',
    '        <label>None</label>',
    '        <a class="delete-button">Delete sub1</a>',
    '        <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '      </div>',
    '    </div>',
    '    <div class="container deleted conditional-option test:sub2:option:1 inline">',
    '      <a class="add-button">Add sub2</a>',
    '      <div class="deleted">',
    '      <label>None</label>',
    '      <a class="delete-button">Delete sub2</a>',
    '      <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    var obj = $(html);
    var select = obj.find('select');
    obj.xmltools({
        jstree_selector: '#tree',
        jstree_url: 'http://fake.url'
    });
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
    '      <a class="add-button hidden">Add sub1</a>',
    '      <div class="deleted">',
    '        <label>None</label>',
    '        <a class="delete-button">Delete sub1</a>',
    '        <textarea name="test:sub1:value" id="test:sub1" class="sub1" rows="2">first textarea</textarea>',
    '      </div>',
    '    </div>',
    '    <div class="container conditional-option test:sub2:option:1">',
    '      <a class="add-button hidden">Add sub2</a>',
    '      <div>',
    '      <label>None</label>',
    '      <a class="delete-button">Delete sub2</a>',
    '      <textarea name="test:sub2:value" id="test:sub2" class="sub2"></textarea>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    equal(counter, 0, 'Counter has not changed');
    select.val(select.find('option:last').val());
    select.trigger('change');
    equal(obj.html(), $(expected).html(), 'Display last option')
    obj.remove();
    equal(counter, 1, 'Counter has changed');


    var html = [
        '<div><div class="conditional-container">',
        '<select class="conditional">',
        '<option value="">Add new</option>',
        '<option value="test:test1:option:0">test1</option>',
        '</select>',
        '<div class="container">',
        '<fieldset id="test:test1" class="test1 deleted conditional-option test:test1:option:0">',
        '<legend>test1</legend>',
        '<div class="container">',
        '<label>None</label>',
        '<textarea name="test:test1:sub1:value" id="test:test1:sub1" class="sub1"></textarea>',
        '</div>',
        '</fieldset></div>',
        '</div></div>',
    ].join('\n');
    
    var expected = [
        '<div><div class="conditional-container">',
        '<select class="conditional hidden">',
        '<option value="">Add new</option>',
        '<option value="test:test1:option:0">test1</option>',
        '</select>',
        '<div class="container">',
        '<fieldset id="test:test1" class="test1 conditional-option test:test1:option:0">',
        '<legend>test1</legend>',
        '<div class="container">',
        '<label>None</label>',
        '<textarea name="test:test1:sub1:value" id="test:test1:sub1" class="sub1"></textarea>',
        '</div>',
        '</fieldset></div>',
        '</div></div>',
    ].join('\n');
    

    equal(counter, 1, 'Counter has not changed');
    var obj = $(html);
    var select = obj.find('select');
    select.val(select.find('option:last').val());
    obj.xmltools({
        jstree_selector: '#tree',
        jstree_url: 'http://fake.url'
    });
    select.trigger('change');
    equal(obj.html(), $(expected).html(), 'Conditional container required children');
    equal(counter, 2, 'Counter has changed');
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
    '        <a class="growing-delete-button">Delete None</a>',
    '        <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>',
    '        <a class="growing-add-button">New growing1</a>',
    '      </div>',
    '    </div>',
    '    <div class="deleted conditional-option growing2:option:1 growing-container">',
    '      <div class="container growing-source" id="growing2:textarea_child2">',
    '        <label>None</label>',
    '        <a class="growing-delete-button">Delete None</a>',
    '        <textarea name="growing2:textarea_child2:0:value" id="growing2:textarea_child2:0" rows="2"></textarea>',
    '        <a class="growing-add-button">New growing2</a>',
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
    '        <a class="growing-delete-button">Delete None</a>',
    '        <textarea name="growing1:textarea_child1:0:value" id="growing1:textarea_child1:0" rows="2"></textarea>',
    '        <a class="growing-add-button">New growing1</a>',
    '      </div>',
    '    </div>',
    '    <div class="conditional-option growing2:option:1 growing-container">',
    '      <div class="container growing-source" id="growing2:textarea_child2">',
    '        <label>None</label>',
    '        <a class="growing-delete-button">Delete None</a>',
    '        <textarea name="growing2:textarea_child2:0:value" id="growing2:textarea_child2:0" rows="2"></textarea>',
    '        <a class="growing-add-button">New growing2</a>',
    '      </div><div class="container">',
    '        <label>None</label>',
    '        <a class="growing-delete-button">Delete None</a>',
    '        <textarea name="growing2:textarea_child2:1:value" id="growing2:textarea_child2:1" rows="2"></textarea>',
    '        <a class="growing-add-button">New growing2</a>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>'
    ].join('\n')

    var obj = $(html);
    var select = obj.find('select');
    equal(counter, 2, 'Counter has not changed');
    select.val(select.find('option:last').val());
    obj.xmltools({
        jstree_selector: '#tree',
        jstree_url: 'http://fake.url'
    });
    select.trigger('change');
    equal(obj.html(), $(expected).html(), 'Conditional container with Growing');
    obj.remove();
    equal(counter, 3, 'Counter has not changed');
});

test("form submit", function() {
    expect(1);

    var html = [
    '<div>',
    '<form action="javascript:" class="xmltools-form">',
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
    form.xmltools();
    obj.appendTo($("body"));
    form.trigger('submit');
    equal(form.serialize(), 'input1=1&input5=5', 'submit');
    obj.remove();
});


QUnit.module('Test xmltools.jstree functions');
test("xmltools.jstree.update_node", function() {
    expect(6);
    var node = $('<li class="tree_test:old:1 class1 class2" />');
    node.data('id', 'test:old:1');
    xmltools.jstree.update_node(node, 'test:old:1', 'test:new:1');
    equal(node.attr('id'), 'tree_test:new:1', 'id updated');
    equal(node.data('id'), 'test:new:1', 'data id updated');
    equal(node.attr('class'), 'tree_test:new:1 class1 class2', 'class updated');

    var node = $('<li class="tree_test:old:1:question class1 class2" />');
    node.data('id', 'test:old:1:question');
    xmltools.jstree.update_node(node, 'test:old:1', 'test:new:1');
    equal(node.attr('id'), 'tree_test:new:1:question', 'id updated');
    equal(node.data('id'), 'test:new:1:question', 'data id updated');
    equal(node.attr('class'), 'tree_test:new:1:question class1 class2', 'class updated');
});

test("xmltools.jstree.update_node_and_children", function() {
    expect(7);
    var node = $([
        '<li class="tree_test:old:1 class1 class2">',
        '<ul>',
        '<li class="tree_test:old:1:children0"/>',
        '<li class="tree_test:old:1:children1"/>',
        '</ul>',
        '</li>'
        ].join(''));
    node.data('id', 'test:old:1');
    node.find('li').each(function(index){
        $(this).data('id', 'test:old:1:children' + index);
    });
    xmltools.jstree.update_node_and_children(node, 'test:new:1');
    equal(node.attr('id'), 'tree_test:new:1', 'id updated');
    equal(node.data('id'), 'test:new:1', 'data id updated');
    equal(node.attr('class'), 'tree_test:new:1 class1 class2', 'class updated');
    var li1 = node.find('li:first');
    equal(li1.attr('id'), 'tree_test:new:1:children0', 'id updated');
    equal(li1.data('id'), 'test:new:1:children0', 'data id updated');
    var li2 = node.find('li:last');
    equal(li2.attr('id'), 'tree_test:new:1:children1', 'id updated');
    equal(li2.data('id'), 'test:new:1:children1', 'data id updated');

});

test("xmltools.jstree.increment_id", function() {
    expect(9);
    var html = [
    '<ul>',
    '  <li id="tree_test:comment:1" class="tree_test:comment"></li> ',
    '  <li id="tree_test:comment:1" class="tree_test:comment"></li> ',
    '  <li id="tree_test:comment:4"></li> ',
    '</ul>',
    ].join('\n');
    
    var obj = $(html);
    var lis = obj.find('li');
    obj.find('li').each(function(){
        $(this).data('id', $(this).attr('id').replace('tree_', ''));
    });
    var node = obj.find('li:first');
    xmltools.jstree.increment_id(node);
    equal($(lis[0]).attr('id'), 'tree_test:comment:1', "current node attr id hasn't changed");
    equal($(lis[0]).data('id'), 'test:comment:1', "current node data id hasn't changed");
    equal($(lis[0]).attr('class'), 'tree_test:comment', "current node class hasn't changed");

    equal($(lis[1]).attr('id'), 'tree_test:comment:2', "sibling node attr id has changed");
    equal($(lis[1]).data('id'), 'test:comment:2', "sibling node data id has changed");
    equal($(lis[1]).attr('class'), 'tree_test:comment', "sibling node class has changed");

    equal($(lis[2]).attr('id'), 'tree_test:comment:4', "no class node attr id hasn't changed");
    equal($(lis[2]).data('id'), 'test:comment:4', "no class node data id hasn't changed");
    equal($(lis[2]).attr('class'), '', "no class node class hasn't changed");
});

test("xmltools.jstree.increment_id with children", function() {
    expect(9);
    var html = [
    '<ul>',
    '  <li id="tree_test:comment:1" class="tree_test:comment"></li>',
    '  <li id="tree_test:comment:1" class="tree_test:comment">',
    '  <ul>',
    '    <li id="tree_test:comment:1:username" class="tree_test:comment:1:username">',
    '  </ul>',
    '  </li> ',
    '</ul>',
    ].join('\n');
    
    var obj = $(html);
    var lis = obj.find('li');
    obj.find('li').each(function(){
        $(this).data('id', $(this).attr('id').replace('tree_', ''));
    });
    var node = obj.find('li:first');
    xmltools.jstree.increment_id(node);
    equal($(lis[0]).attr('id'), 'tree_test:comment:1', "current node attr id hasn't changed");
    equal($(lis[0]).data('id'), 'test:comment:1', "current node data id hasn't changed");
    equal($(lis[0]).attr('class'), 'tree_test:comment', "current node class hasn't changed");

    equal($(lis[1]).attr('id'), 'tree_test:comment:2', "sibling node attr id has changed");
    equal($(lis[1]).data('id'), 'test:comment:2', "sibling node data id has changed");
    equal($(lis[1]).attr('class'), 'tree_test:comment', "sibling node class has changed");

    equal($(lis[2]).attr('id'), 'tree_test:comment:2:username', "child attr id has changed");
    equal($(lis[2]).data('id'), 'test:comment:2:username', "child data id has changed");
    equal($(lis[2]).attr('class'), 'tree_test:comment:2:username', "child class has changed");
});


test("xmltools.jstree.create_nodes", function() {
    expect(3);
    var tree = $('<div id="tree"></div>');
    var node = {
        data: 'node 1',
        attr: {
            'id': 'id1',
            'class': 'class1'
        }
    }
    tree.jstree();
    xmltools.jstree.create_nodes(tree, node, tree, 'inside');
    expected = [
        '<ul>',
        '<li id="id1" class="class1 jstree-last jstree-leaf">',
        '<ins class="jstree-icon">&nbsp;</ins>',
        '<a href="#"><ins class="jstree-icon">&nbsp;</ins>node 1</a>',
        '</li>',
        '</ul>'
    ].join('');
    equal(tree.html(), expected, 'add node');

    var tree = $('<div id="tree"></div>');
    var node = {
        data: 'node 1',
        attr: {
            'id': 'tree_id:1',
            'class': 'tree_class'
        },
        metadata:{
            'id': 'id:1'
        },
        children: [{
            data: 'node 2',
            attr: {
                'id': 'tree_id2',
                'class': 'tree_class2'
            },
            metadata: {
                'id': 'id2',
            }
        }]
    }
    tree.jstree();
    xmltools.jstree.create_nodes(tree, node, tree, 'inside');
    expected = [
        '<ul>',
        '<li id="tree_id:1" class="tree_class jstree-last jstree-open">',
        '<ins class="jstree-icon">&nbsp;</ins>',
        '<a href="#"><ins class="jstree-icon">&nbsp;</ins>node 1</a>',
        '<ul>',
        '<li id="tree_id2" class="tree_class2 jstree-last jstree-leaf">',
        '<ins class="jstree-icon">&nbsp;</ins>',
        '<a href="#"><ins class="jstree-icon">&nbsp;</ins>node 2</a>',
        '</li>',
        '</ul>',
        '</li>',
        '</ul>'
    ].join('');
    equal(tree.html(), expected, 'add node with children');

    var node = {
        data: 'node 3',
        attr: {
            'id': 'tree_id:1',
            'class': 'tree_class'
        },
        metadata:{
            'id': 'id:1',
        }
    }
    xmltools.jstree.create_nodes(tree, node, tree, 'inside');
    expected = [
        '<ul>',
        '<li id="tree_id:1" class="tree_class jstree-leaf">',
        '<ins class="jstree-icon">&nbsp;</ins>',
        '<a href="#"><ins class="jstree-icon">&nbsp;</ins>node 3</a>',
        '</li>',
        '<li id="tree_id:2" class="tree_class jstree-open jstree-last">',
        '<ins class="jstree-icon">&nbsp;</ins>',
        '<a href="#"><ins class="jstree-icon">&nbsp;</ins>node 1</a>',
        '<ul>',
        '<li id="tree_id2" class="tree_class2 jstree-leaf jstree-last">',
        '<ins class="jstree-icon">&nbsp;</ins>',
        '<a href="#"><ins class="jstree-icon">&nbsp;</ins>node 2</a>',
        '</li>',
        '</ul>',
        '</li>',
        '</ul>'
    ].join('')
    equal(tree.html(), expected, 'add node with increment_id');
});

test("xmltools.jstree.delete_node", function() {
    expect(2);

    var tree = $('<div id="tree"></div>');
    var node = {
        data: 'node 1',
        attr: {
            'id': 'tree_id1',
            'class': 'class1'
        }
    }
    tree.jstree();
    xmltools.jstree.create_nodes(tree, node, tree, 'inside');
    expected = [
        '<ul>',
        '<li id="tree_id1" class="class1 jstree-last jstree-leaf">',
        '<ins class="jstree-icon">&nbsp;</ins>',
        '<a href="#"><ins class="jstree-icon">&nbsp;</ins>node 1</a>',
        '</li>',
        '</ul>'
    ].join('');
    equal(tree.html(), expected, 'add node');
    
    var elt = $('<div id="id1"></div>');
    xmltools.jstree.delete_node(tree, elt);
    equal(tree.html(), '<ul></ul>', 'delete node');
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
