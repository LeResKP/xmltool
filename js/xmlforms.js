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
                if (! $(this).hasClass('growing-source') && ! $(this).hasClass('deleted') && !$(this).is(':input')){
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


    $(document).ready(function(){
        $('.delete-button').live('click', function(){
            var container = $(this).parent();
            container.addClass('deleted');
            container.prev().removeClass('hidden');
            exports.update_conditional_container(container);
        });
        $('.growing-delete-button').live('click', function(){
            var container = $(this).parent();
            container.addClass('deleted');
            exports.update_conditional_container(container);
        });
        $('.fieldset-delete-button').live('click', function(){
            var container = $(this).parent('legend').parent('fieldset');
            container.addClass('deleted');
            container.prev().removeClass('hidden');
            exports.update_conditional_container(container);
        });
        $('.growing-fieldset-delete-button').live('click', function(){
            var container = $(this).parent('legend').parent('fieldset').parent('.container');
            container.addClass('deleted');
            exports.update_conditional_container(container);
        });
        $('.add-button').live('click', function(){
            $(this).next().removeClass('deleted');
            $(this).addClass('hidden'); // hide();
        });
        $('.growing-add-button').live('click', function(){
            var id = parseInt($(this).prev().attr('id').replace(/.*:(\d*)$/, '$1'));
            var new_id = id + 1;
            var container = $(this).parent('.container');
            var source = container.parent('.growing-container').children('.growing-source').clone();
            source.removeClass('deleted').removeClass('growing-source');
            exports.replace_id(source, new_id);
            container.after(source);
            var container_id = source.attr('id');
            source.removeAttr('id');
            source.nextAll('.container').each(function(){
                new_id += 1;
                exports.replace_id($(this), new_id, container_id);
            });
        });

        $('select.conditional').live('change', function(){
            if ($(this).val()){
                var cls = $(this).val().replace(/:/g, '\\:');
                var container = $(this).nextAll('.' + cls);
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

        $('form').live('submit', function(){
            $(this).find('.deleted').remove();
            $(this).find('.growing-source').remove();
        });
    });

}(typeof exports === "undefined"
        ? (this.xmlforms = {})
        : exports));

