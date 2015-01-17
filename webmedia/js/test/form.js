(function($) {
	"use strict";

    var $fixture;

    var cleanTreeHtml = function(html) {
        // We should remove the generated ids
        return html.replace(/j[0-9]+_[0-9a-z]+/g, '');
    };

    module('xmltool.form', {
        setup: function() {
          $fixture = $('#qunit-fixture');
        },
        teardown: function() {
            $fixture.html('');
            $.jstree.destroy();
        }
    });

    test('_updateElementsPrefix', function() {
        var $div = $('<div />');
        $div.append($('<div id="prefix:0:child" />'));
        $div.append($('<div id="prefix:0:child" />'));
        $div.append($('<div id="prefix:1:child" />'));
        $div.append($('<div id="prefix:1:child" />'));
        $div.append($('<div id="prefix:2:child" />'));
        $fixture.append($div);

        xmltool.form._updateElementsPrefix($div.children().eq(0), 10, 'prefix');
        equal($div.children().eq(0).attr('id'), 'prefix:11:child');
        equal($div.children().eq(1).attr('id'), 'prefix:11:child');
        equal($div.children().eq(2).attr('id'), 'prefix:12:child');
        equal($div.children().eq(3).attr('id'), 'prefix:12:child');
        equal($div.children().eq(4).attr('id'), 'prefix:13:child');
    });

    test('_add_element', function() {
        expect(8);
        var $data;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/add_element/test.html',
              {async: false}
        ).done(function(data) {
            $data = $(data);
        });

        $data.find('.dom-test').each(function(index){
            if (index !== -1) {
            var $this = $(this),
                btn_selector = $this.attr('data-btn-selector'),
                url = $this.attr('data-url'),
                eltId = $this.attr('data-id');

            var $input = $(this).find('.dom-input-html');
            var $expected = $(this).find('.dom-expected-html');
            var $btn = $input.find(btn_selector);
            if ($btn.is('option')) {
                // The btn is the select
                $btn = $btn.parent();
            }
            var html;
            $.ajax('http://127.0.0.1:9999/' + url,
                  {async: false}
            ).done(function(data) {
                html = data.html;
            });
            xmltool.form._addElement(eltId, $btn, html);
            equal($input.html(), $expected.html());
            }
        });
    });

    test('add_element', function() {
        expect(16);
        var $data;
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/add_element/test.html',
              {async: false}
        ).done(function(data) {
            $data = $(data);
        });
        $data.find('.dom-test').each(function(index){
            var $this = $(this),
                btn_selector = $this.attr('data-btn-selector'),
                url = 'http://127.0.0.1:9999/' + $this.attr('data-url'),
                eltId = $this.attr('data-id');

            var $input = $(this).find('.dom-input-html');
            var $jstree = $(this).find('.dom-input-jstree');
            var $expected = $(this).find('.dom-expected-html');
            var jstreeInput = $.parseJSON($jstree.text());

            // TODO: tree id is hardcoded fix this
            var $tree = $('<div/>').attr('id', 'tree');
            var $form = $('<form id="xmltool-form">').append($input.html());
            var $formContainer = $('<div>').append($form);
            $fixture.html($formContainer);
            $fixture.append($tree);
            xmltool.jstree.load($tree, jstreeInput, $form, $formContainer);

            var $btn = $input.find(btn_selector);
            if ($btn.is('option')) {
                // The btn is the select
                $btn = $btn.prop('selected', true).parent();
            }

            var treeHtml = cleanTreeHtml($tree.html());
            xmltool.form.addElement($btn, url, null, null, $tree, false);
            equal($input.html(), $expected.html());
            notEqual(treeHtml, cleanTreeHtml($tree.html()));
        });
    });

}(jQuery));
