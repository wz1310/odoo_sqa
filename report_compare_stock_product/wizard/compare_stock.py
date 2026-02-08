# pylint: disable=R0903
# -*- coding: utf-8 -*-
"""phyton file for generate report hs_code"""
import io
import base64
from datetime import datetime, timedelta
import xlsxwriter
from odoo.exceptions import Warning as UserError
import pytz
from odoo import api, fields, models, _


class ReportMrp(models.TransientModel):
    """generate report mrp"""
    _name = 'compare.stock'

    data_x = fields.Binary(string="File", readonly=True)
    name = fields.Char('Filename', size=100, readonly=True)
    state_x = fields.Selection((('choose', 'choose'), ('get', 'get'), ),
                               default='choose')
    date_to = fields.Date(default=fields.date.today())
    product_ids = fields.Many2many('product.product', string="Product")
    location_ids = fields.Many2many('stock.location', string="Perpindahan Lokasi")
    company_id = fields.Many2one('res.company',
								 string='Company',
								 required=True, default=lambda self: self.env.company)
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)
    selisih = fields.Boolean('Hanya yg selisih', default=False)

    def get_stock_awal(self, date, product, list_id_location):
        ''' get stock awal product '''
        sql = ''' select
                    pt.id as id,
                    pt.default_code as kode,
                    pt.name as nama_barang,
                    sml.lot_id as lot,
                    sml.reference as ket,
                    sml.date as tanggal,
                    sml.qty_done as quantity,
                    sml.location_id as source_lokasi,
                    sml.location_dest_id as lokasi_destination,
                    sml.id
                from stock_move_line sml
                right join product_product pp on pp.id = sml.product_id
                right join product_template pt on pt.id = pp.product_tmpl_id
                where
                    (sml.location_id in %s or sml.location_dest_id in %s) and
                    sml.location_id != sml.location_dest_id and
                    sml.date <= %s and
                    sml.state = 'done' and
                    pt.id = %s
                order by pt.id, sml.date '''
        params = (
            list_id_location,
            list_id_location,
            date,
            product,
            )
        self.env.cr.execute(sql, params)
        result_sql = self.env.cr.fetchall()
        total_masuk = 0
        total_keluar = 0
        for data in result_sql:
            if data[8] in list_id_location: #masuk
                total_masuk += data[6]
            elif data[7] in list_id_location: #keluar
                total_keluar += data[6]
        stock_awal = total_masuk - total_keluar
        return stock_awal

    def get_stock_quant(self, product, list_id_location):
        """get stock quant"""
        sql = ''' select
                    quantity
                from stock_quant
                where
                    location_id in %s and
                    product_id = %s
                '''
        params = (
            list_id_location,
            product,
            )
        self.env.cr.execute(sql, params)
        result_sql = self.env.cr.fetchall()
        
        total = 0.0
        for data in result_sql:
            total += data[0]
        return total

    def compare_stock_excel_report(self):
        """function for generate product sold excel report"""

        # get product
        products = []
        for item in self.product_ids:
            products.append(item.id)
        list_id_product = tuple(products)

        # get location
        location = []
        for loc in self.location_ids:
            location.append(loc.id)
        list_id_location = tuple(location)

        compare_stock = io.BytesIO()
        workbook = xlsxwriter.Workbook(compare_stock)
        filename = 'Report Stock.xlsx'

        #### STYLE
        #################################################################################
        top_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center'})
        top_style.set_font_name('Courier New')
        top_style.set_font_size('11')
        #################################################################################
        top_style_product = workbook.add_format({'bold': 0, 'valign':'vcenter', 'align':'center'})
        top_style_product.set_font_name('Courier New')
        top_style_product.set_font_size('11')
        #################################################################################
        header_style = workbook.add_format({'bold': 1, 'align':'center', 'valign':'vcenter'})
        header_style.set_border()
        header_style.set_font_name('Courier New')
        header_style.set_font_size('11')
        header_style.set_text_wrap()
        header_style.set_bg_color('#CBCACA')
        #################################################################################
        normal_style_left = workbook.add_format({'valign':'vcenter', 'align':'left'})
        normal_style_left.set_border()
        normal_style_left.set_text_wrap()
        normal_style_left.set_font_name('Courier New')
        normal_style_left.set_font_size('11')
        #################################################################################
        normal_center = workbook.add_format({'valign':'vcenter', 'align':'center'})
        normal_center.set_border()
        normal_center.set_text_wrap()
        normal_center.set_font_name('Courier New')
        normal_center.set_font_size('11')
        #################################################################################
        normal_style_right = workbook.add_format({'valign':'vcenter', 'align':'right'})
        normal_style_right.set_border()
        normal_style_right.set_text_wrap()
        normal_style_right.set_font_name('Courier New')
        normal_style_right.set_font_size('11')
        #################################################################################
        style_total = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'left'})
        style_total.set_border()
        style_total.set_text_wrap()
        style_total.set_font_name('Courier New')
        style_total.set_font_size('11')
        style_total.set_bg_color('#EFHFEF')
        ################################################################################
        style_total_qty = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center'})
        style_total_qty.set_border()
        style_total_qty.set_text_wrap()
        style_total_qty.set_font_name('Courier New')
        style_total_qty.set_font_size('11')
        style_total_qty.set_bg_color('#EFHFEF')
        #################################################################################
        style_downloded = workbook.add_format({'valign':'vcenter', 'align':'left'})
        style_downloded.set_text_wrap()
        style_downloded.set_font_name('Courier New')
        style_downloded.set_font_size('11')

        worksheet = workbook.add_worksheet("Laporan Material")
        worksheet.set_column('A:A', 3)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 10)
        worksheet.set_column('G:G', 17)
        worksheet.set_column('H:H', 40)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 10)
        worksheet.set_column('K:K', 10)
        worksheet.set_column('L:L', 10)
        worksheet.set_column('M:M', 10)

        worksheet.merge_range('A1:M1', 'LAPORAN PERBANDINGAN STOK BARANG', top_style)
        product_ids = self.product_ids
        if not self.product_ids:
            product_ids = self.env['product.product'].search([])
        if self.product_ids:
            name_product = []
            for item in self.product_ids:
                name_product.append(item.name)
            str_name = ", ".join(str(bit) for bit in name_product)
            worksheet.merge_range('A2:M2', 'Product : '+str_name, top_style_product)
        elif not self.product_ids:
            worksheet.merge_range('A2:M2', 'Product : All Product', top_style_product)
        if self.location_ids:
            name_location = []
            for location in self.location_ids:
                name_location.append(location.location_id.name)
            str_name_wh = ", ".join(str(wh) for wh in name_location)
            worksheet.merge_range('A3:M3', 'Warehouse : '+str_name_wh, top_style_product)

        date_to1 = datetime.strptime(str(self.date_to + timedelta(days=1)), "%Y-%m-%d")
        date_to2 = datetime.strftime(date_to1, '%d-%b-%Y')

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        datefrom = pytz.utc.localize(datetime.now()).astimezone(user_tz)
        new_time = datefrom.strftime("%d-%b-%Y %H:%M:%S")
        worksheet.merge_range('A5:D5', 'Downloaded on : '+new_time, style_downloded)

        # HEADER
        worksheet.set_row(5, 28)
        worksheet.write(5, 0, 'No', header_style)
        worksheet.write(5, 1, 'Kode Barang', header_style)
        worksheet.write(5, 2, 'Nama Barang', header_style)
        worksheet.write(5, 3, 'Stock Availability', header_style)
        worksheet.write(5, 4, 'Stock Move', header_style)
        worksheet.write(5, 5, 'Selisih', header_style)
            # line product
        row = 6
        nomor = 1
        for item in product_ids:
            product_tmpl = item.product_tmpl_id
            value_stock_move = self.get_stock_awal(date_to2, 
                                                    product_tmpl.id, 
                                                    list_id_location)
            value_stock_quant = self.get_stock_quant(item.id, list_id_location)
            
            if self.selisih:
                check_selisih = value_stock_move - value_stock_quant
                if check_selisih != 0.0:
                    worksheet.set_row(row, 28)
                    worksheet.write(row, 0, nomor, normal_center) #nomor
                    worksheet.write(row, 1, item.default_code, normal_center) #kode barnag
                    worksheet.write(row, 2, item.name, normal_style_left) #nama barnag
                    # item stock awal
                    
                    
                    worksheet.write(row, 3, value_stock_quant, normal_style_left) #so/po
                    worksheet.write(row, 4, value_stock_move, normal_style_left) #so/po
                    worksheet.write(row, 5, value_stock_quant - value_stock_move, normal_style_left) #so/po
                    nomor += 1
                    row += 1
            else:
                worksheet.set_row(row, 28)
                worksheet.write(row, 0, nomor, normal_center) #nomor
                worksheet.write(row, 1, item.default_code, normal_center) #kode barnag
                worksheet.write(row, 2, item.name, normal_style_left) #nama barnag
                # item stock awal
                
                worksheet.write(row, 3, value_stock_quant, normal_style_left) #so/po
                worksheet.write(row, 4, value_stock_move, normal_style_left) #so/po
                worksheet.write(row, 5, value_stock_quant - value_stock_move, normal_style_left) #so/po
                nomor += 1
                row += 1

        workbook.close()
        out = base64.b64encode(compare_stock.getvalue())
        compare_stock.close()
        file_name = "comparison_stock_report.xlsx"
        return self.set_data_excel(out, file_name)

    def set_data_excel(self, out, filename):
        """ Update data_file and name based from previous process output. And return action url for download excel. """
        self.write({'data_file': out, 'name': filename})

        return {
            'type':
            'ir.actions.act_url',
            'name':
            filename,
            'url':
            '/web/content/%s/%s/data_file/%s' % (
                self._name,
                self.id,
                filename,
            ),
        }
