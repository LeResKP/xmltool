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
                if (typeof(data.children) !== 'undefined'){
                    for(var i=0; i < data.children.length; i++){
                        tree.jstree("create_node", node, 'last', data.children[i]);
                    }
                }
                tree.jstree('open_all', node);
            }
        });
        return self;
    })();

})(window.jQuery, xmltool);
