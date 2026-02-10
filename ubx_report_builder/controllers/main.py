# -*- coding: utf-8 -*-

import json
import base64
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import UserError, AccessError


class ReportBuilderController(http.Controller):
    
    @http.route('/ubx_report_builder/models', type='json', auth='user')
    def get_models(self):
        """Get available models for report building."""
        try:
            report_builder = request.env['report.builder']
            models = report_builder.get_available_models()
            return {'success': True, 'models': models}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/ubx_report_builder/model_fields', type='json', auth='user')
    def get_model_fields(self, model_id):
        """Get fields for a specific model."""
        try:
            if not model_id:
                return {'success': False, 'error': 'Model ID is required'}
            
            report_builder = request.env['report.builder']
            fields_data = report_builder.get_model_fields(model_id)
            return {'success': True, 'fields': fields_data}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/ubx_report_builder/related_fields', type='json', auth='user')
    def get_related_fields(self, model_name, field_name):
        """Get related fields for a relational field."""
        try:
            related_field_model = request.env['report.builder.related.field']
            fields_data = related_field_model.get_related_fields(model_name, field_name)
            return {'success': True, 'fields': fields_data}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/ubx_report_builder/save_report', type='json', auth='user')
    def save_report(self, report_data):
        """Save report configuration."""
        try:
            report_id = report_data.get('report_id')
            report_builder = request.env['report.builder']
            
            if report_id:
                # Update existing report
                report = report_builder.browse(report_id)
                if not report.exists():
                    return {'success': False, 'error': 'Report not found'}
                
                # Check access rights
                report.check_access('write')
                
            else:
                # Create new report
                report = report_builder.create({
                    'name': report_data.get('name', 'New Report'),
                    'description': report_data.get('description', ''),
                    'model_id': report_data.get('model_id'),
                    'filter_domain': json.dumps(report_data.get('domain', [])),
                    'max_records': report_data.get('max_records', 1000),
                })
                report_id = report.id
            
            # Update report fields
            field_model = request.env['report.builder.field']
            
            # Remove existing fields
            existing_fields = field_model.search([('report_id', '=', report_id)])
            existing_fields.unlink()
            
            # Add new fields
            for seq, field_data in enumerate(report_data.get('fields', []), 1):
                field_vals = {
                    'report_id': report_id,
                    'field_name': field_data.get('field_name'),
                    'field_description': field_data.get('field_description'),
                    'field_type': field_data.get('field_type'),
                    'field_label': field_data.get('label'),
                    'sequence': seq,
                    'visible': field_data.get('visible', True),
                    'width': field_data.get('width', 100),
                    'alignment': field_data.get('alignment', 'left'),
                    'aggregation': field_data.get('aggregation', 'none'),
                    'sortable': field_data.get('sortable', True),
                    'filterable': field_data.get('filterable', True),
                    'show_summation': field_data.get('show_summation', False),
                }
                
                # Handle related fields vs regular fields
                if field_data.get('is_related_field') or field_data.get('field_path'):
                    field_vals.update({
                        'is_related_field': True,
                        'field_path': field_data.get('field_path'),
                        # Don't set field_id for related fields
                    })
                else:
                    # Regular field - set field_id
                    field_vals['field_id'] = field_data.get('field_id')
                
                field_model.create(field_vals)
            
            return {
                'success': True, 
                'report_id': report_id,
                'message': _('Report saved successfully')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/ubx_report_builder/load_report', type='json', auth='user')
    def load_report(self, report_id):
        """Load report configuration."""
        try:
            if not report_id:
                return {'success': False, 'error': 'Report ID is required'}
            
            report = request.env['report.builder'].browse(report_id)
            if not report.exists():
                return {'success': False, 'error': 'Report not found'}
            
            # Check access rights
            report.check_access('read')
            
            # Prepare report data
            report_data = {
                'id': report.id,
                'name': report.name,
                'description': report.description or '',
                'model_id': report.model_id.id,
                'model_name': report.model_name,
                'model_description': report.model_id.name,
                'domain': json.loads(report.filter_domain or '[]'),
                'max_records': report.max_records,
                'state': report.state,
                'field_count': report.field_count,
                'record_count': report.record_count,
            }
            
            # Get field configurations
            fields_data = []
            for field_config in report.field_ids.sorted('sequence'):
                field_data = {
                    'id': field_config.field_id.id if field_config.field_id else field_config.field_path or field_config.field_name,
                    'name': field_config.field_name,
                    'field_name': field_config.field_name,
                    'field_description': field_config.field_description,
                    'ttype': field_config.field_type,
                    'field_type': field_config.field_type,
                    'label': field_config.field_label,
                    'sequence': field_config.sequence,
                    'visible': field_config.visible,
                    'width': field_config.width,
                    'alignment': field_config.alignment,
                    'aggregation': field_config.aggregation,
                    'sortable': field_config.sortable,
                    'filterable': field_config.filterable,
                    'show_summation': field_config.show_summation,
                }
                
                # Handle related fields
                if field_config.is_related_field:
                    field_data.update({
                        'is_related_field': True,
                        'field_path': field_config.field_path,
                    })
                
                fields_data.append(field_data)
            
            report_data['fields'] = fields_data
            
            return {'success': True, 'report': report_data}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/ubx_report_builder/preview_data', type='json', auth='user')
    def preview_data(self, report_id, max_records=50, limit=None):
        """Get preview data for a report."""
        try:
            # Handle both max_records and limit parameters
            actual_limit = max_records if max_records else (limit if limit else 50)
            
            if not report_id:
                return {'success': False, 'error': 'Report ID is required'}
            
            report = request.env['report.builder'].browse(report_id)
            if not report.exists():
                return {'success': False, 'error': 'Report not found'}
            
            # Check access rights
            report.check_access('read')
            
            # Get data using the same method as Excel export
            data = report._get_report_data()
            limited_data = data[:actual_limit] if len(data) > actual_limit else data
            
            # Deep convert all data to JSON-safe format
            from datetime import datetime, date
            
            def make_json_safe(obj):
                """Convert any object to JSON-safe format"""
                if obj is None:
                    return ''
                elif isinstance(obj, datetime):
                    return obj.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(obj, date):
                    return obj.strftime('%Y-%m-%d')
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
            
            return {
                'success': True, 
                'data': json_safe_data,
                'total_records': len(data)
            }
            
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Error in preview_data: %s", str(e), exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/ubx_report_builder/export_excel', type='http', auth='user')
    def export_excel(self, report_id, group_by=None, **kwargs):
        """Export report to Excel - HTTP endpoint for file download."""
        try:
            if not report_id:
                return request.not_found()
            
            report = request.env['report.builder'].browse(int(report_id))
            if not report.exists():
                return request.not_found()
            
            # Check access rights
            report.check_access_rights('read')
            
            # Prepare filter context
            filter_context = {}
            
            # Extract all field filters from kwargs
            field_filters = {}
            date_filters = {}
            
            for key, value in kwargs.items():
                if key.startswith('filter_') and not key.startswith('date_filter_'):
                    # Selection field filter
                    field_name = key.replace('filter_', '')
                    field_filters[field_name] = value
                elif key.startswith('date_filter_'):
                    # Date range filter
                    parts = key.replace('date_filter_', '').rsplit('_', 1)
                    if len(parts) == 2:
                        field_name, range_type = parts
                        if field_name not in date_filters:
                            date_filters[field_name] = {}
                        date_filters[field_name][range_type] = value
            
            if field_filters:
                filter_context['field_filters'] = field_filters
            if date_filters:
                filter_context['date_filters'] = date_filters
            if group_by:
                filter_context['group_by'] = group_by
            
            # Generate Excel file with filters
            result = report.with_context(**filter_context).action_export_excel()
            
            if result.get('type') == 'ir.actions.act_url':
                # Extract attachment ID from URL
                url = result.get('url', '')
                if '/web/content/' in url:
                    attachment_id = url.split('/web/content/')[1].split('?')[0]
                    attachment = request.env['ir.attachment'].browse(int(attachment_id))
                    
                    if attachment.exists():
                        # Return file as HTTP response
                        file_content = base64.b64decode(attachment.datas)
                        
                        response = request.make_response(
                            file_content,
                            headers=[
                                ('Content-Type', attachment.mimetype),
                                ('Content-Disposition', 'attachment; filename="%s"' % attachment.name),
                                ('Content-Length', len(file_content))
                            ]
                        )
                        
                        # Clean up temporary attachment
                        attachment.unlink()
                        
                        return response
            
            return request.not_found()
            
        except Exception as e:
            return request.render('http_routing.http_error', {
                'status_code': 500,
                'status_message': 'Internal Server Error',
                'error_message': str(e)
            })
    
    @http.route('/ubx_report_builder/export_pdf', type='http', auth='user')
    def export_pdf(self, report_id, group_by=None, **kwargs):
        """Export report to PDF - HTTP endpoint for file download."""
        try:
            if not report_id:
                return request.not_found()
            
            report = request.env['report.builder'].browse(int(report_id))
            if not report.exists():
                return request.not_found()
            
            # Check access rights
            report.check_access_rights('read')
            
            # Prepare filter context
            filter_context = {}
            
            # Extract all field filters from kwargs
            field_filters = {}
            date_filters = {}
            
            for key, value in kwargs.items():
                if key.startswith('filter_') and not key.startswith('date_filter_'):
                    # Selection field filter
                    field_name = key.replace('filter_', '')
                    field_filters[field_name] = value
                elif key.startswith('date_filter_'):
                    # Date range filter
                    parts = key.replace('date_filter_', '').rsplit('_', 1)
                    if len(parts) == 2:
                        field_name, range_type = parts
                        if field_name not in date_filters:
                            date_filters[field_name] = {}
                        date_filters[field_name][range_type] = value
            
            if field_filters:
                filter_context['field_filters'] = field_filters
            if date_filters:
                filter_context['date_filters'] = date_filters
            if group_by:
                filter_context['group_by'] = group_by
            
            # Generate PDF file with filters
            result = report.with_context(**filter_context).action_export_pdf()
            
            if result.get('type') == 'ir.actions.act_url':
                # Extract attachment ID from URL
                url = result.get('url', '')
                if '/web/content/' in url:
                    attachment_id = url.split('/web/content/')[1].split('?')[0]
                    attachment = request.env['ir.attachment'].browse(int(attachment_id))
                    
                    if attachment.exists():
                        # Return file as HTTP response
                        file_content = base64.b64decode(attachment.datas)
                        
                        response = request.make_response(
                            file_content,
                            headers=[
                                ('Content-Type', attachment.mimetype),
                                ('Content-Disposition', 'attachment; filename="%s"' % attachment.name),
                                ('Content-Length', len(file_content))
                            ]
                        )
                        
                        # Clean up temporary attachment
                        attachment.unlink()
                        
                        return response
            
            return request.not_found()
            
        except Exception as e:
            return request.render('http_routing.http_error', {
                'status_code': 500,
                'status_message': 'Internal Server Error',
                'error_message': str(e)
            })
    
    @http.route('/ubx_report_builder/validate_domain', type='json', auth='user')
    def validate_domain(self, model_name, domain_str):
        """Validate a domain filter."""
        try:
            if not model_name or not domain_str:
                return {'success': False, 'error': 'Model name and domain are required'}
            
            # Parse domain
            try:
                domain = json.loads(domain_str)
            except json.JSONDecodeError:
                return {'success': False, 'error': 'Invalid JSON format'}
            
            # Test domain on model
            try:
                model = request.env[model_name]
                count = model.search_count(domain)
                return {
                    'success': True, 
                    'valid': True,
                    'record_count': count,
                    'message': 'Domain is valid. Found %s records.' % count
                }
            except Exception as e:
                return {
                    'success': True,
                    'valid': False,
                    'error': str(e),
                    'message': 'Invalid domain: %s' % str(e)
                }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
