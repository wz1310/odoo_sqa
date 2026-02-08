/*
    OpenERP, Open Source Management Solution
    This module copyright (C) 2015 Savoir-faire Linux
    (<http://www.savoirfairelinux.com>).

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
/*global openerp, _, $ */
odoo.define('web_widget_datepicker_options.datepicker', function (require) {
    var datepicker = require('web.datepicker');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var time = require('web.time');
    var Widget = require('web.Widget');

    var _t = core._t;
    datepicker.DateWidget.include({
        init: function (parent, options) {
        this._super.apply(this, arguments);
        this.name = parent.name;
        var date_now = new Date()
        this.options = _.extend({
            locale: moment.locale(),
            format : this.type_of_date === 'datetime' ? time.getLangDatetimeFormat() : time.getLangDateFormat(),
            minDate: moment({ y: date_now.getFullYear(), M: date_now.getMonth(), d: date_now.getDate() }),
            // minDate : moment({ y: 1990}),
            maxDate: moment({ y: 9999, M: 11, d: 31 }),
            useCurrent: false,
            icons: {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down',
                previous: 'fa fa-chevron-left',
                next: 'fa fa-chevron-right',
                today: 'fa fa-calendar-check-o',
                clear: 'fa fa-delete',
                close: 'fa fa-check primary',
            },
            calendarWeeks: true,
            buttons: {
                showToday: false,
                showClear: false,
                showClose: false,
            },
            widgetParent: 'body',
            keyBinds: null,
        }, options || {});
        

        this.__libInput = 0;
        // tempusdominus doesn't offer any elegant way to check whether the
        // datepicker is open or not, so we have to listen to hide/show events
        // and manually keep track of the 'open' state
        this.__isOpen = false;
        },

        // changeDatetime: function () {
        //     console.log('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        //     var date_now = new Date()
        //     console.log('aaaaaaaaaaaaaaaaaaa')
        //     if (this.options.abc) {
        //         console.log('aaaaaaaaaaaaaa', this.options, this.options.abc);
        //         this.options.minDate = moment({ y: date_now.getFullYear(), M: date_now.getMonth(), d: date_now.getDate() });
        //     }
        //     console.log('aaaaaaaaaaaaa', this.options, this.options.minDate)
        //     if (this.__libInput > 0) {
                
        //         if (this.options.warn_future) {
        //             this._warnFuture(this.getValue());
        //         }
        //         this.trigger("datetime_changed");
        //         return;
        //     }
        //     var oldValue = this.getValue();
        //     if (this.isValid()) {
        //         this._setValueFromUi();
        //         var newValue = this.getValue();
        //         var hasChanged = !oldValue !== !newValue;
        //         if (oldValue && newValue) {
        //             var formattedOldValue = oldValue.format(time.getLangDatetimeFormat());
        //             var formattedNewValue = newValue.format(time.getLangDatetimeFormat());
        //             if (formattedNewValue !== formattedOldValue) {
        //                 hasChanged = true;
        //             }
        //         }
        //         if (hasChanged) {
        //             if (this.options.warn_future) {
        //                 this._warnFuture(newValue);
        //             }
        //             this.trigger("datetime_changed");
        //         }
        //     } else {
        //         var formattedValue = oldValue ? this._formatClient(oldValue) : null;
        //         this.$input.val(formattedValue);
        //     }
        // },
    });
});
