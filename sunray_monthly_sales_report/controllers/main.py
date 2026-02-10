from odoo import http, fields
from odoo.http import request, content_disposition
import io
import xlsxwriter
from datetime import datetime
from dateutil.relativedelta import relativedelta

class MonthlySalesReportController(http.Controller):

    def _get_report_data(self, month=None, year=None, user_ids=None, date_start=None, date_end=None):
        month_name = ""
        
        # Priority 1: Date Range Provided
        if date_start and date_end:
            _start = datetime.strptime(date_start, '%Y-%m-%d').date()
            _end = datetime.strptime(date_end, '%Y-%m-%d').date()
            # If using range, month/year are just informative or derived
            month_name = f"{_start.strftime('%b %d')} - {_end.strftime('%b %d')}"
            year = _start.year
            
        # Priority 2: Fallback to Month/Year logic (or default)
        else:
            if not month:
                month = str(datetime.now().month)
            if not year:
                year = '2026'
            
            _start = datetime.strptime(f'{year}-{month}-01', '%Y-%m-%d').date()
            _end = _start + relativedelta(months=1, days=-1)
            month_name = dict(request.env['sunray.monthly.sales.report.wizard'].fields_get(['month'])['month']['selection']).get(str(month))

        domain = [
            ('date_order', '>=', _start),
            ('date_order', '<=', _end),
            ('state', 'in', ['sale', 'done'])
        ]
        
        users_list = []
        if user_ids and user_ids != 'false':
            try:
                # Robustly handle user_ids from list or comma-string
                raw_ids = request.httprequest.args.getlist('user_ids')
                if not raw_ids and user_ids:
                    raw_ids = user_ids.split(',')
                
                user_ids_list = [int(x) for x in raw_ids if x]
                if user_ids_list:
                    domain.append(('user_id', 'in', user_ids_list))
                    users_list = user_ids_list
            except:
                pass

        sale_orders = request.env['sale.order'].search(domain, order='user_id, date_order')
        
        # Group data
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
            'sales_by_user': sales_by_user,
            'month': month, # might be strictly month number or None if range
            'month_name': month_name,
            'year': year,
            'selected_user_ids': users_list,
            'date_start': _start,
            'date_end': _end,
            'company': request.env.company,
            'currency': request.env.company.currency_id,
        }

    @http.route('/sunray_monthly_sales/report_html', type='http', auth='user')
    def report_html(self, month=None, year=None, user_ids=None, date_start=None, date_end=None, **kwargs):
        data = self._get_report_data(month, year, user_ids, date_start, date_end)
        
        # Add extra context for the HTML view (dropdowns)
        data['all_users'] = request.env['res.users'].search([('share', '=', False)])
        data['years'] = sorted([str(y) for y in range(2020, 2031)], reverse=True)
        
        return request.render("sunray_monthly_sales_report.report_html_screen", data)

    @http.route('/sunray_monthly_sales/report_xlsx', type='http', auth='user')
    def report_xlsx(self, month=None, year=None, user_ids=None, date_start=None, date_end=None, **kwargs):
        data = self._get_report_data(month, year, user_ids, date_start, date_end)
        sales_by_user = data['sales_by_user']
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Monthly Sales')
        
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#fcefdc', 'border': 1})
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        
        # Title
        display_period = data["month_name"] if data.get('date_start') else f'{data["month"]}/{data["year"]}'
        sheet.merge_range('A1:E1', f'Monthly Sales Report - {display_period} {data["year"]}', title_format)
        
        row = 3
        
        for user, user_data in sales_by_user.items():
            sheet.write(row, 0, f"Salesperson: {user.name}", workbook.add_format({'bold': True, 'font_color': '#d35400'}))
            row += 1
            
            # Table Header
            headers = ['Date', 'Order #', 'Customer', 'Status', 'Total']
            for col, text in enumerate(headers):
                sheet.write(row, col, text, header_format)
            row += 1
            
            for order in user_data['orders']: # Note: user_data is dict here
                sheet.write(row, 0, order.date_order, date_format)
                sheet.write(row, 1, order.name)
                sheet.write(row, 2, order.partner_id.name)
                sheet.write(row, 3, order.state)
                sheet.write(row, 4, order.amount_total, money_format)
                row += 1
            
            # Subtotal
            sheet.write(row, 3, 'Total', workbook.add_format({'bold': True, 'align': 'right'}))
            sheet.write(row, 4, user_data['total_amount'], money_format)
            row += 2 # Space between users
            
        workbook.close()
        output.seek(0)
        
        filename = f"Sales_Report_{data['year']}.xlsx"
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename))
            ]
        )

    @http.route('/sunray_monthly_sales/report_pdf', type='http', auth='user')
    def report_pdf(self, month=None, year=None, user_ids=None, date_start=None, date_end=None, **kwargs):
        data = self._get_report_data(month, year, user_ids, date_start, date_end)
        
        pdf, _ = request.env['ir.actions.report'].with_context(landscape=False).sudo()._render_qweb_pdf(
            report_ref='sunray_monthly_sales_report.action_report_monthly_sales',
            res_ids=[request.env.company.id], 
            data=data
        )
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', content_disposition(f'Sales_Report_{data["year"]}.pdf'))
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
