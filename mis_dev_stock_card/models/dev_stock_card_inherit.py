# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from datetime import timedelta
import itertools
from operator import itemgetter
import operator
# ========For Excel========
from io import BytesIO
import xlwt
from xlwt import easyxf
import base64
# =====================


class mis_dev_stock_card(models.TransientModel):
    _inherit = 'dev.stock.card'

    def get_lines(self, location_id):
        product_ids = self.get_product_ids()
        result = []
        if product_ids:
            in_lines = self.in_lines(product_ids, location_id)
            out_lines = self.out_lines(product_ids, location_id)
            lst = in_lines + out_lines

            print('>>> in_lines : ' + str(in_lines))
            print('>>> out_lines : ' + str(out_lines))
            print('>>> lst : ' + str(lst))

            new_lst = sorted(lst, key=itemgetter('product'))
            groups = itertools.groupby(new_lst, key=operator.itemgetter('product'))
            result = [{'product': k, 'values': [x for x in v]} for k, v in groups]
            for res in result:
                print
                l_data = res.get('values')
                new_lst = sorted(l_data, key=lambda item: datetime.strptime(item.get('date'), "%d-%m-%Y"))
                res['values'] = new_lst

        return result

    def in_lines(self, product_ids, location_id):

        state = 'done'
        # query = """select DATE(sm.date) as date, sm.origin as origin, sm.reference as ref, pt.name as product,\
        #           sm.product_uom_qty as in_qty, pp.id as product_id , sm.purchase_line_id as po_line, sm.sale_line_id as so_line from stock_move as sm \
        #           JOIN product_product as pp ON pp.id = sm.product_id \
        #           JOIN product_template as pt ON pp.product_tmpl_id = pt.id \
        #           where sm.date >= %s and sm.date <= %s \
        #           and sm.location_dest_id = %s and sm.product_id in %s \
        #           and sm.state = %s and sm.company_id = %s
        #           """
        query = """select pp.default_code as product_code, pt.name as product_name, DATE( sm.date + interval '7' HOUR) as date, sm.origin as origin, sm.reference as ref, pt.name as product,\
                    sm.product_uom_qty as in_qty, pp.id as product_id , sm.purchase_line_id as po_line, sm.sale_line_id as so_line,\
                    spt.name as type_tran, sp.name as no_sj, concat(sl_parent.name,'/',sl.name) as location, concat(sls_parent.name,'/',sls.name) as location_sumber, \
                    sp.no_sj_wim as no_wim,sp.no_sj_vendor as no_sj_vendor \
                    from stock_move as sm \
                    JOIN product_product as pp ON pp.id = sm.product_id \
                    JOIN product_template as pt ON pp.product_tmpl_id = pt.id \
		            LEFT JOIN stock_picking sp ON sm.picking_id = sp.id \
                    LEFT JOIN stock_picking_type spt ON sm.picking_type_id = spt.id \
                    LEFT JOIN stock_location sl ON sm.location_dest_id = sl.id \
                    LEFT JOIN stock_location sl_parent ON sl.location_id = sl_parent.id \
                    LEFT JOIN stock_location sls ON sm.location_id = sls.id \
                    LEFT JOIN stock_location sls_parent ON sls.location_id = sls_parent.id \
                    where ( sm.date + interval '7' HOUR) BETWEEN %s and %s \
                    and sm.location_dest_id = %s and sm.product_id in %s \
                    and sm.state = %s and sm.company_id = %s
                  """

        #   where sm.date >= %s and sm.date <= %s \
        params = (self.start_date, self.end_date, location_id.id,
                  tuple(product_ids), state, self.company_id.id)

        s_date = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()
        start_date_1 = s_date.strftime('%m-%d-%Y')

        print(">>> Tuple Id In Line : " + str(tuple(product_ids)))
        print(">>> start_date_1 : " + str(start_date_1))
        print(">>> start_date : " + str(self.start_date))
        print(">>> end_date : " + str(self.end_date))
        print(">>> location : " + str(location_id.id))
        print(">>> company : " + str(self.company_id.id))

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        for res in result:
            f_date = ' '
            if res.get('date'):
                data_date = datetime.strptime(str(res.get('date')), '%Y-%m-%d')
                f_date = data_date.strftime('%d-%m-%Y')
            to = False
            if res.get('so_line'):
                so = self.env['sale.order'].search(
                    [('order_line', 'in', res.get('so_line'))], limit=1)
                to = so.partner_id.name or ''
            elif res.get('po_line'):
                po = self.env['purchase.order'].search(
                    [('order_line', 'in', res.get('po_line'))], limit=1)
                to = po.partner_id.name or ''
            elif res.get('origin') and 'po' in res.get('origin').lower():
                po = self.env['purchase.order'].search(
                    [('name', '=', res.get('origin'))], limit=1)
                to = po.partner_id.name or ''
            elif res.get('origin') and 'so' in res.get('origin').lower():
                so = self.env['sale.order'].search(
                    [('name', '=', res.get('origin'))], limit=1)
                to = so.partner_id.name or ''
            elif not res.get('origin', False) and 'pos' in res.get('ref').lower():
                pick_pos = self.env['stock.picking'].search(
                    [('name', '=', res.get('ref'))], limit=1)
                to = pick_pos.partner_id.name or ''
            elif not res.get('origin', False) and 'int' in res.get('ref').lower():
                pick_int = self.env['stock.picking'].search(
                    [('name', '=', res.get('ref'))], limit=1)
                to = pick_int.location_dest_id.display_name or ''
            res.update({
                'out_qty': 0.0,
                'date': f_date,
                'to': to
            })
        return result

    def out_lines(self, product_ids, location_id):

        state = 'done'
        move_type = 'outgoing'
        m_type = ''
        if location_id:
            m_type = 'and sm.location_id = %s'

        query = """select pp.default_code as product_code, pt.name as product_name, DATE( sm.date + interval '7' HOUR) as date, CASE WHEN sm.reference = 'New' THEN pg.name ELSE sm.origin END as origin, sm.reference as ref, pt.name as product,\
                      sm.product_uom_qty as out_qty, pp.id as product_id , sm.purchase_line_id as po_line, sm.sale_line_id as so_line, \
                      spt.name as type_tran, sp.doc_name as no_sj, concat(sl_parent.name,'/',sl.name) as location, concat(sls_parent.name,'/',sls.name) as location_sumber,sp.no_sj_wim as no_wim,sp.no_sj_vendor as no_sj_vendor, sp.internal_sale_notes\
                      from stock_move as sm JOIN product_product as pp ON pp.id = sm.product_id \
                      JOIN product_template as pt ON pp.product_tmpl_id = pt.id \
                      LEFT JOIN stock_picking sp ON sm.picking_id = sp.id \
                      LEFT JOIN stock_picking_type spt ON sm.picking_type_id = spt.id \
                      LEFT JOIN stock_location sl ON sm.location_dest_id = sl.id \
                      LEFT JOIN stock_location sl_parent ON sl.location_id = sl_parent.id \
                      LEFT JOIN stock_location sls ON sm.location_id = sls.id \
                      LEFT JOIN stock_location sls_parent ON sls.location_id = sls_parent.id \
                      LEFT JOIN procurement_group pg ON pg.id = sm.group_id                          
                      where ( sm.date + interval '7' HOUR) BETWEEN %s and %s \
                      and sm.location_id = %s and sm.product_id in %s \
                      and sm.state = %s and sm.company_id = %s
                      """
        #   where sm.date >= %s and sm.date <= %s \
        params = (self.start_date, self.end_date, location_id.id,
                  tuple(product_ids), state, self.company_id.id)

        print(">>> Tuple Id Out Line : " + str(tuple(product_ids)))
        print(">>> start_date : " + str(self.start_date))
        print(">>> end_date : " + str(self.end_date))
        print(">>> location : " + str(location_id.id))
        print(">>> company : " + str(self.company_id.id))

        self.env.cr.execute(query, params)

        result = self.env.cr.dictfetchall()
        for res in result:
            f_date = ' '
            if res.get('date'):
                data_date = datetime.strptime(str(res.get('date')), '%Y-%m-%d')
                f_date = data_date.strftime('%d-%m-%Y')
            to = False
            if res.get('so_line'):
                so = self.env['sale.order'].search(
                    [('order_line', 'in', res.get('so_line'))], limit=1)
                to = so.partner_id.name or ''
            elif res.get('po_line'):
                po = self.env['purchase.order'].search(
                    [('order_line', 'in', res.get('po_line'))], limit=1)
                to = po.partner_id.name or ''
            elif res.get('origin') and 'po' in res.get('origin').lower():
                po = self.env['purchase.order'].search(
                    [('name', '=', res.get('origin'))], limit=1)
                to = po.partner_id.name or ''
            elif res.get('origin') and 'so' in res.get('origin').lower():
                so = self.env['sale.order'].search(
                    [('name', '=', res.get('origin'))], limit=1)
                to = so.partner_id.name or ''
            elif not res.get('origin', False) and 'pos' in res.get('ref').lower():
                pick_pos = self.env['stock.picking'].search(
                    [('name', '=', res.get('ref'))], limit=1)
                to = pick_pos.partner_id.name or ''
            elif not res.get('origin', False) and 'int' in res.get('ref').lower():
                pick_int = self.env['stock.picking'].search(
                    [('name', '=', res.get('ref'))], limit=1)
                to = pick_int.location_dest_id.display_name or ''
            res.update({
                'in_qty': 0.0,
                'date': f_date,
                'to': to
            })
        return result

    def create_excel_header(self, worksheet, main_header_style, text_left, text_center, left_header_style, text_right, header_style):
        self.start_date = self.start_date + timedelta(hours=7)
        self.end_date = self.end_date + timedelta(hours=7)
        worksheet.write_merge(0, 1, 1, 3, 'Stock Card', main_header_style)
        row = 2
        col = 1
        start_date = datetime.strptime(
            str(self.start_date), '%Y-%m-%d %H:%M:%S')
        start_date = datetime.strftime(start_date, "%d-%m-%Y ")

        end_date = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strftime(end_date, "%d-%m-%Y ")

        date = start_date + ' To ' + end_date
        worksheet.write_merge(row, row, col, col+2, date, text_center)
        row += 2
        worksheet.col(1).width = 256 * 65

        for location_id in self.location_id:
            lines = self.get_lines(location_id)
            if lines:
                worksheet.write(row, 0, 'Location', left_header_style)
                worksheet.write_merge(
                    row, row, 1, 2, location_id.display_name, text_left)
                row += 1
                worksheet.write(row, 0, 'Company', left_header_style)
                worksheet.write_merge(
                    row, row, 1, 2, self.company_id.name, text_left)
                row += 2

                worksheet.write(row, 0, 'Kode Produk', left_header_style)
                worksheet.write(row, 1, 'Nama Produk', left_header_style)
                worksheet.write(row, 2, 'Date', left_header_style)
                worksheet.write(row, 3, 'Location', left_header_style)
                worksheet.write(row, 4, 'Type', left_header_style)
                worksheet.write(row, 5, 'No. SJ', left_header_style)
                worksheet.write(row, 6, 'No. SJ WIM', left_header_style)
                worksheet.write(row, 7, 'No. SJ Vendor', left_header_style)
                worksheet.write(row, 8, 'Source Document', left_header_style)
                worksheet.write(row, 9, 'In Qty', header_style)
                worksheet.write(row, 10, 'Out Qty', header_style)
                worksheet.write(row, 11, 'Balance', header_style)
                worksheet.write(row, 12, 'Internal Note', header_style)

                p_group_style = easyxf('font:height 200;pattern: pattern solid, fore_color ivory;'
                                       'align: horiz left;font: color black; font:bold True;'
                                       "borders: top thin,left thin,right thin,bottom thin")

                group_style = easyxf('font:height 200;pattern: pattern solid, fore_color ice_blue;'
                                     'align: horiz left;font: color black; font:bold True;'
                                     "borders: top thin,left thin,right thin,bottom thin")

                group_style_right = easyxf('font:height 200;pattern: pattern solid, fore_color ice_blue;'
                                           'align: horiz right;font: color black; font:bold True;'
                                           "borders: top thin,left thin,right thin,bottom thin", num_format_str='0.00')

                row += 1
                for line in lines:
                    worksheet.write_merge(
                        row, row, 0, 12, line.get('product'), p_group_style)
                    row += 1
                    count = 0
                    balance = 0
                    t_in_qty = t_out_qty = 0
                    for val in line.get('values'):
                        count += 1
                        if count == 1:
                            worksheet.write_merge(
                                row, row, 0, 9, 'Opening Quantity', group_style)
                            op_qty = self.get_opening_quantity(
                                val.get('product_id'), location_id)
                            balance = op_qty
                            worksheet.write(row, 10, '', group_style_right)
                            worksheet.write(row, 11, op_qty, group_style_right)
                            row += 1
                        balance += val.get('in_qty') - val.get('out_qty')
                        t_in_qty += val.get('in_qty')
                        t_out_qty += val.get('out_qty')

                        worksheet.write(row, 0, val.get(
                            'product_code'), text_left)
                        worksheet.write(row, 1, val.get(
                            'product_name'), text_left)
                        worksheet.write(row, 2, val.get('date'), text_left)
                        worksheet.write(row, 3, (val.get(
                            'location_sumber') or '') + ' --> ' + (val.get('location') or ''), text_left)
                        worksheet.write(row, 4, val.get(
                            'type_tran'), text_left)
                        worksheet.write(row, 5, val.get('no_sj'), text_left)
                        worksheet.write(row, 6, val.get('no_wim'), text_left)
                        worksheet.write(row, 7, val.get(
                            'no_sj_vendor'), text_left)
                        worksheet.write(
                            row, 8, (val.get('origin') or val.get('ref')), text_left)
                        worksheet.write(row, 9, val.get('in_qty'), text_right)
                        worksheet.write(row, 10, val.get(
                            'out_qty'), text_right)
                        worksheet.write(row, 11, balance, text_right)
                        worksheet.write(row, 12, val.get(
                            'internal_sale_notes'), text_left)

                        row += 1
                    worksheet.write_merge(
                        row, row, 0, 7, 'Total', group_style_right)
                    worksheet.write(row, 9, t_in_qty, group_style_right)
                    worksheet.write(row, 10, t_out_qty, group_style_right)
                    worksheet.write(row, 11, balance, group_style_right)
                    row += 2

                row += 1
        return worksheet, row
