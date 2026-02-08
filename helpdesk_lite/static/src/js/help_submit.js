odoo.define('helpdesk_lite.new_ticket', function (require) {
'use strict';

var publicWidget = require('web.public.widget');

publicWidget.registry.HelpSubmit = publicWidget.Widget.extend({
    selector: '.s_website_form',
    events: {
        'click button[name="sending"]': '_onSubmit',
        'click button[name="cancel"]': '_onCancel'
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */_onSubmit: function () {
        if ($('input[name="name"]').val()!==''){
            // alert('jangannnnnnnnnnn');
            $('button[name="cancel"]').attr('disabled', 'disabled');
            $('input[name="Attachment"]').attr('disabled', 'disabled');
            $('textarea[name="description"]').attr('disabled', 'disabled');
            $('select[name="priority"]').attr('disabled', 'disabled');
            $('input[name="date_deadline"]').attr('disabled', 'disabled');
            $('select[name="sub_category_id"]').attr('disabled', 'disabled');
            $('input[name="name"]').attr('disabled', 'disabled');
            $('button[name="sending"]').attr('disabled', 'disabled');
            $('#status').show();
            $('#preloader').show();
            // $('button[name="sending"]').prepend('<i class="fa fa-refresh fa-spin"/> ');
            // $btn.prepend('<i class="fa fa-refresh fa-spin"/> ');
        }
        
    
    },
    _onCancel: function () {
        // $('button[name="cancel"]').attr('class', '');
        // $('input[name="name"]').val('');
        window.location.href = '/my/home';
    },
});
});
