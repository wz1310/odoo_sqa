/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class ReportDisplayWidget extends Component {
    static template = "ubx_report_builder.ReportDisplayWidget";
    static props = {
        action: { type: Object, optional: true },
        context: { type: Object, optional: true },
        "*": true,
    };
    
    setup() {
        // Always use fallback RPC methods for reliability
        this.rpc = this.makeRpcCall.bind(this);
        this.notification = {
            add: (message, options = {}) => {
                console.log(`Notification: ${message}`, options);
                if (options.type === 'danger') {
                    console.error(`Error: ${message}`);
                    // Show user-friendly error message
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'alert alert-danger mt-3';
                    errorDiv.innerHTML = `<strong>Error:</strong> ${message}`;
                    const container = document.querySelector('.o_report_display_widget') || document.body;
                    container.insertBefore(errorDiv, container.firstChild);
                    setTimeout(() => errorDiv.remove(), 5000);
                } else {
                    // Show success message
                    const successDiv = document.createElement('div');
                    successDiv.className = 'alert alert-success mt-3';
                    successDiv.innerHTML = message;
                    const container = document.querySelector('.o_report_display_widget') || document.body;
                    container.insertBefore(successDiv, container.firstChild);
                    setTimeout(() => successDiv.remove(), 3000);
                }
            }
        };
        this.actionService = {
            doAction: (action) => {
                console.log("Action:", action);
                if (action.type === 'ir.actions.act_window') {
                    let url = '/web#';
                    if (action.res_model === 'report.builder') {
                        url += 'action=ubx_report_builder.action_report_builder';
                        if (action.res_id) {
                            url += `&id=${action.res_id}&view_type=form`;
                        }
                    }
                    window.location.href = url;
                }
            }
        };
        
        // Get report ID from various sources
        this.reportId = this.getReportId();
        
        this.state = useState({
            reportConfig: {},
            reportFields: [],
            filterableFields: [],
            reportData: [],
            filteredData: [],
            loading: false,
            
            // Filter states
            filters: {},
            groupBy: '',
            showZeroValues: true,
            
            // Pagination
            currentPage: 1,
            pageSize: 10,
            totalRecords: 0,
            
            // Data processing
            groupedData: {},
            availableGroupByFields: [],
        });
        
        onWillStart(async () => {
            if (this.reportId) {
                await this.loadReportConfig();
                await this.loadReportData();
            }
        });
    }
    
    getReportId() {
        // Try to get report ID from various sources
        if (this.props.action?.context?.report_id) {
            return this.props.action.context.report_id;
        }
        if (this.props.action?.context?.active_id) {
            return this.props.action.context.active_id;
        }
        if (this.props.context?.report_id) {
            return this.props.context.report_id;
        }
        if (this.props.context?.active_id) {
            return this.props.context.active_id;
        }
        // Try to get from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('report_id')) {
            return parseInt(urlParams.get('report_id'));
        }
        if (urlParams.get('id')) {
            return parseInt(urlParams.get('id'));
        }
        return null;
    }
    
    async makeRpcCall(route, data = {}) {
        try {
            console.log('Making RPC call to:', route, 'with data:', data);
            
            // Get CSRF token from meta tag
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            
            const headers = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            };
            
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            const response = await fetch(route, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: data,
                    id: Math.floor(Math.random() * 1000000),
                }),
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('RPC response:', result);
            
            if (result.error) {
                console.error('RPC error:', result.error);
                throw new Error(result.error.data?.message || result.error.message || 'RPC call failed');
            }
            
            return result.result;
        } catch (error) {
            console.error('RPC call failed:', error);
            throw error;
        }
    }
    
    async loadReportConfig() {
        if (!this.reportId) {
            console.error('No report ID available for config');
            this.notification.add("No report ID provided", { type: 'danger' });
            return;
        }
        
        this.state.loading = true;
        try {
            console.log('Loading report config for report ID:', this.reportId);
            
            const result = await this.rpc("/ubx_report_builder/load_report", { report_id: this.reportId });
            
            console.log('Report config result:', result);
            
            if (result && result.success) {
                this.state.reportConfig = result.report || {};
                this.state.reportFields = result.report?.fields || [];
                
                console.log('Loaded report fields:', this.state.reportFields);
                
                // Filter fields available for filtering - only selection and date types
                this.state.filterableFields = this.state.reportFields.filter(field => 
                    ['selection', 'date', 'datetime'].includes(field.field_type)
                );
                
                // Initialize filters for filterable fields
                this.state.filterableFields.forEach(field => {
                    const filterKey = field.field_path || field.field_name;
                    if (['date', 'datetime'].includes(field.field_type)) {
                        // Date fields have from/to filters
                        this.state.filters[filterKey + '_from'] = '';
                        this.state.filters[filterKey + '_to'] = '';
                    } else {
                        this.state.filters[filterKey] = '';
                    }
                });
                
                // Set available group by fields (only certain field types)
                this.state.availableGroupByFields = this.state.reportFields.filter(field => 
                    ['char', 'selection', 'many2one', 'date', 'datetime', 'boolean'].includes(field.field_type)
                ).map(field => ({
                    ...field,
                    key: field.field_path || field.field_name
                }));
                
                console.log('Available group by fields:', this.state.availableGroupByFields);
            } else {
                const errorMsg = result?.error || "Failed to load report configuration";
                console.error('Report config error:', errorMsg);
                this.notification.add(errorMsg, { type: 'danger' });
            }
        } catch (error) {
            console.error('Error loading report config:', error);
            this.notification.add(`Failed to load report configuration: ${error.message}`, { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    async loadReportData() {
        if (!this.reportId) {
            console.error('No report ID available');
            this.notification.add("No report ID provided", { type: 'danger' });
            return;
        }
        
        this.state.loading = true;
        try {
            
            const result = await this.rpc("/ubx_report_builder/preview_data", { 
                report_id: this.reportId,
                max_records: 10000 // Load all data
            });
            
            console.log('Report data result:', result);
            
            if (result && result.success) {
                this.state.reportData = result.data || [];
                this.state.totalRecords = result.total_records || result.data?.length || 0;
                console.log('Loaded', this.state.reportData.length, 'records');
                this.applyFilters();
            } else {
                const errorMsg = result?.error || "Failed to load report data";
                console.error('Report data error:', errorMsg);
                this.notification.add(errorMsg, { type: 'danger' });
            }
        } catch (error) {
            console.error('Error loading report data:', error);
            this.notification.add(`Failed to load report data: ${error.message}`, { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    getActiveFilters() {
        const activeFilters = {};
        Object.keys(this.state.filters).forEach(fieldName => {
            const filterValue = this.state.filters[fieldName];
            if (filterValue && filterValue.trim()) {
                activeFilters[fieldName] = filterValue.trim();
            }
        });
        return activeFilters;
    }
    
    applyFilters() {
        let filteredData = [...this.state.reportData];
        
        // Apply field filters only for filterable fields
        if (this.state.filterableFields) {
            this.state.filterableFields.forEach(field => {
                const fieldName = field.field_path || field.field_name;
                
                if (['date', 'datetime'].includes(field.field_type)) {
                    // Handle date range filters - both from and to must be provided
                    const fromValue = this.state.filters[fieldName + '_from'];
                    const toValue = this.state.filters[fieldName + '_to'];
                    
                    // Only apply filter if both from and to dates are provided
                    if (fromValue && toValue) {
                        filteredData = filteredData.filter(record => {
                            const fieldData = record[fieldName];
                            if (!fieldData) return false;
                            
                            // Get the original value (not the formatted display value)
                            let rawDateValue = '';
                            if (fieldData && typeof fieldData === 'object') {
                                rawDateValue = fieldData.value || fieldData.formatted || '';
                            } else {
                                rawDateValue = String(fieldData);
                            }
                            
                            if (!rawDateValue) return false;
                            
                            // Extract date part in yyyy-mm-dd format (remove time if present)
                            let recordDate = rawDateValue.split(' ')[0];
                            
                            // If date is in dd/mm/yyyy format, convert to yyyy-mm-dd
                            if (recordDate.includes('/')) {
                                const parts = recordDate.split('/');
                                if (parts.length === 3) {
                                    recordDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
                                }
                            }
                            
                            // Compare dates in yyyy-mm-dd format
                            return recordDate >= fromValue && recordDate <= toValue;
                        });
                    }
                } else {
                    // Handle selection filters
                    const filterValue = this.state.filters[fieldName];
                    if (filterValue && filterValue.trim()) {
                        filteredData = filteredData.filter(record => {
                            const value = this.getRecordValue(record, field);
                            return value.toLowerCase().includes(filterValue.toLowerCase());
                        });
                    }
                }
            });
        }
        
        // Filter zero values if needed
        if (!this.state.showZeroValues) {
            filteredData = filteredData.filter(record => {
                return this.state.reportFields.some(field => {
                    if (['integer', 'float', 'monetary'].includes(field.field_type)) {
                        const value = this.getRecordValue(record, field);
                        return parseFloat(value) !== 0;
                    }
                    return true;
                });
            });
        }
        
        this.state.filteredData = filteredData;
        
        // Apply grouping if needed
        if (this.state.groupBy) {
            this.applyGrouping();
        }
    }
    
    applyGrouping() {
        const grouped = {};
        this.state.filteredData.forEach(record => {
            const groupField = this.state.reportFields.find(f => (f.field_path || f.field_name) === this.state.groupBy);
            const groupValue = this.getRecordValue(record, groupField || { field_name: this.state.groupBy, name: this.state.groupBy }) || 'Undefined';
            if (!grouped[groupValue]) {
                grouped[groupValue] = [];
            }
            grouped[groupValue].push(record);
        });
        this.state.groupedData = grouped;
    }
    
    getRecordValue(record, field) {
        if (!record || !field) return '';
        
        // Try to get the field value using various possible keys
        const possibleKeys = [
            field.field_path,     // For related fields like 'partner_id.name'
            field.field_name,     // For regular fields
            field.name           // Fallback
        ].filter(Boolean);
        
        for (const key of possibleKeys) {
            if (record.hasOwnProperty(key)) {
                const value = record[key];
                
                // Handle structured field data from backend
                if (value && typeof value === 'object' && (value.formatted || value.value !== undefined)) {
                    let formatted = value.formatted || String(value.value || '');
                    
                    // Format dates to dd/mm/yyyy
                    if ((value.type === 'date' || value.type === 'datetime') && formatted) {
                        const datePart = formatted.split(' ')[0]; // Remove time if present
                        const parts = datePart.split('-');
                        if (parts.length === 3) {
                            formatted = `${parts[2]}/${parts[1]}/${parts[0]}`;
                        }
                    }
                    
                    // Format monetary fields with commas and 2 decimals
                    if ((value.type === 'monetary' || value.type === 'float' || field.field_type === 'monetary' || field.field_type === 'float') && value.value !== undefined && value.value !== null && value.value !== '') {
                        const numValue = parseFloat(value.value);
                        if (!isNaN(numValue)) {
                            formatted = numValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                        }
                    }
                    
                    return formatted;
                }
                
                // Handle simple values
                if (value !== null && value !== undefined) {
                    return String(value);
                }
            }
        }
        
        return '';
    }
    
    getFormattedValue(record, field) {
        if (!record || !field) return '';
        const possibleKeys = [field.field_path, field.field_name, field.name].filter(Boolean);
        for (const key of possibleKeys) {
            if (record.hasOwnProperty(key)) {
                const value = record[key];
                if (value && typeof value === 'object' && value.formatted !== undefined) {
                    let formatted = value.formatted;
                    
                    // Format dates to dd/mm/yyyy (remove time)
                    if (value.type === 'date' || value.type === 'datetime') {
                        // If it's a datetime string like "2025-10-21 15:21:21" or date "2025-10-21"
                        if (typeof formatted === 'string') {
                            // Extract date part (remove time if present)
                            const datePart = formatted.split(' ')[0];
                            
                            // Convert from yyyy-mm-dd to dd/mm/yyyy
                            const parts = datePart.split('-');
                            if (parts.length === 3) {
                                formatted = `${parts[2]}/${parts[1]}/${parts[0]}`;
                            }
                        }
                    }
                    
                    // Format monetary fields with commas and 2 decimals
                    if ((value.type === 'monetary' || value.type === 'float' || field.field_type === 'monetary' || field.field_type === 'float') && value.value !== undefined && value.value !== null && value.value !== '') {
                        const numValue = parseFloat(value.value);
                        if (!isNaN(numValue)) {
                            formatted = numValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                        }
                    }
                    
                    return formatted;
                }
            }
        }
        return '';
    }
    
    onFilterChange(fieldName, event) {
        this.state.filters[fieldName] = event.target.value;
        this.applyFilters();
    }
    
    onDateRangeChange(fieldName, rangeType, event) {
        const value = event.target.value;
        const filterKey = fieldName + '_' + rangeType;
        this.state.filters[filterKey] = value;
        this.applyFilters();
    }
    
    onGroupByChange(event) {
        this.state.groupBy = event.target.value;
        this.applyFilters();
    }
    
    onShowZeroValuesChange(event) {
        this.state.showZeroValues = event.target.checked;
        this.applyFilters();
    }
    
    refreshData() {
        this.loadReportData();
    }
    
    openReportSettings() {
        this.actionService.doAction({
            name: _t('Report Settings'),
            type: 'ir.actions.act_window',
            res_model: 'report.builder',
            res_id: this.reportId,
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
        });
    }
    
    async exportToExcel() {
        if (this.reportId) {
            // Build URL with current filters
            let url = `/ubx_report_builder/export_excel?report_id=${this.reportId}`;
            
            // Add selection field filters and date range filters
            if (this.state.filterableFields) {
                this.state.filterableFields.forEach(field => {
                    const fieldName = field.field_path || field.field_name;
                    
                    if (['date', 'datetime'].includes(field.field_type)) {
                        // Add date range filters
                        const fromValue = this.state.filters[fieldName + '_from'];
                        const toValue = this.state.filters[fieldName + '_to'];
                        
                        if (fromValue && toValue) {
                            url += `&date_filter_${encodeURIComponent(fieldName)}_from=${encodeURIComponent(fromValue)}`;
                            url += `&date_filter_${encodeURIComponent(fieldName)}_to=${encodeURIComponent(toValue)}`;
                        }
                    } else {
                        // Add selection field filter
                        const filterValue = this.state.filters[fieldName];
                        if (filterValue && filterValue.trim()) {
                            url += `&filter_${encodeURIComponent(fieldName)}=${encodeURIComponent(filterValue)}`;
                        }
                    }
                });
            }
            
            // Add groupby if applied
            if (this.state.groupBy) {
                url += `&group_by=${encodeURIComponent(this.state.groupBy)}`;
            }
            
            window.open(url, '_blank');
        }
    }
    
    async exportToPDF() {
        if (this.reportId) {
            // Build URL with current filters
            let url = `/ubx_report_builder/export_pdf?report_id=${this.reportId}`;
            
            // Add selection field filters
            if (this.state.filterableFields) {
                this.state.filterableFields.forEach(field => {
                    const fieldName = field.field_path || field.field_name;
                    
                    if (['date', 'datetime'].includes(field.field_type)) {
                        // Add date range filters
                        const fromValue = this.state.filters[fieldName + '_from'];
                        const toValue = this.state.filters[fieldName + '_to'];
                        
                        if (fromValue && toValue) {
                            url += `&date_filter_${encodeURIComponent(fieldName)}_from=${encodeURIComponent(fromValue)}`;
                            url += `&date_filter_${encodeURIComponent(fieldName)}_to=${encodeURIComponent(toValue)}`;
                        }
                    } else {
                        // Add selection field filter
                        const filterValue = this.state.filters[fieldName];
                        if (filterValue && filterValue.trim()) {
                            url += `&filter_${encodeURIComponent(fieldName)}=${encodeURIComponent(filterValue)}`;
                        }
                    }
                });
            }
            
            // Add groupby if applied
            if (this.state.groupBy) {
                url += `&group_by=${encodeURIComponent(this.state.groupBy)}`;
            }
            
            window.open(url, '_blank');
        }
    }
    
    goBack() {
        this.actionService.doAction({
            name: _t('Reports'),
            type: 'ir.actions.act_window',
            res_model: 'report.builder',
            view_mode: 'kanban,list,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            target: 'current',
        });
    }
    
    getPaginatedData() {
        const data = this.state.groupBy ? Object.values(this.state.groupedData).flat() : this.state.filteredData;
        const start = (this.state.currentPage - 1) * this.state.pageSize;
        const end = start + this.state.pageSize;
        return data.slice(start, end);
    }
    
    getTotalPages() {
        const totalData = this.state.groupBy ? Object.values(this.state.groupedData).flat().length : this.state.filteredData.length;
        return Math.ceil(totalData / this.state.pageSize);
    }
    
    previousPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
        }
    }
    
    nextPage() {
        if (this.state.currentPage < this.getTotalPages()) {
            this.state.currentPage++;
        }
    }
    
    // Calculate summation totals for fields with show_summation enabled
    calculateSummations() {
        const summations = {};
        const dataToSum = this.state.filteredData;
        
        this.state.reportFields.forEach(field => {
            if (field.show_summation && ['integer', 'float', 'monetary'].includes(field.field_type)) {
                const fieldName = field.field_path || field.field_name;
                let total = 0;
                
                dataToSum.forEach(record => {
                    const fieldData = record[fieldName];
                    let value = 0;
                    
                    if (fieldData && typeof fieldData === 'object') {
                        value = parseFloat(fieldData.value) || 0;
                    } else {
                        value = parseFloat(fieldData) || 0;
                    }
                    
                    total += value;
                });
                
                // Format the total based on field type
                if (field.field_type === 'monetary' || field.field_type === 'float') {
                    summations[fieldName] = total.toLocaleString('en-US', { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: 2 
                    });
                } else {
                    summations[fieldName] = total.toLocaleString('en-US');
                }
            }
        });
        
        return summations;
    }
    
    // Check if any field has summation enabled
    hasSummation() {
        return this.state.reportFields.some(field => field.show_summation);
    }
}

// Simple client action registration that properly handles the component
class ReportDisplayClientAction {
    setup(env, props) {
        this.component = ReportDisplayWidget;
        this.props = props;
        this.env = env;
    }
    
    getComponent() {
        return this.component;
    }
}

// Register the client action
registry.category("actions").add("report_display_widget", ReportDisplayWidget);
