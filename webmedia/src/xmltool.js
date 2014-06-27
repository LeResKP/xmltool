if (typeof xmltool === 'undefined') {
    /*jshint -W020 */
    xmltool = {};
}


(function($){

    function Xmltool(element, options){
        this.options = $.extend({}, Xmltool.DEFAULTS, options);
        this.$tree = null;
        this.init(element);
        this.message = this.options.message;
    }

    Xmltool.prototype.init = function(element) {
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
        if(typeof this.options.jstreeData !== 'undefined') {
            this.loadJstree(this.options.jstreeData);
        }
    };

    Xmltool.prototype.loadJstree = function(data){
        var that = this;
        this.$tree.jstree({
            "json_data" : {'data': [data]},
            "plugins" : ["themes", "json_data", "ui", "crrm", "dnd", "contextmenu"],
            "core": {
                html_titles: true
            },
            "ui" : {select_multiple_modifier: false},
            "crrm" : {
                "move" : {
                    "check_move" : xmltool.jstree.check_move,
                }
            },
            "dnd" : {
                "drop_target" : false,
                "drag_target" : false
            },
            contextmenu: {
                items: function(node){
                    // TODO: support to not display this menu when we don't
                    // have the url to copy/paste.
                    return {
                        copyItem: {
                            label: 'Copy',
                            action: function(n) {
                                xmltool.jstree.copy(n);
                            },
                        },
                        pasteItem: {
                            label: 'Paste',
                            action: function(n) {
                                xmltool.jstree.paste(n);
                            }
                        }
                    };
                }
            }
        }).bind("select_node.jstree", function (e, data) {
            var id = data.rslt.obj.attr("id");
            id = id.replace(/^tree_/, '');
            var elt = $('#' + id.replace(/:/g,'\\:'));
            elt.focus();
            var treeContainer = $(that.options.treeContainerSelector);
            var t =  elt.offset().top + treeContainer.scrollTop() - treeContainer.offset().top - 30;
            treeContainer.animate({
                scrollTop: t,
                }, 1000
            );
        }).bind("loaded.jstree", function (event, data) {
            that.$tree.jstree('open_all');
            that.$tree.height($(that.options.treeContainer).height());
            that.$form.trigger('loadedJstree');

            // To not call this events when we call 'open_all' after loading we
            // defined them here
            $(this).bind('close_node.jstree', function(event, data){
                if (event.isDefaultPrevented()) {
                    return false;
                }
                var id = data.rslt.obj.attr("id");
                id = id.replace(/^tree_/, '');
                var elt = $('#' + id.replace(/:/g,'\\:') + ' > .panel-collapse');
                if(!elt.data('bs.collapse')) {
                    elt.collapse({'toggle': false});
                }
                elt.collapse('hide');
                event.preventDefault();
            }).bind('open_node.jstree', function(event, data){
                if (event.isDefaultPrevented()) {
                    return false;
                }
                var id = data.rslt.obj.attr("id");
                id = id.replace(/^tree_/, '');
                var elt = $('#' + id.replace(/:/g,'\\:') + ' > .panel-collapse');
                if(!elt.data('bs.collapse')) {
                    elt.collapse({'toggle': false});
                }
                elt.collapse('show');
                event.preventDefault();
            });
        }).bind("move_node.jstree", function(event, data){
            that.message('info', 'Moving...', {overlay: true, modal: true});
            setTimeout(function(){
                xmltool.jstree.move_node(event, data);
                that.message('success', 'Moved!');
            }, 50);
        });
    };

    Xmltool.prototype.add_node = function(data){
            var jstree_data = $(data.jstree_data);
            var previous = $(data.previous);

            for(var i=0; i < previous.length; i++){
                var position = previous[i][0];
                var selector = xmltool.utils.escape_id(previous[i][1]);
                var parentobj = $(selector + ':last');
                if (parentobj.length > 1){
                    this.message('error', "Can't add a node in the tree");
                    return false;
                }
                if (parentobj.length){
                    // Create node
                    xmltool.jstree.create_nodes(this.$tree, jstree_data[0], parentobj, position);
                    break;
                }
            }
        };

    Xmltool.prototype.addElement = function($btn, elt_id){
        if ($btn.is('select')) {
            elt_id = $btn.val();
        }
        else {
            elt_id = $btn.data('elt-id');
        }
        var that = this;
        var params = {
            elt_id: elt_id,
            dtd_url: this.dtdUrl
        };
        $.ajax({
            type: 'GET',
            url: this.options.add_element_url,
            data: params,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                var objs = $(data.html);
                if($btn.hasClass('btn-list')){
                    $btn.after(objs);
                    // Last is the button to add more
                    var last = $(objs[objs.length-1]);
                    var nexts = last.nextAll();
                    // TODO: Make sure this is correclty tested
                    var longprefix = xmltool.utils.get_prefix(elt_id);
                    var prefix = xmltool.utils.get_prefix(longprefix);
                    var index = xmltool.utils.get_index(longprefix);
                    xmltool.utils.increment_id(prefix, nexts, index, 2);
                }
                else {
                    $btn.replaceWith(objs);
                }

                if ($btn.is('select')) {
                    $btn.val($btn.find('option:first').val());
                }

                //jstree
                    that.add_node(data);
            },
            error: function(jqXHR, textStatus, errorThrown){
                var msg = jqXHR.status + ' ' + jqXHR.statusText;
                that.message('error', msg);
            }
        });
    };

    Xmltool.prototype.removeElement = function($btn){
        var $addBtn = $btn.prev('.btn-add');
        var $parent = this.$form.find(xmltool.utils.escape_id($btn.data('target')));
        if($btn.hasClass('btn-list')) {
            var nexts = $parent.nextAll();
            // Remove the add button
            // NOTE: we delete the button after the parent to keep indexing
            // consistent.
            $parent.next().remove();
            $parent.remove();
            var longprefix = xmltool.utils.get_prefix($parent.attr('id'));
            var prefix = xmltool.utils.get_prefix(longprefix);
            var index = xmltool.utils.get_index(longprefix);
            xmltool.utils.decrement_id(prefix, nexts, index, 2, 1);
        }
        else {
            $parent.replaceWith($addBtn);
            $addBtn.removeClass('hidden');
        }
        this.delete_node('tree_' + $parent.attr('id'));
    };

    Xmltool.prototype.delete_node = function(node_id){
        var node = this.$tree.find('#' + xmltool.utils.escape_id(node_id));
        if (node.length > 1){
            this.message('error', "Can't delete a node in the tree");
        }
        var css_class = node.attr('class').split(' ')[0];
        var nexts = node.nextAll('.'+xmltool.utils.escape_id(css_class));
        var longprefix = xmltool.utils.get_prefix(node.attr('id'));
        var prefix = xmltool.utils.get_prefix(longprefix);
        var index = xmltool.utils.get_index(longprefix);
        xmltool.utils.decrement_id(prefix, nexts, index);
        this.$tree.jstree('delete_node', node);
    };

    Xmltool.prototype.setEvents = function(){
        var that = this;

        $(this.$form).on('shown.bs.collapse', '.panel-collapse', function (e) {
            if (e.isDefaultPrevented()) {
                return false;
            }
            var id = $(this).attr('id');
            id = id.replace(/^collapse-/, '');
            var o = $('#tree_' + xmltool.utils.escape_id(id));
            that.$tree.jstree("open_node", o);
            e.preventDefault();
        }).on('hidden.bs.collapse', '.panel-collapse', function (e) {
            if (e.isDefaultPrevented()) {
                return false;
            }
            var id = $(this).attr('id');
            id = id.replace(/^collapse-/, '');
            var o = $('#tree_' + xmltool.utils.escape_id(id));
            that.$tree.jstree("close_node", o);
            e.preventDefault();
        });

        $(this.$form).on('focus', 'textarea.form-control', function(){
            var id = xmltool.utils.escape_id($(this).parent().attr('id'));
            that.$tree.jstree('hover_node', $('#tree_' + id));
            $(this).on('keyup.xmltool', function(){
                // TODO: this method should be improved to make
                // sure the user has made an update
                that.$form.trigger('field_change.xmltool');
            });
        }).on('blur', 'textarea.form-control', function(){
            var id = xmltool.utils.escape_id($(this).parent().attr('id'));
            var a = $('#tree_' + id).find('a');
            var elt = a.find('._tree_text');
            if (elt.length === 0){
                elt = $('<span class="_tree_text"/>').appendTo(a);
            }
            if($(this).val()){
                elt.text(' (' + xmltool.utils.truncate($(this).val(), 30) + ')');
            }
            else{
                elt.text('');
            }
            $(this).unbind('keyup.xmltool');
        }).on('click', '.btn-delete', function(e){
            e.preventDefault();
            that.removeElement($(this));
            // We need to return false because of bootstrap collapsable. It
            // doesn't handle 'preventDefault'.
            return false;
        }).on('click', 'a.btn-add', function(e){
            e.preventDefault();
            that.addElement($(this));
            return false;
        }).on('change', 'select.btn-add', function(e){
            e.preventDefault();
            that.addElement($(this));
            return false;
        }).on('click', '.btn-comment',function(e){
            e.preventDefault();
            var self = $(this);

            var comment_textarea = self.next('._comment');

            if (!comment_textarea.length){
                comment_textarea = $('<textarea>').attr('name', self.data('comment-name')).addClass('_comment').addClass('form-control');
                self.after(comment_textarea);
            }
            // Create the dialog
            var modal = self.data('modal');
            if(modal === undefined){
                $.ajax({
                    type: 'GET',
                    url: that.options.comment_modal_url,
                    data: {'comment': comment_textarea.val()},
                    dataType: 'json',
                    async: false,
                    success: function(data, textStatus, jqXHR){
                        modal = $(data.content);
                        self.data('modal', modal);
                        modal.find('.submit').click(function(){
                            var value = modal.find('textarea').val();
                            comment_textarea.val(value);
                            that.options.close_dialog(modal);

                            self.attr('title', value);
                            if (value){
                                self.addClass('has-comment');
                            }
                            else{
                                self.removeClass('has-comment');
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
            that.options.open_dialog(modal);
            return false;
        });
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
