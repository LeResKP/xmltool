/*
 * contenteditablesync
 * https://github.com/LeResKP/jquery.contenteditablesync
 *
 * Copyright (c) 2014 Aurélien Matouillot
 * Licensed under the MIT license.
 */

(function($, window) {

    var ContenteditableSync = function(element, options) {
        this.options = $.extend({}, ContenteditableSync.DEFAULTS, options);
        this.init(element);
    };


    ContenteditableSync.prototype.init = function(element) {
        this.$element = $(element);
        var target = this.$element.data('target');
        if(target) {
            this.$target = $(target);
        }
        else {
            this.$target = this.$element.prev();
        }

        this.timer = null;
        var that = this;
        this.value = this.options.getContent(this.$element);

        this.$element.on('focus', function() {
            that.watch();
        });

        this.$element.on('blur', function() {
            window.clearInterval(that.timer);
            that.timer = null;
            that.sync();
        });

    };

    ContenteditableSync.prototype.watch = function() {
        if (this.timer) {
            return false;
        }
        this.timer = window.setInterval($.proxy(this.sync, this), this.options.interval);
    };


    ContenteditableSync.prototype.sync = function() {
        var newvalue = this.options.getContent(this.$element);
        if (newvalue !== this.value) {
            this.$target.text(newvalue).trigger('change.contenteditablesync');
            this.value = newvalue;
        }
    };


    ContenteditableSync.DEFAULTS = {
        interval: 2000,
        getContent: function($element) {
            return $element.text();
        }
    };

    $.fn.contenteditablesync = function(option) {
        return this.each(function(){
            var $this = $(this),
                data = $this.data('contenteditablesync'),
                options = typeof option === 'object' && option;

            if(!data){
                $this.data('contenteditablesync', (data=new ContenteditableSync(this, options)));
            }
            if (typeof option === 'string') {
                data[option]();
            }
        });
    };

    $.fn.contenteditablesync.Constructor = ContenteditableSync;

})(jQuery, window);
