(function($) {
    module('xmltool.utils');

    test("escape_id", function() {
        expect(1);
        equal(xmltool.utils.escape_id('bob:1'), 'bob\\:1', 'id escaped');
    });

    test("get_prefix", function() {
        expect(1);
        equal(xmltool.utils.get_prefix('bob:children:10'), 'bob:children');
    });

    test("get_index", function() {
        expect(1);
        equal(xmltool.utils.get_index('bob:children:10'), 10);
    });

    test("_attr", function() {
        expect(3);
        var elt = $('<input type="text" />');
        var res = xmltool.utils._attr(elt, 'type');
        equal(res, 'text');

        res = xmltool.utils._attr(elt, 'type', 'email');
        equal(typeof(res), 'undefined');
        equal(elt.attr('type'), 'email');
    });

    test("_data", function() {
        expect(3);
        var elt = $('<input type="text" data-id="test" />');
        var res = xmltool.utils._data(elt, 'id');
        equal(res, 'test');

        res = xmltool.utils._data(elt, 'id', 'my-id');
        equal(typeof(res), 'undefined');
        equal(elt.data('id'), 'my-id');
    });

    test("_increment_id", function() {
        expect(6);
        var elt = $('<div id="name:0:_value" data-name="data-name:0:_value"/>');
        equal(elt.attr('id'), 'name:0:_value');
        equal(elt.data('name'), 'data-name:0:_value');
        var prefix = 'name';
        var func = xmltool.utils._attr;
        var names = ['id', 'name'];
        var diff = 1;
        xmltool.utils._increment_id(prefix, elt, func, names, diff);
        equal(elt.attr('id'), 'name:1:_value');
        equal(elt.data('name'), 'data-name:0:_value');

        func = xmltool.utils._data;
        prefix = 'data-name';
        xmltool.utils._increment_id(prefix, elt, func, names, diff);
        equal(elt.attr('id'), 'name:1:_value');
        equal(elt.data('name'), 'data-name:1:_value');
    });

    test("increment_id", function() {
        var elt = $('<div id="name:0:_value" data-id="name:0:_value" />');
        elt.append('<div class="class1 name:0:class1 otherprefix:0:class1" />');
        elt.append('<div data-target="name:0:target" />');
        var prefix = 'name';
        xmltool.utils.increment_id(prefix, elt);
        equal(elt.attr('id'), 'name:1:_value');
        equal(elt.data('id'), 'name:1:_value');
        var child1 = $(elt.children()[0]);
        equal(child1.attr('class'), 'class1 name:1:class1 otherprefix:0:class1');
        var child2 = $(elt.children()[1]);
        equal(child2.data('target'), 'name:1:target');
    });

    test("decrement_id", function() {
        var elt = $('<div id="name:1:_value" data-id="name:1:_value" />');
        elt.append('<div class="class1 name:1:class1 otherprefix:1:class1" />');
        elt.append('<div data-target="name:1:target" />');
        var prefix = 'name';
        xmltool.utils.decrement_id(prefix, elt);
        equal(elt.attr('id'), 'name:0:_value');
        equal(elt.data('id'), 'name:0:_value');
        var child1 = $(elt.children()[0]);
        equal(child1.attr('class'), 'class1 name:0:class1 otherprefix:1:class1');
        var child2 = $(elt.children()[1]);
        equal(child2.data('target'), 'name:0:target');
    });

    test("_replace_id", function() {
        var elt = $('<div id="name:0:_value" data-name="data-name:0:_value"/>');
        equal(elt.attr('id'), 'name:0:_value');
        equal(elt.data('name'), 'data-name:0:_value');
        var prefix = 'name';
        var func = xmltool.utils._attr;
        var names = ['id', 'name'];
        xmltool.utils._replace_id(prefix, elt, func, names, 10);
        equal(elt.attr('id'), 'name:10:_value');
        equal(elt.data('name'), 'data-name:0:_value');

        func = xmltool.utils._data;
        prefix = 'data-name';
        xmltool.utils._increment_id(prefix, elt, func, names, 5);
        equal(elt.attr('id'), 'name:10:_value');
        equal(elt.data('name'), 'data-name:5:_value');
    });

    test('truncate', function(){
        expect(2);
        var text = 'Short text';
        equal(xmltool.utils.truncate(text, 30), text, 'Short text is not truncated');
        text = 'This text is very too long and will be truncated';
        var expected = 'This text is very too long and...';
        equal(xmltool.utils.truncate(text, 30), expected, 'Long text is truncated');
    });

    test('get_first_class', function(){
        expect(3);
        var elt = $('<div>');
        var res = xmltool.utils.get_first_class(elt);
        equal(res, null);

        elt = $('<div class="class1">');
        res = xmltool.utils.get_first_class(elt);
        equal(res, 'class1');

        elt = $('<div class="class1 class2">');
        res = xmltool.utils.get_first_class(elt);
        equal(res, 'class1');
    });


}(jQuery));
