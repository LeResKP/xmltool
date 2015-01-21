(function($) {
	"use strict";

    var $fixture;
    var ns = xmltool.jstree;
    var fakeNode = {
        'a_attr': {
            id: 'tree_myid'
        }
    };

    var cleanTreeHtml = function(html) {
        // We should remove the generated ids
        return html.replace(/j[0-9]+_[0-9a-z]+/g, '');
    };

    module('xmltool.jstree.utils', {
        setup: function() {
          $fixture = $('#qunit-fixture');
        },
        teardown: function() {
            $fixture.html('');
        }
    });

    test("getFormId", function() {
        expect(1);
        var res = ns.utils.getFormId(fakeNode);
        equal(res, 'myid');
    });

    test("getFormElement", function() {
        expect(2);
        var $elt = ns.utils.getFormElement(fakeNode);
        equal($elt.length, 0, 'Found nothing');

        var $div = $('<div>').attr('id', 'myid');
        $fixture.append($div);
        $elt = ns.utils.getFormElement(fakeNode);
        equal($elt.get(0), $div.get(0), 'Found element in the dom');
    });

    test("getCollapsibleElement", function() {
        expect(2);
        var $elt = ns.utils.getCollapsibleElement(fakeNode);
        equal($elt.length, 0, 'Found nothing');

        var $col = $('<div>').addClass('panel-collapse');
        var $div = $('<div>').attr('id', 'myid').append($col);
        $fixture.append($div);
        $elt = ns.utils.getCollapsibleElement(fakeNode);
        equal($elt.get(0), $col.get(0), 'Found element in the dom');
    });

    test("getTreeElement", function() {
        expect(2);
        var $textarea = $('<textarea>');
        $fixture.append($textarea);
        var $node = $('<div>').attr('id', 'tree_myid');
        $fixture.append($node);

        var $elt = ns.utils.getTreeElement($textarea);
        equal($elt.length, 0, 'Found nothing');

        var $div = $('<div>').attr('id', 'myid').append($textarea);
        $fixture.append($div);
        $elt = ns.utils.getTreeElement($textarea);
        equal($elt.get(0), $node.get(0));
    });

    test("getTreeElementFromCollapsible", function() {
        expect(1);
        var $col = $('<div>').attr('id', 'collapse_myid');
        $fixture.append($col);
        var $node = $('<div>').attr('id', 'tree_myid');
        $fixture.append($node);

        var $elt = ns.utils.getTreeElementFromCollapsible($col);
        equal($elt.get(0), $node.get(0), 'Found element in the dom');
    });

    test("getFirstClass", function() {
        expect(3);
        var node = {
            'li_attr': {
                'class': 'class1 class2'
            }
        };
        var res = ns.utils.getFirstClass(node);
        equal(res, 'class1');

        node['li_attr']['class'] = 'class';
        res = ns.utils.getFirstClass(node);
        equal(res, 'class');

        node['li_attr']['class'] = '';
        res = ns.utils.getFirstClass(node);
        equal(res, '');
    });

    test("getFormPrefix", function() {
        expect(1);
        var node = {
            'li_attr': {
                'class': 'tree_class1 class2'
            }
        };
        var res = ns.utils.getFormPrefix(node);
        equal(res, 'class1');
    });

    test("findParentNodeAndPosition", function() {
        expect(3);
        var selectors = [['inside', '#myid']];
        var res = ns.utils.findParentNodeAndPosition(selectors);
        deepEqual(res, {});

        var $div = $('<div />').attr('id', 'myid');
        $fixture.append($div);
        res = ns.utils.findParentNodeAndPosition(selectors);
        equal(res.position, 'inside');
        equal(res.parentobj.attr('id'), 'myid');
    });

    test("getNodePositionInChildren", function() {
        expect(2);
        var node = {id: 'id1'},
            children = [{id: 'id2'}];
        var res = ns.utils.getNodePositionInChildren(node, children);
        equal(res, -1);

        children = [{id: 'id2'}, {id: 'id1'}];
        res = ns.utils.getNodePositionInChildren(node, children);
        equal(res, 1);
    });

    test("addNode", function() {
        expect(16);
        var $data;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/add_element/test-jstree.html',
            {async: false}
        ).done(function(data) {
            $data = $(data);
        });
        $data.find('.dom-test').each(function(index){
            if (index !== -1) {
            var $this = $(this),
                btn_selector = $this.attr('data-btn-selector'),
                url = $this.attr('data-url');

            var $input = $(this).find('.dom-input');
            var $jstree = $(this).find('.dom-jstree');
            var $expected = $(this).find('.dom-expected');
            var jstreeInput = $.parseJSON($jstree.text());
            var jstreeExpected = $.parseJSON($expected.text());
            $fixture.html($input);
            var $btn = $input.find(btn_selector);
            if ($btn.is('option')) {
                // The btn is the select
                $btn = $btn.parent();
            }
            var data;
            $.ajax('http://127.0.0.1:9999/' + url,
                  {async: false}
            ).done(function(d) {
                data = d;
            });
            // TODO: tree id is hardcoded fix this
            var $tree = $('<div/>').attr('id', 'tree');
            var $form = $('#xmltool-form');
            var $formContainer = $form.parent();
            $fixture.append($tree);
            xmltool.jstree.load($tree, jstreeInput, $form, $formContainer);
            var res = xmltool.jstree.utils.addNode($btn, $tree, data);
            ok(typeof res !== 'undefined');
            var inputHtml = $tree.html().replace(/j[0-9]+_[0-9a-z]+/g, '');
            $.jstree.destroy();
            $tree.html('');
            xmltool.jstree.load($tree, jstreeExpected, $form, $formContainer);
            // Just replaces the generated ids
            var expectedHtml = $tree.html().replace(/j[0-9]+_[0-9a-z]+/g, '');
            equal(inputHtml, expectedHtml);
            $.jstree.destroy();
            }
        });
    });

    test("xmltool.jstree.utils.real", function() {
        expect(6);

        $.ajax('http://127.0.0.1:9999/js/test/fixtures/jstree_utils.html',
              {async: false}
        ).done(function(data) {
            $fixture.append(data);
        });
        var tree_data;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/jstree_utils.json',
              {async: false, json: true}
        ).done(function(data) {
            tree_data = data;
        });

        var $form = $('#xmltool-form');
        var $formContainer = $form.parent();
        var $tree = $('#tree');
        ns.load($tree, tree_data, $form, $formContainer);
        var jstreeObj = $tree.data('jstree');

        var $textarea = $('textarea');
        equal($textarea.attr('name'), 'texts:list__text:0:text:subtext:_value');
        var $elt = ns.utils.getTreeElement($textarea);
        equal($elt.attr('id'), 'tree_texts:list__text:0:text:subtext');

        var node = jstreeObj.get_node($elt);

        var id = ns.utils.getFormId(node);
        equal(id, 'texts:list__text:0:text:subtext');

        $elt = ns.utils.getFormElement(node);
        equal($elt.attr('id'), 'texts:list__text:0:text:subtext');

        var parentNode = jstreeObj.get_node(node.parent);
        var $col = ns.utils.getCollapsibleElement(parentNode);
        equal($col.length, 1);

        $elt = ns.utils.getTreeElementFromCollapsible($col);
        node = jstreeObj.get_node($elt);
        equal(node.id, parentNode.id);
    });

    test("xmltool.jstree.events", function() {
        expect(19);
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/jstree_utils.html',
              {async: false}
        ).done(function(data) {
            $fixture.append(data);
        });
        var tree_data;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/jstree_utils.json',
              {async: false, json: true}
        ).done(function(data) {
            tree_data = data;
        });

        var $form = $('#xmltool-form');
        var $formContainer = $form.parent();
        var $tree = $('#tree');
        ns.load($tree, tree_data, $form, $formContainer);
        var jstreeObj = $tree.data('jstree');

        // Test collapse behaviours according to tree node
        var node = jstreeObj.get_node('tree_texts:list__text:0:text');
        var $elt = ns.utils.getCollapsibleElement(node);
        equal($elt.hasClass('in'), true, 'node opened by default');

        jstreeObj.close_node(node);
        equal($elt.hasClass('in'), false, 'node closed');

        jstreeObj.open_node(node);
        equal($elt.hasClass('in'), true, 'node opened');

        var $treeElt = jstreeObj.get_node(node, true);
        equal($treeElt.hasClass('jstree-open'), true, 'tree opened 1');
        equal($treeElt.hasClass('jstree-closed'), false, 'tree not closed 1');

        $elt.collapse('hide');
        equal($treeElt.hasClass('jstree-open'), false, 'tree not opened 2');
        equal($treeElt.hasClass('jstree-closed'), true, 'tree closed 2');

        $elt.collapse('show');
        // We need to reload the dom element
        $treeElt = jstreeObj.get_node(node, true);
        equal($treeElt.hasClass('jstree-open'), true, 'tree opened 3');
        equal($treeElt.hasClass('jstree-closed'), false, 'tree not closed 3');

        // Update the css to test the scroll is called
        $formContainer.css({overflow: 'auto', 'height': '20px'});
        $tree.css({overflow: 'auto', 'height': '20px'});
        equal($('textarea').length, 1);
        equal($formContainer.scrollTop(), 0);
        equal($tree.scrollTop(), 0);

        node = jstreeObj.get_node('tree_texts:list__text:0:text:subtext');
        $('textarea').bind('focus.test', function() {
            ok(true);
        });
        jstreeObj.select_node(node, true);
        notEqual($formContainer.scrollTop(), 0);

        $('textarea').unbind('focus.test');
        jstreeObj.deselect_node(node);
        equal($tree.scrollTop(), 0);
        $treeElt = jstreeObj.get_node(node, true);
        var $a = $treeElt.find('a');
        equal($a.hasClass('jstree-clicked'), false);
        $('textarea').trigger('focus');
        equal($a.hasClass('jstree-clicked'), true);
        notEqual($tree.scrollTop(), 0);

        $('textarea').text('Hello world').trigger('blur');
        // Need to reget the node since the object is cloned when jstree redraw it!
        $treeElt = jstreeObj.get_node(node, true);
        var text = $treeElt.find('._tree_text').text();
        $tree.jstree('redraw', $treeElt);
        equal(text, ' (Hello world)');
    });

    test("xmltool.jstree.move_event", function() {
        expect(20);
        var $data;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/move_element.html',
            {async: false}
        ).done(function(data) {
            $data = $(data);
        });
        $data.find('.dom-test').each(function(index){
            var $this = $(this),
                childrenIndex = parseInt($this.attr('data-children-index'), 10),
                position = $this.attr('data-position'),
                id = $this.attr('data-id');

            var $inputHtml = $(this).find('.dom-input-html').html();
            var $inputJstree = $(this).find('.dom-input-jstree');
            var $expectedHtml = $(this).find('.dom-expected-html').html();
            var $expectedJstree = $(this).find('.dom-expected-jstree');

            var jstreeInput = $.parseJSON($inputJstree.text());
            var jstreeExpected = $.parseJSON($expectedJstree.text());

            var $container = $('<div />').html($inputHtml);
            $fixture.html($container);
            // TODO: tree id is hardcoded fix this
            var $tree = $('<div/>').attr('id', 'tree');
            var $form = $('#xmltool-form');
            var $formContainer = $form.parent();
            $fixture.append($tree);
            xmltool.jstree.load($tree, jstreeInput, $form, $formContainer);
            var treeObj = $tree.data('jstree');

            var node = treeObj.get_node('tree_' + id);
            var parentNode = treeObj.get_node(node.parent);
            // First children is not list element so check_move should fail
            var res = treeObj.move_node(node, parentNode.children[0], position);
            if (index === 2) {
                // We move node 2 after the first element, it's allowed since 1
                // belong the list
                equal(res, true);
            }
            else {
                equal(res, false);
            }

            res = treeObj.move_node(node, parentNode.children[childrenIndex], position);
            equal(res, true);
            var treeHtml = cleanTreeHtml($tree.html());
            $.jstree.destroy();
            $tree.html('');
            xmltool.jstree.load($tree, jstreeExpected, $form, $formContainer);
            equal($container.html(), $expectedHtml);
            equal(treeHtml, cleanTreeHtml($tree.html()));
        });
    });


    test("xmltool.jstree.copy", function() {
        expect(1);

        $.ajax('http://127.0.0.1:9999/js/test/fixtures/jstree_utils.html',
              {async: false}
        ).done(function(data) {
            $fixture.append(data);
        });
        var tree_data;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/jstree_utils.json',
              {async: false, json: true}
        ).done(function(data) {
            tree_data = data;
        });

        var $form = $('#xmltool-form');
        var $formContainer = $form.parent();
        var $tree = $('#tree');
        ns.load($tree, tree_data, $form, $formContainer);
        var jstreeObj = $tree.data('jstree');

        var $node = $('#tree_texts\\:list__text\\:0\\:text');
        var node = jstreeObj.get_node($node);
        var oldAjax = $.ajax;
        var ajaxOptions;
        $.ajax = function(options) {
            ajaxOptions = options;
        };
        xmltool.jstree.copy(node);
        var expectedData = [
            'texts%3Alist__text%3A0%3Atext%3Asubtext%3A_value=Hello',
            '&elt_id=texts:list__text:0:text'].join('');
        equal(ajaxOptions.data, expectedData);
        $.ajax = oldAjax;
    });

    test("xmltool.jstree.paste", function() {
        expect(2);

        $.ajax('http://127.0.0.1:9999/js/test/fixtures/jstree_utils.html',
              {async: false}
        ).done(function(data) {
            $fixture.append(data);
        });
        var tree_data;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/jstree_utils.json',
              {async: false, json: true}
        ).done(function(data) {
            tree_data = data;
        });

        var $form = $('#xmltool-form');
        var $formContainer = $form.parent();
        var $tree = $('#tree');
        ns.load($tree, tree_data, $form, $formContainer);
        var jstreeObj = $tree.data('jstree');

        $form.data('paste-href', 'http://127.0.0.1:9999/js/test/fixtures/paste.json');
        $form.data('xmltool', {message: function(){}});

        var $node = $('#tree_texts\\:list__text\\:0\\:text');
        var node = jstreeObj.get_node($node);

        var oldAjax = $.ajax;
        // Since POST method is not allowed and I don't want to waste some time
        // here, just overwrite the type on the fly.
        $.ajax = function(options) {
            options.type = 'GET';
            oldAjax(options);
        };
        xmltool.jstree.paste(node);
        $.ajax = oldAjax;

        var expected;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/paste_expected.json',
              {async: false}
        ).done(function(data) {
            expected = data;
        });
        equal($form.html(), expected.html);
        var tree_html = $tree.html().replace(/j[0-9]+_[0-9a-z]+/g, '');
        $.jstree.destroy();
        $tree.html('');
        xmltool.jstree.load($tree, expected.jstree_data, $form, $formContainer);
        equal(tree_html, $tree.html().replace(/j[0-9]+_[0-9a-z]+/g, ''));
    });

})(jQuery);
