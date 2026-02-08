odoo.define('rp_search_one2many_v13.search_section_and_note_backend', function (require) {
    "use strict";

    var SectionAndNoteListRenderer = require('account.section_and_note_backend')

    SectionAndNoteListRenderer.include({
        events: _.extend({
            'keyup .oe_search_input': '_onKeyUp'
        }, SectionAndNoteListRenderer.prototype.events),

        /**
         * We want to add .o_section_and_note_list_view on the table to have stronger CSS.
         *
         * @override
         * @private
         */
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.$('.o_list_table').addClass('o_section_and_note_list_view');
                if (self.arch.tag == 'tree' && self.$el.hasClass('o_list_view')) {
                    var search = '<input type="text" class="oe_search_input mt-2 ml-5 pl-5" placeholder="Search...">';
                    var row_count = '<span class="oe_row_count">Total Row: '+ self.state.data.length+'</span>';
                    self.$el.find('table').addClass('oe_table_search');
                    var $search = $(search).css('border', '1px solid #ccc')
                    .css('width', '50%')
                    .css('border-radius', '10px')
                    // .css('margin-top', '-32px')
                    .css('height', '30px')
                    var $row_count = $(row_count).css('float', 'right')
                    .css('margin-right', '30rem')
                    .css('margin-top', '4px')
                    .css('color', '#666666');
                    self.$el.prepend($search);
                    self.$el.prepend($row_count);
                }
            });
        },

        /**
         * @private
         * @param {keyEvent} event
         */
        _onKeyUp: function (event) {
            var value = $(event.currentTarget).val().toLowerCase();
            var count_row = 0;
            var $el = $(this.$el)
            $(".oe_table_search tr:not(:first)").filter(function() {
                $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
                count_row = $(this).text().toLowerCase().indexOf(value) > -1 ? count_row+1 : count_row
            });
            $el.find('.oe_row_count').text('')
            $el.find('.oe_row_count').text('Total Row: ' + count_row)
        },
    });
});
