/*! Xmltool - v0.1.0 - 2015-05-19
* https://github.com/LeResKP/xmltool
* Copyright (c) 2015 Aurélien Matouillot; Licensed MIT */
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
    this.load = function($tree, data, $form, $formContainer, $treeContainer) {
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
            console.log('scroll to tree');
            xmltool.utils.scrollToElement($elt, $treeContainer);
        }))

        .on('focus', '.contenteditable', transitionDecorator(function(){
            var $textarea = $(this).data('contenteditablesync').$target;
            var $elt = that.utils.getTreeElementFromTextarea($textarea);
            $tree.jstree('deselect_all').jstree('select_node', $elt);
            xmltool.utils.scrollToElement($elt, $treeContainer);
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

if (typeof xmltool === 'undefined') {
    /* jshint -W020 */
    xmltool = {};
}

/** @namespace */
xmltool.utils = {};


(function($) {
	"use strict";

    // When we automatically scroll an element we want to apply a top offset
    var SCROLL_OFFSET = 30;

    // List of attribute name we should update in updatePrefixAttrs
    var ATTRNAMES = [
        'name', 'id', 'data-comment-name', 'data-target', 'data-elt-id', 'value'
    ];

    /**
     * Escape special chars to make a valid jQuery selector.
     * @param {string} value - The attribute value to escape
     * @return {string} The escaped value
     * @memberof xmltool.utils
     * @method escapeAttr
     */
    this.escapeAttr = function(value) {
        return value.replace(/([:\.])/g, '\\$1');
    };

    /**
     * Get a jQuery object from a given id.
     * @param {string} id - The id to get
     * @return {jQuery} The jQuery element selected by id
     * @memberof xmltool.utils
     * @method getElementById
     */
    this.getElementById = function(id){
        return $('#' + this.escapeAttr(id));
    };

    /**
     * Scroll to have a given element visible.
     * @param {jQuery} $elt - the element we want visible
     * @param {jQuery} $container - the container of $elt we want to change
     * the scroll position
     * @memberof xmltool.utils
     * @method scrollToElement
     */
    this.scrollToElement = function($elt, $container) {
        var scrollTop = $elt.offset().top + $container.scrollTop() - $container.offset().top - SCROLL_OFFSET;
        $container.scrollTop(scrollTop);
    };

    /**
     * Replace the prefix of an element and its children recursively
     * @param {jQuery} $elt - the element we want to make the replacement
     * @param {string} prefix - the prefix we want to update
     * @param {string} newPrefix - the new prefix to put instead of prefix
     * @memberof xmltool.utils
     * @method updatePrefixAttrs
     */
    this.updatePrefixAttrs = function($elt, prefix, newPrefix) {
        var re = new RegExp('^(#)?(collapse-)?' + prefix);
        for (var i=0, lenNames=ATTRNAMES.length; i < lenNames; i++) {
            var attrname = ATTRNAMES[i];
            var value = $elt.attr(attrname);
            if (typeof value !== 'undefined') {
                value = value.replace(re, '$1$2' + newPrefix);
                $elt.attr(attrname, value);
            }
        }
        if ($elt.attr('data-toggle') === 'collapse') {
            // Special case for collapsible since the attribute is already
            // 'jQuery' escaped

            // Double escapement since it's a regex
            re = new RegExp('^(#collapse-)' + this.escapeAttr(this.escapeAttr(prefix)));
            var href = $elt.attr('href');
            href = href.replace(re, '$1' + this.escapeAttr(newPrefix));
            $elt.attr('href', href);
        }
        var children = $elt.children();
        for (var j=0, len=children.length; j < len; j++) {
            this.updatePrefixAttrs(children.eq(j), prefix, newPrefix);
        }
    };

    /**
     * Truncate a text on space
     *
     * @param {string} text - the text to truncate
     * @param {integer} limit - the max length of the text. (Default: 30)
     * @return {string} the truncated text
     * @memberof xmltool.utils
     * @method truncateText
     */
    this.truncateText = function(text, limit) {
        limit = limit || 30;
        var bits, i;
        bits = text.split('');
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
    };

    /**
     * Cleanup contenteditable content. This function is a bit specific to
     * CKEditor but it should work for all contenteditable
     *
     * @param {string} s - the string to cleanup
     * @return {string} The cleaned string
     * @memberof xmltool.utils
     * @method cleanupContenteditableContent
     */
    this.cleanupContenteditableContent = function(s) {
        // We want \n as new line when the text comes from contenteditale
        s = s.replace(/\r?\n?/g, '');
        s = s.replace(/<br ?\/?>/g, '\n');
        // Remove the non breaking spaces since we don't want to add it in
        // the XML files
        s = s.replace(/\u00A0/g, ' ');
        return s;
    };

    /**
     * Get the prefix and the index of an id of a list element.
     * The element should be like this: root:list_tag:0:tag
     *
     * @param {string} eltId - the list element id to get the prefix and index
     * @return {object} containing index and prefixId
     * @memberof xmltool.utils
     * @method getPrefixIndexFromListEltId
     */
    this.getPrefixIndexFromListEltId = function(eltId) {
        var lis = eltId.split(':'),
            len = lis.length;
        return {
            index: parseInt(lis[len - 2], 10),
            prefixId:lis.slice(0, len - 2).join(':')
        };
    };

    /**
     * Get the button according to the given eltId
     *
     * @param {string} eltId - the element id corresponding to the button
     * @return {jQuery} the button
     * @memberof xmltool.utils
     * @method findAddButton
     */
    this.getAddButton = function(eltId) {
        // If it's a choice the button should be an option of a select
        var $btn = $('.btn-add').find('[value="'+ eltId+'"]');

        if ($btn.length === 1) {
            $btn = $btn.parent('select');
        }
        else {
            // the button should be a HTML a
            $btn = $('[data-elt-id="'+ eltId +'"]');
        }
        return $btn;
    };

}).call(xmltool.utils, jQuery);

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
                $(this.options.formContainerSelector),
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
        // treeContainerSelector: use to scroll on the node in the tree
        treeContainerSelector: '#tree',
        formContainerSelector: 'body',
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
