
var logging = function(){

    var self = this;

    $.extend(self,{
        log: function(text){
            console.log(text);
        }
    });
}

var logger = new logging();


var create_nodes = function(tree, data, parentobj, position){
    var node = tree.jstree("create_node", parentobj, position, data);
    var css_class = node.attr('class').split(' ')[0];
    var nexts = node.nextAll('.'+xmltool.escape_id(css_class));
    var longprefix = xmltool.get_prefix(node.attr('id'));
    var prefix = xmltool.get_prefix(longprefix);
    xmltool.increment_id(prefix, nexts);
    // self.increment_id(node);
    if (typeof(data.children) != 'undefined'){
        for(var i=0; i < data.children.length; i++){
            tree.jstree("create_node", node, 'last', data.children[i]);
        }
    }
    tree.jstree('open_all', node);
};


(function(exports){
    var re_split = new RegExp('^(.*):([^:]+)$');

    var attrnames = ['name', 'id', 'class', 'value'];
    var datanames = ['id', 'comment-name'];

    var functions = {
        escape_id: function(id){
            return id.replace(/:/g, '\\:');
        },
        get_prefix: function(id){
            return id.replace(re_split, '$1');
        },
        get_index: function(id){
            return parseInt(id.replace(re_split, '$2'));
        },
        _attr: function(elt, name, value){
            if(typeof value === 'undefined'){
                return elt.attr(name);
            }
            else{
                elt.attr(name, value);
            }
        },
        _data: function(elt, name, value){
            if(typeof value === 'undefined'){
                return elt.data(name);
            }
            else{
                elt.data(name, value);
            }
        },
        _increment_id: function(prefix, elt, func, names, diff){
            var re_id = new RegExp('^'+prefix+':(\\d+)');
            for (var key in names){
                var name = names[key];
                var value = func(elt, name);
                // TODO: split value on ' ' and make sure we update all .
                // it's needed for the css class
                if(value){
                    values = value.split(' ');
                    var output = []
                    for(var i=0; i<values.length; i++){
                        var v = values[i];
                        var index = parseInt(v.replace(re_id, '$1'));
                        var re = new RegExp('^'+prefix+':'+index);
                        var new_value = v.replace(re, prefix + ':' + (index+diff));
                        output.push(new_value);
                    }
                    func(elt, name, output.join(' '));
                }
            }
        },
        increment_id: function(prefix, elts){
            for (var i=0; i< elts.length; i++){
                var elt = $(elts[i]);
                xmltool._increment_id(prefix, elt, xmltool._attr, attrnames, 1);
                xmltool._increment_id(prefix, elt, xmltool._data, datanames, 1);
                xmltool.increment_id(prefix, elt.children());
            }
        },
        _replace_id: function(prefix, elt, func, names, index){
            var re_id = new RegExp('^'+prefix+':(\\d+)');
            for (var key in names){
                var name = names[key];
                var value = func(elt, name);
                if(value){
                    values = value.split(' ');
                    var output = []
                    for(var i=0; i<values.length; i++){
                        var v = values[i];
                        var old_index = parseInt(v.replace(re_id, '$1'));
                        var re = new RegExp('^'+prefix+':'+old_index);
                        var new_value = v.replace(re, prefix + ':' + index);
                        output.push(new_value);
                    }
                    func(elt, name, output.join(' '));
                }
            }
        },
        replace_id: function(prefix, elts, step, force_index){
            step = step || 1;
            var index = 0;
            for (var i=0; i< elts.length; i++){
                var elt = $(elts[i]);
                console.log('elt');
                console.log(elt);
                console.log(index);
                if (typeof force_index != 'undefined'){
                    var tmp_index = force_index;
                }
                else{
                    var tmp_index = index;
                }
                xmltool._replace_id(prefix, elt, xmltool._attr, attrnames, tmp_index);
                xmltool._replace_id(prefix, elt, xmltool._data, datanames, tmp_index);
                xmltool.replace_id(prefix, elt.children(), 1, tmp_index);

                if (step == 1){
                    index += 1;
                }
                else if((i+1) % step == 0 && i != 0){
                    index += 1;
                }
                console.log('  ');
            }
        },
        decrement_id: function(prefix, elts){
            for (var i=0; i< elts.length; i++){
                var elt = $(elts[i]);
                xmltool._increment_id(prefix, elt, xmltool._attr, attrnames, -1);
                xmltool._increment_id(prefix, elt, xmltool._data, datanames, -1);
                xmltool.decrement_id(prefix, elt.children());
            }
        },
        truncate: function (str, limit) {
            var bits, i;
            bits = str.split('');
            if (bits.length > limit) {
                for (i = bits.length - 1; i > -1; --i) {
                    if (i > limit) {
                        bits.length = i;
                    }
                    else if (' ' === bits[i]) {
                        bits.length = i;
                        break;
                    }
                }
                bits.push('...');
            }
            return bits.join('');
        },
        get_first_class: function(obj){
            return obj.attr('class').split(' ')[0];
        }
    }

    for (key in functions){
        exports[key] = functions[key];
    }
}(typeof exports === "undefined"? (this.xmltool={}): exports));


