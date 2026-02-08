# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date

class mbuku(models.Model):
    _name = "master.buku"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nama Buku')
    pgr = fields.Char('Pengarang')
    buku_ids_count = fields.Integer(
        compute="_compute_buku_ids_count", string="Jumlah Chart")
    tgl = fields.Date('Tanggal Terbit')
    jn_bk = fields.Selection([('ipa', 'IPA'),('ips', 'IPS'),
                                                   ('bio', 'BIOLOGI')],
                                                  string="Jenis Buku", default="ipa")
    kateg_bk = fields.Selection([('sd', 'Buku SD'),('smp', 'Buku SMP')],
                                                  string="Kategori Buku", default="sd")
    desc = fields.Many2one('Keterangan')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')], 'Status', copy=False, default='draft')
    book_line = fields.One2many('master.buku.line','book_move_id')
    tags = fields.Many2many('master.buku.line', 'm_book_rel' , 'book_move_id')

    def submit_(self):
        self.state = 'done'

    def cancel_(self):
        self.state = 'draft'

    def _compute_buku_ids_count(self):
        for rec in self:
            rec.buku_ids_count = len(rec.book_line)

class mbukuline(models.Model):
    _name = "master.buku.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Bab')
    hal = fields.Char('Halaman')
    halex = fields.Text('Hal Extra')
    halex1 = fields.Text('Hal Extra1')
    desc = fields.Text('Keterangan')
    book_move_id = fields.Many2one('master.buku')
    # tags = fields.Many2many('Tags')