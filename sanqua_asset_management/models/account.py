# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def post_asset(self):
        for line in self.invoice_line_ids:
            if not line.asset_account_id:
                raise UserError(_("%s has not Asset Account. Please fill it before confirm.")%(line.product_id.display_name))
        form = self.env.ref('sanqua_asset_management.view_invoice_asset_wizard', raise_if_not_found=False)
        return {
                'name': _('Create Asset'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'invoice.asset.wizard',
                'views': [(form.id, 'form')],
                'view_id': form.id,
                'target': 'new',
                'context': {
                    'default_move_id': self.id
                }
        }

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    type = fields.Selection(related='move_id.type')
    asset_account_id = fields.Many2one('account.account', string='Asset Account')

    def btn_update_asset(self):
        view_id = self.env.ref('sanqua_asset_management.account_move_line_view_form_update_asset').id
        return {
            'name':'Update Asset Account',
            'view_type':'form',
            'view_mode':'tree',
            'views':[(view_id,'form')],
            'res_model':'account.move.line',
            'view_id':view_id,
            'res_id':self.id,
            'type':'ir.actions.act_window',
            'target':'new'
               }
    
    def confirm(self):
        return {'type': 'ir.actions.act_window_close'}

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_model_id = fields.Many2one('account.asset', string='Asset Model')
    purchase_ids = fields.Many2many('purchase.order',compute='_compute_product_ids')
    purchase_line_ids = fields.Many2many('purchase.order.line',compute='_compute_product_ids')
    product_ids = fields.Many2many('product.product',compute='_compute_product_ids', string='Product')
    entries_ids = fields.Many2many('account.move','account_asset_account_move_rel', 
                        'asset_id', 'invoice_id', string='Journal Entries') # field to save all journal from Asset

    @api.depends('original_move_line_ids')
    def _compute_product_ids(self):
        for rec in self:
            if rec.original_move_line_ids:
                product_ids = []
                po_line = []
                po = []
                for line in rec.original_move_line_ids:
                    product_ids.append(line.product_id.id)
                    po_line.append(line.purchase_line_id.id)
                    po.append(line.purchase_line_id.order_id.id)
                rec.product_ids = [(6,0,product_ids)]
                rec.purchase_line_ids = [(6,0,po_line)]
                rec.purchase_ids = [(6,0,set(po))]
            else:
                rec.product_ids = False
                rec.purchase_ids = False
                rec.purchase_line_ids = False

    def validate(self):
        print(" JALAN _inherit = 'account.asset'")
        res = super(AccountAsset,self).validate()
        line_ids = []
        for line in self.original_move_line_ids:
            line_ids.append((0, 0, {
                'name': 'Asset',
                'account_id': line.asset_account_id.id,
                'partner_id':line.partner_id.id,
                'debit': line.price_total,
                'credit': 0.0,
            }))
            line_ids.append((0, 0, {
                'name': 'Non Current asset',
                'account_id': line.product_id.categ_id.property_stock_account_input_categ_id.id,
                'partner_id':line.partner_id.id,
                'debit': 0.0,
                'credit': line.price_total,
            }))
        
        if len(line_ids) > 0:
            journal_id = self.env['account.move'].create({
                'type': 'entry',
                'asset_id': self.id,
                'ref': 'Entries Of '+self.name,
                'date': self.acquisition_date,
                'line_ids': line_ids
            })
            self.entries_ids = [(4,journal_id.id)]
        return res

    def set_to_close(self, invoice_line_id, date=None):
        self.ensure_one()
        disposal_date = date or fields.Date.today()
        if invoice_line_id and self.children_ids.filtered(lambda a: a.state in ('draft', 'open') or a.value_residual > 0):
            raise UserError("You cannot automate the journal entry for an asset that has a running gross increase. Please use 'Dispose' on the increase(s).")
        full_asset = self + self.children_ids
        move_ids = full_asset._get_disposal_moves([invoice_line_id] * len(full_asset), disposal_date)
        full_asset.write({'state': 'close', 'disposal_date': disposal_date})
        if move_ids:
            return self._return_disposal_view(move_ids)
        if self.entries_ids:
            for entries in self.entries_ids:
                entries.write({'state': 'cancel'})