from odoo import http, fields
from odoo.http import request, content_disposition
import io
import xlsxwriter
from datetime import datetime
from dateutil.relativedelta import relativedelta

class InventoryReportController(http.Controller):

    def _get_report_data(self, date_start, date_end, location_ids=None):
        domain = [
            ('date_done', '>=', date_start),
            ('date_done', '<=', date_end),
            ('state', '=', 'done')
        ]
        if location_ids:
            if isinstance(location_ids, str) and location_ids.strip():
                location_id_list = [int(id) for id in location_ids.split(',')]
                domain += [('location_id', 'in', location_id_list)]
            elif isinstance(location_ids, list):
                domain += [('location_id', 'in', location_ids)]

        pickings = request.env['stock.picking'].sudo().search(domain, order='location_id, date_done')
        
        # Menggunakan nama lokasi (string) sebagai key agar aman di template QWeb
        data_per_location = {}
        for pick in pickings:
            loc_name = pick.location_id.display_name
            if loc_name not in data_per_location:
                data_per_location[loc_name] = {'lines': [], 'total_qty': 0.0}
            
            for move in pick.move_ids:
                data_per_location[loc_name]['lines'].append({
                    'id': pick.id,
                    'date': pick.date_done,
                    'name': pick.name,
                    'product': move.product_id.display_name,
                    'dest': pick.location_dest_id.display_name,
                    'qty': move.quantity,
                    'uom': move.product_uom.name,
                })
                data_per_location[loc_name]['total_qty'] += move.quantity
        
        return data_per_location

    @http.route('/inventory_location/report_html', type='http', auth='user', website=True)
    def report_html(self, month=None, year=None, location_ids=None, **kwargs):
        # Default Current Date jika tidak ada input
        now = datetime.now()
        month = month or str(now.month)
        year = year or str(now.year)
        
        date_start = datetime.strptime(f'{year}-{month}-01', '%Y-%m-%d').date()
        date_end = date_start + relativedelta(months=1, days=-1)

        # Build Domain
        domain = [('date_done', '>=', date_start), ('date_done', '<=', date_end), ('state', '=', 'done')]
        
        if location_ids and location_ids != '[]':
            # Handle list dari JS atau string comma separated
            loc_list = [int(i) for i in location_ids.split(',')] if isinstance(location_ids, str) else location_ids
            domain += [('location_id', 'in', loc_list)]

        pickings = request.env['stock.picking'].sudo().search(domain, order='location_id, date_done')
        
        # Group Data
        report_data = {}
        for pick in pickings:
            loc_name = pick.location_id.display_name
            if loc_name not in report_data:
                report_data[loc_name] = {'lines': [], 'total_qty': 0.0}
            
            for move in pick.move_ids:
                report_data[loc_name]['lines'].append({
                    'id': pick.id,
                    'date': pick.date_done,
                    'name': pick.name,
                    'product': move.product_id.display_name,
                    'dest': pick.location_dest_id.display_name,
                    'qty': move.quantity,
                    'uom': move.product_uom.name,
                })
                report_data[loc_name]['total_qty'] += move.quantity

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        all_locations = request.env['stock.location'].sudo().search([('usage', '=', 'internal')])

        return request.render('inventory_location_report.report_html_screen', {
            'report_data': report_data,
            'date_start': date_start,
            'date_end': date_end,
            'base_url': base_url,
            'current_month': month,
            'current_year': year,
            'all_locations': all_locations,
        })