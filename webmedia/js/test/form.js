(function($) {
	"use strict";

    var $fixture;

    module('xmltool.form', {
        setup: function() {
          $fixture = $('#qunit-fixture');
        },
        teardown: function() {
            $fixture.html('');
        }
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

            var $input = $(this).find('.dom-input');
            var $expected = $(this).find('.dom-expected');
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

}(jQuery));
