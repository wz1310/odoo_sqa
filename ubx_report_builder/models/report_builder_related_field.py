# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ReportBuilderRelatedField(models.Model):
    _name = 'report.builder.related.field'
    _description = 'Report Builder Related Field'
    _rec_name = 'field_path'

    parent_field_id = fields.Many2one('report.builder.field', string='Parent Field', ondelete='cascade')
    field_path = fields.Char(string='Field Path', required=True, help='Dot notation path to the field (e.g., partner_id.name)')
    field_name = fields.Char(string='Field Name', required=True)
    field_description = fields.Char(string='Field Description', required=True)
    field_type = fields.Char(string='Field Type', required=True)
    related_model_name = fields.Char(string='Related Model', required=True)
    is_relational = fields.Boolean(string='Is Relational Field', default=False)
    
    @api.model
    def get_related_fields(self, model_name, field_name, max_depth=2, current_depth=0):
        """
        Get related fields for a relational field.
        
        Args:
            model_name: Name of the model (e.g., 'sale.order')
            field_name: Name of the relational field (e.g., 'partner_id')
            max_depth: Maximum depth to traverse relationships
            current_depth: Current traversal depth
            
        Returns:
            List of field dictionaries with related field information
        """
        if current_depth >= max_depth:
            return []
            
        try:
            # Get the model and field information
            model = self.env[model_name]
            if field_name not in model._fields:
                return []
                
            field_info = model._fields[field_name]
            
            # Check if it's a relational field
            if field_info.type not in ['many2one', 'one2many', 'many2many']:
                return []
                
            # Get the related model
            related_model_name = field_info.comodel_name
            if not related_model_name:
                return []
                
            related_model = self.env[related_model_name]
            related_fields = []
            
            # Get all fields from the related model
            for fname, finfo in related_model._fields.items():
                # Skip system fields and non-stored fields
                if (fname.startswith('_') or 
                    fname in ['id', 'create_date', 'create_uid', 'write_date', 'write_uid'] or
                    not getattr(finfo, 'store', True)):
                    continue
                    
                # Create field path
                field_path = "%s.%s" % (field_name, fname)
                
                field_data = {
                    'id': "%s.%s" % (model_name, field_path),
                    'name': fname,
                    'field_name': fname,
                    'field_description': finfo.string or fname.replace('_', ' ').title(),
                    'ttype': finfo.type,
                    'field_path': field_path,
                    'related_model_name': related_model_name,
                    'is_relational': finfo.type in ['many2one', 'one2many', 'many2many'],
                    'is_related_field': True,
                    'parent_field': field_name,
                    'depth': current_depth + 1,
                }
                
                # Add help text if available
                if hasattr(finfo, 'help') and finfo.help:
                    field_data['help'] = finfo.help
                    
                related_fields.append(field_data)
                
                # If this is also a relational field and we haven't reached max depth,
                # recursively get its related fields (but limit to avoid infinite loops)
                if (finfo.type in ['many2one'] and 
                    current_depth < max_depth - 1 and
                    finfo.comodel_name and
                    finfo.comodel_name != model_name):  # Avoid self-references
                    
                    try:
                        nested_fields = self.get_related_fields(
                            related_model_name, 
                            fname, 
                            max_depth, 
                            current_depth + 1
                        )
                        # Add nested fields with updated paths
                        for nested_field in nested_fields:
                            nested_field['field_path'] = "%s.%s" % (field_path, nested_field['name'])
                            nested_field['id'] = "%s.%s" % (model_name, nested_field['field_path'])
                            nested_field['parent_field'] = field_path
                            related_fields.append(nested_field)
                    except Exception as e:
                        _logger.warning("Error getting nested fields for %s: %s", field_path, str(e))
                        continue
            
            # Sort fields by description for better UX
            related_fields.sort(key=lambda x: x.get('field_description', ''))
            
            return related_fields
            
        except Exception as e:
            _logger.error("Error getting related fields for %s.%s: %s", model_name, field_name, str(e))
            return []
    
    @api.model
    def format_related_field_value(self, record, field_path):
        """
        Get value from a record using dot notation field path.
        
        Args:
            record: The record to get value from
            field_path: Dot notation path (e.g., 'partner_id.name')
            
        Returns:
            Dictionary with value, formatted, and type information
        """
        try:
            if not record or not field_path:
                return {'value': '', 'formatted': '', 'type': 'char'}
                
            # Split the path and traverse the record
            path_parts = field_path.split('.')
            current_value = record
            
            for part in path_parts:
                if not current_value:
                    break
                    
                if hasattr(current_value, part):
                    current_value = getattr(current_value, part)
                else:
                    current_value = None
                    break
            
            # Format the final value
            if current_value is None:
                return {'value': '', 'formatted': '', 'type': 'char'}
            elif hasattr(current_value, 'display_name'):
                # For recordsets, use display_name
                return {
                    'value': current_value.id if len(current_value) == 1 else [r.id for r in current_value],
                    'formatted': current_value.display_name if len(current_value) == 1 else ', '.join(current_value.mapped('display_name')),
                    'type': 'many2one' if len(current_value) == 1 else 'many2many'
                }
            elif isinstance(current_value, (list, tuple)):
                return {
                    'value': current_value,
                    'formatted': ', '.join(str(v) for v in current_value),
                    'type': 'list'
                }
            elif isinstance(current_value, bool):
                return {
                    'value': current_value,
                    'formatted': _('Yes') if current_value else _('No'),
                    'type': 'boolean'
                }
            elif isinstance(current_value, (int, float)):
                return {
                    'value': current_value,
                    'formatted': str(current_value),
                    'type': 'numeric'
                }
            else:
                return {
                    'value': current_value,
                    'formatted': str(current_value),
                    'type': 'char'
                }
                
        except Exception as e:
            _logger.error("Error formatting related field value for %s: %s", field_path, str(e))
            return {'value': '', 'formatted': '', 'type': 'char'}