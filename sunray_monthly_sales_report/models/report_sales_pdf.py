from odoo import models, api

class MonthlySalesReportPDF(models.AbstractModel):
    _name = 'report.sunray_monthly_sales_report.report_sales'
    _description = 'Monthly Sales Report PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        # When calling from controller with data, docids is just [company_id]
        # and data contains our custom dictionary.
        
        # If data is None (e.g. printed from wizard without custom data path?), 
        # we might need fallback logic, but our controller always passes data.
        if not data:
            data = {}
            
        # We need to ensure the keys from 'data' are top-level variables
        return {
            'doc_ids': docids,
            'doc_model': 'res.company', 
            'docs': self.env['res.company'].browse(docids),
            'sales_by_user': data.get('sales_by_user'),
            'month': data.get('month'),
            'month_name': data.get('month_name'),
            'year': data.get('year'),
            'date_start': data.get('date_start'),
            'date_end': data.get('date_end'),
            'company': self.env['res.company'].browse(data.get('company').id) if data.get('company') else self.env.company,
            'data': data,
        }
