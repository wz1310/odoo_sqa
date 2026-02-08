# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class EvaluasiSupplier(models.Model):
    _name = 'evaluasi.supplier'
    _description = 'Evaluasi SUpplier'

    partner_id = fields.Many2one('res.partner', string='Supplier')
    rating = fields.Integer(string='Nilai')
    date_rating = fields.Date(string='Tanggal Penilaian')
    note = fields.Text(string='Keterangan')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='State',default='draft')


    def action_submit(self):
        """set state to done"""
        self.write({'state':'done'})
        self.partner_id.current_rating = self.rating

