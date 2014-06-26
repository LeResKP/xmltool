if (typeof xmltool === 'undefined') {
    /*jshint -W020 */
    xmltool = {};
}


(function($, ns){
    var re_split = new RegExp('^(.*):([^:]+)$');

    // To make the selector by attributes works on 'data' we need to use the attr
    // property insteaf of data.
    var ATTRNAMES = ['name', 'id', 'class', 'value', 'href',
                     'data-id', 'data-comment-name', 'data-target', 'data-elt-id'];

    ns.utils = {
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
        increment_id: function(prefix, elts, index, step, offset, force_index){
            step = step || 1;
            offset = offset || 0;
            for (var i=0; i< elts.length; i++){
                var elt = $(elts[i]);
                var tmp_index;
                if (typeof force_index !== 'undefined') {
                    tmp_index = force_index;
                }
                else {
                    tmp_index = index + 1;
                }

                ns.utils._replace_id(prefix, elt, ns.utils._attr, ATTRNAMES, tmp_index);
                ns.utils.increment_id(prefix, elt.children(), 0, 1, offset, tmp_index);

                if (step === 1){
                    index += 1;
                }
                // offet==0 : we have div + btn + div ...
                //            We always want btn + div have the same index but
                //            the first div is alone
                // offet==1 : we have btn + div + btn + div ...
                else if(((i+offset) % step) === 0){
                    index += 1;
                }
            }
        },
        decrement_id: function(prefix, elts, index, step, offset){
            return ns.utils.increment_id(prefix, elts, index-1, step, offset);
        },
        _replace_id: function(prefix, elt, func, names, index){
            var re_id = new RegExp('^#?(collapse-)?'+prefix+':(\\d+)');
            for (var key in names){
                var name = names[key];
                var value = func(elt, name);
                if(value){
                    var values = value.split(' ');
                    var output = [];
                    for(var i=0; i<values.length; i++){
                        var v = values[i];
                        var old_index = parseInt(v.replace(re_id, '$2'), 10);
                        var re_str = prefix+':'+old_index;
                        var escaped = false;
                        var re_id_escaped;
                        if (isNaN(old_index)) {
                            // Perhaps the ':' are escaped
                            var s = '^#?(collapse-)?'+prefix+':(\\d+)';
                            s = s.replace(/:/g, '\\\\:');
                            re_id_escaped = new RegExp(s);
                            old_index = parseInt(v.replace(re_id_escaped, '$2'), 10);
                            re_str = (prefix+':'+old_index).replace(/:/g, '\\\\:');
                            escaped = true;
                        }
                        if (isNaN(old_index)) {
                            // Nothing to do, we keep the value
                            output.push(v);
                            continue;
                        }
                        var re = new RegExp('^(#?(collapse-)?)'+re_str);
                        var out = '$1' + prefix + ':' + index;
                        if (escaped) {
                            out = out.replace(/:/g, '\\:');
                        }
                        var new_value = v.replace(re, out);
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
                ns.utils._replace_id(prefix, elt, ns.utils._attr, ATTRNAMES, tmp_index);
                ns.utils.replace_id(prefix, elt.children(), 1, tmp_index);

                if (step === 1){
                    index += 1;
                }
                // In some cases we have btn + div + btn + div ...
                // We want btn + div have the same index
                else if(((i+1) % step) === 0 && i !== 0){
                    index += 1;
                }
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
            var cls = obj.attr('class');
            if (typeof cls === 'undefined') {
                return null;
            }
            return cls.split(' ')[0];
        },
        update_contenteditable_eol: function(s) {
            // We want \n as new line when the text comes from contenteditale
            s = s.replace(/\r?\n?/g, '');
            s = s.replace(/<br ?\/?>/g, '\n');
            return s;
        }
    };

})(window.jQuery, xmltool);
