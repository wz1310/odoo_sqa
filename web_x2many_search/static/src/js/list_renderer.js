odoo.define('web_x2many_search.ListRenderer', function (require) {
    "use strict";

    const ListRenderer = require('web.ListRenderer');
    const _t = require('web.core')._t;

    ListRenderer.include({
        events: _.extend({}, ListRenderer.prototype.events, {
            'keyup .input_search': '_onSearchKeyup',
        }),

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.search = parent.search;
        },

        _renderSearch: function () {
            return $(`
                <div class="search_wrapper input-group">
                    <div class="input-group-prepend">
                        <i class="fa fa-search input-group-text"/>
                    </div>
                    <input type="text" class="input_search form-control" placeholder="${_t('Search...')}"/>
                    <div class="input-group-append">
                        <p class="input-group-text">
                            ${_t('Total Row')}: 
                            <span class="row_count text-right" style="min-width: 48px;">
                                ${this.state.count}
                            </span>
                        </p>
                    </div>
                </div>
            `);
        },

        _renderView: function () {
            const self = this;
            return this._super.apply(this, arguments).then(() => {
                if (self.search) {
                    self.$el.prepend(self._renderSearch());
                }
            });
        },

        _onSearchKeyup: function (e) {
            const value = e.currentTarget.value.toLowerCase();
            let row_count = 0;
            this.$('.o_data_row:not(.o_is_line_section,.o_is_line_note)').filter((index, row) => {
                const $row = $(row);
                const show = row.textContent.toLowerCase().includes(value);
                $row.toggle(show);
                show && row_count++;
            });
            this.$('.row_count').text(row_count);
        },
    })
});