(function(exports){

    exports.jstree = function(){
        var self = {};

        $.extend(self,{
            same_node: function(node1, node2){
                // We assume there is no multiple selection, node1 and node2 are not list!
                if(node1 === node2)
                    return true;
                if(node1[0] && node2[0] && node1[0] === node2[0])
                    return true;
                return false;
            },
            same_class: function(node1, node2){
                if (xmltool.get_first_class(node1) == xmltool.get_first_class(node2))
                    return true;
                return false;
            },
            check_move: function (m) {
                // Only be able to move elements with the same parent and the
                // same class
                var p = this._get_parent(m.o);
                if(!p) return false;
                p = p == -1 ? this.get_container() : p;
                if (! self.same_node(p, m.np)){
                    return false;
                }
                if (!self.same_class(m.o, m.r)){
                    return false;
                }
                return true;
            },
            move_node: function (event, data) {
                var position = data.rslt.p;
                var drag_node = data.rslt.o; // The node we are moving
                var drag_node_id = data.rslt.o.attr('id').replace(/^tree_/, '');
                var reference_node = data.rslt.r; // The reference where we are moving the node
                var reference_node_id = reference_node.attr('id').replace(/^tree_/, '');
                var drag_elt = $('#' + xmltool.escape_id(drag_node_id)).parent();
                var reference_elt = $('#' + xmltool.escape_id(reference_node_id)).parent();
                var button = drag_elt.prev();
                if (position == 'before'){
                    // The previous element is a button to add elements to the list
                    var prev = reference_elt.prev();
                    prev.before(button);
                    prev.before(drag_elt);
                }
                else if (position == 'after'){
                    reference_elt.after(drag_elt);
                    reference_elt.after(button);
                }

                var elts = drag_node.parent().children();
                var longprefix = xmltool.get_prefix(drag_node.attr('id'));
                var prefix = xmltool.get_prefix(longprefix);
                xmltool.replace_id(prefix, elts);

                var elts = drag_elt.parent().children();
                prefix = prefix.replace(/^tree_/, '');
                xmltool.replace_id(prefix, elts, step=2);
            }
        });
        return self;
    }();

}(typeof exports === "undefined"? this.xmltool: exports));


