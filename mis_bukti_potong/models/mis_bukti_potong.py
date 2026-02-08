# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime
import requests
import xmltodict, json

class MisBupot(models.Model):

    _name = "mis.bukti.potong"
    _description = 'Bukti Potong'
    _inherit = ["approval.matrix.mixin", 'mail.thread', 'mail.activity.mixin']


    name = fields.Char(track_visibility='onchange')
    moveline_id = fields.Many2one('account.move.line',string="Id Account Move Line")
    state_bupot = fields.Selection([
        ('draft', 'Draft'),
        ('wait', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')],
        default='draft')
    product_id = fields.Many2one('product.product',string="Product")
    label = fields.Char(string="Label")
    qty = fields.Float(string="Quantity")
    tgl_potong = fields.Date(string="Tanggal Pemotongan")
    pn_npwp_nik = fields.Char(string="Penerima Penghasilan? (NPWP/NIK)")
    npwp_phs = fields.Char(string="NPWP (tanpa format/tanda baca)")
    nik_phs = fields.Char(string="NIK (tanpa format/tanda baca)")
    nm_penerima_nik = fields.Char(string="Nama Penerima Penghasilan Sesuai NIK")
    no_telp = fields.Char(string="Nomor Telp")
    qq_nik = fields.Char(string="qq (khusus NPWP Keluarga)")
    pdt_bp = fields.Char(string="Penandatangan BP ? (Pengurus/Kuasa)")
    pdt_nik = fields.Selection([
        ('npwp', 'NPWP'),
        ('nik', 'NIK')],
        default='npwp',string="Penandatangan Menggunakan NPWP/NIK ?")
    no_dtp = fields.Char(string="Nomor Aturan DTP")
    lb = fields.Char(string="LB Diproses Oleh ? (Pemotong/Pemindahbukuan)")
    no_suket = fields.Char(string="Nomor Suket PP23")
    no_work = fields.Char(string="No. worksheet")
    # jn_dok = fields.Char(string="Jenis dokumen")
    jn_dok = fields.Selection([
        ('01', 'Faktur Pajak'),
        ('02', 'Invoice'),
        ('03', 'Pengumuman'),
        ('04', 'Surat Perjanjian'),
        ('05', 'Bukti Pembayaran'),
        ('06', 'Akta Perikatan'),
        ('07', 'Akta RUPS'),
        ('08', 'Surat Pernyataan'),
        ],
        default='01',string="Jenis dokumen")
    no_dok = fields.Char(string="Nomor Dokumen")
    tgl_dok = fields.Date(string="Tgl Dokumen (dd/MM/yyyy)")
    note = fields.Text(string="Note")
    price = fields.Char(string="Price")
    pph_pasal = fields.Many2one('mis.pph.bukti.potong',string="PPh Pasal")
    kode_objek = fields.Many2one('mis.kode.objek.line',string="Kode Objek Pajak",domain="[('pph_bupot_id', '=', pph_pasal)]")
    npwp_pdt = fields.Char(string="NPWP Penandatangan (tanpa format/tanda baca)")
    nik_pdt = fields.Char(string="NIK Penandatangan (tanpa format/tanda baca)")
    nm_pdt_nik = fields.Char(string="Nama Penandatangan Sesuai NIK")
    pg_bruto = fields.Char(string="Penghasilan Bruto")
    mp_fasilitas = fields.Selection([
        ('n', 'N'),
        ('skb', 'SKB'),
        ('pp23', 'PP23'),
        ('dtp', 'DTP'),
        ('lain', 'Lainnya'),
        ],
        default='pp23',string="Mendapatkan Fasilitas ? (N/SKB / PP23/DTP / Lainnya)")
    no_skb = fields.Char(string="Nomor SKB")
    fs_pph = fields.Char(string="Fasilitas PPh Lainnya")
    trf_pph = fields.Char(string="Tarif PPh Berdasarkan Fas. PPh Lainnya")
    jpb = fields.Float(string="Jumlah Penghasilan Bruto (Rp)")
    jpd = fields.Float(string="Jumlah Pajak Dipotong (Rp)")
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id, track_visibility='onchange')

    def draft_(self):
        self.note = ''
        self.state_bupot = 'draft'
        msgs = []
        msgs.append("Bukti Potong %s Set to draft"%(self.name))
        self.moveline_id.move_id.message_post(body=msgs[0])

    def submit_(self):
        self.checking_approval_matrix(add_approver_as_follower=False, data={
                                      'state_bupot': 'wait'})
        # self.state_bupot = 'wait'

    def approved_(self):
        self.approving_matrix(post_action='action_approve')
        # self.state_bupot = 'approved'

    def action_approve(self):
        self.state_bupot = 'approved'
        msgs = []
        msgs.append("Bukti Potong %s Approved"%(self.name))
        self.moveline_id.move_id.message_post(body=msgs[0])

    def rejected_(self):
        self.state_bupot = 'rejected'

    @api.onchange('pph_pasal')
    def onch_pasal(self):
        if self.kode_objek.pph_bupot_id.id != self.pph_pasal.id:
            self.kode_objek = ''
            self.jpb = 0
            self.jpd = 0

class PphBupot(models.Model):

    _name = "mis.pph.bukti.potong"
    _description = 'PPH Bukti Potong'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='PPH')
    kode_objek_line = fields.One2many('mis.kode.objek.line','pph_bupot_id')

