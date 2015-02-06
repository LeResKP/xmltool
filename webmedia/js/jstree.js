if (typeof xmltool === 'undefined') {
    /*jshint -W020 */
    xmltool = {};
}


/** @namespace xmltool.jstree */
xmltool.jstree = {};


(function($, xmltool){
	"use strict";

    /**
     * Some functions use to find node from form and vice versa.
     * Also functions to manage the node, updating class, id, adding new node, ...
     *
     * @namespace xmltool.jstree.utils
     * */

    var TREE_PREFIX = 'tree_';
    var COLLAPSIBLE_PREFIX = 'collapse_';

    /**
     * Get the form id corresponding to a given node. In the tree the ids are
     * the same prefixed by TREE_PREFIX.
     *
     * @param {jstreeNode} node - a jstree node
     * @return {string} The form id corresponding to the node
     *
     * @memberof xmltool.jstree.utils
     * @method getFormId
     */
    this.getFormId = function(node) {
        return node.a_attr.id.slice(TREE_PREFIX.length);
    };

    /**
     * Get the form element corresponding to a given node. This form element is
     * a <div>.
     *
     * @param {jstreeNode} node - a jstree node
     * @return {jQuery} The form element corresponding to the node
     *
     * @memberof xmltool.jstree.utils
     * @method getFormElement
     */
    this.getFormElement = function(node) {
        var id = this.getFormId(node);
        return xmltool.utils.getElementById(id);
    };

    /**
     * Get the collapsible element corresponding to a given node.
     *
     * @param {jstreeNode} node - a jstree node
     * @return {jQuery} The form element corresponding to the node
     *
     * @memberof xmltool.jstree.utils
     * @method getCollapsibleElement
     */
    this.getCollapsibleElement = function(node) {
        var id = this.getFormId(node);
        return $('#' + xmltool.utils.escapeAttr(id) + ' > .panel-collapse');
    };

    /**
     * Get the tree element corresponding to the given form id.
     *
     * @param {String} id - form id we want to get the tree element corresponding
     *
     * @memberof xmltool.jstree.utils
     * @method getTreeElementFromId
     */
    this.getTreeElementFromId = function(id) {
        var treeId = TREE_PREFIX + id;
        return xmltool.utils.getElementById(treeId);
    };

    /**
     * Get the tree element corresponding to a textarea.
     *
     * @param {jQuery} $textarea - a jQuery textarea object
     * @return {jQuery} The tree element corresponding to the textarea
     *
     * @memberof xmltool.jstree.utils
     * @method getTreeElementFromTextarea
     */
    this.getTreeElementFromTextarea = function($textarea) {
        var id = TREE_PREFIX + $textarea.parent().attr('id');
        return xmltool.utils.getElementById(id);
    };

    /**
     * Get the tree element corresponding to a collapsible.
     *
     * @param {jQuery} $collapsible - a bootstrap collapsible
     * @return {jQuery} The tree element corresponding to the collapsible
     *
     * @memberof xmltool.jstree.utils
     * @method getTreeElementFromCollapsible
     */
    this.getTreeElementFromCollapsible = function($collapsible) {
        var id = TREE_PREFIX + $collapsible.attr('id').slice(COLLAPSIBLE_PREFIX.length);
        return xmltool.utils.getElementById(id);
    };

    /**
     * Get the first class of a node
     *
     * @param {object} node - a jstree node
     * @return {string} The first class of the node
     *
     * @memberof xmltool.jstree.utils
     * @method getFirstClass
     */
    this.getFirstClass = function(node) {
        return node.li_attr['class'].split(' ')[0];
    };

    /**
     * Get the form prefix corresponding to a node
     * It's the prefix of elements from the same list
     *
     * @param {object} node - a jstree node
     * @return {string} The form prefix
     *
     * @memberof xmltool.jstree.utils
     * @method getFormPrefix
     */
    this.getFormPrefix = function(node) {
        return this.getFirstClass(node).slice(TREE_PREFIX.length);
    };

    /**
     * Get the tree element corresponding to a collapsible.
     *
     * @param {Array} selectors - a list of 2 elements list [['position', 'selector']]
     * @return {object} Returns 2 keys parentobj and position when finding the parent jQuery object
     *
     * @memberof xmltool.jstree.utils
     * @method findParentNodeAndPosition
     */
    this.findParentNodeAndPosition = function(selectors) {
        for(var i=0; i < selectors.length; i++){
            var position = selectors[i][0];
            var parentobj = $(selectors[i][1]);
            if (parentobj.length > 1){
                return {};
            }
            if (parentobj.length){
                return {
                    parentobj: parentobj,
                    position: position
                };
            }
        }
        return {};
    };

    /**
     * Get the position of the node in the children
     *
     * @param {object} node - a jstree node
     * @param {Array} node - list of jstree nodes
     * @return {int} The position of the node in children 
     *
     * @memberof xmltool.jstree.utils
     * @method getNodePositionInChildren
     */
    this.getNodePositionInChildren = function(node, children) {
        for (var i=0, len=children.length; i < len; i++) {
            if (children[i].id === node.id) {
                return i;
            }
        }
        return -1;
    };

    /**
     * Get the node sibling of the same list.
     *
     * @param {object} node - a jstree node
     * @return {Array} List of nodes
     *
     * @memberof xmltool.jstree.utils
     * @method getNodeSiblingsAndSelf
     */
    this.getNodeSiblingsAndSelf = function(node) {
        // TODO: remove hardcoded tree id
        var parentNode = $('#tree').jstree('get_node', node.parent),
            firstClass = this.getFirstClass(node),
            index = 0,
            children = [];
        for (var i=0, len=parentNode.children.length; i < len; i++) {
            var tmpNode = $('#tree').jstree('get_node', parentNode.children[i]);
            if (this.getFirstClass(tmpNode) === firstClass) {
                children.push(tmpNode);
            }
        }
        return children;
    };

    /**
     * Update the node classes and id. When we insert or mode node we have to
     * update the classes and id which correspond with the position
     *
     * @param {jQuery} $tree - the tree object
     * @param {object} node - a jstree node
     * @param {string} prefix - The current prefix to replace
     * @param {string} newPrefix - The new prefix
     *
     * @memberof xmltool.jstree.utils
     * @method updateNodePrefix
     */
    this.updateNodePrefix = function($tree, node, prefix, newPrefix) {
        var re = new RegExp('^' + prefix);
        node.a_attr['id'] = node.a_attr['id'].replace(re, newPrefix);
        // Also update the css classes
        var cssClasses = node.li_attr['class'].split(' ');
        for(var k=0, lenk=cssClasses.length; k < lenk; k++) {
            cssClasses[k] = cssClasses[k].replace(re, newPrefix);
        }
        node.li_attr['class'] = cssClasses.join(' ');

        for (var i=0, len=node.children.length; i < len; i++) {
            var child = $tree.jstree("get_node", node.children[i]);
            this.updateNodePrefix($tree, child, prefix, newPrefix);
        }
        $tree.jstree("_node_changed", node.id);
    };

    /**
     * Update the nodes classes and id.
     *
     * @param {jQuery} $tree - the tree object
     * @param {object} node - a jstree node
     * @param {boolean} includeSelf - If true also replace the id of the given node
     *
     * @memberof xmltool.jstree.utils
     * @method updateNodesPrefix
     */
    this.updateNodesPrefix = function($tree, node, includeSelf) {
        includeSelf = includeSelf || false;
        var children = this.getNodeSiblingsAndSelf(node),
            pos = this.getNodePositionInChildren(node, children),
            firstClass = this.getFirstClass(node);

        for(var j=0, len=children.length; j < len; j++) {
            if (j > pos || (includeSelf && j === pos)) {
                var child = children[j];
                var prefix = firstClass + ':[0-9]+:';
                var newPrefix = firstClass + ':' + j + ':';
                this.updateNodePrefix($tree, child, prefix, newPrefix);
            }
        }
        $tree.jstree("redraw");
    };

    /**
     * Add a new node to the tree
     *
     * @param {jQuery} $btn - the button clicked to add a node
     * @param {jQuery} $tree - the tree object
     * @param {object} data - The node data to create
     *
     * @memberof xmltool.jstree.utils
     * @method addNode
     */
    this.addNode = function($btn, $tree, data) {
        var isList = $btn.hasClass('btn-list'),
            jstree_data = $(data.jstree_data),
            previous = data.previous;

        var parentData = this.findParentNodeAndPosition(previous);
        if (typeof parentData === 'undefined') {
            // TODO: support message
            // this.message('error', "Can't add a node in the tree");
            return null;
        }
        var newNodeId = $tree.jstree("create_node",
                            parentData.parentobj,
                            data.jstree_data,
                            parentData.position),
            newNode = $tree.jstree("get_node", newNodeId);
        if (isList) {
            this.updateNodesPrefix($tree, newNode);
        }
        return newNodeId;
    };

    /**
     * Remove a node from the tree
     *
     * @param {jQuery} $btn - the button clicked to add a node
     * @param {String} eltId - The form id corresponding to the node to delete
     * @param {jQuery} $tree - The tree element
     *
     * @memberof xmltool.jstree.utils
     * @method addNode
     */
    this.removeNode = function($btn, eltId, $tree) {
        var $node = this.getTreeElementFromId(eltId);
        var node = $tree.jstree('get_node', $node);

        var res;
        if($btn.hasClass('btn-list')) {
            var children = this.getNodeSiblingsAndSelf(node),
                pos = this.getNodePositionInChildren(node, children);
            res = $tree.jstree('delete_node', $node);
            if ((pos+1) < children.length) {
                var nextNode = $tree.jstree('get_node', children[pos+1]);
                this.updateNodesPrefix($tree, nextNode, true);
            }
        }
        else {
            res = $tree.jstree('delete_node', $node);
        }
        return res;
    };


}).call(xmltool.jstree.utils={}, jQuery, xmltool);

