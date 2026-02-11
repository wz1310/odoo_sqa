/** @odoo-module **/
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { markup } from "@odoo/owl"; 
const { Component, onWillStart, useState } = owl;

export class SalesReportClientAction extends Component {
    setup() {
        this.state = useState({
            html_content: "",
            loading: true,
            groupby: "customer",
        });

        onWillStart(async () => {
            await this.fetchReportHtml();
        });
    }

    async fetchReportHtml() {
        this.state.loading = true;
        try {
            const context = this.props.action.context || {};
            const data = await rpc("/sales_report/report_html", {
                month: context.month || "",
                year: context.year || "",
                groupby: this.state.groupby,
            });
            this.state.html_content = markup(data);
        } catch (error) {
            this.state.html_content = markup("<div class='alert alert-danger'>Gagal memuat data.</div>");
        } finally {
            this.state.loading = false;
        }
    }

    handleMainClick(ev) {
        // 1. Logika Ganti Grouping
        const groupBtn = ev.target.closest('.js_change_groupby');
        if (groupBtn) {
            this.state.groupby = groupBtn.getAttribute('data-groupby');
            this.fetchReportHtml();
            return;
        }

        // 2. Logika Fold / Unfold All
        const foldBtn = ev.target.closest('.js_fold_all');
        if (foldBtn) {
            const action = foldBtn.getAttribute('data-action');
            const display = action === 'unfold' ? 'table-row' : 'none';
            
            document.querySelectorAll('.row-detail').forEach(el => el.style.display = display);
            document.querySelectorAll('.row-customer-group').forEach(el => {
                if (action === 'unfold') el.classList.add('is-expanded');
                else el.classList.remove('is-expanded');
            });
            return;
        }

        // 3. Logika Expand Individual
        const headerRow = ev.target.closest('.row-customer-group');
        if (headerRow) {
            const id = headerRow.getAttribute('data-id');
            const detailRows = document.querySelectorAll(`.detail-${id}`);
            const isClosing = headerRow.classList.contains('is-expanded');
            
            detailRows.forEach(row => row.style.display = isClosing ? 'none' : 'table-row');
            headerRow.classList.toggle('is-expanded');
        }
    }
}

SalesReportClientAction.template = "sale_sales_report.sales_report_client_template";
registry.category("actions").add("sale_sales_report.sales_client_action", SalesReportClientAction);