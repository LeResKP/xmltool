var xmltool = xmltool || {};

var create_nodes = function(tree, data, parentobj, position){
    var node = tree.jstree("create_node", parentobj, position, data);
    var css_class = node.attr('class').split(' ')[0];
    var nexts = node.nextAll('.'+xmltool.escape_id(css_class));
    var longprefix = xmltool.get_prefix(node.attr('id'));
    var prefix = xmltool.get_prefix(longprefix);
    xmltool.increment_id(prefix, nexts);
    if (typeof(data.children) !== 'undefined'){
        for(var i=0; i < data.children.length; i++){
            tree.jstree("create_node", node, 'last', data.children[i]);
        }
    }
    tree.jstree('open_all', node);
};


(function($, ns){
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
            return parseInt(id.replace(re_split, '$2'), 10);
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
                if(value){
                    var values = value.split(' ');
                    var output = [];
                    for(var i=0; i<values.length; i++){
                        var v = values[i];
                        var index = parseInt(v.replace(re_id, '$1'), 10);
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
                    var values = value.split(' ');
                    var output = [];
                    for(var i=0; i<values.length; i++){
                        var v = values[i];
                        var old_index = parseInt(v.replace(re_id, '$1'), 10);
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
                var tmp_index;
                if (typeof force_index !== 'undefined'){
                    tmp_index = force_index;
                }
                else{
                    tmp_index = index;
                }
                xmltool._replace_id(prefix, elt, xmltool._attr, attrnames, tmp_index);
                xmltool._replace_id(prefix, elt, xmltool._data, datanames, tmp_index);
                xmltool.replace_id(prefix, elt.children(), 1, tmp_index);

                if (step === 1){
                    index += 1;
                }
                else if(((i+1) % step) === 0 && i !== 0){
                    index += 1;
                }
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
    };

    for (var key in functions){
        ns[key] = functions[key];
    }
})(window.jQuery, xmltool);


(function($, ns){

    ns.jstree = (function(){
        var self = {};

        $.extend(self,{
            same_node: function(node1, node2){
                // We assume there is no multiple selection, node1 and node2 are not list!
                if(node1 === node2){
                    return true;
                }
                if(node1[0] && node2[0] && node1[0] === node2[0]){
                    return true;
                }
                return false;
            },
            same_class: function(node1, node2){
                if (xmltool.get_first_class(node1) === xmltool.get_first_class(node2)){
                    return true;
                }
                return false;
            },
            check_move: function (m) {
                // Only be able to move elements with the same parent and the
                // same class
                var p = this._get_parent(m.o);
                if(!p) {return false;}
                p = (p === -1) ? this.get_container() : p;
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
                var drag_elt = $('#' + xmltool.escape_id(drag_node_id));
                var reference_elt = $('#' + xmltool.escape_id(reference_node_id));

                if(drag_elt.is('textarea')){
                    drag_elt = drag_elt.parent();
                    reference_elt = reference_elt.parent();
                }
                var button = drag_elt.prev();
                if (position === 'before'){
                    // The previous element is a button to add elements to the list
                    var prev = reference_elt.prev();
                    prev.before(button);
                    prev.before(drag_elt);
                }
                else if (position === 'after'){
                    reference_elt.after(drag_elt);
                    reference_elt.after(button);
                }

                var elts = drag_node.parent().children();
                var longprefix = xmltool.get_prefix(drag_node.attr('id'));
                var prefix = xmltool.get_prefix(longprefix);
                xmltool.replace_id(prefix, elts);

                elts = drag_elt.parent().children();
                prefix = prefix.replace(/^tree_/, '');
                xmltool.replace_id(prefix, elts, 2);
            }
        });
        return self;
    })();

})(window.jQuery, xmltool);


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
                var selector = xmltool.escape_id(previous[i][1]);
                var parentobj = $(selector + ':last');
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

    Xmltool.prototype.addElement = function($btn, elt_id){
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
                    var longprefix = xmltool.get_prefix(elt_id);
                    var prefix = xmltool.get_prefix(longprefix);
                    xmltool.increment_id(prefix, nexts);
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
        var $addBtn = $btn.prev('.btn');
        var $parent = this.$form.find(xmltool.escape_id($btn.data('target')));
        if($btn.hasClass('btn-list')) {
            var nexts = $parent.nextAll();
            // Remove the add button
            $parent.prev().remove();
            $parent.remove();
            var longprefix = xmltool.get_prefix($parent.data('id'));
            var prefix = xmltool.get_prefix(longprefix);
            xmltool.decrement_id(prefix, nexts);
        }
        else {
            $parent.replaceWith($addBtn);
            $addBtn.removeClass('hidden');
        }
        this.delete_node('tree_' + $parent.data('id'));
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

        Xmltool.prototype.set_btn_event = function(p){
                    p.find('textarea').autosize().focus(
                        function(){
                            var id = xmltool.escape_id($(this).attr('id'));
                            var tree = $('#tree');
                            tree.jstree('hover_node', $('#tree_' + id));
                            $(this).on('keyup.xmltool', function(){
                                // TODO: this method should be improved to make
                                // sure the user has made an update
                                self.trigger('field_change.xmltool');
                            });
                        }).blur(function(){
                            var id = xmltool.escape_id($(this).attr('id'));
                            var a = $('#tree_' + id).find('a');
                            var elt = a.find('._tree_text');
                            if (elt.length === 0){
                                elt = $('<span class="_tree_text"/>').appendTo(a);
                            }
                            if($(this).val()){
                                elt.text(' (' + xmltool.truncate($(this).val(), 30) + ')');
                            }
                            else{
                                elt.text('');
                            }
                            $(this).unbind('keyup.xmltool');
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
                var $btn = $(this);
                xt.removeElement($btn);
            });

            p.find('a.btn-add-ajax').on('click', function(){
                var $btn = $(this);
                xt.addElement($btn, $btn.data('id'));
            });
            p.find('select.btn-add-ajax').on('change', function(){
                var $btn = $(this);
                xt.addElement($btn, $btn.val());
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
