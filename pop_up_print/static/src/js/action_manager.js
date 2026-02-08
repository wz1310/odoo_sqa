odoo.define('pop_up_print.ActionManager', function (require) {
    "use strict";
    var ActionManager = require('web.ActionManager')


    ActionManager.include({
        doAction: function(action, options){
            if(options['report_url']){
                window.open(options['report_url'],'_blank')
            }
            return this._super.apply(this, arguments);

        }
    })

})