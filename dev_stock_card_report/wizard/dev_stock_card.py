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
#========For Excel========
from io import BytesIO
import xlwt
from xlwt import easyxf
import base64
# =====================



class dev_stock_card(models.TransientModel):
    _name ='dev.stock.card'
    
    
    location_id = fields.Many2many('stock.location',string='Locations', domain="[('usage','=','internal')]", required="1")
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    filter_by = fields.Selection([('product','Product'),('category','Product Category')],string='Filter By', default='product')
    category_id = fields.Many2one('product.category',string='Category')
    product_ids = fields.Many2many('product.product',string='Products')
    company_id = fields.Many2one('res.company', required="1", default = lambda self:self.env.company)
    excel_file = fields.Binary('Excel File')
    
    def get_product_ids(self):
        product_pool = self.env['product.product']
        if self.filter_by and self.filter_by == 'product':
            return self.product_ids.ids
        elif self.filter_by and self.filter_by == 'category':
            product_ids = product_pool.search([('type', '=', 'product'), ('categ_id', 'child_of', self.category_id.id)])
            return product_ids.ids
        else:
            product_ids = product_pool.search([('type', '=', 'product')])
            return product_ids.ids
            
    
    def in_lines(self,product_ids, location_id):
        state = 'done'
        # query = """select DATE(sm.date) as date, sm.origin as origin, sm.reference as ref, pt.name as product,\
        #           sm.product_uom_qty as in_qty, pp.id as product_id , sm.purchase_line_id as po_line, sm.sale_line_id as so_line from stock_move as sm \
        #           JOIN product_product as pp ON pp.id = sm.product_id \
        #           JOIN product_template as pt ON pp.product_tmpl_id = pt.id \
        #           where sm.date >= %s and sm.date <= %s \
        #           and sm.location_dest_id = %s and sm.product_id in %s \
        #           and sm.state = %s and sm.company_id = %s
        #           """
        query = """select DATE(sm.date) as date, sm.origin as origin, sm.reference as ref, pt.name as product,\
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
                    where sm.date >= %s and sm.date <= %s \
                    and sm.location_dest_id = %s and sm.product_id in %s \
                    and sm.state = %s and sm.company_id = %s
                  """
        params = (self.start_date, self.end_date, location_id.id, tuple(product_ids), state, self.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        for res in result:
            f_date = ' '
            if res.get('date'):
                data_date = datetime.strptime(str(res.get('date')),'%Y-%m-%d')
                f_date = data_date.strftime('%d-%m-%Y')
            to = False
            if res.get('so_line'):
                so = self.env['sale.order'].search([('order_line','in', res.get('so_line'))], limit=1)
                to = so.partner_id.name or ''
            elif res.get('po_line'):
                po = self.env['purchase.order'].search([('order_line','in', res.get('po_line'))], limit=1)
                to = po.partner_id.name or ''
            elif res.get('origin') and 'po' in res.get('origin').lower():
                po = self.env['purchase.order'].search([('name','=', res.get('origin'))], limit=1)
                to = po.partner_id.name or ''
            elif res.get('origin') and 'so' in res.get('origin').lower():
                so = self.env['sale.order'].search([('name','=', res.get('origin'))], limit=1)
                to = so.partner_id.name or ''
            elif not res.get('origin',False) and 'pos' in res.get('ref').lower():
                pick_pos = self.env['stock.picking'].search([('name','=', res.get('ref'))], limit=1)
                to = pick_pos.partner_id.name or ''
            elif not res.get('origin',False) and 'int' in res.get('ref').lower():
                pick_int = self.env['stock.picking'].search([('name','=', res.get('ref'))], limit=1)
                to = pick_int.location_dest_id.display_name or ''
            res.update({
                'out_qty':0.0,
                'date':f_date,
                'to': to
            })
        return result

    def out_lines(self, product_ids, location_id):
        state = 'done'
        move_type = 'outgoing'
        m_type = ''
        if location_id:
            m_type = 'and sm.location_id = %s'

        query = """select DATE(sm.date) as date, CASE WHEN sm.reference = 'New' THEN pg.name ELSE sm.origin END as origin, sm.reference as ref, pt.name as product,\
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
                      where sm.date >= %s and sm.date <= %s \
                      and sm.location_id = %s and sm.product_id in %s \
                      and sm.state = %s and sm.company_id = %s
                      """
        params = (self.start_date, self.end_date, location_id.id, tuple(product_ids), state, self.company_id.id)

        self.env.cr.execute(query, params)

        result = self.env.cr.dictfetchall()
        for res in result:
            f_date = ' '
            if res.get('date'):
                data_date = datetime.strptime(str(res.get('date')),'%Y-%m-%d')
                f_date = data_date.strftime('%d-%m-%Y')
            to = False
            if res.get('so_line'):
                so = self.env['sale.order'].search([('order_line','in', res.get('so_line'))], limit=1)
                to = so.partner_id.name or ''
            elif res.get('po_line'):
                po = self.env['purchase.order'].search([('order_line','in', res.get('po_line'))], limit=1)
                to = po.partner_id.name or ''
            elif res.get('origin') and 'po' in res.get('origin').lower():
                po = self.env['purchase.order'].search([('name','=', res.get('origin'))], limit=1)
                to = po.partner_id.name or ''
            elif res.get('origin') and 'so' in res.get('origin').lower():
                so = self.env['sale.order'].search([('name','=', res.get('origin'))], limit=1)
                to = so.partner_id.name or ''
            elif not res.get('origin',False) and 'pos' in res.get('ref').lower():
                pick_pos = self.env['stock.picking'].search([('name','=', res.get('ref'))], limit=1)
                to = pick_pos.partner_id.name or ''
            elif not res.get('origin',False) and 'int' in res.get('ref').lower():
                pick_int = self.env['stock.picking'].search([('name','=', res.get('ref'))], limit=1)
                to = pick_int.location_dest_id.display_name or ''
            res.update({
                'in_qty': 0.0,
                'date':f_date,
                'to': to
            })
        return result
        
    def get_opening_quantity(self,product, location_id):
        product = self.env['product.product'].browse(product)
        # date = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S')
        
        # date = date - timedelta(days=1)
        # date = date.strftime('%Y-%m-%d')
        # qty = product.with_context(to_date=date, location_id=self.location_id.id).qty_available

        #PCI CODE
        qty_start = 0.0
        ##############################################################
        ## beginning balance in
        ##############################################################
        sql = "select sum(product_uom_qty) as qty_open from stock_move as sm " \
                "where sm.product_id= %s " \
                "and sm.location_dest_id= %s " \
                "and sm.state = 'done'" \
                "and sm.date <= '%s'" % (product.id, location_id.id, self.start_date)
        self.env.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        for res in result:
            if res.get('qty_open'):
                qty_start = res.get('qty_open')
                print("--------INPUT---------",qty_start)
        ##############################################################
        ## beginning balance out
        ##############################################################
        sql = "select sum(product_uom_qty) as qty_open from stock_move as sm " \
                "where sm.product_id= %s " \
                "and sm.location_id= %s " \
                "and sm.state = 'done'" \
                "and sm.date <= '%s'" % (product.id, location_id.id, self.start_date)
        self.env.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        for res in result:
            if res.get('qty_open'):
                qty_start = qty_start - res.get('qty_open')
        return qty_start
            
    
    
    def get_lines(self, location_id):
        product_ids = self.get_product_ids()
        result = []
        if product_ids:
            in_lines = self.in_lines(product_ids, location_id)
            out_lines = self.out_lines(product_ids, location_id)
            lst = in_lines + out_lines
            new_lst = sorted(lst, key=itemgetter('product'))
            groups = itertools.groupby(new_lst, key=operator.itemgetter('product'))
            result = [{'product': k, 'values': [x for x in v]} for k, v in groups]
            for res in result:
                print 
                l_data = res.get('values')
                new_lst = sorted(l_data, key=lambda item: datetime.strptime(item.get('date'), "%d-%m-%Y"))
                res['values'] = new_lst

        return result
        
    
    def print_pdf(self):
        data={}
        data['form'] = self.read()[0]
        return self.env.ref('dev_stock_card_report.print_stock_card_report').report_action(self, data=None)
    
    def get_date(self):
        s_date = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S').date()
        start_date = s_date.strftime('%m-%d-%Y')
        e_date = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S').date()
        end_date = e_date.strftime('%m-%d-%Y')        
        
        data = {'start_date':start_date , 'end_date':end_date}
        return data
    
    def get_style(self):
        main_header_style = easyxf('font:height 300;'
                                   'align: horiz center;font: color black; font:bold True;'
                                   "borders: top thin,left thin,right thin,bottom thin")
                                   
        header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz right;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        
        left_header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz left;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
        
        
        text_left = easyxf('font:height 200; align: horiz left;')
        
        text_right = easyxf('font:height 200; align: horiz right;', num_format_str='0.00')
        
        text_left_bold = easyxf('font:height 200; align: horiz right;font:bold True;')
        
        text_right_bold = easyxf('font:height 200; align: horiz right;font:bold True;', num_format_str='0.00') 
        text_center = easyxf('font:height 200; align: horiz center;'
                             "borders: top thin,left thin,right thin,bottom thin")  
        
        return [main_header_style, left_header_style,header_style, text_left, text_right, text_left_bold, text_right_bold, text_center]
    
    def create_excel_header(self,worksheet,main_header_style,text_left,text_center,left_header_style,text_right,header_style):
        worksheet.write_merge(0, 1, 1, 3, 'Stock Card', main_header_style)
        row = 2
        col=1
        start_date = datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S')
        start_date = datetime.strftime(start_date, "%d-%m-%Y ")
        
        end_date = datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strftime(end_date, "%d-%m-%Y ")
        
        date = start_date + ' To '+ end_date
        worksheet.write_merge(row,row, col, col+2, date, text_center)
        row += 2
        worksheet.col(1).width = 256 * 65

        for location_id in self.location_id:
            lines = self.get_lines(location_id)
            if lines:
                worksheet.write(row, 0, 'Location', left_header_style)
                worksheet.write_merge(row,row, 1, 2, location_id.display_name, text_left)
                row+=1
                worksheet.write(row, 0, 'Company', left_header_style)
                worksheet.write_merge(row,row, 1, 2, self.company_id.name, text_left)
                row+=2
                
                
                worksheet.write(row, 0, 'Date', left_header_style)
                worksheet.write(row,1, 'Location', left_header_style)
                worksheet.write(row,2, 'Type', left_header_style)
                worksheet.write(row,3, 'No. SJ', left_header_style)
                worksheet.write(row,4, 'No. SJ WIM', left_header_style)
                worksheet.write(row,5, 'No. SJ Vendor', left_header_style)
                worksheet.write(row,6, 'Source Document', left_header_style)
                worksheet.write(row,7, 'In Qty', header_style)
                worksheet.write(row,8, 'Out Qty', header_style)
                worksheet.write(row,9, 'Balance', header_style)
                worksheet.write(row,10, 'Internal Note', header_style)
                
                p_group_style = easyxf('font:height 200;pattern: pattern solid, fore_color ivory;'
                                    'align: horiz left;font: color black; font:bold True;'
                                    "borders: top thin,left thin,right thin,bottom thin")
                                    
                group_style = easyxf('font:height 200;pattern: pattern solid, fore_color ice_blue;'
                                    'align: horiz left;font: color black; font:bold True;'
                                    "borders: top thin,left thin,right thin,bottom thin")
                
                group_style_right = easyxf('font:height 200;pattern: pattern solid, fore_color ice_blue;'
                                    'align: horiz right;font: color black; font:bold True;'
                                    "borders: top thin,left thin,right thin,bottom thin", num_format_str='0.00')
                                    
                                    
                row+=1
                for line in lines:
                    worksheet.write_merge(row,row, 0,9, line.get('product'), p_group_style)
                    row += 1
                    count = 0
                    balance = 0
                    t_in_qty = t_out_qty = 0
                    for val in line.get('values'):
                        count += 1
                        if count == 1:
                            worksheet.write_merge(row,row,0,7, 'Opening Quantity', group_style)
                            op_qty = self.get_opening_quantity(val.get('product_id'), location_id)
                            balance = op_qty
                            worksheet.write(row,8, '', group_style_right)
                            worksheet.write(row,9, op_qty, group_style_right)
                            row+=1
                        balance += val.get('in_qty') - val.get('out_qty')
                        t_in_qty += val.get('in_qty')
                        t_out_qty += val.get('out_qty')
                        worksheet.write(row,0, val.get('date'), text_left)
                        worksheet.write(row,1, (val.get('location_sumber') or '') +' --> '+ (val.get('location') or ''), text_left)
                        worksheet.write(row,2, val.get('type_tran'), text_left)
                        worksheet.write(row,3, val.get('no_sj'), text_left)
                        worksheet.write(row,4, val.get('no_wim'), text_left)
                        worksheet.write(row,5, val.get('no_sj_vendor'), text_left)
                        worksheet.write(row,6, (val.get('origin') or val.get('ref')), text_left)
                        worksheet.write(row,7, val.get('in_qty'), text_right)
                        worksheet.write(row,8, val.get('out_qty'), text_right)
                        worksheet.write(row,9, balance, text_right)
                        worksheet.write(row,10, val.get('internal_sale_notes'), text_left)
                        
                        
                        row+=1
                    worksheet.write_merge(row,row,0,5, 'Total', group_style_right)
                    worksheet.write(row,7, t_in_qty, group_style_right)
                    worksheet.write(row,8, t_out_qty, group_style_right)
                    worksheet.write(row,9, balance, group_style_right)
                    row+=2
                
                row+=1
        return worksheet, row
    
    
    def action_generate_excel(self):
        #====================================
        # Style of Excel Sheet 
        excel_style = self.get_style()
        main_header_style = excel_style[0]
        left_header_style = excel_style[1]
        header_style = excel_style[2]
        text_left = excel_style[3]
        text_right = excel_style[4]
        text_left_bold = excel_style[5]
        text_right_bold = excel_style[6]
        text_center = excel_style[7]
        # ====================================
        
        workbook = xlwt.Workbook()
        filename = 'Stock Card Report.xls'
        worksheet = workbook.add_sheet('Stock Card', cell_overwrite_ok=True)
        for i in range(0,10):
            worksheet.col(i).width = 150 * 30
        
        
        
        worksheet,row = self.create_excel_header(worksheet,main_header_style,text_left,text_center,left_header_style,text_right,header_style)
        
        
        #download Excel File
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodestring(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})

        if self.excel_file:
            active_id = self.ids[0]
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=dev.stock.card&download=true&field=excel_file&id=%s&filename=%s' % (
                    active_id, filename),
                'target': 'new',
            }
                
    



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
