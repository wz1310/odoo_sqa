# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class InvoiceAssetWizard(models.TransientModel):
    _name = 'invoice.asset.wizard'

    move_id = fields.Many2one('account.move', string='Vendor Bill')
    asset_id = fields.Many2one('account.asset', string='Asset Account',required=True)
    line_ids = fields.Many2many('account.move.line', string='Invoice Lines',readonly=False)

    def confirm(self):
        for line in self.line_ids:
            line.write({
                'asset_id' : self.asset_id.id
            })
        view_id = self.env.ref('account_asset.view_account_asset_purchase_tree').id
        return {
                'name':'Assets',
                'view_mode': 'tree,form',
                'view_ids':[(view_id, 'tree'),(False, 'form')],
                'res_model':'account.asset',
                'type':'ir.actions.act_window',
                'target':'current',
                'domain':[('id', 'in', self.asset_id.ids)],
                'res_id':self.asset_id.ids,
                'context':{'asset_type': 'purchase', 'default_asset_type': 'purchase'}
               }

    @api.depends('move_id')
    def _compute_line_ids(self):
        for rec in self:
            if rec.move_id:
                line_ids = [(5,)]
                for line in rec.move_id.invoice_line_ids:
                    # if line.asset_id == False:
                    line_ids.append((0,0, {
                        'id': line.id,
                    }))
                rec.line_ids = line_ids
