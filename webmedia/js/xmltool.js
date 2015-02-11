if (typeof xmltool === 'undefined') {
    /*jshint -W020 */
    xmltool = {};
}



/** @namespace */
xmltool.form = {};


(function($) {

    /**
     * Update the prefix of the element which belong a list.
     * @param {jQuery} $btn - The button clicked used to get all the next element
     * @param {string} position - The position of the new element in the list
     * @param {string} prefixId - the prefix of the list
     * @memberof xmltool.form
     * @method _updateElementsPrefix
     */
    this._updateElementsPrefix = function($btn, position, prefixId) {
            var $nexts = $btn.nextAll().andSelf();
            for (var i=0, len=$nexts.length; i < len; i++) {
                var $elt = $nexts.eq(i);
                var prefix = prefixId + ':[0-9]+:';
                var newPrefix = prefixId + ':' + position + ':';
                xmltool.utils.updatePrefixAttrs($elt, prefix, newPrefix);

                if (i % 2 !== 0) {
                    position += 1;
                }
            }
    };

    /**
     * Add element to the dom.
     * @param {string} eltId - The id of the new element
     * @param {jQuery} $btn - The button clicked
     * @param {string} html - the html of the element to insert
     * @memberof xmltool.form
     * @method _addElement
     */
    this._addElement = function(eltId, $btn, html) {
        var objs = $(html);
        if($btn.hasClass('btn-list')){
            // We have to increment the attributes' index of the next elements
            var d = xmltool.utils.getPrefixIndexFromListEltId(eltId);
            var index = d.index;
            this._updateElementsPrefix($btn, (index + 1), d.prefixId);
            $btn.before(objs);
        }
        else {
            $btn.replaceWith(objs);
        }

        if ($btn.is('select')) {
            $btn.val($btn.find('option:first').val());
        }
    };

    /**
     * Add an element to the form and the tree after clicking on a button.
     * The button can be a 'select' or a 'a'.
     * @param {jQuery} $btn - The button clicked
     * @param {string} url - The url to call to get the form elements to add in the dom
     * @param {string} dtdUrl - The url of the dtd of the file we are updating
     * @param {function} msgFunc - The function to render the message to display
     * @param {jQuery} $tree - The tree element
     * @memberof xmltool.form
     * @method addElement
     */
    this.addElement = function($btn, url, dtdUrl, msgFunc, $tree, async, extra_params) {
        async = (typeof async === 'undefined')? true: async;
        var eltId;
        if ($btn.is('select')) {
            eltId = $btn.val();
        }
        else {
            eltId = $btn.attr('data-elt-id');
        }
        var that = this;

        var params = {
                elt_id: eltId,
                dtd_url: dtdUrl
            };

        if (typeof extra_params !== 'undefined') {
            for (var i=0, len=extra_params.length; i < len; i++) {
                var tmp = extra_params[i];
                params[tmp.name] = tmp.value;
            }
        }

        $.ajax({
            type: 'GET',
            url: url,
            data: params,
            async: async,
            dataType: 'json',
            success: function(data){
                if (typeof data.modal !== 'undefined') {
                    // We support to return a modal if we need more information
                    // for adding a new element.
                    var modal = $(data.modal);
                    modal.find('form').on('submit', function(e) {
                        e.preventDefault();
                        modal.modal('hide');
                        var p = $(this).serializeArray();
                        that.addElement($btn, url, dtdUrl, msgFunc, $tree, async, p);
                    });
                    modal.modal('show');
                }
                else {
                    that._addElement(eltId, $btn, data.html);
                    xmltool.jstree.utils.addNode($btn, $tree, data);
                }
            },
            error: function(jqXHR){
                var msg = jqXHR.status + ' ' + jqXHR.statusText;
                msgFunc('error' + msg);
            },
        });
    };

    /**
     * Remove an element from the form and the tree after clicking on a button.
     * @param {jQuery} $btn - The button clicked
     * @param {jQuery} $tree - The tree element
     * @memberof xmltool.form
     * @method removeElement
     */
    this.removeElement = function($btn, $tree) {
        var $target = $(xmltool.utils.escapeAttr($btn.data('target')));
        var targetId = $target.attr('id');
        if($btn.hasClass('btn-list')) {
            // We have to decrement the attributes' index of the next elements
            var d = xmltool.utils.getPrefixIndexFromListEltId($target.attr('id'));
            var index = d.index;
            this._updateElementsPrefix($target.next(), index, d.prefixId);
            $target.prev('.btn-add').remove();
            $target.remove();
        }
        else {
            var $addBtn = $btn.prev('.btn-add').removeClass('hidden');
            $target.replaceWith($addBtn);
        }
        xmltool.jstree.utils.removeNode($btn, targetId, $tree);
    };

}).call(xmltool.form, jQuery);


