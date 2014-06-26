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

    test("increment_id", function() {
        var elt = $('<div id="name:0:_value" data-id="name:0:_value" />');
        elt.append('<div class="class1 name:0:class1 otherprefix:0:class1" />');
        elt.append('<div data-target="#name:0:target" />');
        var prefix = 'name';
        xmltool.utils.increment_id(prefix, elt, 0);
        equal(elt.attr('id'), 'name:1:_value');
        equal(elt.data('id'), 'name:1:_value');
        var child1 = $(elt.children()[0]);
        equal(child1.attr('class'), 'class1 name:1:class1 otherprefix:0:class1');
        var child2 = $(elt.children()[1]);
        equal(child2.data('target'), '#name:1:target');
    });

    test("increment_id many elts", function() {
        var container = $('<div/>');
        var elt1 = $('<div id="name:0:_value" data-id="name:0:_value" />');
        elt1.append('<div class="class1 name:0:class1 otherprefix:0:class1" />');
        elt1.append('<div data-target="#name:0:target" />');
        var elt2 = $('<div id="name:1:_value" data-id="name:1:_value" />');
        elt2.append('<div class="class1 name:1:class1 otherprefix:1:class1" />');
        elt2.append('<div data-target="#name:1:target" />');
        var prefix = 'name';
        var elts = container.append(elt1).append(elt2).children();
        xmltool.utils.increment_id(prefix, elts, 0);
        equal(elt1.attr('id'), 'name:1:_value');
        equal(elt1.data('id'), 'name:1:_value');
        var child11 = $(elt1.children()[0]);
        equal(child11.attr('class'), 'class1 name:1:class1 otherprefix:0:class1');
        var child12 = $(elt1.children()[1]);
        equal(child12.data('target'), '#name:1:target');

        equal(elt2.attr('id'), 'name:2:_value');
        equal(elt2.data('id'), 'name:2:_value');
        var child21 = $(elt2.children()[0]);
        equal(child21.attr('class'), 'class1 name:2:class1 otherprefix:1:class1');
        var child22 = $(elt2.children()[1]);
        equal(child22.data('target'), '#name:2:target');
    });

    test("increment_id many elts with step", function() {
        var container = $('<div/>');
        var a1 = $('<a id="name:0:_link" />');
        var elt1 = $('<div id="name:0:_value" data-id="name:0:_value" />');
        elt1.append('<div class="class1 name:0:class1 otherprefix:0:class1" />');
        elt1.append('<div data-target="#name:0:target" />');
        var a2 = $('<a id="name:1:_link" />');
        var elt2 = $('<div id="name:1:_value" data-id="name:1:_value" />');
        elt2.append('<div class="class1 name:1:class1 otherprefix:1:class1" />');
        elt2.append('<div data-target="#name:1:target" />');
        var prefix = 'name';
        var elts = container.append(a1).append(elt1).append(a2).append(elt2).children();
        xmltool.utils.increment_id(prefix, elts, 0, 2);
        equal(a1.attr('id'), 'name:1:_link');
        equal(elt1.attr('id'), 'name:2:_value');
        equal(elt1.data('id'), 'name:2:_value');
        var child11 = $(elt1.children()[0]);
        equal(child11.attr('class'), 'class1 name:2:class1 otherprefix:0:class1');
        var child12 = $(elt1.children()[1]);
        equal(child12.data('target'), '#name:2:target');

        equal(a2.attr('id'), 'name:2:_link');
        equal(elt2.attr('id'), 'name:3:_value');
        equal(elt2.data('id'), 'name:3:_value');
        var child21 = $(elt2.children()[0]);
        equal(child21.attr('class'), 'class1 name:3:class1 otherprefix:1:class1');
        var child22 = $(elt2.children()[1]);
        equal(child22.data('target'), '#name:3:target');
    });

    test("increment_id many elts with step and offset", function() {
        var container = $('<div/>');
        var a1 = $('<a id="name:0:_link" />');
        var elt1 = $('<div id="name:0:_value" data-id="name:0:_value" />');
        elt1.append('<div class="class1 name:0:class1 otherprefix:0:class1" />');
        elt1.append('<div data-target="#name:0:target" />');
        var a2 = $('<a id="name:1:_link" />');
        var elt2 = $('<div id="name:1:_value" data-id="name:1:_value" />');
        elt2.append('<div class="class1 name:1:class1 otherprefix:1:class1" />');
        elt2.append('<div data-target="#name:1:target" />');
        var prefix = 'name';
        var elts = container.append(a1).append(elt1).append(a2).append(elt2).children();
        xmltool.utils.increment_id(prefix, elts, 0, 2, 1);
        equal(a1.attr('id'), 'name:1:_link');
        equal(elt1.attr('id'), 'name:1:_value');
        equal(elt1.data('id'), 'name:1:_value');
        var child11 = $(elt1.children()[0]);
        equal(child11.attr('class'), 'class1 name:1:class1 otherprefix:0:class1');
        var child12 = $(elt1.children()[1]);
        equal(child12.data('target'), '#name:1:target');

        equal(a2.attr('id'), 'name:2:_link');
        equal(elt2.attr('id'), 'name:2:_value');
        equal(elt2.data('id'), 'name:2:_value');
        var child21 = $(elt2.children()[0]);
        equal(child21.attr('class'), 'class1 name:2:class1 otherprefix:1:class1');
        var child22 = $(elt2.children()[1]);
        equal(child22.data('target'), '#name:2:target');
    });

    test("decrement_id", function() {
        var elt = $('<div id="name:1:_value" data-id="name:1:_value" />');
        elt.append('<div class="class1 name:1:class1 otherprefix:1:class1" />');
        elt.append('<div data-target="#name:1:target" />');
        var prefix = 'name';
        xmltool.utils.decrement_id(prefix, elt, 0);
        equal(elt.attr('id'), 'name:0:_value');
        equal(elt.data('id'), 'name:0:_value');
        var child1 = $(elt.children()[0]);
        equal(child1.attr('class'), 'class1 name:0:class1 otherprefix:1:class1');
        var child2 = $(elt.children()[1]);
        equal(child2.data('target'), '#name:0:target');
    });

    test("decrement_id many elts", function() {
        var container = $('<div/>');
        var elt1 = $('<div id="name:1:_value" data-id="name:1:_value" />');
        elt1.append('<div class="class1 name:1:class1 otherprefix:0:class1" />');
        elt1.append('<div data-target="#name:1:target" />');
        var elt2 = $('<div id="name:2:_value" data-id="name:2:_value" />');
        elt2.append('<div class="class1 name:2:class1 otherprefix:1:class1" />');
        elt2.append('<div data-target="#name:2:target" />');
        var prefix = 'name';
        var elts = container.append(elt1).append(elt2).children();
        xmltool.utils.decrement_id(prefix, elts, 0);
        equal(elt1.attr('id'), 'name:0:_value');
        equal(elt1.data('id'), 'name:0:_value');
        var child11 = $(elt1.children()[0]);
        equal(child11.attr('class'), 'class1 name:0:class1 otherprefix:0:class1');
        var child12 = $(elt1.children()[1]);
        equal(child12.data('target'), '#name:0:target');

        equal(elt2.attr('id'), 'name:1:_value');
        equal(elt2.data('id'), 'name:1:_value');
        var child21 = $(elt2.children()[0]);
        equal(child21.attr('class'), 'class1 name:1:class1 otherprefix:1:class1');
        var child22 = $(elt2.children()[1]);
        equal(child22.data('target'), '#name:1:target');
    });

    test("_replace_id", function() {
        var elt = $('<div id="name:0:_value" data-name="name:0:_value"/>');
        equal(elt.attr('id'), 'name:0:_value');
        equal(elt.data('name'), 'name:0:_value');
        var prefix = 'name';
        var func = xmltool.utils._attr;
        var names = ['id', 'name', 'data-name'];
        xmltool.utils._replace_id(prefix, elt, func, names, 10);
        equal(elt.attr('id'), 'name:10:_value');
        // Weird, the data('name') is not updated, only the attr is updated
        equal(elt.data('name'), 'name:0:_value');
        equal(elt.attr('data-name'), 'name:10:_value');

        xmltool.utils._replace_id(prefix, elt, func, names, 5);
        equal(elt.attr('id'), 'name:5:_value');
        equal(elt.data('name'), 'name:0:_value');
        equal(elt.attr('data-name'), 'name:5:_value');
    });

    test("_replace_id_collapse", function() {
        var prefix = 'name';
        var elt = $('<div href="#collapse-name\\:0\\:test" id="#name:1:_value" />');
        var func = xmltool.utils._attr;
        var names = ['href', 'id'];
        xmltool.utils._replace_id(prefix, elt, func, names, 10);
        equal(elt.attr('href'), '#collapse-name\\:10\\:test');
        equal(elt.attr('id'), '#name:10:_value');
    });

    test("replace_id many elts", function() {
        var container = $('<div/>');
        var elt1 = $('<div id="name:1:_value" data-id="name:1:_value" />');
        elt1.append('<div class="class1 name:0:class1 otherprefix:1:class1" />');
        elt1.append('<div data-target="#name:1:target" />');
        var elt2 = $('<div id="name:5:_value" data-id="name:5:_value" />');
        elt2.append('<div class="class5 name:1:class1 otherprefix:5:class1" />');
        elt2.append('<div data-target="#name:5:target" />');
        var prefix = 'name';
        var elts = container.append(elt1).append(elt2).children();
        xmltool.utils.replace_id(prefix, elts);
        equal(elt1.attr('id'), 'name:0:_value');
        equal(elt1.data('id'), 'name:0:_value');
        var child11 = $(elt1.children()[0]);
        equal(child11.attr('class'), 'class1 name:0:class1 otherprefix:1:class1');
        var child12 = $(elt1.children()[1]);
        equal(child12.data('target'), '#name:0:target');

        equal(elt2.attr('id'), 'name:1:_value');
        equal(elt2.data('id'), 'name:1:_value');
        var child21 = $(elt2.children()[0]);
        equal(child21.attr('class'), 'class5 name:1:class1 otherprefix:5:class1');
        var child22 = $(elt2.children()[1]);
        equal(child22.data('target'), '#name:1:target');
    });

    test("replace_id with step", function() {
        var container = $('<div/>');
        var elt1_a = $('<a id="name:1:_link" />');
        var elt1 = $('<div id="name:1:_value" data-id="name:1:_value" />');
        elt1.append('<div class="class1 name:0:class1 otherprefix:1:class1" />');
        elt1.append('<div data-target="#name:1:target" />');
        var elt2_a = $('<div id="name:5:_link" />');
        var elt2 = $('<div id="name:5:_value" data-id="name:5:_value" />');
        elt2.append('<div class="class5 name:1:class1 otherprefix:5:class1" />');
        elt2.append('<div data-target="#name:5:target" />');
        var prefix = 'name';
        var elts = container.append(elt1_a).append(elt1).append(elt2_a).append(elt2).children();
        xmltool.utils.replace_id(prefix, elts, 2);
        equal(elt1_a.attr('id'), 'name:0:_link');
        equal(elt1.attr('id'), 'name:0:_value');
        equal(elt1.data('id'), 'name:0:_value');
        var child11 = $(elt1.children()[0]);
        equal(child11.attr('class'), 'class1 name:0:class1 otherprefix:1:class1');
        var child12 = $(elt1.children()[1]);
        equal(child12.data('target'), '#name:0:target');

        equal(elt2_a.attr('id'), 'name:1:_link');
        equal(elt2.attr('id'), 'name:1:_value');
        equal(elt2.data('id'), 'name:1:_value');
        var child21 = $(elt2.children()[0]);
        equal(child21.attr('class'), 'class5 name:1:class1 otherprefix:5:class1');
        var child22 = $(elt2.children()[1]);
        equal(child22.data('target'), '#name:1:target');
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

    test('update_contenteditable_eol', function(){
        expect(4);
        var s = 'Hello world\nNew line';
        var res = xmltool.utils.update_contenteditable_eol(s);
        var expected = 'Hello worldNew line';
        equal(res, expected);

        s = 'Hello world\nNew<br />\n line';
        res = xmltool.utils.update_contenteditable_eol(s);
        expected = 'Hello worldNew\n line';
        equal(res, expected);

        s = 'Hello world\r\nNew<br>\n line';
        res = xmltool.utils.update_contenteditable_eol(s);
        expected = 'Hello worldNew\n line';
        equal(res, expected);

        s = 'Hello world\rNew<br >\n line';
        res = xmltool.utils.update_contenteditable_eol(s);
        expected = 'Hello worldNew\n line';
        equal(res, expected);

    });

}(jQuery));
