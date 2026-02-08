# import pandas as pd
# import glob
# from datetime import datetime
# import logging
# import base64
# from odoo import api, fields, models, _
# from odoo.exceptions import UserError, ValidationError
# from io import BytesIO
# from calendar import monthrange

# try:
#     from odoo.tools.misc import xlsxwriter
# except ImportError:
#     import xlsxwriter
# _logger = logging.getLogger(__name__)


# class ExportFPM(models.TransientModel):
#     """Wizard form view of generate E-Faktur"""

#     _name = 'export.bupot'
#     name = fields.Char(string="Filename", readonly=True)
#     data_file = fields.Binary(string="File", readonly=True)
#     ex_type = fields.Selection([('xlsx', 'XLSX')], default='xlsx')

#     # state_x = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
#     # data_x = fields.Binary('File', readonly=True)
#     # name = fields.Char('Filename', readonly=True)
#     # delimiter = fields.Selection([(',', 'comma'), (';', 'semicolon')],
#     #                              string='Delimiter', default=',')
#     # npwp_o = fields.Boolean('NPWP000', default=False)

#     def btn_confirm(self):
#         data = self.export_bupot()
#         return self.generate_excel(data)

#     def get_active_ids(self):
#         active_ids = ''
#         context = self.env.context
#         model_name = context.get('active_model')
#         if model_name == 'account.move':
#             move_id = self.env[model_name].browse(context.get('active_ids'))
#             print("ID MOVELINE",tuple(move_id.invoice_line_ids.ids))
#             if len(move_id.invoice_line_ids.ids)>1:
#                 active_ids = tuple(move_id.invoice_line_ids.ids)
#             # elif any(not x.fpm_move_id.id for x in move_id):
#             #     raise UserError(_("No FPM in %s" % ([x.name for x in move_id if not x.fpm_move_id.id])))
#             # elif any(x.fpm_move_id.id and x.fpm_move_id.state_fpm != 'approved' for x in move_id):
#             #     raise UserError(_("State FPM not approved in %s" % ([x.name for x in move_id if x.fpm_move_id.state_fpm != 'approved'])))
#             elif len(move_id.invoice_line_ids.ids)==1:
#                 active_ids = "(%s)" % move_id.invoice_line_ids.id
#         return active_ids

#     def export_bupot(self):
#         active_ids = str(self.get_active_ids())
#         query = """
#         SELECT
#         ROW_NUMBER() OVER (ORDER BY id),
#         tgl_potong,
#         pn_npwp_nik,
#         npwp_phs,
#         nik_phs,
#         nm_penerima_nik,
#         qq_nik,
#         no_telp,
#         kode_objek,
#         pdt_bp,
#         pdt_nik,
#         npwp_pdt,
#         nik_pdt,
#         nm_pdt_nik,
#         pg_bruto,
#         mp_fasilitas,
#         no_skb,
#         no_dtp,
#         no_suket,
#         fs_pph,
#         trf_pph,
#         lb,
#         no_work,
#         jn_dok,
#         no_dok,
#         tgl_dok
#         FROM "mis_bukti_potong" 
#         WHERE state_bupot='approved'
#         AND pph_pasal not in (14)
#         AND moveline_id in """+active_ids+"""
#         """
#         self.env.cr.execute(query)
#         query_res = self.env.cr.fetchall()
#         return query_res

#     def generate_excel(self, data):
#         """ Generate excel based from label.print record. """
#         fp = BytesIO()
#         workbook = xlsxwriter.Workbook(fp)
#         workbook.formats[0].set_font_name('Arial')
#         ##################################################################
#         normal_style = workbook.add_format({'valign':'vcenter','font_name':'Calibri', 'font_size':11})
#         bord_style = workbook.add_format({'valign':'vcenter','font_name':'Calibri', 'font_size':11,'border':1})
#         bords_style = workbook.add_format({'bg_color':'#edebeb','valign':'vcenter','font_name':'Calibri', 'font_size':11,'border':1})
#         # normal_style.set_text_wrap()
#         #################################################################################
#         bold_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'border':1,
#             'font_name':'Arial', 'font_size':10})
#         bold_style.set_text_wrap()
#         #################################################################################
#         bolder_style = workbook.add_format({
#             'bg_color':'#edebeb',
#             'font_name':'Calibri',
#             'font_size':11,
#             'text_wrap':True,
#             'valign':'vcenter',
#             'align':'center'})
#         green = workbook.add_format({'bg_color':'#23a128','font_size':16, 'border':2})
#         grey = workbook.add_format({'bg_color':'#828282','font_size':16})
#         greys = workbook.add_format({'bg_color':'#e0e0e0','font_size':16, 'border':2})
#         # bolder_style.set_text_wrap()
#         #################################################################################
#         center_style = workbook.add_format({'valign':'vcenter', 'align':'center', 'border':1,
#             'font_name':'Arial', 'font_size':10})
#         center_style.set_text_wrap()
#         #################################################################################
#         b_center_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center',
#             'border':1, 'font_name':'Arial', 'font_size':10})
#         b_center_style.set_text_wrap()
#         #################################################################################
#         mb_center_style = workbook.add_format({'bold': 1, 'valign':'vcenter',
#             'font_name':'Arial', 'font_size':16})
#         mb_center_style.set_text_wrap()
#         #################################################################################
#         right_style = workbook.add_format({'valign':'vcenter', 'align':'right', 'border':1,
#             'num_format': '#,##0', 'font_name':'Arial', 'font_size':10})
#         right_style.set_text_wrap()
#         #################################################################################
#         normal_style_date = workbook.add_format({'valign':'vcenter', 'border':1, 'text_wrap':True,
#             'font_size':16, 'font_name': 'Arial', 'num_format': 'yyyy'})
#         #################################################################################
#         tahun_pjk = workbook.add_format({'valign':'vcenter', 'border':2,
#             'font_size':16, 'align':'center', 'font_name': 'Arial', 'num_format': 'yyyy'})
#         #################################################################################
#         bln_pjk = workbook.add_format({'valign':'vcenter', 'border':2,
#             'font_size':16, 'font_name': 'Arial', 'align':'center', 'num_format': 'mm'})
#         #################################################################################
#         jbpt = workbook.add_format({'valign':'vcenter', 'border':2,
#             'font_size':16, 'font_name': 'Arial', 'align':'center'})
#         #################################################################################
#         jbptph = workbook.add_format({'valign':'vcenter', 'border':2,
#             'font_size':16, 'font_name': 'Arial', 'align':'center'})
#         #################################################################################
#         tg_pt = workbook.add_format({'valign':'vcenter',
#             'font_size':11, 'font_name': 'Calibri', 'align':'center', 'num_format': 'dd-mm-yy'})
#         #################################################################################

