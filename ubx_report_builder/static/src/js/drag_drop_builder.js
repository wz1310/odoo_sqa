/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export class DragDropBuilder extends Component {
    static template = "ubx_report_builder.DragDropBuilder";
    static props = {
        selectedFields: Array,
        onFieldRemove: Function,
        onFieldMove: Function,
        onFieldUpdate: Function,
    };
    
    setup() {
        this.containerRef = useRef("container");
        this.state = useState({
            draggedIndex: null,
            dragOverIndex: null,
        });
        
        onMounted(() => {
            this.setupSortable();
        });
    }
    
    setupSortable() {
        const container = this.containerRef.el;
        if (!container) return;
        
        // Add drag event listeners to field items
        this.updateDragHandlers();
    }
    
    updateDragHandlers() {
        const items = this.containerRef.el?.querySelectorAll('.field-item');
        items?.forEach((item, index) => {
            item.draggable = true;
            item.addEventListener('dragstart', (e) => this.onDragStart(e, index));
            item.addEventListener('dragover', (e) => this.onDragOver(e, index));
            item.addEventListener('drop', (e) => this.onDrop(e, index));
            item.addEventListener('dragend', (e) => this.onDragEnd(e));
        });
    }
    
    onDragStart(event, index) {
        this.state.draggedIndex = index;
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/html', event.target.outerHTML);
        event.target.classList.add('dragging');
    }
    
    onDragOver(event, index) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
        
        if (this.state.draggedIndex !== index) {
            this.state.dragOverIndex = index;
        }
    }
    
    onDrop(event, index) {
        event.preventDefault();
        
        const draggedIndex = this.state.draggedIndex;
        if (draggedIndex !== null && draggedIndex !== index) {
            this.props.onFieldMove(draggedIndex, index);
        }
        
        this.state.dragOverIndex = null;
    }
    
    onDragEnd(event) {
        event.target.classList.remove('dragging');
        this.state.draggedIndex = null;
        this.state.dragOverIndex = null;
    }
    
    removeField(field, index) {
        this.props.onFieldRemove(field, index);
    }
    
    updateField(field, property, value) {
        this.props.onFieldUpdate(field, property, value);
    }
    
    moveFieldUp(field, index) {
        if (index > 0) {
            this.props.onFieldMove(index, index - 1);
        }
    }
    
    moveFieldDown(field, index) {
        if (index < this.props.selectedFields.length - 1) {
            this.props.onFieldMove(index, index + 1);
        }
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
        };
        return iconMap[fieldType] || 'fa-question';
    }
    
    get alignmentOptions() {
        return [
            { value: 'left', label: _t('Left') },
            { value: 'center', label: _t('Center') },
            { value: 'right', label: _t('Right') }
        ];
    }
    
    get aggregationOptions() {
        return [
            { value: 'none', label: _t('None') },
            { value: 'sum', label: _t('Sum') },
            { value: 'avg', label: _t('Average') },
            { value: 'count', label: _t('Count') },
            { value: 'min', label: _t('Minimum') },
            { value: 'max', label: _t('Maximum') }
        ];
    }
    
    getValidAggregations(fieldType) {
        if (['integer', 'float', 'monetary'].includes(fieldType)) {
            return this.aggregationOptions;
        } else {
            return [
                { value: 'none', label: _t('None') },
                { value: 'count', label: _t('Count') }
            ];
        }
    }
}

registry.category("components").add("DragDropBuilder", DragDropBuilder);
