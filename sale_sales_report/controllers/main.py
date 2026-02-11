from odoo import http
from odoo.http import request
from collections import defaultdict

class SalesIntelligenceController(http.Controller):
    @http.route('/sales_report/report_html', type='json', auth='user')
    def get_report_html(self, month=None, year=None, groupby='customer'):
        # Filter Order yang sudah dikonfirmasi
        domain = [('state', 'in', ['sale', 'done'])]
        sales_orders = request.env['sale.order'].sudo().search(domain)
        
        report_data = defaultdict(lambda: {'total_amount': 0.0, 'lines': []})
        
        for order in sales_orders:
            for line in order.order_line:
                # Logika Dinamis Grouping
                if groupby == 'order':
                    group_key = order.name
                elif groupby == 'product':
                    group_key = line.product_id.display_name or "Unknown Product"
                else: # Default: Customer
                    group_key = order.partner_id.name or "Unknown Customer"
                
                report_data[group_key]['total_amount'] += line.price_subtotal
                report_data[group_key]['lines'].append({
                    'order_id': order.id,
                    'ref': order.name,
                    'description': line.name or '',
                    'salesperson': order.user_id.name or '',
                    'qty': line.product_uom_qty,
                    'delivered': line.qty_delivered,
                    'invoiced': line.qty_invoiced,
                    'to_invoice': line.qty_to_invoice,
                    'subtotal': line.price_subtotal,
                })

        return request.env['ir.ui.view']._render_template(
            'sale_sales_report.report_sales_html_screen', {
                'report_data': dict(report_data),
                'groupby': groupby,
                'month_name': "Februari",
                'year': 2026,
                'base_url': request.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            }
        )