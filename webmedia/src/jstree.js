if (typeof xmltool === 'undefined') {
    /*jshint -W020 */
    xmltool = {};
}

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
                if (xmltool.utils.get_first_class(node1) === xmltool.utils.get_first_class(node2)){
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
                var drag_elt = $('#' + xmltool.utils.escape_id(drag_node_id));
                var reference_elt = $('#' + xmltool.utils.escape_id(reference_node_id));

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

                var css_class = xmltool.utils.get_first_class(drag_node);
                var elts = drag_node.parent().children('.' + xmltool.utils.escape_id(css_class));
                var longprefix = xmltool.utils.get_prefix(drag_node.attr('id'));
                var prefix = xmltool.utils.get_prefix(longprefix);
                xmltool.utils.replace_id(prefix, elts);

                elts = drag_elt.parent().children();
                prefix = prefix.replace(/^tree_/, '');
                // We need to update the index only the 2 steps because we have
                // button + div + button + div so we want to keep the same
                // index for each button + div group
                xmltool.utils.replace_id(prefix, elts, 2);
            },
            create_nodes: function(tree, data, parentobj, position){
                var node = tree.jstree("create_node", parentobj, position, data);
                var css_class = node.attr('class').split(' ')[0];
                var nexts = node.nextAll('.'+xmltool.utils.escape_id(css_class));
                var longprefix = xmltool.utils.get_prefix(node.attr('id'));
                var prefix = xmltool.utils.get_prefix(longprefix);
                var index = xmltool.utils.get_index(longprefix);
                xmltool.utils.increment_id(prefix, nexts, index);

                xmltool.jstree.create_sub_nodes(tree, node, data);
                tree.jstree('open_all', node);
            },
            create_sub_nodes: function(tree, node, data) {
                if (typeof(data.children) !== 'undefined'){
                    for(var i=0; i < data.children.length; i++){
                        var child = data.children[i];
                        var n = tree.jstree("create_node", node, 'last', child);
                        xmltool.jstree.create_sub_nodes(tree, n, child);
                    }
                }
            },
            copy: function(node) {
                var id = node.attr('id').replace(/^tree_/, '');
                var selector = xmltool.utils.escape_id(id);
                var elt = $('#' + selector);
                var form = elt.parents('form');
                var params = form.serialize();

                // xmltool.jstree.copy_id = id;
                var url = form.data('copy-href');
                var xmltoolObj = form.data('xmltool');
                var dtdUrl = xmltoolObj.dtdUrl;
                params += '&elt_id=' + id + '&dtd_url=' + dtdUrl;
                $.ajax({
                    type: 'POST',
                    url: url,
                    data: params,
                    dataType: 'json',
                    async: false,
                    success: function(data, textStatus, jqXHR){
                        if (data.error_msg){
                            xmltoolObj.message('error', data.error_msg);
                        }
                        else if (data.info_msg){
                            xmltoolObj.message('info', data.info_msg);
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        var msg = jqXHR.status + ' ' + jqXHR.statusText;
                        xmltoolObj.message('error', msg);
                    }
                });
            },
            paste: function(node) {
                var id = node.attr('id').replace(/^tree_/, '');
                var selector = xmltool.utils.escape_id(id);

                var elt = $('#' + selector);
                var form = elt.parents('form');
                var params = form.serialize();
                var url = form.data('paste-href');
                var xmltoolObj = form.data('xmltool');
                var dtdUrl = xmltoolObj.dtdUrl;

                params += '&elt_id=' + id + '&dtd_url=' + dtdUrl;
                $.ajax({
                    type: 'POST',
                    url: url,
                    data: params,
                    dataType: 'json',
                    async: false,
                    success: function(data, textStatus, jqXHR){
                        if (data.error_msg){
                            xmltoolObj.message('error', data.error_msg);
                            return false;
                        }

                        var elt_id = data.elt_id;
                        var $btn;
                        if(data.is_choice) {
                            $btn = $('.btn-add').find('[value="'+ data.elt_id+'"]');
                            $btn = $btn.parent('select');
                        }
                        else {
                            $btn = $('[data-elt-id="'+ data.elt_id +'"]');
                        }
                        var objs = $(data.html);
                        // TODO: the following logic should be refactorized
                        // with the function which add element
                        if($btn.hasClass('btn-list')){
                            $btn.after(objs);
                            // Last is the button to add more
                            var last = $(objs[objs.length-1]);
                            var nexts = last.nextAll();
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
                        form.data('xmltool').add_node(data);
                        xmltoolObj.message('info', 'Pasted');
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        var msg = jqXHR.status + ' ' + jqXHR.statusText;
                        xmltoolObj.message('error', msg);
                    }
                });
            }
        });
        return self;
    })();

})(window.jQuery, xmltool);
