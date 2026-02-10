# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, date
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)


class ReportBuilderController(http.Controller):
    
    @http.route('/ubx_report_builder/models', type='json', auth='user', methods=['POST'])
    def get_models(self, **kwargs):
        """Get available models for report building."""
        try:
            report_builder = request.env['report.builder']
            models = report_builder.get_available_models()
            return {
                'success': True,
                'models': models
            }
        except Exception as e:
            _logger.error("Error getting models: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/ubx_report_builder/model_fields', type='json', auth='user', methods=['POST'])
    def get_model_fields(self, model_id, **kwargs):
        """Get available fields for a specific model."""
        try:
            report_builder = request.env['report.builder']
            fields = report_builder.get_model_fields(model_id)
            return {
                'success': True,
                'fields': fields
            }
        except Exception as e:
            _logger.error("Error getting model fields: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/ubx_report_builder/load_report', type='json', auth='user', methods=['POST'])
    def load_report(self, report_id, **kwargs):
        """Load existing report configuration."""
        try:
            report = request.env['report.builder'].browse(report_id)
            if not report.exists():
                return {
                    'success': False,
                    'error': _('Report not found')
                }
            
            # Check access rights
            report.check_access('read')
            
            field_data = []
            for field in report.field_ids.sorted('sequence'):
                field_data.append({
                    'id': field.field_id.id,
                    'field_id': field.field_id.id,
                    'field_name': field.field_name,
                    'field_path': field.field_name,  # Use field_name as field_path for consistency
                    'field_description': field.field_description,
                    'field_type': field.field_type,  # Changed from ttype to field_type
                    'ttype': field.field_type,
                    'label': field.field_label,
                    'visible': field.visible,
                    'width': field.width,
                    'alignment': field.alignment,
                    'aggregation': field.aggregation,
                    'sortable': field.sortable,
                    'filterable': field.filterable,
                    'sequence': field.sequence,
                })
            
            return {
                'success': True,
                'report': {
                    'id': report.id,
                    'name': report.name,
                    'description': report.description,
                    'model_id': report.model_id.id,
                    'model_name': report.model_name,
                    'model_description': report.model_id.name,
                    'domain': json.loads(report.filter_domain or '[]'),
                    'max_records': report.max_records,
                    'fields': field_data,
                }
            }
        except Exception as e:
            _logger.error("Error loading report: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/ubx_report_builder/save_report', type='json', auth='user', methods=['POST'])
    def save_report(self, report_data, **kwargs):
        """Save report configuration."""
        try:
            report_builder_env = request.env['report.builder']
            
            # Prepare report values
            vals = {
                'name': report_data.get('name', 'Untitled Report'),
                'description': report_data.get('description', ''),
                'model_id': report_data.get('model_id'),
                'filter_domain': json.dumps(report_data.get('domain', [])),
                'max_records': report_data.get('max_records', 1000),
                'state': 'draft',
            }
            
            report_id = report_data.get('report_id')
            if report_id:
                # Update existing report
                report = report_builder_env.browse(report_id)
                if report.exists():
                    report.write(vals)
                    # Clear existing fields
                    report.field_ids.unlink()
                else:
                    return {
                        'success': False,
                        'error': _('Report not found')
                    }
            else:
                # Create new report
                report = report_builder_env.create(vals)
                report_id = report.id
            
            # Create field configurations
            field_env = request.env['report.builder.field']
            for i, field_data in enumerate(report_data.get('fields', [])):
                field_vals = {
                    'report_id': report_id,
                    'field_id': field_data.get('field_id'),
                    'field_description': field_data.get('field_description', ''),
                    'field_label': field_data.get('label'),
                    'sequence': i + 1,
                    'visible': field_data.get('visible', True),
                    'width': field_data.get('width', 100),
                    'alignment': field_data.get('alignment', 'left'),
                    'aggregation': field_data.get('aggregation', 'none'),
                    'sortable': field_data.get('sortable', True),
                    'filterable': field_data.get('filterable', True),
                }
                field_env.create(field_vals)
            
            return {
                'success': True,
                'report_id': report_id,
                'message': _('Report saved successfully')
            }
            
        except Exception as e:
            _logger.error("Error saving report: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/ubx_report_builder/preview_data', type='json', auth='user', methods=['POST'])
    def get_preview_data(self, model_id=None, fields=None, domain=None, max_records=10, report_id=None, filters=None, group_by=None, **kwargs):
        """Get preview data for a report using the same method as Excel export."""
        try:
            if report_id:
                # Load existing report
                report = request.env['report.builder'].browse(report_id)
                if not report.exists():
                    return {
                        'success': False,
                        'error': 'Report not found'
                    }
                
                try:
                    # Use the exact same method as Excel export
                    data = report._get_report_data()
                    limited_data = data[:max_records] if len(data) > max_records else data
                    
                    # Deep convert all data to JSON-safe format
                    def make_json_safe(obj):
                        """Convert any object to JSON-safe format"""
                        if obj is None:
                            return ''
                        elif isinstance(obj, (datetime, date)):
                            return obj.strftime('%Y-%m-%d %H:%M:%S') if isinstance(obj, datetime) else obj.strftime('%Y-%m-%d')
                        elif isinstance(obj, (list, tuple)):
                            return [make_json_safe(item) for item in obj]
                        elif isinstance(obj, dict):
                            return {str(k): make_json_safe(v) for k, v in obj.items()}
                        elif isinstance(obj, bool):
                            return 'Yes' if obj else 'No'
                        elif isinstance(obj, (int, float)):
                            return str(obj)
                        else:
                            return str(obj)
                    
                    json_safe_data = []
                    for record in limited_data:
                        json_record = {}
                        for key, value in record.items():
                            if isinstance(value, dict):
                                # Handle structured data
                                json_record[key] = {
                                    'value': make_json_safe(value.get('value')),
                                    'formatted': make_json_safe(value.get('formatted')),
                                    'type': str(value.get('type', 'char'))
                                }
                            else:
                                # Handle simple value
                                json_record[key] = {
                                    'value': make_json_safe(value),
                                    'formatted': make_json_safe(value),
                                    'type': 'char'
                                }
                        json_safe_data.append(json_record)
                        _logger.info(json_record)
                    
                    return {
                        'success': True,
                        'data': json_safe_data,
                        'total_records': len(data)
                    }
                    
                except Exception as e:
                    _logger.error("Error getting report data: %s", str(e), exc_info=True)
                    return {
                        'success': False,
                        'error': str(e)
                    }
            else:
                # Preview without saving - use provided data
                if not model_id or not fields:
                    return {
                        'success': False,
                        'error': _('Model and fields are required for preview')
                    }
                
                model = request.env['ir.model'].browse(model_id)
                if not model.exists():
                    return {
                        'success': False,
                        'error': _('Model not found')
                    }
                
                # Get model records for preview
                model_obj = request.env[model.model]
                search_domain = domain or []
                
                # Get field names to read
                field_names = [field.get('field_name') for field in fields if field.get('field_name')]
                if not field_names:
                    return {
                        'success': False,
                        'error': _('No valid fields provided')
                    }
                
                # Search and read records
                records = model_obj.search(search_domain, limit=max_records)
                data = records.read(field_names)
                
                # Format data
                formatted_data = []
                for record in data:
                    formatted_record = {}
                    for field in fields:
                        field_name = field.get('field_name')
                        if field_name and field_name in record:
                            raw_value = record[field_name]
                            # Simple formatting
                            if raw_value is None or raw_value is False:
                                formatted_value = ''
                            elif isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
                                # Many2one field returns [id, name]
                                formatted_value = raw_value[1] if len(raw_value) > 1 else str(raw_value[0])
                            else:
                                formatted_value = str(raw_value)
                            
                            formatted_record[field_name] = {
                                'value': raw_value,
                                'formatted': formatted_value
                            }
                    formatted_data.append(formatted_record)
                
                return {
                    'success': True,
                    'data': formatted_data,
                    'total_records': len(records)
                }
            
        except Exception as e:
            _logger.error("Error getting preview data: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/ubx_report_builder/export_excel', type='http', auth='user', methods=['GET'])
    def export_excel(self, report_id, **kwargs):
        """Export report to Excel."""
        try:
            report = request.env['report.builder'].browse(int(report_id))
            if not report.exists():
                return request.not_found()
            
            # Use the existing export functionality
            return report.action_export_excel()
            
        except Exception as e:
            _logger.error("Error exporting Excel: %s", str(e))
            return request.make_response(
                "Error exporting report: {}".format(str(e)), 
                status=500
            )
