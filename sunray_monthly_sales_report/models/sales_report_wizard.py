from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class MonthlySalesReportWizard(models.TransientModel):
    _name = 'sunray.monthly.sales.report.wizard'
    _description = 'Monthly Sales Report Wizard'

    def _get_default_year(self):
        return str(datetime.now().year)

    def _get_default_month(self):
        return str(datetime.now().month)

    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True, default=_get_default_month)
    
    year = fields.Selection([(str(num), str(num)) for num in range(2020, 2031)], string='Year', required=True, default=_get_default_year)
    
    user_ids = fields.Many2many('res.users', string='Salespersons', help="Select salespersons to generate report for. Leave empty for all.")
    
    def action_view_onscreen(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'sunray_monthly_sales_report.client_action',
            'name': 'Monthly Sales Report',
            'context': {
                'month': self.month,
                'year': self.year,
                'user_ids': self.user_ids.ids if self.user_ids else [],
            }
        }
    
    def action_print_report(self):
        self.ensure_one()
        # Calculate dates
        date_start = datetime.strptime(f'{self.year}-{self.month}-01', '%Y-%m-%d').date()
        date_end = date_start + relativedelta(months=1, days=-1)
        
        users = self.user_ids or self.env['res.users'].search([])
        
        # Filter users who actually have sales in that period to avoid empty pages?
        # Maybe let the report handle it or filter here.
        # Let's pass the wizard ID and handle logic in the report (or pass data).
        
        data = {
            'form': {
                'date_start': date_start,
                'date_end': date_end,
                'user_ids': users.ids,
                'month_name': dict(self._fields['month'].selection).get(self.month),
                'year': self.year,
            }
        }
        
        return self.env.ref('sunray_monthly_sales_report.action_report_monthly_sales').report_action(self, data=data)