#         rekap = workbook.add_worksheet('Rekap')
#         nm_no_work = [line[22] for line in data]
#         if nm_no_work:
#             n_frs = nm_no_work[0]
#         else:
#             n_frs = ''
#         worksheet = workbook.add_worksheet(n_frs)
#         nr = workbook.add_worksheet('NR')
#         dsr_ptg = workbook.add_worksheet('Dasar Pemotongan')

#         ref_kp = workbook.add_worksheet('Ref Daftar Kode Bukti Potong')
#         ref_kdn = workbook.add_worksheet('Ref Daftar Kode Negara')
#         ref_jdr = workbook.add_worksheet('Ref Jenis Dokumen Referensi')

#         # ===================MERGING DATA FROM DIR========================
#         path_rkp = '/opt/Sanqua_Odoo/Sanqua_Odoo_Addon/sanqua_mis/mis_bukti_potong/template/Ref Daftar Kode Bukti Potong.xlsx'
#         path_kdn = '/opt/Sanqua_Odoo/Sanqua_Odoo_Addon/sanqua_mis/mis_bukti_potong/template/Ref Daftar Kode Negara.xlsx'
#         path_jdr = '/opt/Sanqua_Odoo/Sanqua_Odoo_Addon/sanqua_mis/mis_bukti_potong/template/Ref Jenis Dokumen Referensi.xlsx'
#         file_refkp = glob.glob(path_rkp)
#         file_refkdn = glob.glob(path_kdn)
#         file_refjdr = glob.glob(path_jdr)

#         # =============== HEADER ===============
#         header_format = workbook.add_format({'bold': True,'align':'center'})
#         center_format = workbook.add_format({'align':'center'})
#         tgl_n = fields.Date.today()
#         jm_bpt = 0
#         jm_bptph = 0
#         if data :
#             jm_bpt = len(data)
#         # worksheet.set_column('A:Z', 20)
#         # worksheet.merge_range('A1:E2','Report Limit Credit',mb_center_style)
#         rekap.set_column('B:F',13)
#         rekap.write(0, 0, "",grey)
#         rekap.write(1, 0, "",grey)
#         rekap.write(2, 0, "",grey)
#         rekap.write(3, 0, "",grey)
#         rekap.write(4, 0, "",grey)

#         rekap.write(0, 1, "",grey)
#         rekap.write(0, 2, "",grey)
#         rekap.write(0, 3, "",grey)
#         rekap.write(0, 4, "",grey)
#         rekap.write(0, 5, "",grey)
#         rekap.write(0, 6, "",grey)
#         rekap.write(0, 7, "",grey)

#         rekap.write(1, 7, "",grey)
#         rekap.write(2, 7, "",grey)
#         rekap.write(3, 7, "",grey)
#         rekap.write(4, 7, "",grey)

#         rekap.write(4, 1, "",grey)
#         rekap.write(4, 2, "",grey)
#         rekap.write(4, 3, "",grey)
#         rekap.write(4, 4, "",grey)
#         rekap.write(4, 5, "",grey)
#         rekap.write(4, 6, "",grey)
#         rekap.write(4, 7, "",grey)

#         rekap.write(1, 3, tgl_n,tahun_pjk)
#         rekap.write(1, 6, tgl_n,bln_pjk)
#         rekap.write(2, 6, jm_bpt,jbpt)
#         rekap.write(3, 6, jm_bptph,jbptph)

#         rekap.merge_range('B2:C2', 'Tahun Pajak', greys)
#         rekap.merge_range('E2:F2', 'Masa Pajak', greys)
#         rekap.merge_range('B3:F3', 'Jml Bukti Potong/Pungut PPh Ps 4 ayat (2), Ps 15, Ps 22, Ps 23', greys)
#         rekap.merge_range('B4:F4', 'Jml Bukti Potong/Pungut PPh Non Residen', greys)

#         nr.merge_range('A1:Y1', '', green)
#         nr.set_row(1, 45)
#         nr.set_column('D:S',16)
#         nr.set_column('T:Y',20)
#         nr.set_column('A:A',4)

#         nr.write(1, 0, "No",bolder_style)
#         nr.write(1, 1, "Tgl Pemotongan (dd/MM/yyyy)",bolder_style)
#         nr.write(1, 2, "TIN (dengan format/tanda baca)",bolder_style)
#         nr.write(1, 3, "Nama Penerima Penghasilan",bolder_style)
#         nr.write(1, 4, "Tgl Lahir Penerima Penghasilan (dd/MM/yyyy)",bolder_style)
#         nr.write(1, 5, "Tempat Lahir Penerima Penghasilan",bolder_style)
#         nr.write(1, 6, "Alamat Penerima Penghasilan",bolder_style)
#         nr.write(1, 7, "No Paspor Penerima Penghasilan",bolder_style)
#         nr.write(1, 8, "No Kitas Penerima Penghasilan",bolder_style)
#         nr.write(1, 9, "Kode Negara",bolder_style)
#         nr.write(1, 10, "Kode Objek Pajak",bolder_style)
#         nr.write(1, 11, "Penandatangan BP ? (Pengurus/Kuasa)",bolder_style)
#         nr.write(1, 12, "Penandatangan Menggunakan NPWP/NIK ?",bolder_style)
#         nr.write(1, 13, "NPWP Penandatangan (tanpa format/tanda baca)",bolder_style)
#         nr.write(1, 14, "NIK Penandatangan (tanpa format/tanda baca)",bolder_style)
#         nr.write(1, 15, "Nama Penandatangan Sesuai NIK",bolder_style)
#         nr.write(1, 16, "Penghasilan Bruto",bolder_style)
#         nr.write(1, 17, "Perkiraan Penghasilan Neto (%)",bolder_style)
#         nr.write(1, 18, "Mendapatkan Fasilitas ? (N/SKD / DTP/Lainnya)",bolder_style)
#         nr.write(1, 19, "Nomor Tanda Terima SKD",bolder_style)
#         nr.write(1, 20, "Tarif SKD",bolder_style)
#         nr.write(1, 21, "Nomor Aturan DTP",bolder_style)
#         nr.write(1, 22, "Fasilitas PPh Lainnya",bolder_style)
#         nr.write(1, 23, "Tarif PPh Berdasarkan Fas. PPh Lainnya",bolder_style)
#         nr.write(1, 24, "LB Diproses Oleh ? (Pemotong/Pemindahbukuan)",bolder_style)

