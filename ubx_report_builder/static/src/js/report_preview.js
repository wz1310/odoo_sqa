/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class ReportPreview extends Component {
    static template = "ubx_report_builder.ReportPreview";
    static props = {
        reportId: Number,
    };
    
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        
        this.state = useState({
            data: [],
            loading: false,
            totalRecords: 0,
            previewCount: 0,
            fields: [],
            sortField: null,
            sortOrder: 'asc',
        });
        
        onWillStart(async () => {
            await this.loadPreviewData();
        });
    }
    
    async loadPreviewData() {
        this.state.loading = true;
        try {
            const result = await this.rpc("/ubx_report_builder/preview_data", { 
                report_id: this.props.reportId,
                limit: 20
            });
            if (result.success) {
                this.state.data = result.data;
                this.state.totalRecords = result.total_records;
                this.state.previewCount = result.preview_count;
                
                // Extract field names from first record
                if (result.data.length > 0) {
                    this.state.fields = Object.keys(result.data[0]);
                }
            } else {
                this.notification.add(result.error, { type: 'danger' });
            }
        } catch (error) {
            this.notification.add(_t("Failed to load preview data"), { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    sortBy(field) {
        if (this.state.sortField === field) {
            this.state.sortOrder = this.state.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.sortField = field;
            this.state.sortOrder = 'asc';
        }
        
        this.state.data.sort((a, b) => {
            const aVal = a[field]?.value || '';
            const bVal = b[field]?.value || '';
            
            if (this.state.sortOrder === 'asc') {
                return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
            } else {
                return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
            }
        });
    }
    
    getSortIcon(field) {
        if (this.state.sortField !== field) {
            return 'fa-sort';
        }
        return this.state.sortOrder === 'asc' ? 'fa-sort-asc' : 'fa-sort-desc';
    }
    
    formatValue(cellData) {
        if (!cellData) return '';
        return cellData.formatted || cellData.value || '';
    }
    
    getFieldLabel(fieldName) {
        // Convert snake_case to Title Case
        return fieldName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
}

registry.category("components").add("ReportPreview", ReportPreview);

// Register as a client action for popup preview
export class ReportPreviewWidget extends Component {
    static template = "ubx_report_builder.ReportPreviewWidget";
    static props = {
        action: { type: Object, optional: true },
        "*": true,
    };
    
    setup() {
        try {
            this.rpc = useService("rpc");
            this.notification = useService("notification");
            this.actionService = useService("action");
        } catch (error) {
            console.warn("Services not available, using fallback");
            this.rpc = this.makeRpcCall.bind(this);
            this.notification = {
                add: (message, options = {}) => {
                    console.log(`Notification: ${message}`, options);
                }
            };
            this.actionService = {
                doAction: (action) => {
                    if (action.type === 'ir.actions.act_window_close') {
                        window.history.back();
                    }
                }
            };
        }
        
        this.reportId = this.props.action?.context?.report_id;
        
        this.state = useState({
            data: [],
            fields: [],
            loading: false,
        });
        
        onWillStart(async () => {
            if (this.reportId) {
                await this.loadPreviewData();
            }
        });
    }
    
    async makeRpcCall(url, params = {}) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: params,
                    id: Math.floor(Math.random() * 1000000),
                }),
            });
            
            const data = await response.json();
            return data.result || data;
        } catch (error) {
            console.error('RPC call failed:', error);
            throw error;
        }
    }
    
    async loadPreviewData() {
        this.state.loading = true;
        try {
            const result = await this.rpc("/ubx_report_builder/preview_data", { 
                report_id: this.reportId,
                limit: 20
            });
            if (result.success) {
                this.state.data = result.data;
                this.state.fields = result.fields || [];
            } else {
                this.notification.add(result.error, { type: 'danger' });
            }
        } catch (error) {
            this.notification.add(_t("Failed to load preview data"), { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    closePreview() {
        this.actionService.doAction({
            type: 'ir.actions.act_window_close'
        });
    }
}

registry.category("actions").add("report_preview_widget", ReportPreviewWidget);