(function($){

    function Xmltool(element, options){
        this.options = $.extend({}, Xmltool.DEFAULTS, options);
        this.$tree = null;
        this.init(element);
        this.message = this.options.message;
    }

    Xmltool.prototype.init = function(element) {
        var that = this;
        this.element = element;
        this.$form = $(element);
        this.dtdUrl = this.$form.find(this.options.dtdUrlSelector).val();
        this.setEvents();
        if(typeof this.options.jstreeSelector !== 'undefined') {
            var $tree = $(this.options.jstreeSelector);
            if ($tree.length) {
                this.$tree = $tree;
            }
        }

        this.$form.on('click', 'a.btn-add', function(e){
          e.preventDefault();
          xmltool.form.addElement($(this), that.options.add_element_url, that.dtdUrl, that.message, that.$tree);
          return false;
        })

        .on('change', 'select.btn-add', function(e){
          e.preventDefault();
          xmltool.form.addElement($(this), that.options.add_element_url, that.dtdUrl, that.message, that.$tree);
          return false;
        })

        .on('mouseenter focus', '.contenteditable', function(e){
            var $this = $(this);
            $this.ckeditor({removePlugins: 'toolbar'});
            $this.contenteditablesync({
                getContent: function($element) {
                    var s = $element.ckeditorGet().getData();
                    return xmltool.utils.cleanupContenteditableContent(s);
                }
            });
        })

        .on('click', '.btn-delete', function(e){
          e.preventDefault();
          xmltool.form.removeElement($(this), that.$tree);
          return false;
        })

        .on('click', '.btn-comment', function(e){
            e.preventDefault();
            var $this = $(this);
            var $textarea = $this.next('._comment');

            if (!$textarea.length){
                $textarea = $('<textarea>').attr('name', $this.data('comment-name')).addClass('_comment').addClass('form-control');
                $this.after($textarea);
            }

            // Create the dialog
            var modal = $this.data('modal');
            if(modal === undefined){
                $.ajax({
                    type: 'GET',
                    url: that.options.comment_modal_url,
                    data: {'comment': $textarea.val()},
                    dataType: 'json',
                    async: false,
                    success: function(data, textStatus, jqXHR){
                        modal = $(data.content);
                        modal.on('shown.bs.modal', function () {
                            $(this).find('textarea').focus();
                        });
                        $this.data('modal', modal);
                        modal.find('.submit').click(function(){
                            var value = modal.find('textarea').val();
                            $textarea.val(value);
                            modal.modal('hide');

                            $this.attr('title', value);
                            if (value){
                                $this.addClass('has-comment');
                            }
                            else{
                                $this.removeClass('has-comment');
                            }
                            return false;
                        });
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        var msg = jqXHR.status + ' ' + jqXHR.statusText;
                        that.message('error', msg);
                    }
                });
            }
            modal.modal('show');
            return false;
        });

        if(typeof this.options.jstreeData !== 'undefined') {
            xmltool.jstree.load(
                this.$tree,
                this.options.jstreeData,
                this.$form,
                $(this.options.treeContainerSelector)
            );
        }
    };


    Xmltool.prototype.setEvents = function(){
        var that = this;


        // }).on('blur', '.contenteditable', function(){
        //     // TODO: refactor this function with the previous one, the
        //     // difference is the way to get the string.
        //     var id = xmltool.utils.escape_id($(this).parent().attr('id'));
        //     var a = $('#tree_' + id).find('a');
        //     var elt = a.find('._tree_text');
        //     if (elt.length === 0){
        //         elt = $('<span class="_tree_text"/>').appendTo(a);
        //     }
        //     var s = $(this).ckeditorGet().getData();
        //     if(s){
        //         s = xmltool.utils.update_contenteditable_eol(s);
        //         elt.text(' (' + xmltool.utils.truncate(s, 30) + ')');
        //     }
        //     else{
        //         elt.text('');
        //     }
        // }).on('mouseenter focus', '.contenteditable', function(){
        //     $(this).ckeditor({removePlugins: 'toolbar'});
        //     $(this).contenteditablesync({
        //         getContent: function($element) {
        //             var s = $element.ckeditorGet().getData();
        //             return xmltool.utils.update_contenteditable_eol(s);
        //         }
        //     });
        // })
        //
    };

    Xmltool.DEFAULTS = {
        open_dialog: function(dialog){
            dialog.modal('show');
        },
        close_dialog: function(dialog){
            dialog.modal('hide');
        },
        message: function(type, msg, options) {
            alert(type + ': ' + msg);
        },
        treeContainerSelector: 'body',
        dtdUrlSelector: '#_xml_dtd_url'
    };

    $.fn.xmltool = function(options){
        return this.each(function(){
            var $this = $(this);
            var data = $this.data('xmltool');
            if (!data) {
                data = new Xmltool(this, options);
                $this.data('xmltool', data);
            }
        });
    };
})(window.jQuery);