#         worksheet.merge_range('A1:V1', '', green)
#         worksheet.set_row(1, 45)
#         worksheet.set_column('D:R',14)
#         worksheet.set_column('A:A',4)

#         worksheet.write(1, 0, "No",bolder_style)
#         worksheet.write(1, 1, "Tgl Pemotongan (dd/MM/yyyy)",bolder_style)
#         worksheet.write(1, 2, "Penerima Penghasilan? (NPWP/NIK)",bolder_style)
#         worksheet.write(1, 3, "NPWP (tanpa format/tanda baca)",bolder_style)
#         worksheet.write(1, 4, "NIK (tanpa format/tanda baca)",bolder_style)
#         worksheet.write(1, 5, "Nama Penerima Penghasilan Sesuai NIK",bolder_style)
#         worksheet.write(1, 6, "qq (khusus NPWP Keluarga)",bolder_style)
#         worksheet.write(1, 7, "Nomor Telp",bolder_style)
#         worksheet.write(1, 8, "Kode Objek Pajak",bolder_style)
#         worksheet.write(1, 9, "Penandatangan BP ? (Pengurus/Kuasa)",bolder_style)
#         worksheet.write(1, 10, "Penandatangan Menggunakan NPWP/NIK ?",bolder_style)
#         worksheet.write(1, 11, "NPWP Penandatangan (tanpa format/tanda baca)",bolder_style)
#         worksheet.write(1, 12, "NIK Penandatangan (tanpa format/tanda baca)",bolder_style)
#         worksheet.write(1, 13, "Nama Penandatangan Sesuai NIK",bolder_style)
#         worksheet.write(1, 14, "Penghasilan Bruto",bolder_style)
#         worksheet.write(1, 15, "Mendapatkan Fasilitas ? (N/SKB / PP23/DTP / Lainnya)",bolder_style)
#         worksheet.write(1, 16, "Nomor SKB",bolder_style)
#         worksheet.write(1, 17, "Nomor Aturan DTP",bolder_style)
#         worksheet.write(1, 18, "Nomor Suket PP23",bolder_style)
#         worksheet.write(1, 19, "Fasilitas PPh Lainnya",bolder_style)
#         worksheet.write(1, 20, "Tarif PPh Berdasarkan Fas. PPh Lainnya",bolder_style)
#         worksheet.write(1, 21, "LB Diproses Oleh ? (Pemotong/Pemindahbukuan)",bolder_style)

#         dsr_ptg.merge_range('A1:E1', '', green)
#         dsr_ptg.set_row(1, 30)
#         dsr_ptg.set_column('A:A',4)
#         dsr_ptg.set_column('B:B',14)
#         dsr_ptg.set_column('C:C',11)
#         dsr_ptg.set_column('D:E',23)
#         dsr_ptg.write(1, 0, "No",bolder_style)
#         dsr_ptg.write(1, 1, "Worksheet",bolder_style)
#         dsr_ptg.write(1, 2, "Jenis Dokumen",bolder_style)
#         dsr_ptg.write(1, 3, "Nomor Dokumen",bolder_style)
#         dsr_ptg.write(1, 4, "Tgl Dokumen (dd/MM/yyyy)",bolder_style)

#         ref_kp.write(1, 1, "Kode Objek Pajak",bords_style)
#         ref_kp.write(1, 2, "Nama Objek Pajak",bords_style)
#         ref_kp.write(1, 3, "PPH Pasal",bords_style)
#         ref_kp.set_column('A:A',2)
#         ref_kp.set_column('B:B',16)
#         ref_kp.set_column('C:C',130)
#         ref_kp.set_column('D:D',9)

#         ref_kdn.write(1, 1, "KODE",bords_style)
#         ref_kdn.write(1, 2, "Nama Negara",bords_style)
#         ref_kdn.set_column('A:A',2)
#         ref_kdn.set_column('B:B',9)
#         ref_kdn.set_column('C:C',35)

#         ref_jdr.write(1, 1, "KODE",bords_style)
#         ref_jdr.write(1, 2, "Jenis Dokumen",bords_style)
#         ref_jdr.set_column('A:A',2)
#         ref_jdr.set_column('B:B',9)
#         ref_jdr.set_column('C:C',30)
#         # worksheet.write(3, 14, "Kendala Pengiriman",bolder_style)
#         # =============== HEADER ===============

#         # =============== BODY ===============
#         format_right = workbook.add_format({'align': 'right'})

#         m_f = ''
#         pp_npw = ''
#         k_obj = ''
#         row_idx = 2
#         for line in data:
#             creditable = ''
#             if line[13] == True:
#                 creditable = 1
#             elif line[13] == False:
#                 creditable = 0
#             elif line[8]:
#                 k_obj = self.env['mis.kode.objek.line'].search([('id','=',line[8])]).name
#             if line[10] == 'npwp':
#                 pp_npw = "NPWP"
#             elif line[10] == 'nik':
#                 pp_npw = "NIK"
#             if line[15] == 'n':
#                 m_f = "N"
#             if line[15] == 'skb':
#                 m_f = "SKB"
#             elif line[15] == 'pp23':
#                 m_f = "PP23"
#             elif line[15] == 'dtp':
#                 m_f = "DTP"
#             elif line[15] == 'lain':
#                 m_f = "Lainnya"
#             worksheet.write(row_idx, 0, line[0], normal_style)
#             worksheet.write(row_idx, 1, line[1], tg_pt)
#             worksheet.write(row_idx, 2, line[2], normal_style)
#             worksheet.write(row_idx, 3, line[3], normal_style)
#             worksheet.write(row_idx, 4, line[4], normal_style)
#             worksheet.write(row_idx, 5, line[5], normal_style)
#             worksheet.write(row_idx, 6, line[6], normal_style)
#             worksheet.write(row_idx, 7, line[7], normal_style)
#             worksheet.write(row_idx, 8, k_obj, normal_style)
#             worksheet.write(row_idx, 9, line[9], normal_style)
#             worksheet.write(row_idx, 10, pp_npw, normal_style)
#             worksheet.write(row_idx, 11, line[11], normal_style)
#             worksheet.write(row_idx, 12, line[12], normal_style)
#             worksheet.write(row_idx, 13, line[13], normal_style)
#             worksheet.write(row_idx, 14, line[14], normal_style)
#             worksheet.write(row_idx, 15, m_f, normal_style)
#             worksheet.write(row_idx, 16, line[16], normal_style)
#             worksheet.write(row_idx, 17, line[17], normal_style)
#             worksheet.write(row_idx, 18, line[18], normal_style)
#             worksheet.write(row_idx, 19, line[19], normal_style)
#             worksheet.write(row_idx, 20, line[20], normal_style)
#             worksheet.write(row_idx, 21, line[21], normal_style)

