/**
 *  @file xmltool.utils
 *
 *  Some useful functions need to manipulate the dom.
 *
 *  @author Aurélien Matouillot
 */

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
        // 'class',  'href', 'data-id'
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

}).call(xmltool.utils, jQuery);
