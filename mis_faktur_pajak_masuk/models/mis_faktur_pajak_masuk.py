# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime
import requests
import xmltodict, json

class FakturPajakMasukan(models.Model):

    _name = "faktur.pajak.masuk"
    _description = 'Faktur Pajak Pemasukan'
    _inherit = ["approval.matrix.mixin", 'mail.thread', 'mail.activity.mixin']


    name = fields.Char(track_visibility='onchange')
    fm = fields.Char(string='FM',track_visibility='onchange')
    kode_jenis = fields.Char(string='Kode Jenis Transaksi',track_visibility='onchange')
    fg_pengganti = fields.Char(string='FG Pengganti',track_visibility='onchange')
    v_bill = fields.Many2one('account.move',string='Vendor Bill')
    no_faktur = fields.Char(string='Nomor Faktur',track_visibility='onchange')
    masa_pajak = fields.Char(string='Masa Pajak',track_visibility='onchange')
    tahun_pajak = fields.Char(string='Tahun Pajak',track_visibility='onchange')
    tanggal_faktur = fields.Date(string='Tanggal Pajak',track_visibility='onchange')
    npwp = fields.Char(string='NPWP',track_visibility='onchange')
    nama_vendor = fields.Char(string='Vendor',track_visibility='onchange')
    alamat = fields.Char(string='Alamat Lengkap',track_visibility='onchange')
    jumlah_dpp = fields.Float(string='Jumlah DPP',track_visibility='onchange')
    jumlah_ppn = fields.Float(string='Jumlah PPN',track_visibility='onchange')
    jumlah_ppnbm = fields.Float(string='Jumlah PPNBM',track_visibility='onchange')
    is_creditable = fields.Boolean(string='Is creditable',track_visibility='onchange')
    fpml_line = fields.One2many('faktur.pajak.masuk.line','fpm_move_id')
    state_fpm = fields.Selection([
        ('draft', 'Draft'),
        ('wait', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')],
        default='draft')
    reject_note = fields.Text('Detail Rejected')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id, track_visibility='onchange')

    def unlink(self):
        if self.fpml_line.ids:
            res = self.env.cr.execute("""DELETE FROM faktur_pajak_masuk_line WHERE id in %s""",(tuple(self.fpml_line.ids),))
        return super(FakturPajakMasukan, self).unlink()

    def submit_(self):
        # date_now = datetime.strptime(str(fields.Date.today()),'%Y-%m-%d')
        # bulan = date_now.strftime('%m')
        # tahun = date_now.strftime('%Y')
        # self.masa_pajak = str(bulan)
        # self.tahun_pajak = str(tahun)
        self.checking_approval_matrix(add_approver_as_follower=False, data={
                                      'state_fpm': 'wait'})
        # print("DATATATATATA", datetime.strptime(str(fields.Date.today()),'%m'))
        # self.state_fpm = 'wait'

    def draft_(self):
        self.reject_note = False
        self.state_fpm = 'draft'

    def approved_(self):
        self.approving_matrix(post_action='action_approve')
        # self.state_fpm = 'approved'

    def action_approve(self):
        self.state_fpm = 'approved'
        msgs = []
        msgs.append("Faktur Pajak Masukan %s Approved"%(self.name))
        self.v_bill.message_post(body=msgs[0])

    def rejected_(self):
        self.state_fpm = 'rejected'

class FakturPajakMasukanLine(models.Model):

    _name = "faktur.pajak.masuk.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Nama')
    hrg_satuan = fields.Char(string='Harga Satuan')
    jlm_barang = fields.Char(string='Jumlah Barang')
    hrg_total = fields.Char(string='Harga Total')
    f_disc = fields.Char(string='Diskon')
    dpp = fields.Char(string='DPP')
    ppn = fields.Char(string='PPN')
    trf_ppnbm = fields.Char(string='Tarif PPNBM')
    ppnbm = fields.Char(string='PPNBM')
    fpm_move_id = fields.Many2one('faktur.pajak.masuk')
    # fpml_line_move_ids = fields.Many2one('account.move')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id, track_visibility='onchange')

class FakturBillMove(models.Model):

    _inherit = "account.move"

    fpm_barcode = fields.Char()
    # v_bill = fields.Many2one('account.move',string='Vendor Bill')
    fm = fields.Char(related='fpm_move_id.fm',string='FM')
    kode_jenis = fields.Char(related='fpm_move_id.kode_jenis',string='Kode Jenis Transaksi')
    fg_pengganti = fields.Char(related='fpm_move_id.fg_pengganti',string='FG Pengganti')
    no_faktur = fields.Char(related='fpm_move_id.no_faktur',string='Nomor Faktur')
    masa_pajak = fields.Char(related='fpm_move_id.masa_pajak',string='Masa Pajak')
    tahun_pajak = fields.Char(related='fpm_move_id.tahun_pajak',string='Tahun Pajak')
    tanggal_faktur = fields.Date(related='fpm_move_id.tanggal_faktur',string='Tanggal Pajak')
    npwp = fields.Char(related='fpm_move_id.npwp',string='NPWP')
    nama_vendor = fields.Char(related='fpm_move_id.nama_vendor',string='Vendor')
    alamat = fields.Char(related='fpm_move_id.alamat',string='Alamat Lengkap')
    jumlah_dpp = fields.Float(related='fpm_move_id.jumlah_dpp',string='Jumlah DPP')
    jumlah_ppn = fields.Float(related='fpm_move_id.jumlah_ppn',string='Jumlah PPN')
    jumlah_ppnbm = fields.Float(related='fpm_move_id.jumlah_ppnbm',string='Jumlah PPNBM')
    is_creditable = fields.Boolean(string='Is creditable')
    fpm_move_id = fields.Many2one('faktur.pajak.masuk')
    # fpml_line = fields.One2many('faktur.pajak.masuk.line','fpml_line_move_ids')
    fpml_line = fields.One2many(related='fpm_move_id.fpml_line')
    state_fpm = fields.Selection(related='fpm_move_id.state_fpm')
    reject_note = fields.Text(related='fpm_move_id.reject_note')
    user_can_approve = fields.Boolean(related='fpm_move_id.user_can_approve',string="User can approve")
    approval_ids = fields.One2many(related='fpm_move_id.approval_ids') 
    # company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id, track_visibility='onchange')

    @api.onchange('fpm_barcode')
    def onchange_barcode(self):
        if self.ids:
            self.scan_barcode()

    def set_submit(self):
        self.fpm_move_id.submit_()
        msgs = []
        msgs.append("Faktur Pajak Masukan %s Submitted"%(self.fpm_move_id.name))
        self.message_post(body=msgs[0])

    def set_approve(self):
        self.fpm_move_id.approved_()

    def set_reject(self):
        return self.reject_wizard()

    def set_draft(self):
        self.fpm_move_id.draft_()
        msgs = []
        msgs.append("Faktur Pajak Masukan %s Set to draft"%(self.fpm_move_id.name))
        self.message_post(body=msgs[0])

    def scan_barcode(self):
        if not self.fpm_move_id:
            return self.open_fpm_wizard()
        if self.fpm_move_id and self.state_fpm == 'draft':
            return self.open_fpm_wizard()

    def action_show_fpm(self,datas):
        if self.fpm_barcode:
            url = self.fpm_barcode
            payload={}
            headers = {}
            # response = requests.request("GET", url, headers=headers, data=payload)
            try:
                response = requests.request("GET", url, headers=headers, data=payload)
            except requests.exceptions.ConnectionError:
                raise UserError("Check your connection and try again")
            except requests.exceptions.MissingSchema:
                raise UserError("Check your barcode format and try again")
            # response = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            #     <resValidateFakturPm>
            #     <kdJenisTransaksi>01</kdJenisTransaksi>
            #     <fgPengganti>1</fgPengganti>
            #     <nomorFaktur>0062251420526</nomorFaktur>
            #     <tanggalFaktur>31/08/2022</tanggalFaktur>
            #     <npwpPenjual>014951255431000</npwpPenjual>
            #     <namaPenjual>PT BOKOMA SENTUL RAYA</namaPenjual>
            #     <alamatPenjual>DESA SENTUL NO. 88 RT. 001 RW 005 , BOGOR</alamatPenjual>
            #     <npwpLawanTransaksi>312009384403000</npwpLawanTransaksi>
            #     <namaLawanTransaksi>PT. KENCANA ABADI JAYA</namaLawanTransaksi>
            #     <alamatLawanTransaksi>JL. RAYA BOGOR KM. 39 Blok - No.- RT:003 RW:001 Kel.PABUARAN MEKAR Kec.CIBINONG Kota/Kab.BOGOR JAWA BARAT 00000</alamatLawanTransaksi>
            #     <jumlahDpp>4600000</jumlahDpp>
            #     <jumlahPpn>506000</jumlahPpn>
            #     <jumlahPpnBm>0</jumlahPpnBm>
            #     <statusApproval>Faktur Valid, Sudah Diapprove oleh DJP</statusApproval>
            #     <statusFaktur>Faktur Pajak Normal-Pengganti</statusFaktur>
            #     <detailTransaksi>
            #         <nama>BARANG KE 1</nama>
            #         <hargaSatuan>23000</hargaSatuan>
            #         <jumlahBarang>192</jumlahBarang>
            #         <hargaTotal>4416000</hargaTotal>
            #         <diskon>0</diskon>
            #         <dpp>4416000</dpp>
            #         <ppn>485760</ppn>
            #         <tarifPpnbm>0</tarifPpnbm>
            #         <ppnbm>0</ppnbm>
            #     </detailTransaksi>
            #     <detailTransaksi>
            #         <nama>BARANG KE 2</nama>
            #         <hargaSatuan>23000</hargaSatuan>
            #         <jumlahBarang>8</jumlahBarang>
            #         <hargaTotal>184000</hargaTotal>
            #         <diskon>0</diskon>
            #         <dpp>184000</dpp>
            #         <ppn>20240</ppn>
            #         <tarifPpnbm>0</tarifPpnbm>
            #         <ppnbm>0</ppnbm>
            #     </detailTransaksi>
            #     </resValidateFakturPm> """
            # print("response",response)
            obj = xmltodict.parse(response.text)
            data = json.dumps(obj)
            if 'html' in data:
                raise UserError("No data in barcode, please try again")
            if 'kdJenisTransaksi' not in data:
                raise UserError("Faktur is not valid")
            n_data = json.loads(data)
            master = n_data['resValidateFakturPm']
            kdJenisTransaksi = master['kdJenisTransaksi']
            detailTransaksi = master['detailTransaksi']
            fgPengganti = master['fgPengganti']
            nomorFaktur = master['nomorFaktur']
            tanggalFaktur = master['tanggalFaktur']
            npwpPenjual = master['npwpPenjual']
            namaPenjual = master['namaPenjual']
            alamatPenjual = master['alamatPenjual']
            jumlahDpp = master['jumlahDpp']
            jumlahPpn = master['jumlahPpn']
            jumlahPpnBm = master['jumlahPpnBm']
            datas = {
            'kdJenisTransaksi':kdJenisTransaksi,
            'detailTransaksi':detailTransaksi,
            'fgPengganti':fgPengganti,
            'nomorFaktur':nomorFaktur,
            'tanggalFaktur':tanggalFaktur,
            'npwpPenjual':npwpPenjual,
            'namaPenjual':namaPenjual,
            'alamatPenjual':alamatPenjual,
            'jumlahDpp':jumlahDpp,
            'jumlahPpn':jumlahPpn,
            'jumlahPpnBm':jumlahPpnBm,
            }
        else:
            raise UserError("Barcode is empty")
        self.sudo().env['account.move'].browse(self.id).write({'fpm_barcode':False})
        return datas

    def open_fpm_wizard(self,datas=None):
        self.ensure_one()

        datas = self.action_show_fpm(datas)        
        form = self.env.ref('mis_faktur_pajak_masuk.open_post_wizard_fpm_view')
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'default_fm':'FM',
            'default_kode_jenis':datas['kdJenisTransaksi'],
            'default_fg_pengganti':datas['fgPengganti'],
            'detailTransaksi': datas['detailTransaksi'],
            'default_no_faktur':datas['nomorFaktur'],
            'default_tanggal_faktur':datetime.strptime(datas['tanggalFaktur'],'%d/%m/%Y'),
            'default_npwp':datas['npwpPenjual'],
            'default_nama_vendor':datas['namaPenjual'],
            'default_alamat':datas['alamatPenjual'],
            'default_jumlah_dpp':datas['jumlahDpp'],
            'default_jumlah_ppn':datas['jumlahPpn'],
            'default_jumlah_ppnbm':datas['jumlahPpnBm'],
            'active_model':'account.move'})
        # print("context",context)
        res = {
            'name': "%s - %s" % (_('Barcode data'), self.fpm_barcode),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'show.fpm.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        self.sudo().env['account.move'].browse(self.id).write({'fpm_barcode':False})
        # print("IDDDDDDDDDDDDDDD", self.env['account.move'].browse(self.id).fpm_barcode)
        return res

    def reject_wizard(self,datas=None):
        self.ensure_one()

        # datas = self.action_show_fpm(datas)        
        form = self.env.ref('mis_faktur_pajak_masuk.open_reject_wizard')
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'active_model':'account.move'})
        # print("context",context)
        res = {
            'name': "%s - %s" % (_('Reject detail'), self.fpm_move_id.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'show.reject.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def write(self,vals):
        res = super(FakturBillMove,self).write(vals)
        if self.fpm_move_id:
            self.fpm_move_id.write({'is_creditable':self.is_creditable})
        return res


class ShowFpm(models.TransientModel):
    _name = 'show.fpm.wizard'

    fm = fields.Char(string='FM')
    kode_jenis = fields.Char(string='Kode Jenis Transaksi')
    fg_pengganti = fields.Char(string='FG Pengganti')
    no_faktur = fields.Char(string='Nomor Faktur')
    tanggal_faktur = fields.Date(string='Tanggal Pajak')
    npwp = fields.Char(string='NPWP')
    nama_vendor = fields.Char(string='Vendor')
    alamat = fields.Char(string='Alamat Lengkap')
    jumlah_dpp = fields.Float(string='Jumlah DPP')
    jumlah_ppn = fields.Float(string='Jumlah PPN')
    jumlah_ppnbm = fields.Float(string='Jumlah PPNBM')
    is_creditable = fields.Boolean(string='Is creditable')


    def confirm(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        if not res_id or not model:
            raise UserError("Require to get context active id and active model!")
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)

        if len(Record) and not Record.fpm_move_id:
            msgs = []
            fmt_etax = ''
            this_fpm = Record.fpm_move_id.create({
                'name':'FPM'+'/'+str(Record.id),
                'v_bill':Record.id,
                'masa_pajak':str(self.tanggal_faktur.strftime("%m")),
                'tahun_pajak':str(self.tanggal_faktur.strftime("%Y"))
                })
            Record.fpm_move_id = this_fpm.id
            Record.fpm_barcode = False
            if this_fpm.no_faktur:
                # tambahan No etax pada bill otomatis terupdate ketika scan FPM
                fmt_etax = this_fpm.kode_jenis+''+this_fpm.fg_pengganti+'.'+this_fpm.no_faktur[:3]+'-'+this_fpm.no_faktur[3:5]+'.'+this_fpm.no_faktur[5:]
            Record.sudo().write({
            'e_tax_vendor_bill':fmt_etax
            })
            msgs.append("Faktur Pajak Masukan %s Created"%(this_fpm.name))
            Record.message_post(body=msgs[0])
            # Record.sudo().fpm_move_id.write({
            #     'fm':'FM',
            #     'v_bill':Record.id,
            #     'fg_pengganti':self.fg_pengganti,
            #     'kode_jenis':self.kode_jenis,
            #     'no_faktur':self.no_faktur,
            #     'tanggal_faktur':self.tanggal_faktur,
            #     'npwp':self.npwp ,
            #     'nama_vendor':self.nama_vendor,
            #     'alamat':self.alamat,
            #     'jumlah_dpp':self.jumlah_dpp,
            #     'jumlah_ppn':self.jumlah_ppn,
            #     'jumlah_ppnbm':self.jumlah_ppnbm
            #     })
            get_one_trans = False
            if 'nama' in self._context['detailTransaksi']:
                get_one_trans = True
            for x in self._context['detailTransaksi'] if get_one_trans == False else [self._context['detailTransaksi']]:
                this_fpml = Record.sudo().fpml_line.create({
                    'fpm_move_id': Record.fpm_move_id.id,
                    'name': x['nama'],
                    'hrg_satuan': x['hargaSatuan'],
                    'jlm_barang': x['jumlahBarang'],
                    'hrg_total': x['hargaTotal'],
                    'f_disc': x['diskon'],
                    'dpp': x['dpp'],
                    'ppn': x['ppn'],
                    'trf_ppnbm': x['tarifPpnbm'],
                    'ppnbm': x['ppnbm'],
                    })

        elif len(Record) and Record.fpm_move_id and Record.state_fpm == 'draft':

            # this_fpm = Record.fpm_move_id.create({
            #     'name':'FPM'+'/'+str(Record.id),
            #     'v_bill':Record.id})
            # Record.fpm_move_id = this_fpm.id
            # Record.fpm_barcode = False
            Record.sudo().fpm_move_id.write({
                'fm':'FM',
                'v_bill':Record.id,
                'fg_pengganti':self.fg_pengganti,
                'kode_jenis':self.kode_jenis,
                'no_faktur':self.no_faktur,
                'tanggal_faktur':self.tanggal_faktur,
                'npwp':self.npwp ,
                'nama_vendor':self.nama_vendor,
                'alamat':self.alamat,
                'jumlah_dpp':self.jumlah_dpp,
                'jumlah_ppn':self.jumlah_ppn,
                'jumlah_ppnbm':self.jumlah_ppnbm,
                'masa_pajak':str(self.tanggal_faktur.strftime("%m")),
                'tahun_pajak':str(self.tanggal_faktur.strftime("%Y"))
                })
            get_one_trans = False
            if 'nama' in self._context['detailTransaksi']:
                get_one_trans = True
            Record.sudo().fpml_line.unlink()
            for x in self._context['detailTransaksi'] if get_one_trans == False else [self._context['detailTransaksi']]:
                this_fpml = Record.sudo().fpml_line.create({
                    'fpm_move_id': Record.fpm_move_id.id,
                    'name': x['nama'],
                    'hrg_satuan': x['hargaSatuan'],
                    'jlm_barang': x['jumlahBarang'],
                    'hrg_total': x['hargaTotal'],
                    'f_disc': x['diskon'],
                    'dpp': x['dpp'],
                    'ppn': x['ppn'],
                    'trf_ppnbm': x['tarifPpnbm'],
                    'ppnbm': x['ppnbm'],
                    })
            # Record.sudo().write({
            # 'e_tax_vendor_bill': Record.fpm_move_id.no_faktur
            # })


class reject(models.TransientModel):
    _name = 'show.reject.wizard'

    reject_detail = fields.Text('Detail reject')


    def confirm_reject(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        if not res_id or not model:
            raise UserError("Require to get context active id and active model!")
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)

        if len(Record):
            msgs = []
            if not self.reject_detail:
                raise UserError("Please fill detail..")
            Record.sudo().fpm_move_id.write({
                'reject_note':self.reject_detail
                })
            Record.sudo().fpm_move_id.rejected_()
            msgs.append("Faktur Pajak Masukan %s Rejected"%(Record.fpm_move_id.name))
            Record.message_post(body=msgs[0])