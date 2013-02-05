(function(exports) {

    var re_id = new RegExp('^(.*):(\\d*)$');

    functions = {
        replace_id: function(container, new_id, container_id){
            var container_id = container_id || container.attr('id');
            var regex = new RegExp('^('+container_id+':)\\d*');
            var id = container_id.replace(regex, '$1') + ':' + new_id;
            $(container).each(function(){
                $(this).find('[id^="'+container_id+':"]').each(function(){
                    var v_id = $(this).attr('id');
                    if(typeof(v_id) != 'undefined'){
                        $(this).attr('id', v_id.replace(regex, id));
                    }
                });
                $(this).find('[name^="'+container_id+':"]').each(function(){
                    var v_name = $(this).attr('name');
                    if(typeof(v_name) != 'undefined'){
                        $(this).attr('name', v_name.replace(regex, id));
                    }
                });
            });
        },
        has_field: function(container){
            var found=false;
            container.find('.conditional-option').each(function(){
                $(this).children().each(function(){
                    if (! $(this).hasClass('growing-source') && ! $(this).hasClass('deleted') && !$(this).is('a')){
                        found=true;
                        return true;
                    }
                });
            });
            return found;
        },
        update_conditional_container: function(obj){
            if (obj.parent().hasClass('conditional-option')){
                var conditional_container = obj.parent().parent();
                if (! exports.has_field(conditional_container)){
                    conditional_container.children(':first').removeClass('hidden');
                    conditional_container.find('.conditional-option').addClass('deleted');
                }
            }
        },
        confirm_delete: function(button){
            var question = 'Are you sure you want to delete this ' + button.text().replace('Delete ', '');
            return confirm(question);
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
        get_first_class: function(elt){
            return elt.attr('class').split(' ')[0];
        },
        escape_id: function(id){
            return id.replace(/:/g, '\\:');
        },
        get_index: function(id){
            return parseInt(id.replace(re_id, '$2'));
        },
        get_prefix: function(id){
            return id.replace(re_id, '$1');
        }
    }

    for (key in functions){
        exports[key] = functions[key];
    }

    exports.jstree = (function(){
        var self = {};
        $.extend(self, {
            update_node: function(node, old_id, new_id){
                var id = node.data("id");
                var re_id = new RegExp('^' + old_id);
                id = id.replace(re_id, new_id);
                node.data('id', id);
                node.attr('id', 'tree_' + id);

                // We assume we just need to update the first class
                classes = node.attr('class').split(' ');
                classes.reverse()
                cls = classes.pop();
                var re_class = new RegExp('^tree_' + old_id);
                cls = cls.replace(re_class, 'tree_'+new_id);
                classes.push(cls);
                classes.reverse();
                node.attr('class', classes.join(' '));
            },
            update_node_and_children: function(node, new_id){
                var old_id = node.data('id')
                self.update_node(node, old_id, new_id);
                node.find('li').each(function(){
                    self.update_node($(this), old_id, new_id); 
                });
            },
            increment_id: function(node){
                var id = $(node).data('id');
                var index = xmltools.get_index(id);
                var prefix_id = xmltools.get_prefix(id);
                var siblings = node.find('~ .' + xmltools.escape_id(xmltools.get_first_class(node)));
                for(var i=0; i < siblings.length; i++){
                    var elt = siblings[i];
                    index ++;
                    self.update_node_and_children($(elt), prefix_id + ':' + index);
                }
            },
            create_nodes: function(tree, data, parentobj, position){
                var node = tree.jstree("create_node", parentobj, position, data);
                self.increment_id(node);
                if (typeof(data.children) != 'undefined'){
                    for(var i=0; i < data.children.length; i++){
                        tree.jstree("create_node", node, 'last', data.children[i]);
                    }
                }
                tree.jstree('open_all', node);
            },
            delete_node: function(tree, elt){
                tree.jstree("delete_node", tree.find('#tree_' + xmltools.escape_id(elt.attr('id'))));
            },
            add_node: function(url, tree, elt){
                var dtd_url = $('form#xmltools-form #_dtd_url').val();
                var params = {
                    elt_id: elt.attr('id'),
                    dtd_url: dtd_url
                }
                $.ajax({
                     type: 'GET',
                     url: url,
                     data: params,
                     dataType: 'json',
                     success: function(data, textStatus, jqXHR){
                        var node = data.elt;
                        var previous = data.previous;
                        for (var i=0; i< previous.length; i++){
                            var selector = xmltools.escape_id(previous[i][0]);
                            var position = previous[i][1];
                            var parentobj = $(selector + ':last');
                            if (parentobj.length){
                                self.create_nodes(tree, node, parentobj, position);
                                break;
                            }
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                      alert('Error ajax loading');
                    }
                });
            },
            same_node: function(node1, node2){
                // We assume there is no multiple selection, node1 and node2 are not list!
                if(node1 === node2)
                    return true;
                if(node1[0] && node2[0] && node1[0] === node2[0])
                    return true;
                return false;
            },
            same_class: function(node1, node2){
                if (xmltools.get_first_class(node1) == xmltools.get_first_class(node2))
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
                var drag_node_id = data.rslt.o.data('id');
                var reference_node = data.rslt.r; // The reference where we are moving the node
                var reference_node_id = reference_node.data('id');
                if(position == 'before'){
                    xmltools.jstree.update_node_and_children(drag_node, reference_node_id);
                    xmltools.jstree.increment_id(drag_node);
                    var old_e = $('#' + xmltools.escape_id(drag_node_id)).parent('.container');
                    var new_e = $('#' + xmltools.escape_id(reference_node_id)).parent('.container');
                    new_e.before(old_e);
                    var container_prefix = xmltools.get_prefix(drag_node_id);
                    var new_id = xmltools.get_index(reference_node_id);
                    xmltools.replace_id(old_e, new_id, container_prefix);
                    old_e.nextAll('.container').each(function(){
                        new_id += 1;
                        xmltools.replace_id($(this), new_id, container_prefix);
                    });
                }
                else if (position == 'after'){
                    var old_e = $('#' + xmltools.escape_id(drag_node_id)).parent('.container');
                    var new_e = $('#' + xmltools.escape_id(reference_node_id)).parent('.container');
                    xmltools.jstree.increment_id(reference_node);
                    new_e.after(old_e);
                    var new_id = xmltools.get_index(reference_node_id);
                    var container_prefix = xmltools.get_prefix(drag_node_id);
                    new_e.nextAll('.container').each(function(){
                        new_id += 1;
                        xmltools.replace_id($(this), new_id, container_prefix);
                    });
                }
                else{
                    alert('Not supported position after move!');
                }
            }
        });
        return self;
    })();

}(typeof exports === "undefined"? (this.xmltools={}): exports));


(function($){
    
    $.fn.xmltools = function(options){
    
        var settings = $.extend({
            'on_submit': function(){
                $(this).find('.deleted').remove();
                $(this).find('.growing-source').remove();
            },
            'jstree': true,
            'jstree_selector': '#tree',
            'jstree_url': ''
        }, options);

        var tree = undefined;
        if (settings['jstree']){
            tree = $(settings['jstree_selector']);
        }

        var set_btn_event = function(p){

            var on_delete = function(elt){
                if (tree && tree.length){
                    xmltools.jstree.delete_node(tree, elt);
                }
            };

            var on_add = function(elt){
                if (tree && tree.length){
                    var url = settings.jstree_url;
                    if (url){
                        xmltools.jstree.add_node(url, tree, elt);
                    }
                }
            }

            p.find('.delete-button').on('click', function(){
                var container = $(this).parent();
                container.addClass('deleted');
                container.parent('.container').addClass('inline');
                container.prev().removeClass('hidden');
                xmltools.update_conditional_container(container);
                on_delete($(this).next());
            });
            p.find('.growing-delete-button').on('click', function(){
                if(xmltools.confirm_delete($(this))){
                    var container = $(this).parent();
                    container.addClass('deleted');
                    xmltools.update_conditional_container(container);
                    on_delete($(this).next());
                }
            });
            p.find('.fieldset-delete-button').on('click', function(){
                if(xmltools.confirm_delete($(this))){
                    var container = $(this).parent('legend').parent('fieldset');
                    container.addClass('deleted');
                    container.parent('.container').addClass('inline');
                    container.prev().removeClass('hidden');
                    xmltools.update_conditional_container(container);
                    on_delete(container);
                }
            });
            p.find('.growing-fieldset-delete-button').on('click', function(){
                if(xmltools.confirm_delete($(this))){
                    var fieldset = $(this).parent('legend').parent('fieldset')
                    var container = fieldset.parent('.container');
                    container.addClass('deleted');
                    xmltools.update_conditional_container(container);
                    on_delete(fieldset);
                }
            });
            p.find('.add-button').on('click', function(){
                $(this).next().removeClass('deleted');
                $(this).addClass('hidden');
                $(this).parent('.container').removeClass('inline');
                var child = $(this).next();
                if (child[0].nodeName != 'FIELDSET')
                    child = child.children('textarea');
                on_add(child);
            });

            p.find('.growing-add-button').on('click',function(){
                var id = xmltools.get_index($(this).prev().attr('id'));
                var new_id = id + 1;
                var container = $(this).parent('.container');
                var source = container.parent('.growing-container').children('.growing-source').clone();
                source.removeClass('deleted').removeClass('growing-source');
                xmltools.replace_id(source, new_id);
                set_btn_event(source);
                container.after(source);
                var container_id = source.attr('id');
                source.removeAttr('id');
                var child = source.children('fieldset');
                if (!child.length)
                    child = source.children('textarea');
                on_add($(child[0]));
                source.nextAll('.container').each(function(){
                    new_id += 1;
                    xmltools.replace_id($(this), new_id, container_id);
                });
            });

        
        if (tree && tree.length){
            p.find('textarea').focus(function(){
                var id = xmltools.escape_id($(this).attr('id'));
                tree.jstree('hover_node', $('#tree_' + id));
            }).blur(function(){
                var id = xmltools.escape_id($(this).attr('id'));
                var elt = $('#tree_' + id).find('a')
                var text = elt.html();
                text = text.replace(/\(.*/, '');
                if($(this).val()){
                    elt.html(text + ' (' + xmltools.truncate($(this).val(), 30) + ')');
                }
                else{
                    elt.html(text);
                }
                
            });
        }

        p.find('select.conditional').on('change', function(){
                if ($(this).val()){
                    var cls = xmltools.escape_id($(this).val());
                    var container = $(this).parent().find('.' + cls);
                    container.removeClass('deleted');
                    var growing_source = container.children('.growing-source');
                    if (growing_source.length){
                        growing_source.children('.growing-add-button').trigger('click');
                    }
                    else{
                        var button = container.children('.add-button');
                        if (button.length)
                            button.trigger('click');
                        else
                            // Make sure the tree (if present) is up to date!
                            on_add(container);
                    }
                    $(this).addClass('hidden');
                }
            });
        
        }

        return this.each(function(){
            set_btn_event($(this));
            $(this).on('submit', settings.on_submit);
        });
    };
})(jQuery);