(function($){

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

        var add_node = function(data){
            //jstree
            var jstree_data = $(data.jstree_data);
            var previous = $(data.previous);

            for(var i=0; i < previous.length; i++){
                var position = previous[i][0];
                var selector = xmltool.escape_id(previous[i][1]);
                var parentobj = $(selector);
                if (parentobj.length > 1){
                    alert('not expected');
                }
                if (parentobj.length){
                    // Create node
                    create_nodes($('#tree'), jstree_data[0], parentobj, position);
                    break;
                }
            }
        };

        var delete_node = function(node_id){
            var tree = $('#tree');
            var node = tree.find('#' + xmltool.escape_id(node_id));
            if (node.length > 1){
                alert('Too many values to delete');
            }
            var css_class = node.attr('class').split(' ')[0];
            var nexts = node.nextAll('.'+xmltool.escape_id(css_class));
            var longprefix = xmltool.get_prefix(node.attr('id'));
            var prefix = xmltool.get_prefix(longprefix);
            xmltool.decrement_id(prefix, nexts);
            tree.jstree('delete_node', node);
        };

        $.extend(self, {
            set_btn_event: function(p){
                    p.find('textarea').autosize().focus(
                        function(){
                            var id = xmltool.escape_id($(this).attr('id'));
                            var tree = $('#tree');
                            tree.jstree('hover_node', $('#tree_' + id));
                        }).blur(function(){
                            var id = xmltool.escape_id($(this).attr('id'));
                            var a = $('#tree_' + id).find('a');
                            var elt = a.find('._tree_text');
                            if (elt.length == 0){
                                elt = $('<span class="_tree_text"/>').appendTo(a);
                            }
                            if($(this).val()){
                                elt.text(' (' + xmltool.truncate($(this).val(), 30) + ')');
                            }
                            else{
                                elt.text('');
                            }
                        });

            var set_fielset = function(fieldsets){
                fieldsets.togglefieldset().bind('hide.togglefieldset', function(e){
                    var o = $('#tree_' + xmltool.escape_id($(this).attr('id')));
                    $('#tree').jstree("close_node", o);
                    return false;
                }).bind('show.togglefieldset', function(e){
                    var o = $('#tree_' + xmltool.escape_id($(this).attr('id')));
                    $('#tree').jstree("open_node", o);
                    return false;
                });
            };

            set_fielset(p.find('fieldset'));
            if(p.is('fieldset')){
                set_fielset(p);
            }


            p.find('.btn-delete').on('click', function(){
                // TODO: Perhaps one delete button class is sufficient since we
                // can know if we are in a list or in a fieldset easily
                var add_btn = $(this).prev('.btn');
                // TODO: this condition should certainly be removed, if we can
                // delete the block, we should be able to read it!
                var parent_obj = $(this).parent();
                if(add_btn.length){
                    parent_obj.replaceWith(add_btn);
                    add_btn.removeClass('hidden');
                }
                else{
                    parent_obj.remove();
                }
                delete_node('tree_' + parent_obj.data('id'));
            });

            p.find('.btn-delete-fieldset').on('click', function(){
                var fieldset = $(this).parent('legend').parent('fieldset');
                if (fieldset.parent('.list-container').length){
                    fieldset.prev().remove(); // the add btn
                }
                var add_btn = $(this).prev('.btn');
                var is_list = fieldset.parent('.list-container').length;
                if (is_list){
                    var longprefix = xmltool.get_prefix(fieldset.attr('id'));
                    var prefix = xmltool.get_prefix(longprefix);
                    var nexts = fieldset.nextAll();
                    xmltool.decrement_id(prefix, nexts);
                }
                if(add_btn.length){
                    fieldset.replaceWith(add_btn);
                    add_btn.removeClass('hidden');
                }
                else{
                    fieldset.remove();
                }
                delete_node('tree_' + fieldset.attr('id'));

            });

            p.find('.btn-delete-list').on('click', function(){
                var parent_obj = $(this).parent();
                var nexts = parent_obj.nextAll();
                parent_obj.prev().remove();
                parent_obj.remove();
                delete_node('tree_' + parent_obj.data('id'));

                var longprefix = xmltool.get_prefix(parent_obj.data('id'));
                var prefix = xmltool.get_prefix(longprefix);
                xmltool.decrement_id(prefix, nexts);
            });

            p.find('.btn-add-ajax').on('click', function(){
                var $this = $(this);
                var dtd_url = $('form#xmltool-form #_xml_dtd_url').val();
                var params = {
                    elt_id: $(this).data('id'),
                    dtd_url: dtd_url
                };
                $.ajax({
                     type: 'GET',
                     url: settings.add_element_url,
                     data: params,
                     dataType: 'json',
                     success: function(data, textStatus, jqXHR){
                         var obj = $(data.html);
                         self.set_btn_event(obj);
                         $this.replaceWith(obj);

                        //jstree
                        add_node(data);
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                      console.log('Error ajax loading');
                    }
                });
            });
            p.find('.btn-add-ajax-choice').on('change', function(){
                // Same as before, the only difference is the way to get the
                // the value and the event.
                var $this = $(this);
                var dtd_url = $('form#xmltool-form #_xml_dtd_url').val();
                var params = {
                    elt_id: $(this).val(),
                    dtd_url: dtd_url
                };
                $.ajax({
                     type: 'GET',
                     url: settings.add_element_url,
                     data: params,
                     dataType: 'json',
                     success: function(data, textStatus, jqXHR){
                         var obj = $(data.html);
                         self.set_btn_event(obj);
                         $this.replaceWith(obj);

                        //jstree
                        add_node(data);
                        $this.val($this.find('option:first').val());
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                      console.log('Error ajax loading');
                    }
                });
            });

            p.find('.btn-add-ajax-choice-list').on('change', function(){
                // Same as before, the only difference is the way to get the
                // the value and the event.
                var $this = $(this);
                var dtd_url = $('form#xmltool-form #_xml_dtd_url').val();
                var params = {
                    elt_id: $(this).val(),
                    dtd_url: dtd_url
                };
                $.ajax({
                     type: 'GET',
                     url: settings.add_element_url,
                     data: params,
                     dataType: 'json',
                     success: function(data, textStatus, jqXHR){
                         var obj = $(data.html);
                        // We use a fake 'div' since we don't get a container,
                        // and we need one to attach the events!
                        self.set_btn_event($('<div/>').append(obj));
                        $this.after(obj);
                        var tmp = $(obj[obj.length-1]);
                        var nexts = tmp.nextAll();
                        // TODO: check it works fine
                        var longprefix = xmltool.get_prefix($this.val());
                        var prefix = xmltool.get_prefix(longprefix);
                        xmltool.increment_id(prefix, nexts);

                        //jstree
                        add_node(data);
                        $this.val($this.find('option:first').val());
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                      console.log('Error ajax loading');
                    }
                });
            });

            p.find('.btn-add-ajax-list').on('click', function(){
                var $this = $(this);
                var dtd_url = $('form#xmltool-form #_xml_dtd_url').val();
                var params = {
                    elt_id: $(this).data('id'),
                    dtd_url: dtd_url
                };
                // TODO: do nothing if elt_id is empty
                $.ajax({
                     type: 'GET',
                     url: settings.add_element_url,
                     data: params,
                     dataType: 'json',
                     success: function(data, textStatus, jqXHR){
                        var obj = $(data.html);
                        // We use a fake 'div' since we don't get a container,
                        // and we need one to attach the events!
                        self.set_btn_event($('<div/>').append(obj));
                        $this.after(obj);
                        var tmp = $(obj[obj.length-1]);
                        var nexts = tmp.nextAll();
                        var longprefix = xmltool.get_prefix($this.data('id'));
                        var prefix = xmltool.get_prefix(longprefix);
                        xmltool.increment_id(prefix, nexts);

                        //jstree
                        add_node(data);

                    },
                    error: function(jqXHR, textStatus, errorThrown){
                      console.log('Error ajax loading');
                    }
                });
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
            }
        });

        return this.each(function(){
            self.set_btn_event($(this));
        });
    };
})(jQuery);
