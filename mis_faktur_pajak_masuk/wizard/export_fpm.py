
from datetime import datetime
import logging
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
from calendar import monthrange

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
_logger = logging.getLogger(__name__)

# class MakeObj(dict):
#     """Make object"""
#     def __getattr__(self, name):
#         if name in self:
#             return self[name]
#         else:
#             raise AttributeError("No such attribute: " + name)

#     def __setattr__(self, name, value):
#         self[name] = value

#     def __delattr__(self, name):
#         if name in self:
#             del self[name]
#         else:
#             raise AttributeError("No such attribute: " + name)


class ExportFPM(models.TransientModel):
    """Wizard form view of generate E-Faktur"""

    _name = 'export.fpm'
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)
    ex_type = fields.Selection([('xlsx', 'XLSX'), ('csv', 'CSV')], default='xlsx')

    # state_x = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    # data_x = fields.Binary('File', readonly=True)
    # name = fields.Char('Filename', readonly=True)
    # delimiter = fields.Selection([(',', 'comma'), (';', 'semicolon')],
    #                              string='Delimiter', default=',')
    # npwp_o = fields.Boolean('NPWP000', default=False)

    def btn_confirm(self):
        data = self.export_fpm()
        print("DATA",data)
        return self.generate_excel(data)

    def get_active_ids(self):
        active_ids = ''
        context = self.env.context
        model_name = context.get('active_model')
        if model_name == 'account.move':
            move_id = self.env[model_name].browse(context.get('active_ids'))
            print("MOVE_ID",[x.id for x in move_id.fpm_move_id])
            if len(move_id.ids)>1:
                active_ids = tuple(move_id.ids)
            # elif any(not x.fpm_move_id.id for x in move_id):
            #     raise UserError(_("No FPM in %s" % ([x.name for x in move_id if not x.fpm_move_id.id])))
            # elif any(x.fpm_move_id.id and x.fpm_move_id.state_fpm != 'approved' for x in move_id):
            #     raise UserError(_("State FPM not approved in %s" % ([x.name for x in move_id if x.fpm_move_id.state_fpm != 'approved'])))
            elif len(move_id.ids)==1:
                active_ids = "(%s)" % move_id.id
        return active_ids

    def export_fpm(self):
        active_ids = str(self.get_active_ids())
        query = """
        SELECT
        fm as FM,
        kode_jenis as KD_JENIS,
        fg_pengganti as FG_PENGGANTI,
        no_faktur as NOMOR_FAKTUR,
        masa_pajak as MASA_PAJAK,
        tahun_pajak as TAHUN_PAJAK,
        tanggal_faktur as TANGGAL_FAKTUR,
        npwp as NPWP,
        nama_vendor as NAMA,
        alamat as ALAMAT_LENGKAP,
        jumlah_dpp as JUMLAH_DPP,
        jumlah_ppn as JUMLAH_PPN,
        jumlah_ppnbm as JUMLAH_PPNBM,
        is_creditable as IS_CREDITABLE
        FROM "faktur_pajak_masuk" 
        WHERE state_fpm ='approved' AND v_bill in """+active_ids+"""
        """
        self.env.cr.execute(query)
        query_res = self.env.cr.fetchall()
        return query_res

    def generate_excel(self, data):
        """ Generate excel based from label.print record. """
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.formats[0].set_font_name('Arial')
        ##################################################################
        normal_style = workbook.add_format({'valign':'vcenter','font_name':'Calibri', 'font_size':11})
        # normal_style.set_text_wrap()
        #################################################################################
        bold_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'border':1,
            'font_name':'Arial', 'font_size':10})
        bold_style.set_text_wrap()
        #################################################################################
        bolder_style = workbook.add_format({'font_name':'Calibri', 'font_size':11})
        # bolder_style.set_text_wrap()
        #################################################################################
        center_style = workbook.add_format({'valign':'vcenter', 'align':'center', 'border':1,
            'font_name':'Arial', 'font_size':10})
        center_style.set_text_wrap()
        #################################################################################
        b_center_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center',
            'border':1, 'font_name':'Arial', 'font_size':10})
        b_center_style.set_text_wrap()
        #################################################################################
        mb_center_style = workbook.add_format({'bold': 1, 'valign':'vcenter',
            'font_name':'Arial', 'font_size':16})
        mb_center_style.set_text_wrap()
        #################################################################################
        right_style = workbook.add_format({'valign':'vcenter', 'align':'right', 'border':1,
            'num_format': '#,##0', 'font_name':'Arial', 'font_size':10})
        right_style.set_text_wrap()
        #################################################################################
        normal_style_date = workbook.add_format({'valign':'vcenter', 'border':1, 'text_wrap':True,
            'font_size':11, 'font_name': 'Arial', 'num_format': 'dd/mm/yyyy'})
        worksheet = workbook.add_worksheet()

        # =============== HEADER ===============
        header_format = workbook.add_format({'bold': True,'align':'center'})
        center_format = workbook.add_format({'align':'center'})
        # worksheet.set_column('A:Z', 20)
        # worksheet.merge_range('A1:E2','Report Limit Credit',mb_center_style)
        worksheet.write(0, 0, "FM",bolder_style)
        worksheet.write(0, 1, "KD_JENIS_TRANSAKSI",bolder_style)
        worksheet.write(0, 2, "FG_PENGGANTI",bolder_style)
        worksheet.write(0, 3, "NOMOR_FAKTUR",bolder_style)
        worksheet.write(0, 4, "MASA_PAJAK",bolder_style)
        worksheet.write(0, 5, "TAHUN_PAJAK",bolder_style)
        worksheet.write(0, 6, "TANGGAL_FAKTUR",bolder_style)
        worksheet.write(0, 7, "NPWP",bolder_style)
        worksheet.write(0, 8, "NAMA",bolder_style)
        worksheet.write(0, 9, "ALAMAT_LENGKAP",bolder_style)
        worksheet.write(0, 10, "JUMLAH_DPP",bolder_style)
        worksheet.write(0, 11, "JUMLAH_PPN",bolder_style)
        worksheet.write(0, 12, "JUMLAH_PPNBM",bolder_style)
        worksheet.write(0, 13, "IS_CREDITABLE",bolder_style)
        # worksheet.write(3, 14, "Kendala Pengiriman",bolder_style)
        # =============== HEADER ===============

        # =============== BODY ===============
        format_right = workbook.add_format({'align': 'right'})

        row_idx = 1
        for line in data:
            creditable = ''
            if line[13] == True:
                creditable = 1
            elif line[13] == False:
                creditable = 0
            worksheet.write(row_idx, 0, line[0], normal_style)
            worksheet.write(row_idx, 1, line[1], normal_style)
            worksheet.write(row_idx, 2, line[2], normal_style)
            worksheet.write(row_idx, 3, line[3], normal_style)
            worksheet.write(row_idx, 4, line[4], normal_style)
            worksheet.write(row_idx, 5, line[5], normal_style)
            worksheet.write(row_idx, 6, line[6].strftime("%d/%m/%Y"), normal_style)
            worksheet.write(row_idx, 7, line[7], normal_style)
            worksheet.write(row_idx, 8, line[8], normal_style)
            worksheet.write(row_idx, 9, line[9], normal_style)
            worksheet.write(row_idx, 10, line[10], normal_style)
            worksheet.write(row_idx, 11, line[11], normal_style)
            worksheet.write(row_idx, 12, line[12], normal_style)
            worksheet.write(row_idx, 13, creditable, normal_style)
            row_idx += 1
        # =============== BODY ===============

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        fp.close()
        filename = 'export_fpm.xlsx'
        return self.set_data_excel(out, filename)

    def set_data_excel(self, out, filename):
        self.write({
            'data_file': out,
            'name': filename
        })

        return {
            'type': 'ir.actions.act_url',
            'name': filename,
            'url': '/web/content?model=export.fpm&field=data_file&filename_field=name&id=%s&download=true&filename=%s' %(self.id, filename,),
        }

        # =================================== export csv ============================= #

    def export_csv_fpm(self):
        data = self.export_fpm()
        # data = {}
        active_ids = ''
        delimiter = ';'
        context = self.env.context
        model_name = context.get('active_model')
        if model_name == 'account.move':
            move_id = self.env[model_name].browse(context.get('active_ids'))
            if len(move_id.ids)>1:
                active_ids = tuple(move_id.ids)
            elif len(move_id.ids)==1:
                active_ids = move_id.id

        # data.update({
        #     'invoice_ids': active_ids
        #     })
        return self._generate_fp_m(data, delimiter)

    def _generate_fp_m(self, data, delimiter):

        filename = 'export_fpm.csv'
        efaktur_values = self._prepare_fpm_csv(delimiter,data)

        # _logger.info('EFAKTUR VALUES %s' %(efaktur_values))
        output_head = '%s\n' %(
            efaktur_values.get('fk_head'),
            # efaktur_values.get('fpm_datas'),
        )
        for line in data:
            credits = ''
            if line[13] == True:
                credits = 1
            elif line[13] == False:
                credits = 0
            fpm_data = {
                'fpm_datas':
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"%s' \
                    '"%s"' \
                    %(
                        line[0] or '', delimiter,
                        line[1] or '', delimiter,
                        line[2] or '', delimiter,
                        line[3] or '', delimiter,
                        line[4] or '', delimiter,
                        line[5] or '', delimiter,
                        line[6].strftime("%d/%m/%Y") or '', delimiter,
                        line[7] or '', delimiter,
                        line[8] or '', delimiter,
                        line[9] or '', delimiter,
                        int(line[10]) or 0, delimiter,
                        int(line[11]) or 0, delimiter,
                        int(line[12]) or 0, delimiter,
                        credits or '',
                    )}
            output_head += '%s\n' %(
                fpm_data.get('fpm_datas'))
        result = self._generate_fpmasukan(data, delimiter,output_head)
        print("Result",result)
        if data:
            my_utf8 = result.encode("utf-8")
        elif not data:
            raise UserError("No FPM data found...")
        out = base64.b64encode(my_utf8)

        self.write({'data_file':out, 'name': filename})

        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/content?model=export.fpm&field=data_file&filename_field=name&id=%s&download=true&filename=%s' %(self.id, filename,),
            'target': 'self',
        }

    def _prepare_fpm_csv(self, delimiter, data):

        efaktur_values = {
            'fk_head':
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"%s' \
                '"%s"' \
                %(
                    'FM', delimiter,
                    'KD_JENIS_TRANSAKSI', delimiter,
                    'FG_PENGGANTI', delimiter,
                    'NOMOR_FAKTUR', delimiter,
                    'MASA_PAJAK', delimiter,
                    'TAHUN_PAJAK', delimiter,
                    'TANGGAL_FAKTUR', delimiter,
                    'NPWP', delimiter,
                    'NAMA', delimiter,
                    'ALAMAT_LENGKAP', delimiter,
                    'JUMLAH_DPP', delimiter,
                    'JUMLAH_PPN', delimiter,
                    'JUMLAH_PPNBM', delimiter,
                    'IS_CREDITABLE'
                )
        }
        return efaktur_values

    def _generate_fpmasukan(self, data, delimiter, output_head):

        return output_head