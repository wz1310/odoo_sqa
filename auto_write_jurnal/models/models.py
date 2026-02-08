# -*- coding: utf-8 -*-

from odoo import models, fields, api


class auto_write_jurnal(models.Model):
    _inherit = 'account.journal'

    @api.model
    def create(self,vals):
        my_comp = self.env.company.id
        res = super(auto_write_jurnal, self).create(vals)
        # cek apakahhh
        if my_comp != 1:
            find_usr_smi = self.env['res.users'].search([('company_id','=',1)])
            for y in find_usr_smi:
                y.sudo().write({'journal_ids':[(4,res.id)]})
        else:
            find_usr = self.env['res.users'].search([('company_id','=',self.company_id.id)])
            for x in find_usr:
                x.sudo().write({'journal_ids':[(4,res.id)]})
        return res

    def write(self,vals):
        res = super(auto_write_jurnal, self).write(vals)
        find_usr = self.env['res.users'].search([('company_id','=',self.company_id.id)])
        for x in find_usr:
            x.sudo().write({'journal_ids':[(4,self.id)]})
        return res