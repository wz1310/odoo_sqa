/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MonthlySalesClient extends Component {
    static template = "sunray_monthly_sales_report.MonthlySalesClient";

    setup() {
        this.state = useState({ loading: true });
        const action = this.props.action || {};
        const context = action.context || this.props.context || {};

        // Extract params from context
        const month = context.month || "";
        const year = context.year || "";
        const user_ids = context.user_ids ? context.user_ids.join(',') : "";

        this.url = `/sunray_monthly_sales/report_html?month=${month}&year=${year}&user_ids=${user_ids}`;
    }

    onIframeLoad() {
        this.state.loading = false;
    }
}

registry.category("actions").add(
    "sunray_monthly_sales_report.client_action",
    MonthlySalesClient
);
