# -*- coding: utf-8 -*-
import base64
import io
import xlsxwriter
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from pytz import timezone, UTC

class WizardMutasiInventoryInherit(models.TransientModel):
    _inherit = "wizard.mutasi.inventory.report"

    def generate_report_excel(self):
        """function for generate report excel"""
        str_start_date = str(self.start_date)+' 00:00:00'
        str_end_date = str(self.end_date)+' 23:59:59'
        sql1="""
                with
                    product_production as (
                        with product as(
                        select pp.id as product_id, pp.default_code, pt.name
                        from product_template pt
                            left join product_product pp on pp.product_tmpl_id = pt.id
                        where product_classification in ('barangjadi', 'barangsetengahjadi') and pt.active = True ),

                        production as (
                        select mp.product_id, sum(mp.product_qty) as qt, sum(mp.bom_amount) as bom_amount, sum(mp.produksi_amount) as produksi_amount,
                            sum(mp.reject_produksi_qty) as reject_qty, sum(mp.reject_produksi_amount) as reject_amount
                        from product_template pt
                            left join product_product pp on pp.product_tmpl_id = pt.id
                            left join mrp_production mp on mp.product_id = pp.id
                        where mp.state in ('done', 'waiting_qc', 'qc_done') and pt.product_classification in ('barangjadi', 'barangsetengahjadi')
                        and mp.date_planned_start >= %s 
                        and mp.date_planned_start <= %s
                        and mp.company_id = %s
                        and pt.active = True
                        group by mp.product_id, pp.default_code, pt.name
                        order by pp.default_code)

                    select * from product full join production on product.product_id = production.product_id
                    )

                    select * from product_production order by default_code"""
        
        params = (str_start_date, str_end_date, self.company_id.id)
        self.env.cr.execute(sql1, params)
        result_sql1 = self.env.cr.fetchall()
        if not result_sql1:
            raise Warning(_("Sorry, There is no data in the selected period."))

        
        # sql2 = ''' 
        #         with
        #             product_production as (
        #                 with product as(
        #                 select pp.id as product_id, pt.product_classification, pp.default_code, pt.name
        #                 from product_template pt
        #                     left join product_product pp on pp.product_tmpl_id = pt.id
        #                 where product_classification in ('bahanbaku', 'barangsetengahjadi') and pt.active = True),

        #                 production as (
        #                 select sm.product_id, sum(sm.product_qty) as qty, sum(sm.bom_amount) as bom_amount, sum(sm.produksi_amount) as produksi_amount,
        #                     sum(sm.reject_produksi_qty) as reject_qty, sum(sm.reject_produksi_amount) as reject_amount
        #                 from stock_move sm
        #                     left join product_product pp on sm.product_id = pp.id
        #                     left join product_template pt on pp.product_tmpl_id = pt.id
        #                     left join mrp_production mp on sm.raw_material_production_id = mp.id
        #                 where mp.state in ('done', 'waiting_qc', 'qc_done') 
        #                     and pt.product_classification in ('bahanbaku', 'barangsetengahjadi')
        #                 and mp.date_planned_start >= %s 
        #                 and mp.date_planned_start <= %s
        #                 and mp.company_id = %s
        #                 and pt.active = True
        #                 group by sm.product_id, pp.default_code
        #                 order by pp.default_code)


        #             select * from product 
        #                 full join production on product.product_id = production.product_id
        #             )

        #             select * from product_production order by default_code, product_classification
        #     '''

        sql2 = ''' 
                with
                    product_production as (
                        with product as(
                        select pp.id as product_id, pt.product_classification, pp.default_code, pt.name
                        from product_template pt
                            left join product_product pp on pp.product_tmpl_id = pt.id
                        where product_classification in ('bahanbaku', 'barangsetengahjadi') and pt.active = True),

                        production as (
                        select sm.product_id, sum(sm.product_qty) as qty, sum(sm.bom_amount) as bom_amount, sum(sm.produksi_amount) as produksi_amount,
                            sum(sm.reject_produksi_qty) as reject_qty, sum(sm.reject_produksi_amount) as reject_amount
                        from stock_move sm
                            left join product_product pp on sm.product_id = pp.id
                            left join product_template pt on pp.product_tmpl_id = pt.id
                            left join mrp_production mp on sm.raw_material_production_id = mp.id
                        where mp.state in ('done', 'waiting_qc', 'qc_done') 
                            and pt.product_classification in ('bahanbaku', 'barangsetengahjadi')
                        and ( sm.date + interval '7' HOUR) between %s and %s
                        and mp.company_id = %s
                        and pt.active = True
                        group by sm.product_id, pp.default_code
                        order by pp.default_code)


                    select * from product 
                        full join production on product.product_id = production.product_id
                    )

                    select * from product_production order by default_code, product_classification
            '''

        print(">>> Start Date : " + str_start_date)
        print(">>> End Date : " + str_end_date)
        print(">>> Company Id : " + str(self.company_id.id))
        params = (str_start_date, str_end_date, self.company_id.id,)
        self.env.cr.execute(sql2, params)
        result_sql2 = self.env.cr.fetchall()
        if not result_sql2:
            raise Warning(_("Sorry, There is no data in the selected period."))

        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        filename = 'Laporan material variance (Periode %s s/d %s).xlsx'  % (self.start_date, self.end_date)

        #### STYLE
        #################################################################################
        top_style = workbook.add_format({'bold': 1, 'valign':'vcenter'})
        top_style.set_font_name('Calibri')
        top_style.set_font_size('18')
        #################################################################################
        header_style = workbook.add_format({'bold': 1, 'align':'center', 'valign':'vcenter'})
        header_style.set_border()
        header_style.set_font_name('Calibri')
        header_style.set_font_size('13')
        header_style.set_text_wrap()
        header_style.set_bg_color('#eeeeee')
        #################################################################################
        total_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'right'})
        total_style.set_border()
        total_style.set_font_name('Calibri')
        total_style.set_font_size('12')
        total_style.set_text_wrap()
        total_style.set_bg_color('#eeeeee')
        #################################################################################
        normal_style_left = workbook.add_format({'valign':'vcenter', 'align':'left'})
        normal_style_left.set_border()
        normal_style_left.set_text_wrap()
        normal_style_left.set_font_name('Calibri')
        normal_style_left.set_font_size('12')
        #################################################################################
        normal_center = workbook.add_format({'valign':'vcenter', 'align':'center'})
        normal_center.set_border()
        normal_center.set_text_wrap()
        normal_center.set_font_name('Calibri')
        normal_center.set_font_size('12')
        #################################################################################
        normal_style_right = workbook.add_format({'valign':'vcenter', 'align':'right', 'num_format': '#,##0.00'})
        normal_style_right.set_border()
        normal_style_right.set_text_wrap()
        normal_style_right.set_font_name('Calibri')
        normal_style_right.set_font_size('12')
        #################################################################################
        normal_style_right_bold = workbook.add_format({'valign':'vcenter', 'align':'right', 'num_format': '#,##0.00',
                                                       'bold': 1})
        normal_style_right_bold.set_border()
        normal_style_right_bold.set_text_wrap()
        normal_style_right_bold.set_font_name('Calibri')
        normal_style_right_bold.set_font_size('12')
        #################################################################################
        normal_percent = workbook.add_format({'valign':'vcenter', 'align':'right',
                                              'num_format': '0.00%'})
        normal_percent.set_border()
        normal_percent.set_text_wrap()
        normal_percent.set_font_name('Calibri')
        normal_percent.set_font_size('12')
        #################################################################################
        normal_percent_bold = workbook.add_format({'valign':'vcenter', 'align':'right',
                                              'num_format': '0.00%', 'bold': 1})
        normal_percent_bold.set_border()
        normal_percent_bold.set_text_wrap()
        normal_percent_bold.set_font_name('Calibri')
        normal_percent_bold.set_font_size('12')
        #################################################################################
        
        
        #sheet 1 barang jadi
        worksheet1 = workbook.add_worksheet("Losses Barang Jadi")
        worksheet1.set_column('A:A', 10)
        worksheet1.set_column('B:B', 30)
        worksheet1.set_column('C:C', 10)
        worksheet1.set_column('D:AG', 15)

        worksheet1.set_row(0, 26)
        worksheet1.set_row(1, 26)
        worksheet1.set_row(2, 26)
        worksheet1.write('A1', 'Losses Barang Jadi', top_style)
        worksheet1.write('A2', 'Periode : '+str(self.start_date)+' s/d '+str(self.end_date), top_style)
        worksheet1.write('A3',  self.company_id.name, top_style)

        # ----------
        row = 4
        #header
        #row col row col
        worksheet1.merge_range(row, 0, row+1, 0, 'Kode', header_style)
        worksheet1.merge_range(row, 1, row+1, 1, 'Nama Barang', header_style)
        worksheet1.merge_range(row, 2, row, 4, 'Hasil Produksi', header_style)
        worksheet1.write(row+1, 2, 'Qty', header_style)
        worksheet1.write(row+1, 3, 'Value', header_style)
        worksheet1.write(row+1, 4, 'Avg.', header_style)
        worksheet1.merge_range(row, 5, row, 7, 'Adjustment', header_style)
        worksheet1.write(row+1, 5, 'Qty', header_style)
        worksheet1.write(row+1, 6, 'Value', header_style)
        worksheet1.write(row+1, 7, 'Avg.', header_style)
        worksheet1.merge_range(row, 8, row, 10, 'Scrap', header_style)
        worksheet1.write(row+1, 8, 'Qty', header_style)
        worksheet1.write(row+1, 9, 'Value', header_style)
        worksheet1.write(row+1, 10, 'Avg.', header_style)
        worksheet1.merge_range(row, 11, row, 13, 'Total Loss', header_style)
        worksheet1.write(row+1, 11, 'Qty', header_style)
        worksheet1.write(row+1, 12, 'Value', header_style)
        worksheet1.write(row+1, 13, '%.', header_style)
        worksheet1.merge_range(row, 14, row, 16, 'Total Penjualan', header_style)
        worksheet1.write(row+1, 14, 'Qty', header_style)
        worksheet1.write(row+1, 15, 'Value', header_style)
        worksheet1.write(row+1, 16, 'Avg.', header_style)
        worksheet1.write(row+1, 17, 'Qty Forecast.', header_style)
        
        total_qty = 0.0
        total_value = 0.0

        total_qty_do = 0.0
        total_value_do = 0.0
        
        total_qty_adj = 0.0
        total_value_adj = 0.0
        
        total_qty_scrap = 0.0
        total_value_scrap = 0.0
        
        total_qty_loss = 0.0
        total_value_loss = 0.0
        
        for data in result_sql1:
            forecast_qty_ids = self.env['mrp.rph.line'].search([('product_id','=', data[0]),('company_id','=', self.company_id.id),('date','>=',self.start_date),('date','<=',self.end_date)])
            forecast_qty = sum(forecast_qty_ids.mapped('qty_forecast'))
            
            initial = self._get_initial(self.results.filtered(lambda l: l.product_id.id == data[0] and l.is_initial and l.tipe == 'Manufacture'))
            nilai_akhir = self._get_initial_balance(self.results.filtered(lambda l: l.product_id.id == data[0] and l.is_initial and l.tipe == 'Manufacture'))
            avg = nilai_akhir/initial if initial > 0.0 else 0.0

            initial_do = abs(self._get_initial(self.results.filtered(lambda l: l.product_id.id == data[0] and l.is_initial and l.tipe in ('Delivery Order','Retur Penjualan','Retur to Retur Penjualan'))))
            nilai_akhir_do = abs(self._get_initial_balance(self.results.filtered(lambda l: l.product_id.id == data[0] and l.is_initial and l.tipe in ('Delivery Order','Retur Penjualan','Retur to Retur Penjualan'))))
            avg_do = nilai_akhir_do/initial_do if initial_do > 0.0 else 0.0
        
            initial_scrap = self._get_initial(self.results.filtered(lambda l: l.product_id.id == data[0] and 'scrap' in l.tipe.lower().split(' ')))
            nilai_akhir_scrap = self._get_initial_balance(self.results.filtered(lambda l: l.product_id.id == data[0] and 'scrap' in l.tipe.lower().split(' ')))
            avg_scrap = nilai_akhir_scrap / initial_scrap if initial_scrap > 0.0  else 0.0
            
            initial_adjust = self._get_initial(self.results.filtered(lambda l: l.product_id.id == data[0] and 'adjustment' in l.tipe.lower().split(' ')))
            nilai_akhir_adjust = self._get_initial_balance(self.results.filtered(lambda l: l.product_id.id == data[0] and 'adjustment' in l.tipe.lower().split(' ')))
            avg_adj = nilai_akhir_adjust / initial_adjust if initial_adjust > 0.0 else 0.0
            
            initial_adj_scrap = initial_adjust + initial_scrap
            nilai_akhir_scrap_adj = nilai_akhir_scrap + nilai_akhir_adjust

            worksheet1.write(row+2, 0, data[1], normal_style_left)
            worksheet1.write(row+2, 1, data[2], normal_style_left)
            #saldo inventory
            worksheet1.write(row+2, 2, initial, normal_style_right)
            worksheet1.write(row+2, 3, nilai_akhir, normal_style_right)
            worksheet1.write(row+2, 4, avg, normal_style_right)
            
            #adj
            worksheet1.write(row+2, 5, initial_adjust, normal_style_right)
            worksheet1.write(row+2, 6, nilai_akhir_adjust, normal_style_right)
            worksheet1.write(row+2, 7, avg_adj, normal_style_right)
            
            #scrap
            worksheet1.write(row+2, 8, initial_scrap, normal_style_right)
            worksheet1.write(row+2, 9, nilai_akhir_scrap, normal_style_right)
            worksheet1.write(row+2, 10, avg_scrap, normal_style_right)
            
            #total loss
            worksheet1.write(row+2, 11, initial_adjust + initial_scrap, normal_style_right)
            worksheet1.write(row+2, 12, nilai_akhir_scrap + nilai_akhir_adjust, normal_style_right)
            worksheet1.write(row+2, 13, nilai_akhir_scrap_adj/nilai_akhir if nilai_akhir > 0.0 else 0.0, normal_percent)
            
            worksheet1.write(row+2, 14, initial_do, normal_style_right)
            worksheet1.write(row+2, 15, nilai_akhir_do, normal_style_right)
            worksheet1.write(row+2, 16, avg_do, normal_style_right)
            worksheet1.write(row+2, 17, forecast_qty, normal_style_right)

            total_qty += initial
            total_value += nilai_akhir
            total_qty_do += initial_do
            total_value_do += nilai_akhir_do
            total_qty_adj += initial_adjust
            total_value_adj += nilai_akhir_adjust
            total_qty_scrap += initial_scrap
            total_value_scrap += nilai_akhir_scrap
            total_qty_loss += initial_adj_scrap
            total_value_loss += nilai_akhir_scrap_adj
            row += 1
        worksheet1.write(row+2, 2, total_qty, normal_style_right_bold)
        worksheet1.write(row+2, 3, total_value, normal_style_right_bold)
        worksheet1.write(row+2, 5, total_qty_adj, normal_style_right_bold)
        worksheet1.write(row+2, 6, total_value_adj, normal_style_right_bold)
        worksheet1.write(row+2, 8, total_qty_scrap, normal_style_right_bold)
        worksheet1.write(row+2, 9, total_value_scrap, normal_style_right_bold)
        worksheet1.write(row+2, 11, total_qty_loss, normal_style_right_bold)
        worksheet1.write(row+2, 12, total_value_loss, normal_style_right_bold)
        worksheet1.write(row+2, 13, total_value_loss/total_value if total_value > 0.0 else 0.0, normal_percent_bold)
        worksheet1.write(row+2, 14, total_qty_do, normal_style_right_bold)
        worksheet1.write(row+2, 15, total_value_do, normal_style_right_bold)

        row = 0
        worksheet2 = workbook.add_worksheet("Material Variance Report")
        worksheet2.set_column('A:A', 10)
        worksheet2.set_column('B:B', 30)
        worksheet2.set_column('C:C', 10)
        worksheet2.set_column('D:AG', 15)

        worksheet2.set_row(0, 26)
        worksheet2.set_row(1, 26)
        worksheet2.set_row(2, 26)
        worksheet2.write('A1', 'Material Variance Report', top_style)
        worksheet2.write('A2', 'Periode : '+str(self.start_date)+' s/d '+str(self.end_date), top_style)
        worksheet2.write('A3',  self.company_id.name, top_style)

        # ----------
        row = 4
        #header
        #row col row col
        worksheet2.merge_range(row, 0, row+1, 0, 'Kode', header_style)
        worksheet2.merge_range(row, 1, row+1, 1, 'Nama Barang', header_style)
        worksheet2.merge_range(row, 2, row, 4, 'Pemakaian Sesuai Standard', header_style)
        worksheet2.write(row+1, 2, 'Qty', header_style)
        worksheet2.write(row+1, 3, 'Value', header_style)
        worksheet2.write(row+1, 4, 'Avg.', header_style)
        worksheet2.merge_range(row, 5, row, 7, 'Realisasi Pemakaian', header_style)
        worksheet2.write(row+1, 5, 'Qty', header_style)
        worksheet2.write(row+1, 6, 'Value', header_style)
        worksheet2.write(row+1, 7, 'Avg.', header_style)
        worksheet2.merge_range(row, 8, row, 10, 'Adjustment', header_style)
        worksheet2.write(row+1, 8, 'Qty', header_style)
        worksheet2.write(row+1, 9, 'Value', header_style)
        worksheet2.write(row+1, 10, 'Avg.', header_style)
        worksheet2.merge_range(row, 11, row, 13, 'Scrap', header_style)
        worksheet2.write(row+1, 11, 'Qty', header_style)
        worksheet2.write(row+1, 12, 'Value', header_style)
        worksheet2.write(row+1, 13, 'Avg.', header_style)
        worksheet2.merge_range(row, 14, row, 16, 'Selisih Pemakaian', header_style)
        worksheet2.write(row+1, 14, 'Qty', header_style)
        worksheet2.write(row+1, 15, 'Value', header_style)
        worksheet2.write(row+1, 16, 'Avg.', header_style)
        worksheet2.merge_range(row, 17, row+1, 17, 'Losses (%)', header_style)
        classification = ''
        #selisih = standar - realisasi - scrap -adj
        for data in result_sql2:
            avg = 0
            qty_bom = 0
            
            data_5 = data[5] if data[5] else 0.0
            data_6 = data[6] if data[6] else 0.0
            data_7 = data[7] if data[7] else 0.0
            data_8 = data[8] if data[8] else 0.0

            print(">>> Data 0: " + str(data[0]))
            print(">>> Data 1: " + data[1])
            print(">>> Data 2: " + data[2])
            print(">>> Data 3: " + data[3])
            print(">>> data_5 : " + str(data_5))
            print(">>> data_8 : " + str(data_8))
            
            
            initial_scrap = self._get_initial(self.result_query2.filtered(lambda l: l.product_id.id == data[0] and l.company_id.id == self.company_id.id and 'scrap' in l.tipe.lower().split(' ')))
            nilai_akhir_scrap = self._get_initial_balance(self.result_query2.filtered(lambda l: l.product_id.id == data[0] and 'scrap' in l.tipe.lower().split(' ')))
            # avg_scrap = nilai_akhir_scrap / initial_scrap if initial_scrap > 0.0  else 0.0
            initial_adjust = self._get_initial(self.result_query2.filtered(lambda l: l.product_id.id == data[0] and l.company_id.id == self.company_id.id and 'adjustment' in l.tipe.lower().split(' ')))
            nilai_akhir_adjust = self._get_initial_balance(self.result_query2.filtered(lambda l: l.product_id.id == data[0] and 'adjustment' in l.tipe.lower().split(' ')))
            # avg_adj = nilai_akhir_adjust / initial_adjust if initial_adjust > 0.0 else 0.0

            if data[1] and data[1] != classification:
                text = ''
                if data[1] == 'bahanbaku':
                    text = 'Bahan Baku'
                if data[1] == 'barangsetengahjadi':
                    text = 'Barang Setengah Jadi'
                worksheet2.merge_range(row+2, 0, row+2, 11, text, header_style)
                row += 1
            
            qty_bom = data_5 - data_8            
            print(">>> qty_bom : " + str(qty_bom))

            worksheet2.write(row+2, 0, data[2], normal_style_left)
            worksheet2.write(row+2, 1, data[3], normal_style_left)
            #sesuai standard
            worksheet2.write(row+2, 2, qty_bom, normal_style_right)
            worksheet2.write(row+2, 3, data_6, normal_style_right)
            
            if qty_bom != 0:
                avg = data_6/qty_bom
            worksheet2.write(row+2, 4, round(avg, 2), normal_style_right)
            
            #realisasi
            realisasi_qty = data_5
            worksheet2.write(row+2, 5, realisasi_qty, normal_style_right)
            worksheet2.write(row+2, 6, round(avg, 2) * realisasi_qty, normal_style_right)
            worksheet2.write(row+2, 7, round(avg, 2) if realisasi_qty != 0.0 else 0.0, normal_style_right)
            
            #adj
            worksheet2.write(row+2, 8, initial_adjust, normal_style_right)
            worksheet2.write(row+2, 9, round(avg, 2) * initial_adjust, normal_style_right)
            worksheet2.write(row+2, 10, round(avg, 2) if initial_adjust != 0.0 else 0.0, normal_style_right)
            
            #scrap
            worksheet2.write(row+2, 11, initial_scrap, normal_style_right)
            worksheet2.write(row+2, 12, round(avg, 2) * initial_scrap, normal_style_right)
            worksheet2.write(row+2, 13, round(avg, 2) if initial_scrap != 0.0 else 0.0, normal_style_right)
            
            #selisih pemakaian
            # PCI Version
            # worksheet2.write(row+2, 14, qty_bom - realisasi_qty - initial_adjust - initial_scrap, normal_style_right)
            # worksheet2.write(row+2, 15, round(avg, 2) * (qty_bom - realisasi_qty - initial_adjust - initial_scrap), normal_style_right)
            
            # SanQua Version
            worksheet2.write(row+2, 14, qty_bom - realisasi_qty + initial_adjust + initial_scrap, normal_style_right)
            worksheet2.write(row+2, 15, round(avg, 2) * (qty_bom - realisasi_qty + initial_adjust + initial_scrap), normal_style_right)
            worksheet2.write(row+2, 16, round(avg, 2), normal_style_right)
            loss = 0.0
            if data_5 != 0 and data_6 != 0:
                loss = (round(avg, 2) * (qty_bom - realisasi_qty)) / data_6
            worksheet2.write(row+2, 17, loss, normal_percent)
            
            row += 1
            classification = data[1]


        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'state':'get', 'data':out, 'name': filename})
        ir_model_data = self.env['ir.model.data']
        fp.close()

        form_res = ir_model_data.get_object_reference('sanqua_mutasi_inventory_report','mutasi_inventory_wizard_form_view')
        form_id = form_res and form_res[1] or False
        return {
            'name'  : 'Download XLS',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.mutasi.inventory.report',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }