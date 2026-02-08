# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from calendar import monthrange
from io import BytesIO
from datetime import date
import base64
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class WizardReturnReport(models.TransientModel):
    _inherit = 'wizard.purchase.order.return.report'

    whs = fields.Many2one('stock.warehouse',string='Warehouse')

    def _get_data_purchase(self):
        print("START", self.start_date)
        print("END", self.end_date)
        print("WHSSS", self.whs)
        wh_filter = ""
        if self.whs:
        	wh_filter = ("AND spt.warehouse_id = %s") % (str(self.whs.id))
        vendor_filter = ""
        if self.vendor_ids:
            if len(self.vendor_ids) == 1:
                data_tuple = "(%s)" % self.vendor_ids.id
            else:
                data_tuple = tuple(self.vendor_ids.ids)
            vendor_filter = ("AND po.partner_id IN %s") % (str(data_tuple))

        product_filter = ""
        if self.product_ids:
            if len(self.product_ids) == 1:
                product_tuple = "(%s)" % self.product_ids.id
            else:
                product_tuple = tuple(self.product_ids.ids)
            product_filter = (" AND po_line.product_id IN %s") % (
                str(product_tuple))
        query = """
            SELECT
                rp.name AS partner_name,
                sp.doc_name AS po_name,
                po.date_order AS date_order,
                pt.name AS product_name,
                po_line.product_qty AS kts,
                po_line.price_unit AS price_unit,
                po_line.qty_received AS total_kts,
                (po_line.product_qty - po_line.qty_received) AS saldo_kts,
                CASE WHEN po.status_po = 'open' THEN 'Sedang Proses'
                WHEN po.status_po = 'done' AND po_line.product_qty != po_line.qty_received THEN 'PO Ditutup'
                WHEN po.status_po = 'done' AND po_line.product_qty = po_line.qty_received THEN 'Terima Penuh'
                WHEN po.status_po = 'close' THEN 'PO ditutup' ELSE 'No Status' END AS status,
                sp.no_sj_vendor as no_sj_vendor,
                po_line.name as deskripsi,
                sp.no_sj_wim as no_sj_wim,
                sp.date_received as tgl_terima,
                sp.scheduled_date as tgl_retur,
                CASE WHEN sp.origin LIKE %s THEN -1 * sm.product_uom_qty ELSE sm.product_uom_qty END as qty_terima,
                cur.name as mata_uang,
                uom.name as satuan, po_line.discount as diskon,
                sp.return_reason as alasan,
                sp.return_type as tipe_retur,
                sp.origin as source_document
            FROM purchase_order po
            LEFT JOIN purchase_order_line po_line ON po_line.order_id = po.id
            JOIN res_partner rp ON rp.id = po.partner_id
            JOIN product_product pp ON pp.id = po_line.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            AND pt.product_classification != 'sparepart'
            LEFT JOIN stock_move sm ON sm.purchase_line_id = po_line.id
            LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
            LEFT JOIN res_currency cur ON po_line.currency_id = cur.id
			LEFT JOIN stock_picking_type spt ON po.picking_type_id = spt.id
            LEFT JOIN uom_uom uom ON po_line.product_uom = uom.id
            WHERE sp.origin LIKE %s AND sp.state = 'done' AND po.company_id = %s AND sp.scheduled_date::DATE BETWEEN %s AND %s """ +wh_filter+vendor_filter+product_filter + """
            ORDER BY sp.date_received, pt.name, rp.name, po.id;
        """
        self._cr.execute(query, ('Return %','Return %',
                         self.company_id.id, self.start_date, self.end_date))
        res = self._cr.dictfetchall()
        return res

    def generate_excel(self, data):
        """ Generate excel based from purchase.order record. """
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet()

        # ========== Format ==============
        header_table = workbook.add_format(
            {'bold': True, 'valign': 'vcenter', 'align': 'center', 'text_wrap': True})
        header_table.set_font_size(12)
        header_table.set_font_name('Times New Roman')
        header_partner_table = workbook.add_format(
            {'bold': True, 'valign': 'vcenter', 'align': 'left', 'text_wrap': True})
        header_partner_table.set_font_size(10)
        header_partner_table.set_font_name('Times New Roman')

        body_table = workbook.add_format()
        body_table.set_align('left')
        body_table.set_align('vcenter')
        body_table.set_font_size(10)
        body_table.set_font_name('Times New Roman')

        body_right_table = workbook.add_format()
        body_right_table.set_align('right')
        body_right_table.set_align('vcenter')
        body_right_table.set_font_size(10)
        body_right_table.set_font_name('Times New Roman')
        body_right_table.set_num_format('#,##0.00')

        header_right_table = workbook.add_format(
            {'bold': True, 'valign': 'vcenter', 'align': 'center', 'text_wrap': True})
        header_right_table.set_align('right')
        header_right_table.set_align('vcenter')
        header_right_table.set_font_size(12)
        header_right_table.set_font_name('Times New Roman')
        header_right_table.set_num_format('#,##0.00')

        # ========== Header ==============
        worksheet.merge_range('A2:I2', self.company_id.name, header_table)
        worksheet.merge_range(
            'A3:I3', 'Laporan Retur Pembelian Bahan Baku ', header_table)
        worksheet.merge_range('A4:I4', (_('Dari %s s/d %s') % (self.start_date.strftime(
            "%d %b %Y"), self.end_date.strftime("%d %b %Y"))), header_table)

        # worksheet.merge_range('B6:G6', 'No. Pesanan',header_table)
        # worksheet.write('C7', 'Tgl Pesan',header_table)
        # worksheet.merge_range('E7:G7', 'Deskripsi Barang',header_table)
        # worksheet.write('I7', 'Qty. Pesan',header_table)
        # worksheet.write('K7', 'Harga Satuan',header_table)
        # worksheet.write('M7', 'Total Qty. Diterima',header_table)
        # worksheet.write('O7', 'Saldo Qty.',header_table)
        # worksheet.merge_range('Q7:R7', 'Status Pesanan',header_table)

