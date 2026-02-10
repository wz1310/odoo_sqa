# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReportBuilderField(models.Model):
    _name = 'report.builder.field'
    _description = 'Report Builder Field Configuration'
    _order = 'sequence, id'
    _rec_name = 'field_label'

    # Relationship
    report_id = fields.Many2one(
        'report.builder', 
        string='Report', 
        required=True, 
        ondelete='cascade'
    )
    
    # Field Configuration
    field_id = fields.Many2one(
        'ir.model.fields',
        string='Field',
        ondelete='cascade',
        domain="[('model_id', '=', parent.model_id)]"
    )
    field_name = fields.Char('Field Name', help="Field name or field path for related fields (e.g., partner_id.name)")
    field_description = fields.Char('Field Description', required=True)
    field_type = fields.Char('Field Type', required=True)
    field_relation = fields.Char('Field Relation')
    is_related_field = fields.Boolean('Is Related Field', default=False)
    field_path = fields.Char('Field Path', help="Full path for related fields")
    
    # Display Configuration
    field_label = fields.Char(
        'Column Label', 
        help="Custom label for the column (uses field description if empty)"
    )
    sequence = fields.Integer('Sequence', default=10, help="Order of the field in the report")
    visible = fields.Boolean('Visible', default=True, help="Show this field in the report")
    
    # Formatting Options
    width = fields.Integer('Column Width', default=100, help="Width of the column in pixels")
    alignment = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right')
    ], default='left', string='Alignment')
    
    # Advanced Options
    aggregation = fields.Selection([
        ('none', 'None'),
        ('sum', 'Sum'),
        ('avg', 'Average'),
        ('count', 'Count'),
        ('min', 'Minimum'),
        ('max', 'Maximum')
    ], default='none', string='Aggregation', help="Mathematical operation to apply")
    
    format_string = fields.Char(
        'Format String', 
        help="Custom format string for the field (e.g., %.2f for decimals)"
    )
    
    # Filtering and Sorting
    sortable = fields.Boolean('Sortable', default=True, help="Allow sorting by this field")
    filterable = fields.Boolean('Filterable', default=True, help="Allow filtering by this field")
    searchable = fields.Boolean('Searchable', default=False, help="Include in global search")
    
    # Summation
    show_summation = fields.Boolean('Show Summation', default=False, help="Include this field in the summation row (for numeric fields only)")
    
    # Conditional Formatting
    conditional_format = fields.Boolean('Enable Conditional Formatting', default=False)
    condition_field = fields.Char('Condition Field', help="Field to base condition on")
    condition_operator = fields.Selection([
        ('>', 'Greater than'),
        ('<', 'Less than'),
        ('>=', 'Greater or equal'),
        ('<=', 'Less or equal'),
        ('=', 'Equal'),
        ('!=', 'Not equal'),
        ('contains', 'Contains'),
        ('not_contains', 'Does not contain')
    ], string='Condition Operator')
    condition_value = fields.Char('Condition Value')
    format_color = fields.Char('Text Color', default='#000000')
    format_bg_color = fields.Char('Background Color', default='#FFFFFF')
    

    
    @api.onchange('field_id')
    def _onchange_field_id(self):
        """Set default label when field changes."""
        if self.field_id:
            # Set field description
            self.field_description = self.field_id.field_description
            
            if not self.field_label:
                self.field_label = self.field_id.field_description
            
            # Set default aggregation for numeric fields
            if self.field_id.ttype in ['integer', 'float', 'monetary']:
                if self.aggregation == 'none':
                    self.aggregation = 'sum'
            
            # Set default alignment based on field type
            if self.field_id.ttype in ['integer', 'float', 'monetary']:
                self.alignment = 'right'
            elif self.field_id.ttype in ['boolean']:
                self.alignment = 'center'
            else:
                self.alignment = 'left'
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle both regular and related fields."""
        for vals in vals_list:
            # Handle related fields
            if vals.get('field_path') or '.' in vals.get('field_name', ''):
                vals['is_related_field'] = True
                if not vals.get('field_path'):
                    vals['field_path'] = vals.get('field_name')
                if not vals.get('field_name'):
                    vals['field_name'] = vals.get('field_path')
                # Don't require field_id for related fields
                vals.pop('field_id', None)
            else:
                # Regular field - populate from field_id if available
                if vals.get('field_id') and not vals.get('field_description'):
                    field = self.env['ir.model.fields'].browse(vals['field_id'])
                    vals['field_description'] = field.field_description
                    if not vals.get('field_name'):
                        vals['field_name'] = field.name
                    if not vals.get('field_type'):
                        vals['field_type'] = field.ttype
                    if not vals.get('field_relation'):
                        vals['field_relation'] = field.relation
        
        return super().create(vals_list)
    
    @api.constrains('width')
    def _check_width(self):
        """Validate column width."""
        for record in self:
            if record.width < 10:
                raise ValidationError(_("Column width must be at least 10 pixels"))
            if record.width > 1000:
                raise ValidationError(_("Column width cannot exceed 1000 pixels"))
    
    @api.constrains('sequence')
    def _check_sequence(self):
        """Validate sequence."""
        for record in self:
            if record.sequence < 0:
                raise ValidationError(_("Sequence must be a positive number"))
    
    def action_move_up(self):
        """Move field up in sequence."""
        self.ensure_one()
        prev_field = self.search([
            ('report_id', '=', self.report_id.id),
            ('sequence', '<', self.sequence)
        ], order='sequence desc', limit=1)
        
        if prev_field:
            prev_field.sequence, self.sequence = self.sequence, prev_field.sequence
        return True
    
    def action_move_down(self):
        """Move field down in sequence."""
        self.ensure_one()
        next_field = self.search([
            ('report_id', '=', self.report_id.id),
            ('sequence', '>', self.sequence)
        ], order='sequence asc', limit=1)
        
        if next_field:
            next_field.sequence, self.sequence = self.sequence, next_field.sequence
        return True
    
    def get_formatted_value(self, value, record=None):
        """Get formatted value based on field configuration."""
        if value is None or value is False:
            return ''
        
        # Apply custom format string if provided
        if self.format_string:
            try:
                if self.field_type in ['float', 'monetary']:
                    return self.format_string % float(value)
                elif self.field_type == 'integer':
                    return self.format_string % int(value)
                else:
                    return self.format_string % value
            except (ValueError, TypeError):
                pass
        
        # Default formatting based on field type
        if self.field_type == 'boolean':
            return _('Yes') if value else _('No')
        elif self.field_type == 'selection' and record:
            # Get selection label
            try:
                field_obj = record._fields.get(self.field_name)
                if field_obj and hasattr(field_obj, 'selection'):
                    selection_dict = dict(field_obj.selection)
                    return selection_dict.get(value, value)
            except:
                pass
        elif self.field_type in ['many2one'] and hasattr(value, 'display_name'):
            return value.display_name
        elif self.field_type in ['one2many', 'many2many']:
            if hasattr(value, 'mapped'):
                return ', '.join(value.mapped('display_name'))
        elif self.field_type == 'monetary':
            # Format monetary values
            if record and hasattr(record, 'currency_id') and record.currency_id:
                return record.currency_id.format(value)
            else:
                return "{:.2f}".format(value)
        elif self.field_type == 'float':
            return "{:.2f}".format(value)
        
        return str(value)

