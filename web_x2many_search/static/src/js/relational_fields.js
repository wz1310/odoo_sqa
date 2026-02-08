odoo.define('web_x2many_search.FieldX2Many', function (require) {
    "use strict";

    const FieldX2Many = require('web.relational_fields').FieldX2Many;

    FieldX2Many.include({
        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            const arch = this.view && this.view.arch;
            if (arch) {
                this.search = arch.attrs.search ? !!JSON.parse(arch.attrs.search) : true;
            }
        },
    });

});
