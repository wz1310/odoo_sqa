import xlsxwriter
import base64

from io import BytesIO
from odoo import api, fields, models

from odoo.exceptions import ValidationError

class RPMreportingWizard(models.TransientModel):
    _name = 'rpm.reporting.wizard'
    _description = 'Rencana Pembelian Material'

    data_x = fields.Binary('File', readonly=True)
    start_date = fields.Date('From')
    end_date = fields.Date('To')
    
    @api.constrains('start_date', 'end_date')
    def constrains_date(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(_("Start date lebih besar dari End date"))

    def procceed(self):
        
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        filename = 'Rencana Pembelian Material'

        # ============================= Styling =============================
        
        worksheet = workbook.add_worksheet('RPM')    
        worksheet.set_page_view()
        worksheet.set_paper(14)

        cell_format_left = workbook.add_format()
        cell_format_left.set_border(1)
        cell_format_left.set_align('left')
        cell_format_left.set_align('top')
        
        cell_border_number = workbook.add_format({'num_format': '#,##0.00'})
        cell_border_number.set_border(1)
        cell_border_number.set_align('right')
        cell_border_number.set_align('top')

        cell_border_number_no_decimal = workbook.add_format({'num_format': '#,##0'})
        cell_border_number_no_decimal.set_border(1)
        cell_border_number_no_decimal.set_align('right')
        cell_border_number_no_decimal.set_align('top')

        cell_format_bold_center_title = workbook.add_format({'bold': True})
        cell_format_bold_center_title.set_font_size(15)
        cell_format_bold_center_title.set_border(1)
        cell_format_bold_center_title.set_align('center')
        cell_format_bold_center_title.set_align('vcenter')

        cell_format_bold_center = workbook.add_format({'bold': True})
        cell_format_bold_center.set_border(1)
        cell_format_bold_center.set_align('center')
        cell_format_bold_center.set_align('top')

        cell_format_bold_center_orange = workbook.add_format({  'bold': True,
                                                                'fg_color':'#fda600'})
        cell_format_bold_center_orange.set_border(1)
        cell_format_bold_center_orange.set_align('center')
        cell_format_bold_center_orange.set_align('top')

        cell_format_bold_left = workbook.add_format({'bold': True})
        cell_format_bold_left.set_border(1)
        cell_format_bold_left.set_align('left')
        cell_format_bold_left.set_align('top')

        # =======================Raw Material Table==========================
        # ============================= Headers =============================
        worksheet.set_column('A:A',15)
        worksheet.set_column('B:B',25)
        worksheet.set_column('C:C',13)
        worksheet.set_column('D:D',15)
        worksheet.set_column('E:E',15)
        worksheet.set_column('F:F',13)
        worksheet.set_column('G:G',21)
        worksheet.set_column('H:H',21)
        worksheet.set_column('I:I',21)
        worksheet.set_column('J:J',21)
        worksheet.set_column('K:K',23)
        worksheet.set_column('L:L',21)
        worksheet.set_column('M:M',21)
        worksheet.set_column('N:N',21)

        worksheet.set_row(1,30)
        worksheet.freeze_panes('D1')

        row = 7
        worksheet.merge_range('D2:J2', 'Rencana Pembelian Material Bulanan', cell_format_bold_center_title) 
        worksheet.merge_range('A8:A9', 'No. Barang', cell_format_bold_center)
        worksheet.merge_range('B8:B9', 'Deskripsi Barang', cell_format_bold_center)
        worksheet.merge_range('C8:C9', 'Unit 1', cell_format_bold_center)
        worksheet.merge_range('D8:D9', 'Gd. Bahan Baku', cell_format_bold_center)
        worksheet.merge_range('E8:E9', 'Gd. Barang Jadi', cell_format_bold_center)
        worksheet.merge_range('F8:F9', 'Gd. Produksi', cell_format_bold_center)
        worksheet.merge_range('G8:G9', 'Total Stock', cell_format_bold_center)
        worksheet.merge_range('H8:H9', 'OutStanding', cell_format_bold_center)
        worksheet.merge_range('I8:I9', 'Rencana Prod\n-', cell_format_bold_center)
        worksheet.merge_range('J8:J9', 'Forcast\n-', cell_format_bold_center)
        worksheet.merge_range('K8:K9', 'Total', cell_format_bold_center_title)
        worksheet.merge_range('L8:L9', 'Buffer\n20%', cell_format_bold_center) 
        worksheet.merge_range('M8:M9', 'Kurang\nPO', cell_format_bold_center) 
        worksheet.merge_range('N8:N9', 'Buka\nPO', cell_format_bold_center) 
        row = row + 2

        # ============================= Contents =============================
        query = """
            SELECT uom_uom.name uom, product_template.name deskripsi, product_template.default_code number, SUM(mrp_rpm_line_raw_material.qty_on_hand) total, SUM(mrp_rpm_line_raw_material.qty_outstanding_po) outstanding, mrp_rpm_line.current_month_production_plan produksi,
            mrp_rpm_line.next_month_production_plan next_produksi, SUM(mrp_rpm_line_raw_material.tolerance) buffer, SUM(mrp_rpm_line_raw_material.qty_to_pr) buka_po  
            FROM mrp_rpm_line_raw_material
            LEFT JOIN mrp_rpm_line ON mrp_rpm_line.id = mrp_rpm_line_raw_material.line_id
            LEFT JOIN mrp_rpm ON mrp_rpm.id = mrp_rpm_line.rpm_id
            LEFT JOIN product_product ON product_product.id = mrp_rpm_line_raw_material.product_id
            LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
            LEFT JOIN uom_uom ON uom_uom.id = product_template.uom_id
            WHERE mrp_rpm.state IN ('approved','done') AND date >= %s AND date <= %s
            GROUP BY uom_uom.name,product_template.name,product_template.default_code,mrp_rpm_line.current_month_production_plan,
            mrp_rpm_line.next_month_production_plan;
        """
        params = (self.start_date, self.end_date)
        self.env.cr.execute(query, params)
        rpm_raws = self.env.cr.dictfetchall()
        
        
        for rpm in rpm_raws:
            worksheet.write(row,0, rpm.get('number'), cell_format_left)
            worksheet.write(row,1, rpm.get('deskripsi'), cell_format_left)
            worksheet.write(row,2, rpm.get('uom'), cell_format_left)
            worksheet.write(row,3, '-', cell_format_left)
            worksheet.write(row,4, '-', cell_format_left)
            worksheet.write(row,5, '-', cell_format_left)
            worksheet.write(row,6, rpm.get('total'), cell_border_number)
            worksheet.write(row,7, rpm.get('produksi'), cell_border_number)
            worksheet.write(row,8, rpm.get('outstanding'), cell_border_number)
            worksheet.write(row,9, rpm.get('next_produksi'), cell_border_number)
            worksheet.write(row,10, rpm.get('total') + rpm.get('outstanding') - rpm.get('produksi') - rpm.get('next_produksi'), cell_border_number)
            worksheet.write(row,11, rpm.get('buffer'), cell_border_number)
            worksheet.write(row,12, '-', cell_border_number)
            worksheet.write(row,13, rpm.get('buka_po'), cell_border_number)
            row +=1

        # ==========================Product Table==========================
        # ============================= Headers =============================
        row +=3
        worksheet.merge_range('E%s:F%s'%(row,row+1), 'Rencana Produksi -', cell_format_bold_center_orange)
        worksheet.merge_range('G%s:G%s'%(row,row+1), 'Realisasi Produksi\n-', cell_format_bold_center_orange)
        worksheet.merge_range('H%s:H%s'%(row,row+1), 'Rencana Produksi\n-', cell_format_bold_center_orange)
        worksheet.merge_range('I%s:I%s'%(row,row+1), 'Rencana -', cell_format_bold_center_orange)
        row +=1

        # ============================= Contents =============================
        querry_product = """
            SELECT product_template.name deskripsi, SUM(mrp_rpm_line.current_month_production_plan) produksi, SUM(mrp_rpm_line.current_month_realization_production) realisasi,
            SUM(mrp_rpm_line.current_month_not_realization) not_realisasi, SUM(mrp_rpm_line.next_month_production_plan) next_month
            FROM mrp_rpm_line
            LEFT JOIN mrp_rpm ON mrp_rpm.id = mrp_rpm_line.rpm_id
            LEFT JOIN product_product ON product_product.id = mrp_rpm_line.product_id
            LEFT JOIN product_template ON product_template.id = product_product.product_tmpl_id
            WHERE mrp_rpm.state IN ('approved','done') AND date >= %s AND date <= %s
            GROUP BY product_template.name;
        """
        self.env.cr.execute(querry_product, params)
        rpm_products = self.env.cr.dictfetchall()
        for rpm in rpm_products:
            worksheet.write(row,4, rpm.get('deskripsi'), cell_format_left)
            worksheet.write(row,5, rpm.get('produksi'), cell_border_number)
            worksheet.write(row,6, rpm.get('realisasi'), cell_border_number)
            worksheet.write(row,7, rpm.get('not_realisasi'), cell_border_number)
            worksheet.write(row,8, rpm.get('next_month'), cell_border_number)
            row+=1

        workbook.close()
        fp.seek(0)
        out = base64.encodestring(fp.getvalue())
        self.write({
            'data_x': out,
        })
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            'url': '/rencana-pembelian-material-report-download?model=%s&id=%s&filename=%s' % (self._name, self.id, self._description),
            'target': 'self',
        }