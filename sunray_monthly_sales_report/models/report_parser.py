from odoo import models, api, fields

class ReportMonthlySales(models.AbstractModel):
    _name = 'report.sunray_monthly_sales_report.report_sales'
    _description = 'Monthly Sales Report Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        
        # Extract data from wizard
        form = data.get('form', {})
        date_start = form.get('date_start')
        date_end = form.get('date_end')
        user_ids = form.get('user_ids', [])
        month_name = form.get('month_name')
        year = form.get('year')

        domain = [
            ('date_order', '>=', date_start),
            ('date_order', '<=', date_end),
            ('state', 'in', ['sale', 'done'])
        ]
        
        if user_ids:
            domain.append(('user_id', 'in', user_ids))
            users = self.env['res.users'].browse(user_ids)
        else:
            # If no users selected, get all users who have sales in this period? or just all users?
            # Better to find distinct users from the sales to avoid showing empty users
            # Logic: Search sales first
            pass

        sale_orders = self.env['sale.order'].search(domain, order='user_id, date_order')
        
        # Group by Salesperson
        sales_by_user = {}
        for so in sale_orders:
            user = so.user_id
            if user not in sales_by_user:
                sales_by_user[user] = {
                    'orders': [],
                    'total_amount': 0.0,
                    'count': 0
                }
            sales_by_user[user]['orders'].append(so)
            sales_by_user[user]['total_amount'] += so.amount_total
            sales_by_user[user]['count'] += 1
            
        return {
            'doc_ids': docids,
            'doc_model': 'sunray.monthly.sales.report.wizard',
            'docs': self.env['sunray.monthly.sales.report.wizard'].browse(docids),
            'date_start': date_start,
            'date_end': date_end,
            'month_name': month_name,
            'year': year,
            'sales_by_user': sales_by_user,
            'company': self.env.company,
            'generated_on': fields.Datetime.now(),
        }