#             dsr_ptg.write(row_idx, 0, line[0], normal_style)
#             dsr_ptg.write(row_idx, 1, line[22], normal_style)
#             dsr_ptg.write(row_idx, 2, line[23], normal_style)
#             dsr_ptg.write(row_idx, 3, line[24], normal_style)
#             dsr_ptg.write(row_idx, 4, line[25], tg_pt)
#             row_idx += 1
#         # =============== BODY ===============
#         # ======================add external excel===============
#         row_kop = 2
#         row_nop = 2
#         row_pph = 2
#         for file in file_refkp:
#             ref_file = pd.read_excel(file)
#             ref_dict = ref_file.to_dict()
#             kop = ref_dict['Kode Objek Pajak'].values()
#             nop = ref_dict['Nama Objek Pajak'].values()
#             phh = ref_dict['PPH Pasal'].values()
#             for x in kop:
#                 ref_kp.write(row_kop,1, x, bord_style)
#                 row_kop += 1
#             for x in nop:
#                 ref_kp.write(row_nop,2, x, bord_style)
#                 row_nop += 1
#             for x in phh:
#                 ref_kp.write(row_pph,3, x, bord_style)
#                 row_pph += 1

#         row_rkd = 2
#         row_nmn = 2
#         for file in file_refkdn:
#             ref_file = pd.read_excel(file)
#             ref_dict = ref_file.to_dict()
#             kd = ref_dict['KODE'].values()
#             nmn = ref_dict['Nama Negara'].values()
#             for x in kd:
#                 ref_kdn.write(row_rkd,1, x, bord_style)
#                 row_rkd += 1
#             for x in nmn:
#                 ref_kdn.write(row_nmn,2, x, bord_style)
#                 row_nmn += 1

#         row_rdk = 2
#         row_jdok = 2
#         for file in file_refjdr:
#             ref_file = pd.read_excel(file)
#             ref_dict = ref_file.to_dict()
#             kd = ref_dict['KODE'].values()
#             jnd = ref_dict['Jenis Dokumen'].values()
#             for x in kd:
#                 ref_jdr.write(row_rdk,1, x, bord_style)
#                 row_rdk += 1
#             for x in jnd:
#                 ref_jdr.write(row_jdok,2, x, bord_style)
#                 row_jdok += 1

#         workbook.close()
#         out = base64.b64encode(fp.getvalue())
#         fp.close()
#         filename = 'export_bupot.xls'
#         return self.set_data_excel(out, filename)

#     def set_data_excel(self, out, filename):
#         self.write({
#             'data_file': out,
#             'name': filename
#         })

#         return {
#             'type': 'ir.actions.act_url',
#             'name': filename,
#             'url': '/web/content?model=export.bupot&field=data_file&filename_field=name&id=%s&download=true&filename=%s' %(self.id, filename,),
#         }

#         # =================================== export csv ============================= #

#     def export_csv_fpm(self):
#         data = self.export_bupot()
#         # data = {}
#         active_ids = ''
#         delimiter = ','
#         context = self.env.context
#         model_name = context.get('active_model')
#         if model_name == 'account.move':
#             move_id = self.env[model_name].browse(context.get('active_ids'))
#             if len(move_id.ids)>1:
#                 active_ids = tuple(move_id.ids)
#             elif len(move_id.ids)==1:
#                 active_ids = move_id.id

#         # data.update({
#         #     'invoice_ids': active_ids
#         #     })
#         return self._generate_efaktur(data, delimiter)

#     def _generate_efaktur(self, data, delimiter):

#         filename = 'export_bupot.csv'
#         efaktur_values = self._prepare_efaktur_csv(delimiter,data)

#         # _logger.info('EFAKTUR VALUES %s' %(efaktur_values))
#         output_head = '%s\n' %(
#             efaktur_values.get('fk_head'),
#             # efaktur_values.get('fpm_datas'),
#         )
#         for line in data:
#             credits = ''
#             if line[13] == True:
#                 credits = 1
#             elif line[13] == False:
#                 credits = 0
#             fpm_data = {
#                 'fpm_datas':
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"%s' \
#                     '"%s"' \
#                     %(
#                         line[0] or '', delimiter,
#                         line[1] or '', delimiter,
#                         line[2] or '', delimiter,
#                         line[3] or '', delimiter,
#                         line[4] or '', delimiter,
#                         line[5] or '', delimiter,
#                         line[6] or '', delimiter,
#                         line[7] or '', delimiter,
#                         line[8] or '', delimiter,
#                         line[9] or '', delimiter,
#                         line[10] or '', delimiter,
#                         line[11] or '', delimiter,
#                         line[12] or '', delimiter,
#                         credits or '',
#                     )}
#             output_head += '%s\n' %(
#                 fpm_data.get('fpm_datas'))
#         result = self._generate_efaktur_purchase(data, delimiter,output_head)
#         if data:
#             my_utf8 = result.encode("utf-8")
#         out = base64.b64encode(my_utf8)

#         self.write({'data_file':out, 'name': filename})

#         return {
#             'type' : 'ir.actions.act_url',
#             'url': '/web/content?model=export.fpm&field=data_file&filename_field=name&id=%s&download=true&filename=%s' %(self.id, filename,),
#             'target': 'self',
#         }

#     def _prepare_efaktur_csv(self, delimiter, data):

#         efaktur_values = {
#             'fk_head':
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"%s' \
#                 '"%s"' \
#                 %(
#                     'FM', delimiter,
#                     'KD_JENIS_TRANSAKSI', delimiter,
#                     'FG_PENGGANTI', delimiter,
#                     'NOMOR_FAKTUR', delimiter,
#                     'MASA_PAJAK', delimiter,
#                     'TAHUN_PAJAK', delimiter,
#                     'TANGGAL_FAKTUR', delimiter,
#                     'NPWP', delimiter,
#                     'NAMA', delimiter,
#                     'ALAMAT_LENGKAP', delimiter,
#                     'JUMLAH_DPP', delimiter,
#                     'JUMLAH_PPN', delimiter,
#                     'JUMLAH_PPNBM', delimiter,
#                     'IS_CREDITABLE'
#                 )
#         }
#         return efaktur_values

