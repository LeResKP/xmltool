if (typeof xmltool === 'undefined') {
    /*jshint -W020 */
    xmltool = {};
}


(function($){


    function Xmltool(element, options){
        this.options = options;
        // TODO: should be in options:
        this.dtd_url_selector = '#_xml_dtd_url';
        this.init(element);
    }

    Xmltool.prototype.init = function(element) {
        this.element = element;
        this.$form = $(element);
        this.dtd_url = this.$form.find(this.dtd_url_selector).val();
    };

    Xmltool.prototype.add_node = function(data){
            //jstree
            var jstree_data = $(data.jstree_data);
            var previous = $(data.previous);

            for(var i=0; i < previous.length; i++){
                var position = previous[i][0];
                var selector = xmltool.utils.escape_id(previous[i][1]);
                var parentobj = $(selector + ':last');
                if (parentobj.length > 1){
                    alert('not expected');
                }
                if (parentobj.length){
                    // Create node
                    xmltool.jstree.create_nodes($('#tree'), jstree_data[0], parentobj, position);
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
            dtd_url: this.dtd_url
        };
        $.ajax({
            type: 'GET',
            url: this.options.add_element_url,
            data: params,
            dataType: 'json',
            success: function(data, textStatus, jqXHR){
                var objs = $(data.html);
                that.set_btn_event($('<div/>').append(objs));
                if($btn.hasClass('btn-list')){
                    $btn.after(objs);
                    // Last is the button to add more
                    var last = $(objs[objs.length-1]);
                    var nexts = last.nextAll();
                    // TODO: Make sure this is correclty tested
                    var longprefix = xmltool.utils.get_prefix(elt_id);
                    var prefix = xmltool.utils.get_prefix(longprefix);
                    xmltool.utils.increment_id(prefix, nexts);
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
                console.log('Error ajax loading');
            }
        });
    };

    Xmltool.prototype.removeElement = function($btn){
        var $addBtn = $btn.prev('.btn-add');
        var $parent = this.$form.find(xmltool.utils.escape_id($btn.data('target')));
        if($btn.hasClass('btn-list')) {
            var nexts = $parent.nextAll();
            // Remove the add button
            $parent.prev().remove();
            $parent.remove();
            var longprefix = xmltool.utils.get_prefix($parent.attr('id'));
            var prefix = xmltool.utils.get_prefix(longprefix);
            xmltool.utils.decrement_id(prefix, nexts);
        }
        else {
            $parent.replaceWith($addBtn);
            $addBtn.removeClass('hidden');
        }
        this.delete_node('tree_' + $parent.attr('id'));
    };


    var default_options = {
        open_dialog: function(dialog){
            dialog.modal('show');
        },
        close_dialog: function(dialog){
            dialog.modal('hide');
        }
    };

    $.fn.xmltool = function(options){
        var self = $(this);
        var settings = $.extend({}, default_options, options);

        var xt = new Xmltool(this, settings);


        Xmltool.prototype.delete_node = function(node_id){
            var tree = $('#tree');
            var node = tree.find('#' + xmltool.utils.escape_id(node_id));
            if (node.length > 1){
                alert('Too many values to delete');
            }
            var css_class = node.attr('class').split(' ')[0];
            var nexts = node.nextAll('.'+xmltool.utils.escape_id(css_class));
            var longprefix = xmltool.utils.get_prefix(node.attr('id'));
            var prefix = xmltool.utils.get_prefix(longprefix);
            xmltool.utils.decrement_id(prefix, nexts);
            tree.jstree('delete_node', node);
        };

        Xmltool.prototype.set_btn_event = function(p){
                    p.find('textarea').autosize().focus(
                        function(){
                            var id = xmltool.utils.escape_id($(this).parent().attr('id'));
                            var tree = $('#tree');
                            tree.jstree('hover_node', $('#tree_' + id));
                            $(this).on('keyup.xmltool', function(){
                                // TODO: this method should be improved to make
                                // sure the user has made an update
                                self.trigger('field_change.xmltool');
                            });
                        }).blur(function(){
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
                        });

            var set_fielset = function(fieldsets){
                fieldsets.togglefieldset().bind('hide.togglefieldset', function(e){
                    var o = $('#tree_' + xmltool.utils.escape_id($(this).attr('id')));
                    $('#tree').jstree("close_node", o);
                    return false;
                }).bind('show.togglefieldset', function(e){
                    var o = $('#tree_' + xmltool.utils.escape_id($(this).attr('id')));
                    $('#tree').jstree("open_node", o);
                    return false;
                });
            };

            set_fielset(p.find('fieldset'));
            if(p.is('fieldset')){
                set_fielset(p);
            }

            p.find('.btn-delete').on('click', function(){
                xt.removeElement($(this));
            });

            p.find('a.btn-add').on('click', function(){
                xt.addElement($(this));
            });
            p.find('select.btn-add').on('change', function(){
                xt.addElement($(this));
            });

            p.find('.btn-comment').on('click', function(){
                var self = $(this);

                var comment_textarea = self.next('._comment');

                if (!comment_textarea.length){
                    comment_textarea = $('<textarea>').attr('name', self.data('comment-name')).addClass('_comment');
                    self.after(comment_textarea);
                }
                // Create the dialog
                var modal = self.data('modal');
                if(modal === undefined){
                    $.ajax({
                        type: 'GET',
                        url: settings.comment_modal_url,
                        data: {'comment': comment_textarea.val()},
                        dataType: 'json',
                        async: false,
                        success: function(data, textStatus, jqXHR){
                            modal = $(data.content);
                            self.data('modal', modal);
                            modal.find('.submit').click(function(){
                                var value = modal.find('textarea').val();
                                comment_textarea.val(value);
                                settings.close_dialog(modal);

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
                            // TODO: Replace all this kind of errors!
                            console.log('Error ajax loading');
                        }
                    });
                }
                settings.open_dialog(modal);
                return false;
             });
            };

        return this.each(function(){
            xt.set_btn_event($(this));
        });
    };
})(window.jQuery);
