/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class ReportBuilderWidget extends Component {
    static template = "ubx_report_builder.ReportBuilderWidget";
    static props = {
        action: { type: Object, optional: true },
        "*": true,
    };
    
    setup() {
        // Try to get services
        let servicesAvailable = true;
        
        try {
            // Try the standard OWL service approach first
            this.rpc = useService("rpc");
            this.notification = useService("notification");
            this.actionService = useService("action");
            console.log('Standard services successfully loaded');
        } catch (error) {
            console.warn("Standard services not available, trying alternative approaches", error);
            servicesAvailable = false;
            
            // Try to use global odoo object if available
            if (typeof window.odoo !== 'undefined' && window.odoo.define) {
                console.log('Trying to use global odoo services');
                try {
                    // This is a fallback - try to get services from the global registry
                    const serviceRegistry = registry.category("services");
                    if (serviceRegistry.contains("rpc")) {
                        console.log('Using registry services');
                        this.rpc = serviceRegistry.get("rpc");
                        this.notification = serviceRegistry.get("notification");
                        this.actionService = serviceRegistry.get("action");
                        servicesAvailable = true;
                    }
                } catch (registryError) {
                    console.warn('Registry approach failed:', registryError);
                }
            }
            
            // If still no services, use fallback methods
            if (!servicesAvailable) {
                console.log('Using fallback RPC implementation');
                this.rpc = this.makeRpcCall.bind(this);
                this.notification = {
                    add: (message, options = {}) => {
                        console.log(`Notification: ${message}`, options);
                        if (options.type === 'danger') {
                            console.error(`Error: ${message}`);
                        } else if (options.type === 'success') {
                            console.log(`Success: ${message}`);
                        }
                    }
                };
                this.actionService = {
                    doAction: (action) => {
                        console.log("Fallback Action Service - Action:", action);
                        if (action.type === 'ir.actions.act_window_close') {
                            if (window.history.length > 1) {
                                window.history.back();
                            } else {
                                window.location.href = '/web';
                            }
                        } else if (action.type === 'ir.actions.act_window') {
                            let url = '/web#';
                            if (action.res_model === 'report.builder') {
                                url += 'action=ubx_report_builder.action_report_builder';
                                if (action.view_mode) {
                                    const viewMode = action.view_mode.split(',')[0];
                                    url += `&view_type=${viewMode}`;
                                }
                            } else if (action.res_model) {
                                url += `model=${action.res_model}`;
                                if (action.view_mode) {
                                    const viewMode = action.view_mode.split(',')[0];
                                    url += `&view_type=${viewMode}`;
                                }
                            }
                            console.log('Navigating to:', url);
                            window.location.href = url;
                        }
                    }
                };
            }
        }
        
        this.state = useState({
            currentStep: 'model_selection', // model_selection, field_selection, configuration, preview
            selectedModel: null,
            availableModels: [],
            availableFields: [],
            selectedFields: [],
            reportConfig: {
                name: 'New Report',
                description: '',
                domain: [],
                max_records: 1000,
            },
            previewData: [],
            loading: false,
            draggedField: null,
            reportId: null,
            // Search and filter states
            modelSearch: '',
            fieldSearch: '',
            fieldTypeFilter: '',
            // Track unsaved changes
            hasUnsavedChanges: false,
            // Services availability
            servicesAvailable: servicesAvailable,
        });
        
        onWillStart(async () => {
            await this.loadModels();
            // Load existing report if report_id is provided in context
            const reportId = this.props.action?.context?.report_id;
            if (reportId) {
                await this.loadExistingReport(reportId);
            }
        });
        
        onMounted(() => {
            // Setup is complete, no drag and drop needed
            console.log('ReportBuilderWidget mounted, methods available:', {
                closeBuilder: typeof this.closeBuilder,
                saveReport: typeof this.saveReport
            });
        });
    }
    
    // Computed properties for filtered data
    get filteredModels() {
        if (!this.state.modelSearch) {
            return this.state.availableModels;
        }
        const search = this.state.modelSearch.toLowerCase();
        return this.state.availableModels.filter(model => 
            model.name.toLowerCase().includes(search) ||
            model.model.toLowerCase().includes(search)
        );
    }

    get filteredFields() {
        let fields = this.state.availableFields;
        
        // Filter by search text
        if (this.state.fieldSearch) {
            const search = this.state.fieldSearch.toLowerCase();
            fields = fields.filter(field => 
                field.field_description.toLowerCase().includes(search) ||
                field.name.toLowerCase().includes(search)
            );
        }
        
        // Filter by field type
        if (this.state.fieldTypeFilter) {
            fields = fields.filter(field => field.ttype === this.state.fieldTypeFilter);
        }
        
        return fields;
    }

    // Filter methods
    filterModels() {
        // Trigger re-render by updating state
        this.render();
    }

    filterFields() {
        // Trigger re-render by updating state
        this.render();
    }

    // Fallback RPC method using fetch
    async makeRpcCall(url, params = {}) {
        console.log('Making fallback RPC call to:', url, 'with params:', params);
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
            
            console.log('Response status:', response.status, response.statusText);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('RPC response data:', data);
            return data.result || data;
        } catch (error) {
            console.error('RPC call failed:', error);
            throw error;
        }
    }
    
    async loadModels() {
        this.state.loading = true;
        try {
            const result = await this.rpc("/ubx_report_builder/models", {});
            if (result.success) {
                this.state.availableModels = result.models;
            } else {
                this.notification.add(result.error, { type: 'danger' });
            }
        } catch (error) {
            this.notification.add(_t("Failed to load models"), { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    async loadExistingReport(reportId) {
        this.state.loading = true;
        try {
            const result = await this.rpc("/ubx_report_builder/load_report", { report_id: reportId });
            if (result.success) {
                const report = result.report;
                this.state.reportId = report.id;
                this.state.selectedModel = {
                    id: report.model_id,
                    name: report.model_description,
                    model: report.model_name,
                };
                this.state.reportConfig = {
                    name: report.name,
                    description: report.description,
                    domain: report.domain,
                    max_records: report.max_records,
                };
                this.state.selectedFields = report.fields || [];
                this.state.currentStep = 'field_selection';
                
                // Load fields for the selected model  
                await this.loadModelFields(report.model_id);
            } else {
                this.notification.add(result.error, { type: 'danger' });
            }
        } catch (error) {
            this.notification.add(_t("Failed to load report"), { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    async selectModel(model) {
        this.state.selectedModel = model;
        this.state.currentStep = 'field_selection';
        this.markAsChanged();
        await this.loadModelFields(model.id);
    }
    
    async loadModelFields(modelId) {
        this.state.loading = true;
        try {
            const result = await this.rpc("/ubx_report_builder/model_fields", { model_id: modelId });
            if (result.success) {
                this.state.availableFields = result.fields.map(field => ({
                    ...field,
                    selected: false,
                    label: field.field_description,
                    width: 100,
                    alignment: this.getDefaultAlignment(field.ttype),
                    aggregation: this.getDefaultAggregation(field.ttype),
                    visible: true,
                    sortable: true,
                    filterable: true,
                    isExpanded: false,
                    relatedFields: [],
                    isLoadingRelated: false,
                }));
            } else {
                this.notification.add(result.error, { type: 'danger' });
            }
        } catch (error) {
            this.notification.add(_t("Failed to load model fields"), { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    getDefaultAlignment(fieldType) {
        if (['integer', 'float', 'monetary'].includes(fieldType)) {
            return 'right';
        } else if (fieldType === 'boolean') {
            return 'center';
        }
        return 'left';
    }
    
    getDefaultAggregation(fieldType) {
        if (['integer', 'float', 'monetary'].includes(fieldType)) {
            return 'sum';
        }
        return 'none';
    }
    
    setupDragAndDrop() {
        // Setup drag and drop functionality
        if (!this.el) {
            console.warn('Component element not available for drag and drop setup');
            return;
        }
        
        const availableFieldsContainer = this.el.querySelector('.available-fields');
        const selectedFieldsContainer = this.el.querySelector('.selected-fields');
        
        if (availableFieldsContainer && selectedFieldsContainer) {
            this.setupDragEvents(availableFieldsContainer, selectedFieldsContainer);
        } else {
            // Retry after a short delay if elements not found
            setTimeout(() => {
                if (this.el) {
                    const availableFields = this.el.querySelector('.available-fields');
                    const selectedFields = this.el.querySelector('.selected-fields');
                    if (availableFields && selectedFields) {
                        this.setupDragEvents(availableFields, selectedFields);
                    }
                }
            }, 500);
        }
    }
    
    setupDragEvents(sourceContainer, targetContainer) {
        // Allow dropping in target container
        targetContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            targetContainer.classList.add('drag-over');
        });
        
        targetContainer.addEventListener('dragleave', (e) => {
            if (!targetContainer.contains(e.relatedTarget)) {
                targetContainer.classList.remove('drag-over');
            }
        });
        
        targetContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            targetContainer.classList.remove('drag-over');
            
            const fieldData = JSON.parse(e.dataTransfer.getData('text/plain'));
            this.addFieldToReport(fieldData);
        });
    }
    
    // Removed drag and drop functionality for better stability
    
    updateFieldConfig(field, property, value) {
        const selectedField = this.state.selectedFields.find(f => f.id === field.id);
        if (selectedField) {
            selectedField[property] = value;
        }
    }
    
    goToStep(step) {
        this.state.currentStep = step;
    }
    
    nextStep() {
        const steps = ['model_selection', 'field_selection', 'configuration', 'preview'];
        const currentIndex = steps.indexOf(this.state.currentStep);
        if (currentIndex < steps.length - 1) {
            this.state.currentStep = steps[currentIndex + 1];
        }
        
        if (this.state.currentStep === 'preview') {
            this.loadPreviewData();
        }
    }
    
    previousStep() {
        const steps = ['model_selection', 'field_selection', 'configuration', 'preview'];
        const currentIndex = steps.indexOf(this.state.currentStep);
        if (currentIndex > 0) {
            this.state.currentStep = steps[currentIndex - 1];
        }
    }
    
    async loadPreviewData() {
        console.log('loadPreviewData called', {
            reportId: this.state.reportId,
            selectedFieldsCount: this.state.selectedFields.length,
            servicesAvailable: this.servicesAvailable
        });
        
        if (!this.state.reportId && this.state.selectedFields.length > 0) {
            console.log('No report ID, saving temporary report for preview');
            // Save temporary report for preview
            await this.saveReport(true);
        }
        
        if (this.state.reportId) {
            this.state.loading = true;
            try {
                console.log('Making RPC call to preview_data with report_id:', this.state.reportId);
                const result = await this.rpc("/ubx_report_builder/preview_data", { 
                    report_id: this.state.reportId,
                    limit: 10
                });
                console.log('Preview data result:', result);
                
                if (result.success) {
                    this.state.previewData = result.data || [];
                    console.log('Preview data set:', this.state.previewData.length, 'records');
                    // Log first record structure for debugging
                    if (this.state.previewData.length > 0) {
                        console.log('First record structure:', this.state.previewData[0]);
                    }
                } else {
                    console.error('Preview data error:', result.error);
                    this.notification.add(result.error, { type: 'danger' });
                }
            } catch (error) {
                console.error('Exception in loadPreviewData:', error);
                this.notification.add(_t("Failed to load preview data"), { type: 'danger' });
            } finally {
                this.state.loading = false;
            }
        } else {
            console.log('No report ID available for preview');
        }
    }
    
    async saveReport(isTemporary = false) {
        if (!this.state.selectedModel || this.state.selectedFields.length === 0) {
            this.notification.add(_t("Please select a model and at least one field"), { type: 'warning' });
            return;
        }
        
        this.state.loading = true;
        try {
            const reportData = {
                report_id: this.state.reportId,
                name: isTemporary ? `Temp_${Date.now()}` : this.state.reportConfig.name,
                description: this.state.reportConfig.description,
                model_id: this.state.selectedModel.id,
                domain: this.state.reportConfig.domain,
                max_records: this.state.reportConfig.max_records,
                fields: this.state.selectedFields.map(field => {
                    const fieldData = {
                        field_name: field.field_path || field.name,
                        field_description: field.field_description,
                        field_type: field.ttype,
                        label: field.label || field.field_description,
                        visible: field.visible !== false,
                        width: field.width || 120,
                        alignment: field.alignment || 'left',
                        aggregation: field.aggregation || 'none',
                        sortable: field.sortable !== false,
                        filterable: field.filterable !== false,
                        show_summation: field.show_summation || false,
                    };
                    
                    // Handle related fields vs regular fields
                    if (field.is_related_field || field.field_path) {
                        fieldData.is_related_field = true;
                        fieldData.field_path = field.field_path || field.name;
                        // Don't send field_id for related fields
                    } else {
                        // Regular field - send field_id
                        fieldData.field_id = field.id;
                    }
                    
                    return fieldData;
                })
            };
            
            const result = await this.rpc("/ubx_report_builder/save_report", { report_data: reportData });
            if (result.success) {
                this.state.reportId = result.report_id;
                if (!isTemporary) {
                    this.notification.add(result.message || 'Report saved successfully', { type: 'success' });
                    this.markSaved();
                } else {
                    this.markSaved();
                }
            } else {
                console.error('Save error:', result.error);
                this.notification.add(result.error || 'Failed to save report', { type: 'danger' });
            }
        } catch (error) {
            console.error('Save exception:', error);
            this.notification.add(_t("Failed to save report"), { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    async exportToExcel() {
        if (!this.state.reportId) {
            await this.saveReport();
        }
        
        if (this.state.reportId) {
            const url = `/ubx_report_builder/export_excel?report_id=${this.state.reportId}`;
            window.open(url, '_blank');
        }
    }
    
    getFieldIcon(fieldType) {
        const iconMap = {
            'char': 'fa fa-font',
            'text': 'fa fa-align-left',
            'integer': 'fa fa-hashtag',
            'float': 'fa fa-calculator',
            'monetary': 'fa fa-money',
            'boolean': 'fa fa-check-square',
            'date': 'fa fa-calendar',
            'datetime': 'fa fa-clock-o',
            'selection': 'fa fa-list',
            'many2one': 'fa fa-link',
            'one2many': 'fa fa-sitemap',
            'many2many': 'fa fa-tags',
            'binary': 'fa fa-file',
            'html': 'fa fa-code',
        };
        return iconMap[fieldType] || 'fa fa-question-circle';
    }

    // Helper method to get record value for display
    getRecordValue(record, field) {
        if (!record || !field) return '';
        
        // Handle related fields with field_path
        if (field.field_path) {
            // For related fields, use the field_path as the key
            if (record.hasOwnProperty(field.field_path)) {
                const value = record[field.field_path];
                if (value && typeof value === 'object') {
                    return value.formatted || value.value || value.toString();
                }
                return value || '';
            }
        }
        
        // Try different field name variations
        const possibleKeys = [
            field.field_path,
            field.name,
            field.field_name,
            field.field_id,
            field.id
        ].filter(Boolean);
        
        for (const key of possibleKeys) {
            if (record.hasOwnProperty(key)) {
                const value = record[key];
                // Handle complex value objects
                if (value && typeof value === 'object') {
                    return value.formatted || value.value || value.toString();
                }
                // Handle simple values
                return value || '';
            }
        }
        
        // Fallback: try to find any matching key (case insensitive)
        const recordKeys = Object.keys(record);
        for (const key of possibleKeys) {
            const matchingKey = recordKeys.find(rKey => 
                rKey.toLowerCase() === (key || '').toLowerCase()
            );
            if (matchingKey) {
                const value = record[matchingKey];
                if (value && typeof value === 'object') {
                    return value.formatted || value.value || value.toString();
                }
                return value || '';
            }
        }
        
        return '';
    }

    // Add field to report (double-click or button click)
    addFieldToReport(field) {
        if (!field || this.state.selectedFields.find(f => f.id === field.id)) {
            return; // Field already selected
        }

        const newField = {
            ...field,
            id: field.id || field.name,
            label: field.field_description || field.name,
            width: 120,
            alignment: field.alignment || this.getDefaultAlignment(field.ttype),
            aggregation: field.aggregation || this.getDefaultAggregation(field.ttype),
            visible: true,
            sortable: true,
            filterable: true,
        };

        this.state.selectedFields.push(newField);
        this.markChanged();
    }

    // Remove field from report
    removeFieldFromReport(field) {
        const index = this.state.selectedFields.findIndex(f => f.id === field.id);
        if (index > -1) {
            this.state.selectedFields.splice(index, 1);
            this.markChanged();
        }
    }

    // Move field up in order
    moveFieldUp(field) {
        const index = this.state.selectedFields.findIndex(f => f.id === field.id);
        if (index > 0) {
            const temp = this.state.selectedFields[index];
            this.state.selectedFields[index] = this.state.selectedFields[index - 1];
            this.state.selectedFields[index - 1] = temp;
            this.markChanged();
        }
    }

    // Move field down in order
    moveFieldDown(field) {
        const index = this.state.selectedFields.findIndex(f => f.id === field.id);
        if (index < this.state.selectedFields.length - 1) {
            const temp = this.state.selectedFields[index];
            this.state.selectedFields[index] = this.state.selectedFields[index + 1];
            this.state.selectedFields[index + 1] = temp;
            this.markChanged();
        }
    }

    // Toggle related fields for a relational field
    async toggleRelatedFields(field) {
        if (!this.isRelationalField(field)) {
            return;
        }

        field.isExpanded = !field.isExpanded;

        // Load related fields if not already loaded
        if (field.isExpanded && field.relatedFields.length === 0) {
            await this.loadRelatedFields(field);
        }
    }

    // Check if field is relational
    isRelationalField(field) {
        return ['many2one', 'one2many', 'many2many'].includes(field.ttype);
    }

    // Load related fields for a relational field
    async loadRelatedFields(field) {
        if (!this.state.selectedModel || field.isLoadingRelated) {
            return;
        }

        field.isLoadingRelated = true;
        try {
            const result = await this.rpc("/ubx_report_builder/related_fields", { 
                model_name: this.state.selectedModel.model,
                field_name: field.name
            });
            
            if (result.success) {
                field.relatedFields = result.fields.map(relatedField => ({
                    ...relatedField,
                    label: relatedField.field_description,
                    width: 120,
                    alignment: this.getDefaultAlignment(relatedField.ttype),
                    aggregation: this.getDefaultAggregation(relatedField.ttype),
                    visible: true,
                    sortable: true,
                    filterable: true,
                    parentField: field,
                }));
            } else {
                this.notification.add(result.error, { type: 'danger' });
            }
        } catch (error) {
            this.notification.add(_t("Failed to load related fields"), { type: 'danger' });
        } finally {
            field.isLoadingRelated = false;
        }
    }

    // Removed drag and drop event handlers - using double-click only
    
    // Update field label
    updateFieldLabel(field, event) {
        field.label = event.target.value;
        this.markChanged();
    }

    // Toggle field summation
    toggleFieldSummation(field, event) {
        field.show_summation = event.target.checked;
        this.markChanged();
    }

    // Mark as having unsaved changes
    markChanged() {
        this.state.hasUnsavedChanges = true;
    }

    // Alternative method for template compatibility
    markAsChanged() {
        this.markChanged();
    }

    // Mark as saved
    markSaved() {
        this.state.hasUnsavedChanges = false;
    }

    // Check if there are unsaved changes
    hasChanges() {
        return this.state.hasUnsavedChanges && (
            this.state.selectedModel || 
            this.state.selectedFields.length > 0 ||
            this.state.reportConfig.name !== 'New Report' ||
            this.state.reportConfig.description
        );
    }

    // Close builder with confirmation if needed
    async closeBuilder() {
        console.log('Close button clicked'); // Debug log
        
        if (this.hasChanges()) {
            const confirmed = await this.showCloseConfirmation();
            if (!confirmed) {
                return; // User cancelled
            }
        }
        
        try {
            // Check if we have a proper action service
            if (this.actionService && typeof this.actionService.doAction === 'function') {
                console.log('Using action service to navigate back to reports');
                
                // Navigate directly to the reports list using the correct action
                this.actionService.doAction({
                    name: _t('Report Builder'),
                    type: 'ir.actions.act_window',
                    res_model: 'report.builder',
                    view_mode: 'kanban,list,form',
                    views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                    target: 'current',
                    context: {
                        'search_default_my_reports': 1,
                        'search_default_active': 1
                    }
                });
                
            } else {
                console.log('Action service not available, using direct navigation');
                // Direct navigation to the reports list using the correct action ID
                window.location.href = '/web#action=ubx_report_builder.action_report_builder&model=report.builder&view_type=kanban';
            }
        } catch (error) {
            console.error('Error closing builder:', error);
            // Fallback to browser history
            if (window.history.length > 1) {
                window.history.back();
            } else {
                // If no history, navigate to the reports directly
                window.location.href = '/web#action=ubx_report_builder.action_report_builder';
            }
        }
    }

    // Show close confirmation dialog
    async showCloseConfirmation() {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.innerHTML = `
                <div class="modal fade show" style="display: block; background: rgba(0,0,0,0.5);" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Unsaved Changes</h5>
                            </div>
                            <div class="modal-body">
                                <p>You have unsaved changes. What would you like to do?</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-success save-btn">
                                    <i class="fa fa-save"></i> Save & Close
                                </button>
                                <button type="button" class="btn btn-danger discard-btn">
                                    <i class="fa fa-trash"></i> Discard & Close
                                </button>
                                <button type="button" class="btn btn-secondary cancel-btn">
                                    <i class="fa fa-times"></i> Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(dialog);
            
            const cleanup = () => {
                document.body.removeChild(dialog);
            };
            
            // Save & Close
            dialog.querySelector('.save-btn').addEventListener('click', async () => {
                cleanup();
                await this.saveReport();
                resolve(true);
            });
            
            // Discard & Close
            dialog.querySelector('.discard-btn').addEventListener('click', () => {
                cleanup();
                resolve(true);
            });
            
            // Cancel
            dialog.querySelector('.cancel-btn').addEventListener('click', () => {
                cleanup();
                resolve(false);
            });
            
            // Close on backdrop click
            dialog.addEventListener('click', (e) => {
                if (e.target === dialog) {
                    cleanup();
                    resolve(false);
                }
            });
        });
    }
}

// Register the widget
registry.category("actions").add("report_builder_widget", ReportBuilderWidget);