#     def _generate_efaktur_purchase(self, data, delimiter, output_head):
#         """Generate E-Faktur for Purchase / Vendor Bills"""

#         # Invoice of Supplier

#         return output_head

import pandas as pd
import glob
from datetime import datetime
import logging
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
from calendar import monthrange
import xlwt
from xlwt import easyxf

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
_logger = logging.getLogger(__name__)


class ExportFPM(models.TransientModel):
    """Wizard form view of generate E-Faktur"""

    _name = 'export.bupot'
    name = fields.Char(string="Filename", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)
    ex_type = fields.Selection([('xlsx', 'XLSX')], default='xlsx')

    # state_x = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    # data_x = fields.Binary('File', readonly=True)
    # name = fields.Char('Filename', readonly=True)
    # delimiter = fields.Selection([(',', 'comma'), (';', 'semicolon')],
    #                              string='Delimiter', default=',')
    # npwp_o = fields.Boolean('NPWP000', default=False)

    def btn_confirm(self):
        data = self.export_bupot()
        return self.generate_excel(data)

    def get_active_ids(self):
        active_ids = ''
        context = self.env.context
        model_name = context.get('active_model')
        if model_name == 'account.move':
            move_id = self.env[model_name].browse(context.get('active_ids'))
            print("ID MOVELINE",tuple(move_id.invoice_line_ids.ids))
            if len(move_id.invoice_line_ids.ids)>1:
                active_ids = tuple(move_id.invoice_line_ids.ids)
            # elif any(not x.fpm_move_id.id for x in move_id):
            #     raise UserError(_("No FPM in %s" % ([x.name for x in move_id if not x.fpm_move_id.id])))
            # elif any(x.fpm_move_id.id and x.fpm_move_id.state_fpm != 'approved' for x in move_id):
            #     raise UserError(_("State FPM not approved in %s" % ([x.name for x in move_id if x.fpm_move_id.state_fpm != 'approved'])))
            elif len(move_id.invoice_line_ids.ids)==1:
                active_ids = "(%s)" % move_id.invoice_line_ids.id
        return active_ids

    def export_bupot(self):
        active_ids = str(self.get_active_ids())
        query = """
        SELECT
        ROW_NUMBER() OVER (ORDER BY id),
        tgl_potong,
        pn_npwp_nik,
        npwp_phs,
        nik_phs,
        nm_penerima_nik,
        qq_nik,
        no_telp,
        kode_objek,
        pdt_bp,
        pdt_nik,
        npwp_pdt,
        nik_pdt,
        nm_pdt_nik,
        pg_bruto,
        mp_fasilitas,
        no_skb,
        no_dtp,
        no_suket,
        fs_pph,
        trf_pph,
        lb,
        no_work,
        jn_dok,
        no_dok,
        tgl_dok
        FROM "mis_bukti_potong" 
        WHERE state_bupot='approved'
        AND pph_pasal not in (9)
        AND moveline_id in """+active_ids+"""
        """
        self.env.cr.execute(query)
        query_res = self.env.cr.fetchall()
        return query_res

    def generate_excel(self, data):
        """ Generate excel based from label.print record. """
        fp = BytesIO()
        workbook = xlwt.Workbook()
        # workbook.formats[0].set_font_name('Arial')
        ##################################################################
        normal_style = easyxf('align: horiz center;')
        bord_style = easyxf('align: wrap on,vert top, horiz center;')
        bords_style = easyxf('align: wrap on,vert top, horiz left;')
        # normal_style.set_text_wrap()
        #################################################################################
        bold_style = easyxf('align: horiz center;')
        # bold_style.set_text_wrap()
        #################################################################################
        bolder_style = easyxf('align: wrap on,vert top, horiz center;pattern: pattern solid, fore_color gray25;'
            "borders: top thin,left thin,right thin,bottom thin")
        green = easyxf('pattern: pattern solid, fore_color dark_green_ega;')
        val_rek = easyxf('align: horiz center;font:height 200;pattern: pattern solid, fore_color light_turquoise;'
            "borders: top thin,left thin,right thin,bottom thin")
        grey = easyxf('font:height 200;pattern: pattern solid, fore_color gray_ega;')
        greys = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
            "borders: top thin,left thin,right thin,bottom thin")
        # bolder_style.set_text_wrap()
        # #################################################################################
        # center_style = workbook.add_format({'valign':'vcenter', 'align':'center', 'border':1,
        #     'font_name':'Arial', 'font_size':10})
        # center_style.set_text_wrap()
        # #################################################################################
        # b_center_style = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center',
        #     'border':1, 'font_name':'Arial', 'font_size':10})
        # b_center_style.set_text_wrap()
        # #################################################################################
        # mb_center_style = workbook.add_format({'bold': 1, 'valign':'vcenter',
        #     'font_name':'Arial', 'font_size':16})
        # mb_center_style.set_text_wrap()
        # #################################################################################
        # right_style = workbook.add_format({'valign':'vcenter', 'align':'right', 'border':1,
        #     'num_format': '#,##0', 'font_name':'Arial', 'font_size':10})
        # right_style.set_text_wrap()
        # #################################################################################
        # normal_style_date = workbook.add_format({'valign':'vcenter', 'border':1, 'text_wrap':True,
        #     'font_size':16, 'font_name': 'Arial', 'num_format': 'yyyy'})
        # #################################################################################
        tahun_pjk = easyxf('align: horiz center;')
        # #################################################################################
        bln_pjk = easyxf('align: horiz center;')
        # #################################################################################
        jbpt = easyxf('align: horiz center;')
        # #################################################################################
        jbptph = easyxf('align: horiz center;')
        # #################################################################################
        tg_pt = easyxf('align: horiz center;')
        # #################################################################################

        rekap = workbook.add_sheet('Rekap',cell_overwrite_ok=True)
        nm_no_work = [line[22] for line in data]
        if nm_no_work:
            n_frs = nm_no_work[0]
        else:
            n_frs = ''
        worksheet = workbook.add_sheet(n_frs)
        nr = workbook.add_sheet('NR',cell_overwrite_ok=True)
        dsr_ptg = workbook.add_sheet('Dasar Pemotongan',cell_overwrite_ok=True)

        ref_kp = workbook.add_sheet('Ref Daftar Kode Bukti Potong',cell_overwrite_ok=True)
        ref_kdn = workbook.add_sheet('Ref Daftar Kode Negara',cell_overwrite_ok=True)
        ref_jdr = workbook.add_sheet('Ref Jenis Dokumen Referensi',cell_overwrite_ok=True)

        # ===================MERGING DATA FROM DIR========================
        path_rkp = 'C:/Users/mispr/OneDrive/Documents/odoo13/addons_tambahan/mis_faktur_pajak_masuk/Ref Daftar Kode Bukti Potong.xlsx'
        path_kdn = 'C:/Users/mispr/OneDrive/Documents/odoo13/addons_tambahan/mis_faktur_pajak_masuk/Ref Daftar Kode Negara.xlsx'
        path_jdr = 'C:/Users/mispr/OneDrive/Documents/odoo13/addons_tambahan/mis_faktur_pajak_masuk/Ref Jenis Dokumen Referensi.xlsx'
        file_refkp = glob.glob(path_rkp)
        file_refkdn = glob.glob(path_kdn)
        file_refjdr = glob.glob(path_jdr)

        # =============== HEADER ===============
        # header_format = workbook.add_format({'bold': True,'align':'center'})
        # center_format = workbook.add_format({'align':'center'})
        tgl_n = fields.Date.today()
        jm_bpt = 0
        jm_bptph = 0
        if data :
            jm_bpt = len(data)
        # worksheet.set_column('A:Z', 20)
        # worksheet.merge_range('A1:E2','Report Limit Credit',mb_center_style)
        rekap.col(1).width = 5000
        rekap.write(0, 0, "",grey)
        rekap.write(1, 0, "",grey)
        rekap.write(2, 0, "",grey)
        rekap.write(3, 0, "",grey)
        rekap.write(4, 0, "",grey)

        rekap.write(0, 1, "",grey)
        rekap.write(0, 2, "",grey)
        rekap.write(0, 3, "",grey)
        rekap.write(0, 4, "",grey)
        rekap.write(0, 5, "",grey)
        rekap.write(0, 6, "",grey)
        rekap.write(0, 7, "",grey)

        rekap.write(1, 7, "",grey)
        rekap.write(2, 7, "",grey)
        rekap.write(3, 7, "",grey)
        rekap.write(4, 7, "",grey)

        rekap.write(4, 1, "",grey)
        rekap.write(4, 2, "",grey)
        rekap.write(4, 3, "",grey)
        rekap.write(4, 4, "",grey)
        rekap.write(4, 5, "",grey)
        rekap.write(4, 6, "",grey)

        rekap.write(1, 3, tgl_n.strftime("%Y"),val_rek)
        rekap.write(1, 6, tgl_n.strftime("%m"),val_rek)
        rekap.write(2, 6, int(jm_bpt),val_rek)
        rekap.write(3, 6, int(jm_bptph),val_rek)

        rekap.write_merge(1,1,1,2, 'Tahun Pajak', greys)
        rekap.write_merge(1,1,4,5, 'Masa Pajak', greys)
        rekap.write_merge(2,2,1,5, 'Jml Bukti Potong/Pungut PPh Ps 4 ayat (2), Ps 15, Ps 22, Ps 23', greys)
        rekap.write_merge(3,3,1,5, 'Jml Bukti Potong/Pungut PPh Non Residen', greys)

        # nr.write('A1:Y1', '', green)
        # nr.set_row(1, 45)
        # nr.set_column('D:S',16)
        # nr.set_column('T:Y',20)
        # nr.set_column('A:A',4)

        # nr.col(0).width = 256 * 30
        nr.col(1).width = 256 * 30
        nr.col(2).width = 256 * 30
        nr.col(3).width = 256 * 30
        nr.col(4).width = 256 * 30
        nr.col(5).width = 256 * 30
        nr.col(6).width = 256 * 30
        nr.col(7).width = 256 * 30
        nr.col(8).width = 256 * 30
        nr.col(9).width = 256 * 30
        nr.col(10).width = 256 * 30
        nr.col(11).width = 256 * 30
        nr.col(12).width = 256 * 30
        nr.col(13).width = 256 * 30
        nr.col(14).width = 256 * 30
        nr.col(15).width = 256 * 30
        nr.col(16).width = 256 * 30
        nr.col(17).width = 256 * 30
        nr.col(18).width = 256 * 30
        nr.col(19).width = 256 * 30
        nr.col(20).width = 256 * 30
        nr.col(21).width = 256 * 30
        nr.col(22).width = 256 * 30
        nr.col(23).width = 256 * 30
        nr.col(24).width = 256 * 30
        nr.write(1, 0, "No",bolder_style)
        nr.write(1, 1, "Tgl Pemotongan (dd/MM/yyyy)",bolder_style)
        nr.write(1, 2, "TIN (dengan format/tanda baca)",bolder_style)
        nr.write(1, 3, "Nama Penerima Penghasilan",bolder_style)
        nr.write(1, 4, "Tgl Lahir Penerima Penghasilan (dd/MM/yyyy)",bolder_style)
        nr.write(1, 5, "Tempat Lahir Penerima Penghasilan",bolder_style)
        nr.write(1, 6, "Alamat Penerima Penghasilan",bolder_style)
        nr.write(1, 7, "No Paspor Penerima Penghasilan",bolder_style)
        nr.write(1, 8, "No Kitas Penerima Penghasilan",bolder_style)
        nr.write(1, 9, "Kode Negara",bolder_style)
        nr.write(1, 10, "Kode Objek Pajak",bolder_style)
        nr.write(1, 11, "Penandatangan BP ? (Pengurus/Kuasa)",bolder_style)
        nr.write(1, 12, "Penandatangan Menggunakan NPWP/NIK ?",bolder_style)
        nr.write(1, 13, "NPWP Penandatangan (tanpa format/tanda baca)",bolder_style)
        nr.write(1, 14, "NIK Penandatangan (tanpa format/tanda baca)",bolder_style)
        nr.write(1, 15, "Nama Penandatangan Sesuai NIK",bolder_style)
        nr.write(1, 16, "Penghasilan Bruto",bolder_style)
        nr.write(1, 17, "Perkiraan Penghasilan Neto (%)",bolder_style)
        nr.write(1, 18, "Mendapatkan Fasilitas ? (N/SKD / DTP/Lainnya)",bolder_style)
        nr.write(1, 19, "Nomor Tanda Terima SKD",bolder_style)
        nr.write(1, 20, "Tarif SKD",bolder_style)
        nr.write(1, 21, "Nomor Aturan DTP",bolder_style)
        nr.write(1, 22, "Fasilitas PPh Lainnya",bolder_style)
        nr.write(1, 23, "Tarif PPh Berdasarkan Fas. PPh Lainnya",bolder_style)
        nr.write(1, 24, "LB Diproses Oleh ? (Pemotong/Pemindahbukuan)",bolder_style)

        # worksheet.merge_range('A1:V1', '', green)
        # worksheet.set_row(1, 45)
        # worksheet.set_column('D:R',14)
        # worksheet.set_column('A:A',4)

        # worksheet.write_merge(0,0,0,21,'',green)
        worksheet.col(1).width = 256 * 30
        worksheet.col(2).width = 256 * 30
        worksheet.col(3).width = 256 * 30
        worksheet.col(4).width = 256 * 30
        worksheet.col(5).width = 256 * 30
        worksheet.col(6).width = 256 * 30
        worksheet.col(7).width = 256 * 30
        worksheet.col(8).width = 256 * 30
        worksheet.col(9).width = 256 * 30
        worksheet.col(10).width = 256 * 30
        worksheet.col(11).width = 256 * 30
        worksheet.col(12).width = 256 * 30
        worksheet.col(13).width = 256 * 30
        worksheet.col(14).width = 256 * 30
        worksheet.col(15).width = 256 * 30
        worksheet.col(16).width = 256 * 30
        worksheet.col(17).width = 256 * 30
        worksheet.col(18).width = 256 * 30
        worksheet.col(19).width = 256 * 30
        worksheet.col(20).width = 256 * 30
        worksheet.col(21).width = 256 * 30
        worksheet.write(1, 0, "No",bolder_style)
        worksheet.write(1, 1, "Tgl Pemotongan (dd/MM/yyyy)",bolder_style)
        worksheet.write(1, 2, "Penerima Penghasilan? (NPWP/NIK)",bolder_style)
        worksheet.write(1, 3, "NPWP (tanpa format/tanda baca)",bolder_style)
        worksheet.write(1, 4, "NIK (tanpa format/tanda baca)",bolder_style)
        worksheet.write(1, 5, "Nama Penerima Penghasilan Sesuai NIK",bolder_style)
        worksheet.write(1, 6, "qq (khusus NPWP Keluarga)",bolder_style)
        worksheet.write(1, 7, "Nomor Telp",bolder_style)
        worksheet.write(1, 8, "Kode Objek Pajak",bolder_style)
        worksheet.write(1, 9, "Penandatangan BP ? (Pengurus/Kuasa)",bolder_style)
        worksheet.write(1, 10, "Penandatangan Menggunakan NPWP/NIK ?",bolder_style)
        worksheet.write(1, 11, "NPWP Penandatangan (tanpa format/tanda baca)",bolder_style)
        worksheet.write(1, 12, "NIK Penandatangan (tanpa format/tanda baca)",bolder_style)
        worksheet.write(1, 13, "Nama Penandatangan Sesuai NIK",bolder_style)
        worksheet.write(1, 14, "Penghasilan Bruto",bolder_style)
        worksheet.write(1, 15, "Mendapatkan Fasilitas ? (N/SKB / PP23/DTP / Lainnya)",bolder_style)
        worksheet.write(1, 16, "Nomor SKB",bolder_style)
        worksheet.write(1, 17, "Nomor Aturan DTP",bolder_style)
        worksheet.write(1, 18, "Nomor Suket PP23",bolder_style)
        worksheet.write(1, 19, "Fasilitas PPh Lainnya",bolder_style)
        worksheet.write(1, 20, "Tarif PPh Berdasarkan Fas. PPh Lainnya",bolder_style)
        worksheet.write(1, 21, "LB Diproses Oleh ? (Pemotong/Pemindahbukuan)",bolder_style)

        # dsr_ptg.merge_range('A1:E1', '', green)
        # dsr_ptg.set_row(1, 30)
        # dsr_ptg.set_column('A:A',4)
        # dsr_ptg.set_column('B:B',14)
        # dsr_ptg.set_column('C:C',11)
        # dsr_ptg.set_column('D:E',23)
        dsr_ptg.col(1).width = 256 * 20
        dsr_ptg.col(2).width = 256 * 20
        dsr_ptg.col(3).width = 256 * 20
        dsr_ptg.col(4).width = 256 * 20
        dsr_ptg.write(1, 0, "No",bolder_style)
        dsr_ptg.write(1, 1, "Worksheet",bolder_style)
        dsr_ptg.write(1, 2, "Jenis Dokumen",bolder_style)
        dsr_ptg.write(1, 3, "Nomor Dokumen",bolder_style)
        dsr_ptg.write(1, 4, "Tgl Dokumen (dd/MM/yyyy)",bolder_style)

        ref_kp.col(1).width = 256 * 20
        ref_kp.col(2).width = 256 * 40
        ref_kp.col(3).width = 256 * 20
        ref_kp.write(1, 1, "Kode Objek Pajak",bolder_style)
        ref_kp.write(1, 2, "Nama Objek Pajak",bolder_style)
        ref_kp.write(1, 3, "PPH Pasal",bolder_style)
        # ref_kp.set_column('A:A',2)
        # ref_kp.set_column('B:B',16)
        # ref_kp.set_column('C:C',130)
        # ref_kp.set_column('D:D',9)

        ref_kdn.col(1).width = 256 * 20
        ref_kdn.col(2).width = 256 * 20
        ref_kdn.write(1, 1, "KODE",bolder_style)
        ref_kdn.write(1, 2, "Nama Negara",bolder_style)
        # ref_kdn.set_column('A:A',2)
        # ref_kdn.set_column('B:B',9)
        # ref_kdn.set_column('C:C',35)

        ref_jdr.col(1).width = 256 * 20
        ref_jdr.col(2).width = 256 * 20
        ref_jdr.write(1, 1, "KODE",bolder_style)
        ref_jdr.write(1, 2, "Jenis Dokumen",bolder_style)
        # ref_jdr.set_column('A:A',2)
        # ref_jdr.set_column('B:B',9)
        # ref_jdr.set_column('C:C',30)
        # worksheet.write(3, 14, "Kendala Pengiriman",bolder_style)
        # =============== HEADER ===============

        # =============== BODY ===============
        # format_right = workbook.add_format({'align': 'right'})

        m_f = ''
        pp_npw = ''
        k_obj = ''
        row_idx = 2
        for line in data:
            creditable = ''
            if line[13] == True:
                creditable = 1
            elif line[13] == False:
                creditable = 0
            elif line[8]:
                k_obj = self.env['mis.kode.objek.line'].search([('id','=',line[8])]).name
            if line[10] == 'npwp':
                pp_npw = "NPWP"
            elif line[10] == 'nik':
                pp_npw = "NIK"
            if line[15] == 'n':
                m_f = "N"
            if line[15] == 'skb':
                m_f = "SKB"
            elif line[15] == 'pp23':
                m_f = "PP23"
            elif line[15] == 'dtp':
                m_f = "DTP"
            elif line[15] == 'lain':
                m_f = "Lainnya"
            worksheet.write(row_idx, 0, line[0], normal_style)
            worksheet.write(row_idx, 1, line[1].strftime("%d/%m/%Y") if line[1] else '', tg_pt)
            worksheet.write(row_idx, 2, line[2], normal_style)
            worksheet.write(row_idx, 3, line[3], normal_style)
            worksheet.write(row_idx, 4, line[4], normal_style)
            worksheet.write(row_idx, 5, line[5], normal_style)
            worksheet.write(row_idx, 6, line[6], normal_style)
            worksheet.write(row_idx, 7, line[7], normal_style)
            worksheet.write(row_idx, 8, k_obj, normal_style)
            worksheet.write(row_idx, 9, line[9], normal_style)
            worksheet.write(row_idx, 10, pp_npw, normal_style)
            worksheet.write(row_idx, 11, line[11], normal_style)
            worksheet.write(row_idx, 12, line[12], normal_style)
            worksheet.write(row_idx, 13, line[13], normal_style)
            worksheet.write(row_idx, 14, int(line[14] or 0), normal_style)
            worksheet.write(row_idx, 15, m_f, normal_style)
            worksheet.write(row_idx, 16, int(line[16] or 0), normal_style)
            worksheet.write(row_idx, 17, line[17], normal_style)
            worksheet.write(row_idx, 18, line[18], normal_style)
            worksheet.write(row_idx, 19, line[19], normal_style)
            worksheet.write(row_idx, 20, line[20], normal_style)
            worksheet.write(row_idx, 21, line[21], normal_style)

            dsr_ptg.write(row_idx, 0, line[0], normal_style)
            dsr_ptg.write(row_idx, 1, int(line[22] or 0), normal_style)
            dsr_ptg.write(row_idx, 2, line[23], normal_style)
            dsr_ptg.write(row_idx, 3, line[24], normal_style)
            dsr_ptg.write(row_idx, 4, line[25].strftime("%d/%m/%Y") if line[25] else '', tg_pt)
            row_idx += 1
        # =============== BODY ===============
        # ======================add external excel===============
        row_kop = 2
        row_nop = 2
        row_pph = 2
        for file in file_refkp:
            ref_file = pd.read_excel(file)
            ref_dict = ref_file.to_dict()
            kop = ref_dict['Kode Objek Pajak'].values()
            nop = ref_dict['Nama Objek Pajak'].values()
            phh = ref_dict['PPH Pasal'].values()
            for x in kop:
                ref_kp.write(row_kop,1, x, bord_style)
                row_kop += 1
            for x in nop:
                ref_kp.write(row_nop,2, x, bords_style)
                row_nop += 1
            for x in phh:
                ref_kp.write(row_pph,3, x, bord_style)
                row_pph += 1

        row_rkd = 2
        row_nmn = 2
        for file in file_refkdn:
            ref_file = pd.read_excel(file)
            ref_dict = ref_file.to_dict()
            kd = ref_dict['KODE'].values()
            nmn = ref_dict['Nama Negara'].values()
            for x in kd:
                ref_kdn.write(row_rkd,1, x, bord_style)
                row_rkd += 1
            for x in nmn:
                ref_kdn.write(row_nmn,2, x, bord_style)
                row_nmn += 1

        row_rdk = 2
        row_jdok = 2
        for file in file_refjdr:
            ref_file = pd.read_excel(file)
            ref_dict = ref_file.to_dict()
            kd = ref_dict['KODE'].values()
            jnd = ref_dict['Jenis Dokumen'].values()
            for x in kd:
                ref_jdr.write(row_rdk,1, x, bord_style)
                row_rdk += 1
            for x in jnd:
                ref_jdr.write(row_jdok,2, x, bord_style)
                row_jdok += 1

        workbook.save(fp)
        fp.seek(0)
        out = base64.encodestring(fp.read())
        fp.close()
        filename = 'export_bupot.xls'
        return self.set_data_excel(out, filename)

    def set_data_excel(self, out, filename):
        self.write({
            'data_file': out,
            'name': filename
        })

        return {
            'type': 'ir.actions.act_url',
            'name': filename,
            'url': '/web/content?model=export.bupot&field=data_file&filename_field=name&id=%s&download=true&filename=%s' %(self.id, filename,),
        }

        # =================================== export csv ============================= #

    def export_csv_fpm(self):
        data = self.export_bupot()
        # data = {}
        active_ids = ''
        delimiter = ','
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
        return self._generate_efaktur(data, delimiter)

    def _generate_efaktur(self, data, delimiter):

        filename = 'export_bupot.csv'
        efaktur_values = self._prepare_efaktur_csv(delimiter,data)

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
                        line[6] or '', delimiter,
                        line[7] or '', delimiter,
                        line[8] or '', delimiter,
                        line[9] or '', delimiter,
                        line[10] or '', delimiter,
                        line[11] or '', delimiter,
                        line[12] or '', delimiter,
                        credits or '',
                    )}
            output_head += '%s\n' %(
                fpm_data.get('fpm_datas'))
        result = self._generate_efaktur_purchase(data, delimiter,output_head)
        if data:
            my_utf8 = result.encode("utf-8")
        out = base64.b64encode(my_utf8)

        self.write({'data_file':out, 'name': filename})

        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/content?model=export.fpm&field=data_file&filename_field=name&id=%s&download=true&filename=%s' %(self.id, filename,),
            'target': 'self',
        }

    def _prepare_efaktur_csv(self, delimiter, data):

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

    def _generate_efaktur_purchase(self, data, delimiter, output_head):
        """Generate E-Faktur for Purchase / Vendor Bills"""

        # Invoice of Supplier

        return output_head