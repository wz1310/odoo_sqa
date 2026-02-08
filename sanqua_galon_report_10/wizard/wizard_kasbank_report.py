# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

import base64
from datetime import datetime
from io import BytesIO

_logger = logging.getLogger(__name__)

class KasBankReportWizard(models.TransientModel):
    _name = 'kas.bank.report.wizard'
    _description = 'Wizard Kas Bank Report'

    date = fields.Date(string='Date')
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)

    def btn_confirm(self):
        query = """
            SELECT 
                ap.name as code,
                rp.name,
                invoice.name,
                CASE WHEN aj.payment_category = 'cek' THEN ap.amount ELSE 0 END as cek,
                CASE WHEN aj.payment_category = 'cash' THEN ap.amount ELSE 0 END as cash
            FROM account_payment ap
            JOIN account_journal aj ON ap.journal_id = aj.id 
            JOIN res_partner rp ON ap.partner_id = rp.id
            JOIN (SELECT srl.settlement_id,ARRAY_AGG(am.name) as name
                    FROM settlement_request_line srl
                    JOIN account_move am ON srl.invoice_id = am.id
                    JOIN settlement_request sr ON srl.settlement_id = sr.id
                    WHERE sr.state = 'done' and am.state = 'posted'
                    GROUP BY srl.settlement_id) as invoice ON invoice.settlement_id = ap.settlement_request_id
            WHERE payment_type = 'inbound' and aj.type in ('cash','bank') and ap.payment_date = %s;
        """
        self.env.cr.execute(query, (self.date.strftime("%Y-%m-%d"),))
        query_res = self.env.cr.fetchall()
        return self.generate_excel(query_res)

    
    def amount_to_text(self, amount):
        """ Convert from amount float to text.
        :param amount: Float. amount value.
        :return: String. Text of amount.
        """
        angka = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan",
                "Sepuluh", "Sebelas"]
        result = " "
        n = int(amount)
        if n >= 0 and n <= 11:
            result = result + angka[n]
        elif n < 20:
            result = amount_to_text(n % 10) + " Belas"
        elif n < 100:
            result = amount_to_text(n / 10) + " Puluh" + amount_to_text(n % 10)
        elif n < 200:
            result = " Seratus" + amount_to_text(n - 100)
        elif n < 1000:
            result = amount_to_text(n / 100) + " Ratus" + amount_to_text(n % 100)
        elif n < 2000:
            result = " Seribu" + amount_to_text(n - 1000)
        elif n < 1000000:
            result = amount_to_text(n / 1000) + " Ribu" + amount_to_text(n % 1000)
        elif n < 1000000000:
            result = amount_to_text(n / 1000000) + " Juta" + amount_to_text(n % 1000000)
        elif n < 1000000000000:
            result = amount_to_text(n / 1000000000) + " Milyar" + amount_to_text(n % 1000000000)
        else:
            result = amount_to_text(n / 1000000000000) + " Triliyun" + amount_to_text(n % 1000000000000)
        return result
        
    def generate_excel(self, data):
        """ Generate excel based from laporan kas bank record. """
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet()

        # =============== HEADER ===============
        header_format = workbook.add_format({'bold': True,'align':'center'})
        header_format.set_border(1)
        center_format = workbook.add_format({'align':'center'})
        worksheet.set_column('A4:A4', 15)
        worksheet.set_column('B4:B4', 15)
        worksheet.set_column('C4:C4', 10)
        worksheet.set_column('D4:E4', 15)
        worksheet.set_column('F4:F4', 15)
        worksheet.merge_range('A1:B1','Bukti penerimaan kas dan bank')
        worksheet.merge_range('D1:E1','Tanggal Kas Bank : ')
        worksheet.write('F1',self.date.strftime("%Y-%m-%d"))
        worksheet.write(3, 0, "Kode",header_format)
        worksheet.write(3, 1, "Nama Konsumen",header_format)
        worksheet.write(3, 2, "No Invoice",header_format)
        worksheet.write(3, 3, "Cek/Giro",header_format)
        worksheet.write(3, 4, "Tunai",header_format)
        worksheet.write(3, 5, "Jumlah",header_format)
        
        # =============== HEADER ===============

        # =============== BODY ===============
        format_right = workbook.add_format({'align': 'right'})
        format_right.set_border(1)
        format_left = workbook.add_format({'align': 'left'})
        format_left.set_border(1)
        sum_total = 0
        row_idx = 4
        for line in data:
            worksheet.write(row_idx, 0, line[0],format_right)
            worksheet.write(row_idx, 1, line[1],format_right)
            worksheet.write(row_idx, 2, ', '.join(line[2]),format_right)
            worksheet.write(row_idx, 3, line[3],format_right)
            worksheet.write(row_idx, 4, line[4],format_right)
            sub_total = float(line[3]) + float(line[4])
            worksheet.write(row_idx, 5, str(sub_total),format_right)
            row_idx += 1
            sum_total = sum_total + sub_total
        # =============== BODY ===============
        row_idx += 2
        worksheet.write(row_idx, 0, "Terbilang")
        worksheet.write(row_idx, 2, "Diserahkan")
        worksheet.write(row_idx, 4, "Diterima")
        worksheet.write(row_idx+1, 0, self.amount_to_text(sum_total))

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        filename = ('bukti_penerimaan_kas_bank_%s.xlsx')%(self.date)
        return self.set_data_excel(out, filename)

    def set_data_excel(self, out, filename):
        """ Update data_file and name based from previous process output. And return action url for download excel. """
        self.write({
            'data_file': out,
            'name': filename
        })

        return {
            'type': 'ir.actions.act_url',
            'name': filename,
            'url': '/web/content/%s/%s/data_file/%s' % (self._name, self.id, filename,),
        }

