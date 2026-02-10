/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class FieldSelector extends Component {
    static template = "ubx_report_builder.FieldSelector";
    static props = {
        modelId: Number,
        onFieldSelect: Function,
        selectedFields: { type: Array, optional: true }
    };
    
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        
        this.state = useState({
            fields: [],
            loading: false,
            searchText: '',
            filterType: 'all',
            expandedRelations: new Set(),
        });
        
        onWillStart(async () => {
            await this.loadFields();
        });
    }
    
    async loadFields() {
        this.state.loading = true;
        try {
            const result = await this.rpc("/ubx_report_builder/model_fields", { 
                model_id: this.props.modelId 
            });
            if (result.success) {
                this.state.fields = result.fields.map(field => ({
                    ...field,
                    isSelected: this.isFieldSelected(field.id),
                    relatedFields: []
                }));
            } else {
                this.notification.add(result.error, { type: 'danger' });
            }
        } catch (error) {
            this.notification.add(_t("Failed to load fields"), { type: 'danger' });
        } finally {
            this.state.loading = false;
        }
    }
    
    isFieldSelected(fieldId) {
        return this.props.selectedFields?.some(f => f.id === fieldId) || false;
    }
    
    get filteredFields() {
        let fields = this.state.fields;
        
        // Filter by search text
        if (this.state.searchText) {
            const search = this.state.searchText.toLowerCase();
            fields = fields.filter(field => 
                field.field_description.toLowerCase().includes(search) ||
                field.name.toLowerCase().includes(search)
            );
        }
        
        // Filter by type
        if (this.state.filterType !== 'all') {
            if (this.state.filterType === 'basic') {
                fields = fields.filter(field => 
                    ['char', 'text', 'integer', 'float', 'boolean', 'date', 'datetime'].includes(field.ttype)
                );
            } else if (this.state.filterType === 'relational') {
                fields = fields.filter(field => 
                    ['many2one', 'one2many', 'many2many'].includes(field.ttype)
                );
            } else {
                fields = fields.filter(field => field.ttype === this.state.filterType);
            }
        }
        
        return fields;
    }
    
    get fieldTypes() {
        const types = new Set(this.state.fields.map(f => f.ttype));
        return Array.from(types).sort();
    }
    
    selectField(field) {
        if (!this.isFieldSelected(field.id)) {
            this.props.onFieldSelect(field);
            field.isSelected = true;
        }
    }
    
    async toggleRelatedFields(field) {
        if (!['many2one', 'one2many', 'many2many'].includes(field.ttype)) {
            return;
        }
        
        const fieldKey = `${field.id}`;
        if (this.state.expandedRelations.has(fieldKey)) {
            this.state.expandedRelations.delete(fieldKey);
        } else {
            this.state.expandedRelations.add(fieldKey);
            
            // Load related fields if not already loaded
            if (field.relatedFields.length === 0) {
                try {
                    const result = await this.rpc("/ubx_report_builder/related_fields", {
                        model_name: field.relation,
                        field_name: field.name
                    });
                    if (result.success) {
                        field.relatedFields = result.fields;
                    }
                } catch (error) {
                    this.notification.add(_t("Failed to load related fields"), { type: 'danger' });
                }
            }
        }
    }
    
    isRelatedFieldExpanded(field) {
        return this.state.expandedRelations.has(`${field.id}`);
    }
    
    getFieldIcon(fieldType) {
        const iconMap = {
            'char': 'fa-font',
            'text': 'fa-align-left',
            'integer': 'fa-hashtag',
            'float': 'fa-calculator',
            'monetary': 'fa-money',
            'boolean': 'fa-check-square',
            'date': 'fa-calendar',
            'datetime': 'fa-clock-o',
            'selection': 'fa-list',
            'many2one': 'fa-link',
            'one2many': 'fa-sitemap',
            'many2many': 'fa-exchange',
            'binary': 'fa-file',
            'html': 'fa-code',
        };
        return iconMap[fieldType] || 'fa-question';
    }
    
    getFieldTypeLabel(fieldType) {
        const labelMap = {
            'char': 'Text',
            'text': 'Long Text',
            'integer': 'Integer',
            'float': 'Decimal',
            'monetary': 'Currency',
            'boolean': 'Boolean',
            'date': 'Date',
            'datetime': 'Date & Time',
            'selection': 'Selection',
            'many2one': 'Link (Many2One)',
            'one2many': 'Lines (One2Many)',
            'many2many': 'Tags (Many2Many)',
            'binary': 'File',
            'html': 'HTML',
        };
        return labelMap[fieldType] || fieldType;
    }
    
    onSearchChange(event) {
        this.state.searchText = event.target.value;
    }
    
    onFilterChange(event) {
        this.state.filterType = event.target.value;
    }
}

registry.category("components").add("FieldSelector", FieldSelector);