(function($, xmltool){
	"use strict";

    /**
     * Functions to manipulate the tree according to the form and vice versa.
     *
     * @namespace xmltool.jstree.core
     */

    var that = this;

    /**
     * Decorator to make sure we can't have conflict (or recursive events)
     * between the actions.
     */
    var transitioning = false;
    var transitionDecorator = function(func) {
        return function() {
            if (transitioning) {
                return false;
            }
            transitioning = true;
            func.apply(this, arguments);
            transitioning = false;
        };
    };

    /**
     * Load jstree plugin and put some events on the tree and on the form.
     *
     * **Tree events**:
     *     * open_node: open the corresponding collapsible
     *     * clone_node: close the corresponding collapsible
     *     * select_node: scroll to the corresponding form element and put the focus on the first editable element.
     *
     * **Form events**:
     *     * textarea.focus: scroll to the corresponding tree node
     *     * textarea.blur: update the description text in the corresponding tree node
     *     * collapse.shown: open the corresponding tree node
     *     * collapse.hidden: close the corresponding tree node
     *
     * @param $tree {jQuery} - the tree container object
     * @memberof xmltool.jstree.core
     * @method load
     */
    this.load = function($tree, data, $form, $formContainer) {
        // TODO: make sure we need all this plugins
        var that = this;
        $tree.removeClass('jstree').empty();
        $tree.jstree({
            "plugins" : ["themes", "ui", "crrm", "dnd", "contextmenu"],
            "core": {
                data : [data],
                html_titles: true,
                check_callback: function (operation, node, node_parent, node_position, more) {
                    if (operation === 'create_node') {
                        return true;
                    }

                    if (operation === 'delete_node') {
                        return true;
                    }

                    if (operation === 'move_node') {
                        if (node.parent !== node_parent.id) {
                            // Node should have the same parent
                            return false;
                        }
                        var children_len = node_parent.children.length;
                        if (children_len === 1) {
                            // We can't move the node since it is unique
                            return false;
                        }

                        if (more.pos === 'i') {
                            // No reason to go inside for now, we just have to
                            // drag and drop near the same children
                            return false;
                        }

                        var old_position = node_parent.children.indexOf(node.id);
                        if (more.pos === 'b' && (node_position - 1) === old_position) {
                            return false;
                        }

                        if (more.pos === 'a' && old_position < node_position) {
                            // For some reason jstree decremment the position
                            // in this case, but since it complicated our
                            // logic, just update the position.  We want
                            // node_position corresponding to the index where
                            // the node will go
                            node_position += 1;
                        }

                        var node_id, position_node;
                        if (node_position < children_len) {
                            // Check the next node has the same class
                            node_id = node_parent.children[node_position];
                            position_node = $tree.jstree("get_node", node_id);
                            if (that.utils.getFirstClass(position_node) === that.utils.getFirstClass(node)) {
                                return true;
                            }
                        }


                        if (node_position > 0) {
                            // Check previous node has the same class
                            node_id = node_parent.children[node_position - 1];
                            position_node = $tree.jstree("get_node", node_id);
                            if (that.utils.getFirstClass(position_node) === that.utils.getFirstClass(node)) {
                                return true;
                            }
                        }
                    }
                    return false;
                }

            },
            contextmenu: {
                items: function(o, cb){
                    // TODO: support to not display this menu when we don't
                    // have the url to copy/paste.
                    return {
                        copyItem: {
                            label: 'Copy',
                            action: function(data) {
                                var node = $tree.jstree("get_node", data.reference);
                                xmltool.jstree.copy(node);
                            },
                        },
                        pasteItem: {
                            label: 'Paste',
                            action: function(data) {
                                var node = $tree.jstree("get_node", data.reference);
                                xmltool.jstree.paste(node);
                            }
                        }
                    };
                }
            }
        })

        /**
         * Open the corresponding collapsible when a node is opened
         */
        .bind('open_node.jstree', transitionDecorator(function(e, data){
            if (e.isDefaultPrevented()) {
                return false;
            }
            var $elt = that.utils.getCollapsibleElement(data.node);
            $elt.collapse('show');
            e.preventDefault();
        }))

        /**
         * Close the corresponding collapsible when a node is closed
         */
        .bind('close_node.jstree', transitionDecorator(function(e, data){
            if (e.isDefaultPrevented()) {
                return false;
            }
            var $elt = that.utils.getCollapsibleElement(data.node);
            $elt.collapse('hide');
            e.preventDefault();
        }))

        /**
         * When a node is selected we want to be sure the corresponding form
         * element is visible and we put focus on the first editable field.
         */
        .bind("select_node.jstree", transitionDecorator(function (e, data) {
            var $elt = that.utils.getFormElement(data.node);
            xmltool.utils.scrollToElement($elt, $formContainer);
            var $textarea = $elt.find('textarea:first');
            if ($textarea.is(':visible')) {
                $textarea.focus();
            }
            else {
                // Focus on contenteditable
                $textarea.next().focus();
            }
        }))

        /**
         * When a node is moved we want to move the form element as well and
         * update the nodes and elements attributes
         */
        .bind("move_node.jstree", transitionDecorator(function(e, data) {
            var $elt = that.utils.getFormElement(data.node),
                $parentElt = $elt.parent('.list-container'),
                $btn = $elt.prev(),
                children = that.utils.getNodeSiblingsAndSelf(data.node),
                positionInList = that.utils.getNodePositionInChildren(data.node, children),
                prefix = that.utils.getFormPrefix(data.node);

            // Move the form element and its button too
            if (positionInList === 0) {
                // Simple case we have to move form elemnt on first position
                $parentElt.prepend($elt);
                $parentElt.prepend($btn);
            }
            else {
                var offset;
                if (data.position < data.old_position) {
                    offset = 0;
                }
                else {
                    offset = 1;
                }
                var $prev = $parentElt.children().eq((positionInList + offset) * 2 - 1);
                $prev.after($elt);
                $prev.after($btn);
            }

            // Now we have to update the prefix of the form elements and nodes
            if (data.position > data.old_position) {
                // We should update the node attributes from the old_position
                var diff = data.position - data.old_position;
                positionInList -= diff;
                var oldNode = $tree.jstree('get_node', children[positionInList]);
                // We need the button to update the form elements
                $elt = that.utils.getFormElement(oldNode);
                $btn = $elt.prev();
            }
            xmltool.form._updateElementsPrefix($btn, positionInList, prefix);

            var firstNodeToUpdate = $tree.jstree('get_node', children[positionInList]);
            that.utils.updateNodesPrefix($tree, firstNodeToUpdate, true);
        }));

        /**
         * When a textarea get focus we select the corresponding node in the
         * tree and make sure it is visible.
         */
        $form.on('focus', 'textarea.form-control', transitionDecorator(function(){
            var $elt = that.utils.getTreeElementFromTextarea($(this));
            $tree.jstree('deselect_all').jstree('select_node', $elt);
            xmltool.utils.scrollToElement($elt, $tree);
        }))

        .on('focus', '.contenteditable', transitionDecorator(function(){
            var $textarea = $(this).data('contenteditablesync').$target;
            var $elt = that.utils.getTreeElementFromTextarea($textarea);
            $tree.jstree('deselect_all').jstree('select_node', $elt);
            xmltool.utils.scrollToElement($elt, $tree);
        }))

        /**
         * Synchronise the content in the tree's preview
         */
        .on('blur', 'textarea', function() {
            var $this = $(this);
            var $elt = that.utils.getTreeElementFromTextarea($this);
            var text = $tree.jstree('get_text', $elt);
            var $text = $elt.find('._tree_text');
            if ($text.length === 0){
                text += '<span class="_tree_text"></span>';
            }
            var v;
            if($this.val()){
                v = ' (' + xmltool.utils.truncateText($this.val()) + ')';
            }
            else{
                v = '';
            }
            text = text.replace(/>[^<]*</, '>'+v+'<');
            $tree.jstree('set_text', $elt, text);
        })

        /**
         * When a collapsible is opened also open the corresponding node
         */
        .on('shown.bs.collapse', '.panel-collapse', transitionDecorator(function (e) {
            if (e.isDefaultPrevented()) {
                return false;
            }
            var $elt = that.utils.getTreeElementFromCollapsible($(this));
            $tree.jstree("open_node", $elt);
            e.preventDefault();
        }))

        /**
         * When a collapsible is closed also close the corresponding node
         */
        .on('hidden.bs.collapse', '.panel-collapse', transitionDecorator(function (e) {
            if (e.isDefaultPrevented()) {
                return false;
            }
            var $elt = that.utils.getTreeElementFromCollapsible($(this));
            $tree.jstree("close_node", $elt);
            e.preventDefault();
        }));
    };

    /**
     * Copy a node. Get the form data corresponding to the node and call an
     * ajax request to send this data to the server. The data are sent to the
     * server because we can copy/paste data from different forms/pages.
     *
     * @param {object} node - a jstree node
     *
     * @memberof xmltool.jstree
     * @method copy
     */
    this.copy = function(node) {
        var id = xmltool.jstree.utils.getFormId(node),
            $elt = xmltool.jstree.utils.getFormElement(node),
            $form = $elt.parents('form'),
            params = $form.serialize();

        var url = $form.data('copy-href');
        var xmltoolObj = $form.data('xmltool');
        params += '&elt_id=' + id;
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
    };

    /**
     * Paste a node. Send the data to the server which should return the node
     * data to insert in the tree.
     *
     * @param {object} node - a jstree node
     *
     * @memberof xmltool.jstree
     * @method copy
     */
    this.paste = function(node) {
        var id = xmltool.jstree.utils.getFormId(node),
            $elt = xmltool.jstree.utils.getFormElement(node),
            $form = $elt.parents('form'),
            params = $form.serialize();

        var url = $form.data('paste-href');
        var xmltoolObj = $form.data('xmltool');

        params += '&elt_id=' + id;
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
                var $btn = xmltool.utils.getAddButton(data.elt_id);
                xmltool.form._addElement(data.elt_id, $btn, data.html);
                // TODO: add constant to get the tree
                xmltool.jstree.utils.addNode($btn, $('#tree'), data);
                xmltoolObj.message('info', 'Pasted!');
            },
            error: function(jqXHR, textStatus, errorThrown){
                var msg = jqXHR.status + ' ' + jqXHR.statusText;
                xmltoolObj.message('error', msg);
            }
        });
    };
}).call(xmltool.jstree, jQuery, xmltool);
