/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class InventoryReportClient extends Component {
    static template = "inventory_location_report.InventoryReportClient";

    setup() {
        this.state = useState({ loading: true });
        const action = this.props.action || {};
        const context = action.context || {};
        const month = context.month || "";
        const year = context.year || "";
        const location_ids = context.location_ids ? context.location_ids.join(',') : "";

        this.url = `/inventory_location/report_html?month=${month}&year=${year}&location_ids=${location_ids}`;
    }

    onIframeLoad() {
        this.state.loading = false;
    }
}

registry.category("actions").add(
    "inventory_location_report.client_action",
    InventoryReportClient
);