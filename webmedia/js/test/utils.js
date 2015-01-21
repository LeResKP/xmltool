(function($) {
	"use strict";

    var ns = xmltool.utils;
    var $fixture;

    module('xmltool.utils', {
        setup: function() {
          $fixture = $('#qunit-fixture');
        },
        teardown: function() {
            $fixture.html('');
        }
    });

    test("escapeAttr", function() {
        expect(2);
        equal(ns.escapeAttr('bob:1'), 'bob\\:1', 'attr escaped');
        equal(ns.escapeAttr('bob:1.ext'), 'bob\\:1\\.ext', 'attr escaped');
    });

    test("getElementById", function() {
        expect(2);
        $fixture.append($('<div>').attr('id', 'myid'));
        var $elt = ns.getElementById('myid');
        equal($elt.length, 1, 'Found myid');
        $elt = ns.getElementById('unexistingid');
        equal($elt.length, 0, 'Unexisting id should not be found');
    });

    test('scrollToElement', function() {
        var $container = $('<div>').attr('style', 'height: 50px; overflow-y: auto; position: relative;');
        var $child1 = $('<div>').attr('style', 'margin-bottom: 100px').html('Hello');
        var $child2 = $('<div>').attr('style', 'margin-top: 100px').html('world');
        $container.append($child1).append($child2);
        $fixture.append($container);

        var v = $container.scrollTop();
        equal(v, 0);

        ns.scrollToElement($child2, $container);
        v = $container.scrollTop();
        equal(v, 91);

        ns.scrollToElement($child1, $container);
        v = $container.scrollTop();
        equal(v, 0);
    });

    test('updatePrefixAttrs', function() {
        expect(8);
        $.ajax('http://127.0.0.1:9999/js/test/fixtures/updatePrefixAttrs.html',
              {async: false}
        ).done(function(data) {
            var $data = $(data);
            $data.find('.dom-test').each(function(){
                var $this = $(this),
                    prefix = $this.attr('prefix'),
                    newprefix = $this.attr('newprefix');
                var $input = $(this).find('.dom-input');
                var $obj = $input.children(':first');
                var $expected = $(this).find('.dom-expected');
                ns.updatePrefixAttrs($obj, prefix, newprefix);
                equal($input.html(), $expected.html());
            });
        });
    });

    test('truncateText', function(){
        expect(3);
        var text = 'Short text';
        equal(ns.truncateText(text), text, 'Short text is not truncated');

        equal(ns.truncateText(text, 7), 'Short...', 'truncate according to the limit');
        text = 'This text is very too long and will be truncated';
        var expected = 'This text is very too long and...';
        equal(ns.truncateText(text), expected, 'Long text is truncated');
    });

    test('getPrefixIndexFromListEltId', function(){
        expect(1);
        var expected = {
            index: 0,
            prefixId: 'root:list_tag'
        };
        deepEqual(ns.getPrefixIndexFromListEltId('root:list_tag:0:tag'), expected);
    });

}(jQuery));
