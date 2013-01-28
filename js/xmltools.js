(function(exports) {

    exports.replace_id = function(container, new_id, container_id){
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
    }

    exports.has_field = function(container){
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
    }

    exports.update_conditional_container = function(obj){
        if (obj.parent().hasClass('conditional-option')){
            var conditional_container = obj.parent().parent();
            if (! exports.has_field(conditional_container)){
                conditional_container.children(':first').removeClass('hidden');
                conditional_container.find('.conditional-option').addClass('deleted');
            }
        }
    }

    exports.confirm_delete = function(button){
        var question = 'Are you sure you want to delete this ' + button.text().replace('Delete ', '');
        return confirm(question);
    }

}(typeof exports === "undefined"? (this.xmltools={}): exports));


(function($){
    
    $.fn.xmltools = function(options){
    
        var settings = $.extend({
            'on_submit': function(){
                $(this).find('.deleted').remove();
                $(this).find('.growing-source').remove();
            }
        }, options);

        return this.each(function(){
            $(this).on('click', '.delete-button', function(){
                var container = $(this).parent();
                container.addClass('deleted');
                container.parent('.container').addClass('inline');
                container.prev().removeClass('hidden');
                xmltools.update_conditional_container(container);
            });
            $(this).on('click', '.growing-delete-button', function(){
                if(xmltools.confirm_delete($(this))){
                    var container = $(this).parent();
                    container.addClass('deleted');
                    xmltools.update_conditional_container(container);
                }
            });
            $(this).on('click', '.fieldset-delete-button', function(){
                if(xmltools.confirm_delete($(this))){
                    var container = $(this).parent('legend').parent('fieldset');
                    container.addClass('deleted');
                    container.parent('.container').addClass('inline');
                    container.prev().removeClass('hidden');
                    xmltools.update_conditional_container(container);
                }
            });
            $(this).on('click', '.growing-fieldset-delete-button', function(){
                if(xmltools.confirm_delete($(this))){
                    var container = $(this).parent('legend').parent('fieldset').parent('.container');
                    container.addClass('deleted');
                    xmltools.update_conditional_container(container);
                }
            });
            $(this).on('click', '.add-button', function(){
                $(this).next().removeClass('deleted');
                $(this).addClass('hidden');
                $(this).parent('.container').removeClass('inline');
            });
        $(this).on('click', '.growing-add-button', function(){
            var id = parseInt($(this).prev().attr('id').replace(/.*:(\d*)$/, '$1'));
            var new_id = id + 1;
            var container = $(this).parent('.container');
            var source = container.parent('.growing-container').children('.growing-source').clone();
            source.removeClass('deleted').removeClass('growing-source');
            xmltools.replace_id(source, new_id);
            container.after(source);
            var container_id = source.attr('id');
            source.removeAttr('id');
            source.nextAll('.container').each(function(){
                new_id += 1;
                xmltools.replace_id($(this), new_id, container_id);
            });
        });

        $(this).on('change', 'select.conditional', function(){
                if ($(this).val()){
                    var cls = $(this).val().replace(/:/g, '\\:');
                    var container = $(this).parent().find('.' + cls);
                    container.removeClass('deleted');
                    var growing_source = container.children('.growing-source');
                    if (growing_source.length){
                        growing_source.children('.growing-add-button').trigger('click');
                    }
                    else{
                        container.children('.add-button').trigger('click');
                    }
                    $(this).addClass('hidden');
                }
            });

            $('body').on('submit', $(this), settings.on_submit);
        });
    };
})(jQuery);
