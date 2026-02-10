# -*- coding: utf-8 -*-

import json
import base64
import io
from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import xlsxwriter

_logger = logging.getLogger(__name__)


class ReportBuilder(models.Model):
    _name = 'report.builder'
    _description = 'Dynamic Report Builder'
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char('Report Name', required=True, help="Name of the custom report")
    description = fields.Text('Description', help="Description of the report purpose")
    
    # Model Configuration
    model_id = fields.Many2one(
        'ir.model', 
        string='Primary Model', 
        required=True,
        ondelete='cascade',
        domain=[('transient', '=', False)],
        help="Main model for the report"
    )
    model_name = fields.Char(related='model_id.model', store=True, readonly=True)
    
    # Report Fields Configuration
    field_ids = fields.One2many(
        'report.builder.field', 
        'report_id', 
        string='Report Fields',
        help="Fields to include in the report"
    )
    
    # Filters and Configuration
    filter_domain = fields.Text(
        'Domain Filter', 
        default='[]',
        help="Domain filter for records (JSON format)"
    )
    group_by_field = fields.Many2one(
        'ir.model.fields',
        string='Group By Field',
        ondelete='set null',
        domain="[('model_id', '=', model_id)]",
        help="Field to group records by"
    )
    
    # Report Settings
    max_records = fields.Integer(
        'Max Records', 
        default=1000,
        help="Maximum number of records to include"
    )
    auto_refresh = fields.Boolean(
        'Auto Refresh', 
        default=False,
        help="Automatically refresh report data"
    )
    
    # Status and Access
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], default='draft', string='Status')
    
    active = fields.Boolean('Active', default=True)
    
    # Computed Fields
    field_count = fields.Integer(
        'Field Count', 
        compute='_compute_field_count',
        help="Number of fields in the report"
    )
    last_generated = fields.Datetime('Last Generated', readonly=True)
    record_count = fields.Integer('Record Count', compute='_compute_record_count')
    
    # Company and User
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users', 
        string='Created By', 
        default=lambda self: self.env.user,
        readonly=True
    )
    
    # PDF Export Configuration
    pdf_orientation = fields.Selection([
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ], string='PDF Orientation', default='portrait', help="Page orientation for PDF export")
    
    @api.depends('field_ids')
    def _compute_field_count(self):
        """Compute the number of fields in the report."""
        for record in self:
            record.field_count = len(record.field_ids)
    
    @api.depends('model_id', 'filter_domain')
    def _compute_record_count(self):
        """Compute the number of records that match the filter."""
        for record in self:
            if record.model_id:
                try:
                    domain = json.loads(record.filter_domain or '[]')
                    if record.model_name:
                        model = self.env[record.model_name]
                        record.record_count = model.search_count(domain)
                    else:
                        record.record_count = 0
                except (json.JSONDecodeError, KeyError, ValueError):
                    record.record_count = 0
            else:
                record.record_count = 0
    
    @api.constrains('filter_domain')
    def _check_filter_domain(self):
        """Validate that filter domain is valid JSON."""
        for record in self:
            if record.filter_domain:
                try:
                    json.loads(record.filter_domain)
                except json.JSONDecodeError:
                    raise ValidationError(_("Invalid JSON format in Domain Filter"))
    
    @api.constrains('max_records')
    def _check_max_records(self):
        """Validate max_records value."""
        for record in self:
            if record.max_records <= 0:
                raise ValidationError(_("Max Records must be greater than 0"))
            if record.max_records > 10000:
                raise ValidationError(_("Max Records cannot exceed 10,000 for performance reasons"))
    
    def action_activate(self):
        """Activate the report."""
        self.ensure_one()
        if not self.field_ids:
            raise UserError(_("Cannot activate report without fields. Please add at least one field."))
        self.state = 'active'
        return True
    
    def action_draft(self):
        """Set report to draft."""
        self.state = 'draft'
        return True
    
    def action_archive(self):
        """Archive the report."""
        self.state = 'archived'
        self.active = False
        return True
    
    def action_duplicate(self):
        """Duplicate the report with a new name."""
        self.ensure_one()
        new_name = _("Copy of %s") % self.name
        copy_vals = {
            'name': new_name,
            'state': 'draft'
        }
        new_report = self.copy(copy_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Report Builder'),
            'res_model': 'report.builder',
            'res_id': new_report.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_open_builder(self):
        """Open the report builder interface."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'report_builder_widget',
            'target': 'fullscreen',
            'context': {
                'report_id': self.id,
                'model_id': self.model_id.id,
            }
        }

    def action_view_report(self):
        """Open the report display interface with filtering capabilities."""
        self.ensure_one()
        if not self.field_ids:
            raise UserError(_("Cannot view report without fields. Please add fields first."))
        
        return {
            'name': _('%s - Report View') % self.name,
            'type': 'ir.actions.client',
            'tag': 'report_display_widget',
            'target': 'current',
            'context': {
                'report_id': self.id,
            }
        }
    
    def action_preview_report(self):
        """Preview the report data."""
        self.ensure_one()
        if not self.field_ids:
            raise UserError(_("Cannot preview report without fields. Please add fields first."))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'report_preview_widget',
            'target': 'new',
            'context': {
                'report_id': self.id,
            }
        }
    
    def action_export_excel(self):
        """Export report to Excel format."""
        self.ensure_one()
        if not self.field_ids:
            raise UserError(_("Cannot export report without fields. Please add fields first."))
        
        # Get filter context
        field_filters = self.env.context.get('field_filters', {})
        date_filters = self.env.context.get('date_filters', {})
        
        # Generate Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(self.name[:31])  # Excel sheet name limit
        
        # Get company information
        company = self.company_id or self.env.company
        
        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#2c3e50'
        })
        
        company_format = workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#495057'
        })
        
        report_name_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#007bff'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#007bff',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True
        })
        
        # Merge cells for header section
        num_cols = len(self.field_ids) + 1  # +1 for serial number
        
        # Row counter
        current_row = 0
        
        # Company Name (main heading)
        worksheet.merge_range(current_row, 0, current_row, num_cols - 1, company.name, title_format)
        worksheet.set_row(current_row, 20)
        current_row += 1
        
        # Company Address
        if company.street or company.street2:
            address = ', '.join(filter(None, [company.street, company.street2]))
            worksheet.merge_range(current_row, 0, current_row, num_cols - 1, address, company_format)
            worksheet.set_row(current_row, 15)
            current_row += 1
        
        # City, Zip, Country
        if company.city or company.zip or company.country_id:
            city_line = ', '.join(filter(None, [company.city, company.zip, company.country_id.name if company.country_id else '']))
            worksheet.merge_range(current_row, 0, current_row, num_cols - 1, city_line, company_format)
            worksheet.set_row(current_row, 15)
            current_row += 1
        
        # Phone and Tax ID
        contact_info = []
        if company.phone:
            contact_info.append('Phone: %s' % company.phone)
        if company.vat:
            contact_info.append('TIN: %s' % company.vat)
        
        if contact_info:
            worksheet.merge_range(current_row, 0, current_row, num_cols - 1, ' | '.join(contact_info), company_format)
            worksheet.set_row(current_row, 15)
            current_row += 1
        
        # Empty row
        current_row += 1
        
        # Report Name
        worksheet.merge_range(current_row, 0, current_row, num_cols - 1, self.name, report_name_format)
        worksheet.set_row(current_row, 18)
        current_row += 1
        
        # Empty row before data
        current_row += 1
        
        # Write headers with serial number
        col = 0
        worksheet.write(current_row, col, '#', header_format)
        worksheet.set_column(col, col, 5)
        col += 1
        
        for field_config in self.field_ids.sorted('sequence'):
            worksheet.write(current_row, col, field_config.field_label or field_config.field_name, header_format)
            # Set column width based on field type
            if field_config.field_type in ['text', 'html']:
                worksheet.set_column(col, col, 30)
            elif field_config.field_type in ['datetime', 'date']:
                worksheet.set_column(col, col, 15)
            else:
                worksheet.set_column(col, col, 15)
            col += 1
        
        current_row += 1
        
        # Get and write data with serial numbers
        data = self._get_report_data()
        
        # Apply selection field filters
        for field_name, filter_value in field_filters.items():
            if filter_value:
                data = [rec for rec in data if field_name in rec and 
                       str(rec[field_name].get('value', '')).lower().find(str(filter_value).lower()) >= 0]
        
        # Apply date range filters
        for field_name, date_range in date_filters.items():
            from_date = date_range.get('from')
            to_date = date_range.get('to')
            
            if from_date and to_date:
                filtered_data = []
                for rec in data:
                    if field_name in rec:
                        field_data = rec[field_name]
                        
                        # Get the raw value (yyyy-mm-dd format)
                        raw_date_value = ''
                        if field_data and isinstance(field_data, dict):
                            raw_date_value = field_data.get('value', '')
                        else:
                            raw_date_value = str(field_data) if field_data else ''
                        
                        if raw_date_value:
                            # Extract date part (remove time if present)
                            record_date = raw_date_value.split(' ')[0]
                            
                            # Convert dd/mm/yyyy to yyyy-mm-dd if needed
                            if '/' in record_date:
                                parts = record_date.split('/')
                                if len(parts) == 3:
                                    record_date = '%s-%s-%s' % (parts[2], parts[1], parts[0])
                            
                            # Compare dates in yyyy-mm-dd format
                            if record_date >= from_date and record_date <= to_date:
                                filtered_data.append(rec)
                        
                data = filtered_data
        
        serial_num = 1
        for record_data in data:
            col = 0
            # Write serial number
            worksheet.write(current_row, col, serial_num, cell_format)
            col += 1
            
            for field_config in self.field_ids.sorted('sequence'):
                field_name = field_config.field_name
                field_data = record_data.get(field_name, {})
                
                # Extract formatted value from the structured data
                if isinstance(field_data, dict):
                    # Use the formatted value directly from our data structure
                    value = field_data.get('formatted', '')
                else:
                    # Fallback for simple values
                    value = str(field_data) if field_data is not None else ''
                
                # Write clean formatted value to Excel
                worksheet.write(current_row, col, value, cell_format)
                col += 1
            current_row += 1
            serial_num += 1
        
        # Add summation row if any field has show_summation enabled
        summation_fields = [f for f in self.field_ids.sorted('sequence') if f.show_summation]
        if summation_fields:
            current_row += 1  # Add empty row before summation
            
            # Calculate totals for each summation field
            summation_totals = {}
            for field_config in self.field_ids.sorted('sequence'):
                if field_config.show_summation and field_config.field_type in ['integer', 'float', 'monetary']:
                    field_name = field_config.field_name
                    total = 0.0
                    
                    for record_data in data:
                        field_data = record_data.get(field_name, {})
                        if isinstance(field_data, dict):
                            value = field_data.get('value', 0)
                        else:
                            value = field_data if field_data is not None else 0
                        
                        try:
                            total += float(value)
                        except (ValueError, TypeError):
                            pass
                    
                    summation_totals[field_name] = total
            
            # Format for summation row
            summation_format = workbook.add_format({
                'bold': True,
                'border': 1,
                'align': 'right',
                'valign': 'top',
                'bg_color': '#e9ecef',
                'font_size': 10
            })
            
            summation_label_format = workbook.add_format({
                'bold': True,
                'border': 1,
                'align': 'center',
                'valign': 'top',
                'bg_color': '#e9ecef',
                'font_size': 10
            })
            
            # Write summation row
            col = 0
            worksheet.write(current_row, col, 'Total', summation_label_format)
            col += 1
            
            for field_config in self.field_ids.sorted('sequence'):
                if field_config.field_name in summation_totals:
                    total = summation_totals[field_config.field_name]
                    if field_config.field_type in ['monetary', 'float']:
                        formatted_total = '{:,.2f}'.format(total)
                    else:
                        formatted_total = '{:,}'.format(int(total))
                    worksheet.write(current_row, col, formatted_total, summation_format)
                else:
                    worksheet.write(current_row, col, '', summation_format)
                col += 1
        
        # Add footer information
        current_row += 2
        footer_format = workbook.add_format({
            'font_size': 9,
            'italic': True,
            'font_color': '#6c757d'
        })
        
        # Generated date/time
        from datetime import datetime
        generated_text = 'Generated on %s' % datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        worksheet.merge_range(current_row, 0, current_row, num_cols - 1, generated_text, footer_format)
        
        workbook.close()
        output.seek(0)
        
        # Update last generated timestamp
        self.last_generated = fields.Datetime.now()
        
        # Create attachment
        filename = "{}_{}.xlsx".format(self.name, fields.Date.today().strftime('%Y%m%d'))
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment.id),
            'target': 'new',
        }
    
    def action_export_pdf(self):
        """Export report to PDF format."""
        self.ensure_one()
        if not self.field_ids:
            raise UserError(_("Cannot export report without fields. Please add fields first."))
        
        # Get filter context
        field_filters = self.env.context.get('field_filters', {})
        date_filters = self.env.context.get('date_filters', {})
        group_by = self.env.context.get('group_by')
        
        # Get report data
        data = self._get_report_data()
        
        # Apply selection field filters
        for field_name, filter_value in field_filters.items():
            if filter_value:
                data = [rec for rec in data if field_name in rec and 
                       str(rec[field_name].get('value', '')).lower().find(str(filter_value).lower()) >= 0]
        
        # Apply date range filters
        for field_name, date_range in date_filters.items():
            from_date = date_range.get('from')
            to_date = date_range.get('to')
            
            if from_date and to_date:
                filtered_data = []
                for rec in data:
                    if field_name in rec:
                        field_data = rec[field_name]
                        
                        # Get the raw value (yyyy-mm-dd format)
                        raw_date_value = ''
                        if field_data and isinstance(field_data, dict):
                            raw_date_value = field_data.get('value', '')
                        else:
                            raw_date_value = str(field_data) if field_data else ''
                        
                        if raw_date_value:
                            # Extract date part (remove time if present)
                            record_date = raw_date_value.split(' ')[0]
                            
                            # Convert dd/mm/yyyy to yyyy-mm-dd if needed
                            if '/' in record_date:
                                parts = record_date.split('/')
                                if len(parts) == 3:
                                    record_date = '%s-%s-%s' % (parts[2], parts[1], parts[0])
                            
                            # Compare dates in yyyy-mm-dd format
                            if record_date >= from_date and record_date <= to_date:
                                filtered_data.append(rec)
                        
                data = filtered_data
        
        # Generate PDF using reportlab
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER
        from reportlab.pdfgen import canvas
        
        output = io.BytesIO()
        
        # Get company information
        company = self.company_id or self.env.company
        
        # Custom canvas class for headers and footers
        class PDFCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                canvas.Canvas.__init__(self, *args, **kwargs)
                self.pages = []
                self.company = company
                self.report_name = self.report_name_value
                
            def showPage(self):
                self.pages.append(dict(self.__dict__))
                self._startPage()
                
            def save(self):
                page_count = len(self.pages)
                for page_num, page in enumerate(self.pages, 1):
                    self.__dict__.update(page)
                    self.draw_header_footer(page_num, page_count)
                    canvas.Canvas.showPage(self)
                canvas.Canvas.save(self)
                
            def draw_header_footer(self, page_num, page_count):
                # Header - using sans-serif fonts similar to Odoo's Lato
                self.saveState()
                
                # Try to register and use Lato font (similar to Odoo), fallback to Helvetica
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                import os
                
                font_bold = 'Helvetica-Bold'
                font_regular = 'Helvetica'
                
                # Try to load Lato font if available in system
                try:
                    # Common font paths
                    lato_paths = [
                        '/usr/share/fonts/truetype/lato/Lato-Bold.ttf',
                        'C:\\Windows\\Fonts\\Lato-Bold.ttf',
                        '/System/Library/Fonts/Lato-Bold.ttf',
                    ]
                    
                    for path in lato_paths:
                        if os.path.exists(path):
                            pdfmetrics.registerFont(TTFont('Lato-Bold', path))
                            font_bold = 'Lato-Bold'
                            break
                    
                    lato_regular_paths = [
                        '/usr/share/fonts/truetype/lato/Lato-Regular.ttf',
                        'C:\\Windows\\Fonts\\Lato-Regular.ttf',
                        '/System/Library/Fonts/Lato-Regular.ttf',
                    ]
                    
                    for path in lato_regular_paths:
                        if os.path.exists(path):
                            pdfmetrics.registerFont(TTFont('Lato', path))
                            font_regular = 'Lato'
                            break
                except:
                    # If Lato not available, use Helvetica (clean sans-serif similar to Lato)
                    pass
                
                self.setFont(font_bold, 14)
                
                # Company name
                self.drawCentredString(self._pagesize[0] / 2, self._pagesize[1] - 0.5 * inch, self.company.name)
                
                # Company details
                self.setFont(font_regular, 9)
                y_position = self._pagesize[1] - 0.7 * inch
                
                if self.company.street or self.company.street2:
                    address = ', '.join(filter(None, [self.company.street, self.company.street2]))
                    self.drawCentredString(self._pagesize[0] / 2, y_position, address)
                    y_position -= 0.15 * inch
                
                if self.company.city or self.company.zip or self.company.country_id:
                    city_line = ', '.join(filter(None, [self.company.city, self.company.zip, self.company.country_id.name if self.company.country_id else '']))
                    self.drawCentredString(self._pagesize[0] / 2, y_position, city_line)
                    y_position -= 0.15 * inch
                
                contact_info = []
                if self.company.phone:
                    contact_info.append(f"Phone: {self.company.phone}")
                if self.company.vat:
                    contact_info.append(f"TIN: {self.company.vat}")
                
                if contact_info:
                    self.drawCentredString(self._pagesize[0] / 2, y_position, ' | '.join(contact_info))
                    y_position -= 0.2 * inch
                
                # Report name
                self.setFont(font_bold, 12)
                self.drawCentredString(self._pagesize[0] / 2, y_position, self.report_name)
                
                # Draw line under header
                self.setStrokeColor(colors.HexColor('#007bff'))
                self.setLineWidth(2)
                self.line(0.5 * inch, self._pagesize[1] - 1.5 * inch, 
                         self._pagesize[0] - 0.5 * inch, self._pagesize[1] - 1.5 * inch)
                
                # Footer
                self.setFont(font_regular, 8)
                self.setFillColor(colors.grey)
                
                # Page number
                footer_text = f"Page {page_num} of {page_count}"
                self.drawCentredString(self._pagesize[0] / 2, 0.5 * inch, footer_text)
                
                # Generated date
                from datetime import datetime
                generated_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.drawRightString(self._pagesize[0] - 0.5 * inch, 0.5 * inch, generated_text)
                
                # Company name in footer
                self.drawString(0.5 * inch, 0.5 * inch, self.company.name)
                
                self.restoreState()
        
        # Determine page orientation based on user preference
        page_size = A4
        if self.pdf_orientation == 'landscape':
            page_size = landscape(A4)
        
        doc = SimpleDocTemplate(
            output, 
            pagesize=page_size,
            topMargin=1.7 * inch,  # Space for header
            bottomMargin=0.75 * inch,  # Space for footer
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch
        )
        
        # Store report name in canvas class
        PDFCanvas.report_name_value = self.name
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Prepare grouped data if groupby is applied
        grouped_data = {}
        if group_by and group_by in [f.field_name for f in self.field_ids]:
            for record in data:
                group_key = record.get(group_by, {}).get('formatted', 'Undefined')
                if group_key not in grouped_data:
                    grouped_data[group_key] = []
                grouped_data[group_key].append(record)
            # Use grouped data for display
            use_grouping = True
        else:
            use_grouping = False
        
        # Prepare table data
        table_data = []
        
        # Add headers with serial number
        headers = ['#']
        for field_config in self.field_ids.sorted('sequence'):
            headers.append(field_config.field_label or field_config.field_description)
        table_data.append(headers)
        
        # Generate table rows based on grouping
        serial_number = 1
        
        if use_grouping:
            # Add grouped data rows
            for group_key in sorted(grouped_data.keys()):
                # Add group header row
                group_header_row = [{'text': f'{group_key}', 'colspan': len(headers)}]
                table_data.append(group_header_row)
                
                # Add records in this group
                for record_data in grouped_data[group_key]:
                    row = [str(serial_number)]
                    for field_config in self.field_ids.sorted('sequence'):
                        field_name = field_config.field_name
                        value_dict = record_data.get(field_name, {})
                        
                        if isinstance(value_dict, dict):
                            formatted_value = value_dict.get('formatted', '')
                        else:
                            formatted_value = str(value_dict) if value_dict is not None else ''
                        
                        row.append(formatted_value)
                    table_data.append(row)
                    serial_number += 1
        else:
            # Add data rows without grouping
            for record_data in data:
                row = [str(serial_number)]
                for field_config in self.field_ids.sorted('sequence'):
                    field_name = field_config.field_name
                    value_dict = record_data.get(field_name, {})
                    
                    if isinstance(value_dict, dict):
                        formatted_value = value_dict.get('formatted', '')
                    else:
                        formatted_value = str(value_dict) if value_dict is not None else ''
                    
                    row.append(formatted_value)
                table_data.append(row)
                serial_number += 1
        
        # Add summation row if any field has show_summation enabled
        summation_fields = [f for f in self.field_ids.sorted('sequence') if f.show_summation]
        if summation_fields:
            summation_row = ['Total']
            summation_totals = {}
            
            # Calculate totals for each summation field
            for field_config in self.field_ids.sorted('sequence'):
                if field_config.show_summation and field_config.field_type in ['integer', 'float', 'monetary']:
                    field_name = field_config.field_name
                    total = 0.0
                    
                    for record_data in data:
                        value_dict = record_data.get(field_name, {})
                        if isinstance(value_dict, dict):
                            value = value_dict.get('value', 0)
                        else:
                            value = value_dict if value_dict is not None else 0
                        
                        try:
                            total += float(value)
                        except (ValueError, TypeError):
                            pass
                    
                    summation_totals[field_name] = total
            
            # Build summation row
            for field_config in self.field_ids.sorted('sequence'):
                if field_config.field_name in summation_totals:
                    total = summation_totals[field_config.field_name]
                    if field_config.field_type in ['monetary', 'float']:
                        summation_row.append('{:,.2f}'.format(total))
                    else:
                        summation_row.append('{:,}'.format(int(total)))
                else:
                    summation_row.append('')
            
            table_data.append(summation_row)
        
        # Create table with proper handling for grouped data
        if use_grouping:
            # Build table with special handling for group headers
            from reportlab.platypus import Paragraph
            
            processed_data = []
            for row in table_data:
                if isinstance(row[0], dict) and 'colspan' in row[0]:
                    # This is a group header
                    # Use Helvetica-Bold for group headers (similar to Odoo's Lato font)
                    group_style = ParagraphStyle(
                        'GroupHeader',
                        parent=styles['Normal'],
                        fontSize=10,
                        textColor=colors.HexColor('#2c3e50'),
                        fontName='Helvetica-Bold',
                        alignment=TA_CENTER,
                    )
                    processed_data.append([Paragraph(row[0]['text'], group_style)])
                else:
                    processed_data.append(row)
            
            table = Table(processed_data)
            
            # Apply styles with span for group headers
            style_commands = [
                # Header styling (first row)
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data styling
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
            
            # Find and style group headers
            row_idx = 1
            for row in table_data[1:]:  # Skip header row
                if isinstance(row[0], dict) and 'colspan' in row[0]:
                    # Group header styling
                    style_commands.extend([
                        ('SPAN', (0, row_idx), (-1, row_idx)),
                        ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#e9ecef')),
                        ('ALIGN', (0, row_idx), (-1, row_idx), 'LEFT'),
                        ('LEFTPADDING', (0, row_idx), (-1, row_idx), 10),
                        ('TOPPADDING', (0, row_idx), (-1, row_idx), 8),
                        ('BOTTOMPADDING', (0, row_idx), (-1, row_idx), 8),
                    ])
                else:
                    # Regular data row
                    style_commands.extend([
                        ('ALIGN', (0, row_idx), (0, row_idx), 'CENTER'),  # Serial number
                        ('BACKGROUND', (0, row_idx), (-1, row_idx), 
                         colors.white if row_idx % 2 == 0 else colors.HexColor('#f8f9fa')),
                    ])
                row_idx += 1
            
            table.setStyle(TableStyle(style_commands))
        else:
            # Regular table without grouping
            table = Table(table_data)
            
            # Determine if we have a summation row
            has_summation = len(summation_fields) > 0
            last_row_idx = len(table_data) - 1
            
            style_commands = [
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data styling (exclude last row if summation exists)
                ('BACKGROUND', (0, 1), (-1, last_row_idx if not has_summation else last_row_idx - 1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, last_row_idx if not has_summation else last_row_idx - 1), colors.black),
                ('ALIGN', (0, 1), (0, last_row_idx if not has_summation else last_row_idx - 1), 'CENTER'),  # Serial number center aligned
                ('FONTNAME', (0, 1), (-1, last_row_idx if not has_summation else last_row_idx - 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, last_row_idx if not has_summation else last_row_idx - 1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors (exclude summation row)
                ('ROWBACKGROUNDS', (0, 1), (-1, last_row_idx if not has_summation else last_row_idx - 1), 
                 [colors.white, colors.HexColor('#f8f9fa')]),
            ]
            
            # Add summation row styling if exists
            if has_summation:
                style_commands.extend([
                    ('BACKGROUND', (0, last_row_idx), (-1, last_row_idx), colors.HexColor('#e9ecef')),
                    ('TEXTCOLOR', (0, last_row_idx), (-1, last_row_idx), colors.black),
                    ('FONTNAME', (0, last_row_idx), (-1, last_row_idx), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, last_row_idx), (-1, last_row_idx), 9),
                    ('ALIGN', (0, last_row_idx), (0, last_row_idx), 'CENTER'),
                    ('TOPPADDING', (0, last_row_idx), (-1, last_row_idx), 8),
                    ('BOTTOMPADDING', (0, last_row_idx), (-1, last_row_idx), 8),
                ])
            
            table.setStyle(TableStyle(style_commands))
        
        elements.append(table)
        
        # Build PDF with custom canvas
        doc.build(elements, canvasmaker=PDFCanvas)
        output.seek(0)
        
        # Update last generated timestamp
        self.last_generated = fields.Datetime.now()
        
        # Create attachment
        filename = "{}_{}.pdf".format(self.name, fields.Date.today().strftime('%Y%m%d'))
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment.id),
            'target': 'new',
        }
    
    def _get_report_data(self):
        """Get the actual data for the report."""
        self.ensure_one()
        if not self.model_name or not self.field_ids:
            return []
        
        try:
            domain = json.loads(self.filter_domain or '[]')
        except json.JSONDecodeError:
            domain = []
        
        # Search records
        model = self.env[self.model_name]
        records = model.search(domain, limit=self.max_records)
        
        if not records:
            return []
        
        # Prepare field paths for export (following Odoo's export approach)
        field_paths = []
        field_config_map = {}
        
        for field_config in self.field_ids.sorted('sequence'):
            field_name = field_config.field_name
            # Split field path into components (e.g., 'partner_id.name' -> ['partner_id', 'name'])
            path_parts = field_name.split('.')
            field_paths.append(path_parts)
            field_config_map[field_name] = field_config
        
        # Use Odoo's export_rows method to get properly formatted data
        try:
            export_data = records._export_rows(field_paths)
        except Exception as e:
            _logger.error("Error exporting data: %s", str(e))
            return []
        
        # Convert export data to our format
        data = []
        for row_index, row_data in enumerate(export_data):
            record_data = {}
            
            # Add record ID
            if row_index < len(records):
                record_data['id'] = records[row_index].id
            
            for i, field_config in enumerate(self.field_ids.sorted('sequence')):
                field_name = field_config.field_name
                raw_value = row_data[i] if i < len(row_data) else ''
                
                # Format the value properly based on Odoo's export format
                # IMPORTANT: Both value and formatted must be JSON-serializable
                if isinstance(raw_value, tuple) and len(raw_value) == 2:
                    # Handle (model, id) tuples from many2one fields
                    formatted_value = str(raw_value[1]) if raw_value[1] else ''
                    actual_value = str(raw_value[1]) if raw_value[1] else ''
                elif hasattr(raw_value, 'mapped') and hasattr(raw_value, '_name'):
                    # Handle recordset objects (many2many, one2many)
                    formatted_value = ', '.join(raw_value.mapped('display_name')) if raw_value else ''
                    actual_value = formatted_value  # Use same as formatted to ensure JSON serializable
                elif isinstance(raw_value, (datetime, date)):
                    # Handle datetime and date objects
                    # Store original in yyyy-mm-dd format for filtering, format display as dd/mm/yyyy
                    if isinstance(raw_value, datetime):
                        actual_value = raw_value.strftime('%Y-%m-%d')  # Keep yyyy-mm-dd for filtering
                        formatted_value = raw_value.strftime('%d/%m/%Y')  # Display format
                    else:
                        actual_value = raw_value.strftime('%Y-%m-%d')  # Keep yyyy-mm-dd for filtering
                        formatted_value = raw_value.strftime('%d/%m/%Y')  # Display format
                elif isinstance(raw_value, (int, float)) and field_config.field_type in ('monetary', 'float'):
                    # Handle monetary and float fields - format with commas and 2 decimals
                    actual_value = raw_value
                    formatted_value = "{:,.2f}".format(float(raw_value))
                else:
                    # Handle simple values (char, integer, float, boolean, etc.)
                    formatted_value = str(raw_value) if raw_value is not None else ''
                    actual_value = formatted_value  # Use formatted string to ensure JSON serializable
                
                record_data[field_name] = {
                    'value': actual_value,
                    'formatted': formatted_value,
                    'type': field_config.field_type or 'char'
                }
            
            data.append(record_data)
        
        return data
    
    @api.model
    def get_available_models(self):
        """Get list of available models for report building."""
        models = self.env['ir.model'].search([
            ('transient', '=', False),
        ], order='name')
        
        # Filter out models that shouldn't be used for reports
        excluded_models = [
            'ir.', 'res.config', 'wizard.', 'temp.', 'report.',
            'base.', 'mail.thread', 'portal.'
        ]
        
        filtered_models = []
        for model in models:
            # Skip models that start with excluded prefixes
            if any(model.model.startswith(prefix) for prefix in excluded_models):
                continue
            # Skip models without proper access
            try:
                self.env[model.model].check_access_rights('read', raise_exception=True)
                filtered_models.append(model)
            except:
                continue
        
        return [{
            'id': model.id,
            'name': model.name,
            'model': model.model,
            'description': model.info or model.name,
        } for model in filtered_models]
    
    @api.model
    def get_model_fields(self, model_id):
        """Get available fields for a specific model."""
        if not model_id:
            return []
        
        model = self.env['ir.model'].browse(model_id)
        if not model.exists():
            return []
        
        fields_data = self.env['ir.model.fields'].search([
            ('model_id', '=', model_id),
            ('store', '=', True),
            ('name', 'not in', ['__last_update', 'write_uid', 'write_date', 'create_uid']),
        ], order='field_description')
        
        field_list = []
        for field in fields_data:
            field_info = {
                'id': field.id,
                'name': field.name,
                'field_description': field.field_description,
                'ttype': field.ttype,
                'relation': field.relation,
                'required': field.required,
                'readonly': field.readonly,
                'help': field.help or '',
            }
            field_list.append(field_info)
        
        return field_list