class KodeObjek(models.Model):

    _name = "mis.kode.objek.line"
    _description = 'Kode Objek Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Kode Objek')
    pph_bupot_id = fields.Many2one('mis.pph.bukti.potong',string="PPH Bupot Id")

class BupotMove(models.Model):

    _inherit = "account.move.line"

    pph_pasal = fields.Many2one(related='bupot_id.pph_pasal',string="PPh Pasal")
    kode_objek = fields.Many2one(related='bupot_id.kode_objek',string="Kode Objek Pajak")
    state_bupot = fields.Selection(related='bupot_id.state_bupot')
    bupot_id = fields.Many2one('mis.bukti.potong',string="Bupot Id")

    def detail_bupot(self):
        return self.bupot_wizard()
        # print("BUPOTTT")

    def bupot_wizard(self):
        self.ensure_one()
        inc_npwp = ''
        no_npwp = ''
        inc_nik = ''
        no_nik = ''
        if self.move_id.partner_id:
            self.env.cr.execute("""
                SELECT replace(concat(split_part(vat, '.',1),split_part(vat, '.',2),
                split_part(vat, '.',3),
                split_part(vat, '.',4),
                split_part(vat, '.',5)),'-','') AS npwp
                FROM
                res_partner
                WHERE id ="""+str(int(self.move_id.partner_id.id))+"""""")
            res = self.env.cr.dictfetchone()
            inc_npwp = 'NPWP'
            no_npwp = res['npwp']
            # print("NAMA VENDOR",res['npwp'])
            self.env.cr.execute("""
                SELECT national_id AS nik
                FROM
                res_partner
                WHERE id ="""+str(int(self.move_id.partner_id.id))+"""""")
            res = self.env.cr.dictfetchone()
            inc_nik = 'NIK'
            no_nik = res['nik']
            # print("NAMA VENDOR",res['npwp'])

        form = self.env.ref('mis_bukti_potong.open_detail_bupot_wizard')
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'default_bupot_id':self.bupot_id.id,
            'default_product_id':self.product_id.id,
            'default_label':self.name,
            'default_qty':self.quantity,
            # tambahan Format digit price dan tarif Pph pada bukti potong
            'default_price':f'{self.price_unit:,.0f}',
            'default_tgl_potong':self.bupot_id.tgl_potong,
            'default_pn_npwp_nik':self.bupot_id.pn_npwp_nik or inc_npwp or inc_nik,
            'default_npwp_phs':self.bupot_id.npwp_phs or no_npwp or no_nik,
            'default_nik_phs':self.bupot_id.nik_phs,
            'default_nm_penerima_nik':self.bupot_id.nm_penerima_nik,
            'default_no_telp':self.bupot_id.no_telp,
            'default_pdt_bp':self.bupot_id.pdt_bp,
            'default_pdt_nik':self.bupot_id.pdt_nik,
            'default_no_dtp':self.bupot_id.no_dtp,
            'default_lb':self.bupot_id.lb,
            'default_no_suket':self.bupot_id.no_suket,
            'default_no_work':self.company_id.no_work,
            'default_jn_dok':self.bupot_id.jn_dok,
            'default_no_dok':self.bupot_id.no_dok or self.move_id.ref,
            'default_tgl_dok':self.bupot_id.tgl_dok,
            'default_note':self.bupot_id.note,
            'default_pph_pasal':self.bupot_id.pph_pasal.id,
            'default_kode_objek':self.bupot_id.kode_objek.id,
            'default_npwp_pdt':self.bupot_id.npwp_pdt,
            'default_qq_nik':self.bupot_id.qq_nik,
            'default_nik_pdt':self.bupot_id.nik_pdt,
            'default_nm_pdt_nik':self.bupot_id.nm_pdt_nik,
            'default_pg_bruto':self.bupot_id.pg_bruto,
            'default_mp_fasilitas':self.bupot_id.mp_fasilitas,
            'default_no_skb':self.bupot_id.no_skb,
            'default_fs_pph':self.bupot_id.fs_pph,
            'default_trf_pph':self.bupot_id.trf_pph,
            'default_note':self.bupot_id.note,
            'default_jpb':self.bupot_id.jpb,
            'default_jpd':self.bupot_id.jpd,
            'active_model':'account.move.line'})
        # print("context",context)
        res = {
            'name': "%s - %s" % (_('Bukti potong detail'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'show.detail.bupot',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res


class DetailBupot(models.TransientModel):
    _name = 'show.detail.bupot'

    product_id = fields.Many2one('product.product',string="Product")
    label = fields.Char(string="Label")
    qty = fields.Float(string="Quantity")
    tgl_potong = fields.Date(string="Tanggal Pemotongan")
    pn_npwp_nik = fields.Char(string="Penerima Penghasilan? (NPWP/NIK)")
    npwp_phs = fields.Char(string="NPWP (tanpa format/tanda baca)")
    nik_phs = fields.Char(string="NIK (tanpa format/tanda baca)")
    nm_penerima_nik = fields.Char(string="Nama Penerima Penghasilan Sesuai NIK")
    qq_nik = fields.Char(string="qq (khusus NPWP Keluarga)")
    no_telp = fields.Char(string="Nomor Telp")
    pdt_bp = fields.Char(string="Penandatangan BP ? (Pengurus/Kuasa)")
    pdt_nik = fields.Selection([
        ('npwp', 'NPWP'),
        ('nik', 'NIK')],
        default='npwp',string="Penandatangan Menggunakan NPWP/NIK ?")
    no_dtp = fields.Char(string="Nomor Aturan DTP")
    lb = fields.Char(string="LB Diproses Oleh ? (Pemotong/Pemindahbukuan)")
    no_suket = fields.Char(string="Nomor Suket PP23")
    no_work = fields.Char(string="No. worksheet")
    # jn_dok = fields.Char(string="Jenis dokumen")
    jn_dok = fields.Selection([
        ('01', 'Faktur Pajak'),
        ('02', 'Invoice'),
        ('03', 'Pengumuman'),
        ('04', 'Surat Perjanjian'),
        ('05', 'Bukti Pembayaran'),
        ('06', 'Akta Perikatan'),
        ('07', 'Akta RUPS'),
        ('08', 'Surat Pernyataan'),
        ],
        default='01',string="Jenis dokumen")
    no_dok = fields.Char(string="Nomor Dokumen")
    tgl_dok = fields.Date(string="Tgl Dokumen (dd/MM/yyyy)")
    note = fields.Text(string="Note")
    price = fields.Char(string="Price")
    pph_pasal = fields.Many2one('mis.pph.bukti.potong',string="PPh Pasal")
    kode_objek = fields.Many2one('mis.kode.objek.line',string="Kode Objek Pajak",domain="[('pph_bupot_id', '=', pph_pasal)]")
    npwp_pdt = fields.Char(string="NPWP Penandatangan (tanpa format/tanda baca)")
    nik_pdt = fields.Char(string="NIK Penandatangan (tanpa format/tanda baca)")
    nm_pdt_nik = fields.Char(string="Nama Penandatangan Sesuai NIK")
    pg_bruto = fields.Char(string="Penghasilan Bruto")
    mp_fasilitas = fields.Selection([
        ('n', 'N'),
        ('skb', 'SKB'),
        ('pp23', 'PP23'),
        ('dtp', 'DTP'),
        ('lain', 'Lainnya'),
        ],
        default='pp23',string="Mendapatkan Fasilitas ? (N/SKB / PP23/DTP / Lainnya)")
    no_skb = fields.Char(string="Nomor SKB")
    fs_pph = fields.Char(string="Fasilitas PPh Lainnya")
    trf_pph = fields.Char(string="Tarif PPh Berdasarkan Fas. PPh Lainnya")
    bupot_id = fields.Many2one('mis.bukti.potong',string="Bupot Id")
    state_bupot = fields.Selection(related='bupot_id.state_bupot')
    user_can_approve = fields.Boolean(related='bupot_id.user_can_approve',string="User can approve")
    approval_ids = fields.One2many(related='bupot_id.approval_ids')
    approved = fields.Boolean(related='bupot_id.approved')
    jpb = fields.Float(string="Jumlah Penghasilan Bruto (Rp)")
    jpd = fields.Float(string="Jumlah Pajak Dipotong (Rp)")


    def confirm_bupot(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        if not res_id or not model:
            raise UserError("Require to get context active id and active model!")
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)

        if len(Record):
            msgs = []
            # if not self.reject_detail:
            #     raise UserError("Please fill detail..")
            if not self.bupot_id:
                new_bupot = Record.bupot_id.create({
                    'name':'BUPOT'+'/'+str(Record.id),
                    'moveline_id': Record.id,
                    'tgl_potong': self.tgl_potong,
                    'nm_penerima_nik': self.nm_penerima_nik,
                    'npwp_phs': self.npwp_phs,
                    'qq_nik': self.qq_nik,
                    'no_telp': self.no_telp,
                    'pdt_bp': self.pdt_bp,
                    'pdt_nik': self.pdt_nik,
                    'no_dtp': self.no_dtp,
                    'lb': self.lb,
                    'no_suket': self.no_suket,
                    'no_work': self.no_work,
                    'jn_dok': self.jn_dok,
                    'no_dok': self.no_dok,
                    'tgl_dok': self.tgl_dok,
                    'note': self.note,
                    'price': self.price,
                    'pph_pasal': self.pph_pasal.id,
                    'kode_objek': self.kode_objek.id,
                    'npwp_pdt': self.npwp_pdt,
                    'nik_pdt': self.nik_pdt,
                    'nm_pdt_nik': self.nm_pdt_nik,
                    'pg_bruto': self.pg_bruto,
                    'mp_fasilitas': self.mp_fasilitas,
                    'no_skb': self.no_skb,
                    'fs_pph': self.fs_pph,
                    'trf_pph': self.trf_pph,
                    'jpb': self.jpb,
                    'jpd': self.jpd,
                    })
                self.user_log = self.env.user.id
                Record.sudo().write({
                    'bupot_id': new_bupot.id,
                    })
                msgs.append("Bukti Potong %s Created"%(new_bupot.name))
                Record.move_id.message_post(body=msgs[0])
            elif self.bupot_id and self.state_bupot not in('wait','approved','rejected'):
                self.write_bupot_()
                # write_bupot = Record.bupot_id.write({
                #     'tgl_potong': self.tgl_potong,
                #     'pn_npwp_nik': self.pn_npwp_nik,
                #     'npwp_phs': self.npwp_phs,
                #     'nik_phs': self.nik_phs,
                #     'nm_penerima_nik': self.nm_penerima_nik,
                #     'qq_nik': self.qq_nik,
                #     'no_telp': self.no_telp,
                #     'pdt_bp': self.pdt_bp,
                #     'pdt_nik': self.pdt_nik,
                #     'no_dtp': self.no_dtp,
                #     'lb': self.lb,
                #     'no_suket': self.no_suket,
                #     'no_work': self.no_work,
                #     'jn_dok': self.jn_dok,
                #     'note': self.note,
                #     'price': self.price,
                #     'pph_pasal': self.pph_pasal.id,
                #     'kode_objek': self.kode_objek.id,
                #     'npwp_pdt': self.npwp_pdt,
                #     'nik_pdt': self.nik_pdt,
                #     'nm_pdt_nik': self.nm_pdt_nik,
                #     'pg_bruto': self.pg_bruto,
                #     'mp_fasilitas': self.mp_fasilitas,
                #     'no_skb': self.no_skb,
                #     'fs_pph': self.fs_pph,
                #     'trf_pph': self.trf_pph,
                #     })

    def write_bupot_(self):
        res_id = self._context.get('active_id')
        Env = self.env['account.move.line']
        Record = Env.sudo().browse(res_id)
        write_bupot = Record.bupot_id.write({
            'tgl_potong': self.tgl_potong,
            'pn_npwp_nik': self.pn_npwp_nik,
            'npwp_phs': self.npwp_phs,
            'nik_phs': self.nik_phs,
            'nm_penerima_nik': self.nm_penerima_nik,
            'qq_nik': self.qq_nik,
            'no_telp': self.no_telp,
            'pdt_bp': self.pdt_bp,
            'pdt_nik': self.pdt_nik,
            'no_dtp': self.no_dtp,
            'lb': self.lb,
            'no_suket': self.no_suket,
            'no_work': self.no_work,
            'jn_dok': self.jn_dok,
            'no_dok': self.no_dok,
            'tgl_dok': self.tgl_dok,
            'note': self.note,
            'price': self.price,
            'pph_pasal': self.pph_pasal,
            'kode_objek': self.kode_objek,
            'npwp_pdt': self.npwp_pdt,
            'nik_pdt': self.nik_pdt,
            'nm_pdt_nik': self.nm_pdt_nik,
            'pg_bruto': self.pg_bruto,
            'mp_fasilitas': self.mp_fasilitas,
            'no_skb': self.no_skb,
            'fs_pph': self.fs_pph,
            'trf_pph': self.trf_pph,
            'jpb': self.jpb,
            'jpd': self.jpd
            })

    def draft_(self):
        self.bupot_id.draft_()
        self.note = False
        context = dict(self.env.context or {})
        res_id = self._context.get('active_id')
        return { 
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'show.detail.bupot',
        'context': context,
        'res_id': self.id,
        'target': 'new',
        }

    def submit_(self):
        self.write_bupot_()
        self.bupot_id.submit_()
        context = dict(self.env.context or {})
        res_id = self._context.get('active_id')
        msgs = []
        msgs.append("Bukti Potong %s Submitted"%(self.bupot_id.name))
        self.bupot_id.moveline_id.move_id.message_post(body=msgs[0])
        return { 
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'show.detail.bupot',
        'context': context,
        'res_id': self.id,
        'target': 'new',
        }

    def approved_(self):
        self.bupot_id.approved_()
        context = dict(self.env.context or {})
        res_id = self._context.get('active_id')
        return { 
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'show.detail.bupot',
        'context': context,
        'res_id': self.id,
        'target': 'new',
        }

    def rejected_(self):
        return self.reject_wizard()

    def reject_wizard(self,datas=None):
        self.ensure_one()

        # datas = self.action_show_fpm(datas)        
        form = self.env.ref('mis_bukti_potong.open_reject_wizard')
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'active_model':'account.move.line'})
        # print("context",context)
        res = {
            'name': "%s - %s" % (_('Reject detail'), self.bupot_id.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'bupot.show.reject.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    @api.onchange('pph_pasal')
    def onch_pasal(self):
        if self.kode_objek.pph_bupot_id.id != self.pph_pasal.id and self.kode_objek:
            self.kode_objek = ''
            self.jpb = 0
            self.jpd = 0

    @api.onchange('trf_pph')
    def onch_trf(self):
        context = dict(self.env.context or {})
        print("CONTEXT", self.trf_pph)
        if self.trf_pph:
            self.trf_pph = "{:,.0f}".format(float(self.trf_pph.replace(',','')))


class reject(models.TransientModel):
    _name = 'bupot.show.reject.wizard'

    reject_detail = fields.Text('Detail reject')


    def confirm_reject(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        ress = self.env['show.detail.bupot'].browse(res_id).reject_wizard()
        bp_id = ress['context']['default_bupot_id']
        # print("ACTIVE IDSSSS",model)
        if not res_id or not model:
            raise UserError("Require to get context active id and active model!")
        
        Env = self.env['mis.bukti.potong']
        Record = Env.sudo().browse(bp_id)

        if len(Record):
            msgs = []
            if not self.reject_detail:
                raise UserError("Please fill detail..")
            Record.write({
                'note':self.reject_detail
                })
            Record.rejected_()
            msgs.append("Bukti Potong %s Rejected"%(Record.name))
            Record.moveline_id.move_id.message_post(body=msgs[0])


class BupotResCompany(models.Model):
    """class inherit res.company"""
    _inherit = 'res.company'

    no_work = fields.Char(sting="No.Worksheet")