# No barang NO PO   NO SJ Vendor    Tanggal SJ  Desk Barang Nama pemasok    Kts Satuan  Harga satuan    Jml Valas   Mata uang   Biaya rata2

        row = 6
        worksheet.write(row, 0, 'No Retur', header_table)
        worksheet.write(row, 1, 'Tgl Retur', header_table)
        worksheet.write(row, 2, 'Deskripsi Barang', header_table)
        worksheet.write(row, 3, 'No SJ Vendor', header_table)
        worksheet.write(row, 4, 'Nama Pemasok', header_table)
        worksheet.write(row, 5, 'Kuantitas', header_table)
        worksheet.write(row, 6, 'Price unit', header_table)
        worksheet.write(row, 7, 'Price total', header_table)
        worksheet.write(row, 8, 'Jenis Retur', header_table)
        worksheet.write(row, 9, 'Alasan Retur', header_table)
        worksheet.write(row, 10, 'No. GR', header_table)

        row = 7
        for rec in data:
            worksheet.write(row, 0, (rec.get('po_name')), body_table)
            worksheet.write(row, 1, rec.get(
                'tgl_retur').strftime("%d %b %Y"), body_table)
            worksheet.write(row, 2, (rec.get('deskripsi')), body_table)
            worksheet.write(row, 3, (rec.get('no_sj_vendor')
                            or rec.get('no_sj_wim')), body_table)
            worksheet.write(row, 4, (rec.get('partner_name')), body_table)
            worksheet.write(row, 5, (rec.get('qty_terima')
                            or '0'), body_right_table)
            worksheet.write(row, 6, (rec.get('price_unit')), body_table)
            worksheet.write(row, 7, (rec.get('qty_terima')*rec.get('price_unit')), body_table)
            worksheet.write(row, 8, (rec.get('tipe_retur')), body_table)
            worksheet.write(row, 9, (rec.get('alasan')), body_table)
            worksheet.write(row, 10, (rec.get('source_document')), body_table)

            row = row + 1

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        filename = ('Laporan Retur Pembelian %s_%s_sd_%s.xlsx') % (
            self.company_id.name, self.start_date, self.end_date)
        return self.set_data_excel(out, filename)

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