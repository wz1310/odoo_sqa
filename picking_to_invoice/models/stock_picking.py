# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError,UserError
from odoo.tools.float_utils import float_compare
from datetime import timedelta

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    old_invoice_id = fields.Many2one('account.move', string='Invoice')
    no_sj_vendor = fields.Char('No. SJ Vendor')
    no_sj_wim = fields.Char(string="No. SJ WIM", compute="_check_sj_wim", store=True)

    def _update_sj_wim(self):
        for this in self.search([]):
            no_doc = 'New'
            if this.sale_id:
                no_doc = this.sale_id.auto_purchase_order_id.interco_picking_id.doc_name
            elif this.purchase_id:
                no_doc = this.purchase_id.interco_picking_id.doc_name
            if no_doc != 'New':
                this.no_sj_wim = no_doc
    @api.depends('sale_id','state','sent','is_locked','purchase_id')
    def _check_sj_wim(self):
        for this in self:
            no_doc = 'New'
            if this.sale_id:
                no_doc = this.sale_id.auto_purchase_order_id.interco_picking_id.doc_name
            elif this.purchase_id:
                no_doc = this.purchase_id.interco_picking_id.doc_name
            if no_doc != 'New':
                this.no_sj_wim = no_doc
            

    def _check_create_invoice(self):
        self.ensure_one()
        # make sure no invoice created on related picking
        if self.invoice_id and self.invoice_id.state in ['draft','posted']:
            raise UserError(_("This Picking already has invoice %s.\n") % (self.invoice_id.display_name,))

        # make sure has qty to picking
        if sum(self.move_lines.mapped('qty_to_invoice'))<=0.0:
            raise UserError(_("No invoiceable qty (%s)!") % (self.display_name,))
    
    def create_invoices(self):
        for rec in self.filtered(lambda r:r.picking_type_code=='outgoing'):
            rec.create_invoice()

    def create_invoice(self):
        print('>>> create_invoice(self) here...')
        if self.env.company.id != self.company_id.id:
            raise UserError(_("You cannot create invoice with this current company active"))
        
        # Warning Jika masih ada DO return yg masing gantung
        origin = "Return of %s" % (self.doc_name,)
        return_ids = self.env['stock.picking'].search([('origin','=', origin),('state','not in',['done','cancel']),('backorder_id','=', False)])
        if return_ids:
            raise UserError(_("You cannot create invoice because you have return not yet validate"))

        # Add validation when invoice can process only when DO already receive
        # Updated By: MIS@SanQua
        # At: 29/12/2021
        # if not self.sent:
        #     raise UserError(_("You can't create invoice because DO not received yet"))
        # If user plant want create invoice of DO Plant to WIM, it must be :
        # 1. check DO WIM to Customer already receive or not.
        # 2. check DO Plant to WIM already receive or not

        if not self.sent:
            raise UserError(_("You can not create invoice because DO not received yet"))

        if self.no_sj_wim:
            if self.env.company.id != self.company_id.id:
                raise UserError(_("You can not create invoice with this current company active"))
            else:
        #       Check if DO Plant to WIM already receive or not
                if not self.sent:
                    raise UserError(_("You can not create invoice because DO not received yet"))
                else:
                    xWIMDO = self.env['stock.picking'].search([('doc_name','=',self.no_sj_wim)])
                    if xWIMDO:
                        if not xWIMDO.sent:
                            raise UserError(_("You can not create invoice because DO WIM to customer not received yet"))
                    else:
                        raise UserError(_("SJ WIM not found"))
        # End Edit by MIS@SanQua

        self = self.filtered(lambda r:r.picking_type_code=='outgoing')
        self.ensure_one()
        self._check_create_invoice()
        
        invoice_id = self.env['account.move'].with_context(default_user_id=self.sale_id.user_id.id).create(self._prepare_invoice(self))
        self.invoice_id = invoice_id
        view = self.env.ref('account.view_move_form')
        return {
            'name': _('Customer Invoice'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'res_id': invoice_id.id,
        }

    def _prepare_invoice(self,picking):
        invoice_vals = {
            'type': 'out_invoice',
            # Updated by : MIS@SanQua
            # At: 12/01/2022
            # Description: The date default is not include timezone.
            'invoice_date': (picking.date_done) + timedelta(hours=7),
            'invoice_origin': picking.name,
            'invoice_user_id': picking.sale_id.user_id.id,
            'narration': picking.note,
            'partner_id': picking.sale_id.partner_invoice_id.id,
            'partner_shipping_id': picking.partner_id.id,
            'team_id': picking.sales_team_id.id,
            # 'source_id': self.id,
            'invoice_line_ids':[],
            'invoice_payment_term_id':picking.sudo().sale_id.payment_term_id.id,
            'locked':False
        }
        for rec in picking.move_ids_without_package.filtered(lambda r:r.qty_to_invoice>0.0 and not r.product_id.reg_in_customer_stock_card):
            invoice_vals['invoice_line_ids'].append(
                    (0, 0, self._prepare_vals_move(rec))
                )
        
        #Adi Remove, Rabu 07 Oktober 2020. request by Vita becuase free product 
        # if picking.sale_id:
        #     reward_so_product = picking.sale_id._get_reward_lines().filtered(lambda r: r.qty_invoiced != r.product_uom_qty).mapped('product_id')
        #     reward_move_product = picking.move_ids_without_package.filtered(lambda r:r.qty_to_invoice>0.0).mapped('product_id')
        #     rewards_product = reward_so_product - reward_move_product
        #     for line in picking.sale_id._get_reward_lines().filtered(lambda r: r.product_id in rewards_product):
        #         invoice_vals['invoice_line_ids'].append(
        #                 (0, 0, self._prepare_vals_sale_order_line(line))
        #             )
        return invoice_vals

    def _prepare_vals_sale_order_line(self,line):
        return  {
                    'name': line.name,
                    'price_unit': line.price_unit,
                    'quantity': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom.id,
                    'sale_line_ids': [(6, 0, line.ids)],
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'multi_discounts' : line.multi_discounts,
                    'discount_fixed_line' : line.discount_fixed_line,
                    'discount' : line.discount,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'analytic_account_id': self.sale_id.analytic_account_id.id,
                }

    def _prepare_vals_move(self,line):

        if( self.env.company.id == 2 ):
            return {
                'name': line.name,
                'price_unit': line.sale_line_id.price_unit,
                'quantity': line.qty_to_invoice,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'sale_line_ids': [(6, 0, line.sale_line_id.ids)],
                'tax_ids': [(6, 0, line.sale_line_id.tax_id.ids)],
                'multi_discounts': line.sale_line_id.multi_discounts,
                'discount_fixed_line': line.sale_line_id.discount_fixed_line,
                'discount': line.sale_line_id.discount,
                'analytic_tag_ids': [(6, 0, line.sale_line_id.analytic_tag_ids.ids)],
                'analytic_account_id': self.sale_id.analytic_account_id.id,
            }
        else:
            return {
                'name': line.name,
                'price_unit': line.sale_line_id.price_unit,
                'quantity': line.qty_to_invoice,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'sale_line_ids': [(6, 0, line.sale_line_id.ids)],
                'tax_ids': [(6, 0, line.sale_line_id.tax_id.ids)],
                'multi_discounts': line.sale_line_id.multi_discounts,
                'discount_fixed_line': line.sale_line_id.discount_fixed_line,
                'discount': line.sale_line_id.discount,
                'analytic_tag_ids': [(6, 0, line.sale_line_id.analytic_tag_ids.ids)],
                'analytic_account_id': self.sale_id.analytic_account_id.id,
            }



class StockMove(models.Model):
    _inherit = 'stock.move'

    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line')
    return_qty = fields.Float(compute='_compute_return_qty', string='Qty Return')
    qty_to_invoice = fields.Float(compute='_compute_qty_to_invoice', string='')
    
    @api.depends('returned_move_ids')
    def _compute_return_qty(self):
        for rec in self:
            if rec.returned_move_ids:
                rec.return_qty = sum(rec.returned_move_ids.filtered(lambda self: self.state == 'done').mapped('quantity_done')) - sum(rec.returned_move_ids.filtered(lambda self: self.state == 'done').mapped('return_qty'))
            else:
                rec.return_qty = 0.0
    
    @api.depends('return_qty')
    def _compute_qty_to_invoice(self):
        for rec in self:
            rec.qty_to_invoice = rec.quantity_done - rec.return_qty

    def _prepare_picking_account_move_line(self, move):
        self.ensure_one()
        qty = self.quantity_done - self.return_qty
        if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
            qty = 0.0

        currency = self.company_id.currency_id
        if move.type == 'in_invoice':
            price = self.purchase_line_id.price_unit
            discount = self.purchase_line_id.discount
            if move.include_tax:
                tax = self.purchase_line_id.taxes_id.ids
            discount_fixed_line = self.purchase_line_id.discount_fixed_line
            multi_discounts = self.purchase_line_id.multi_discounts
        else:
            price = self.sale_line_id.price_unit
            discount = self.sale_line_id.discount
            if move.include_tax:
                tax = self.sale_line_id.tax_id.ids
            discount_fixed_line = self.sale_line_id.discount_fixed_line
            multi_discounts = self.sale_line_id.multi_discounts

        if move.include_tax:
            return {
                'name': '%s: %s' % (self.picking_id.name, self.name),
                'move_id': move.id,
                'currency_id': currency and currency.id or False,
                'date_maturity': move.invoice_date_due,
                'product_uom_id': self.product_uom.id,
                'product_id': self.product_id.id,
                'price_unit': price,
                'quantity': qty,
                'partner_id': move.partner_id.id,
                'analytic_account_id': self.purchase_line_id.account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, self.purchase_line_id.analytic_tag_ids.ids)],
                'tax_ids': [(6, 0, tax)],
                'display_type': self.purchase_line_id.display_type,
                'exclude_from_invoice_tab': False,
                'multi_discounts' : multi_discounts,
                'discount_fixed_line' : discount_fixed_line,
                'discount' : discount,
                'picking_id' : self.picking_id.id,
            }
        else:
            return {
                'name': '%s: %s' % (self.picking_id.name, self.name),
                'move_id': move.id,
                'currency_id': currency and currency.id or False,
                'date_maturity': move.invoice_date_due,
                'product_uom_id': self.product_uom.id,
                'product_id': self.product_id.id,
                'price_unit': price,
                'quantity': qty,
                'partner_id': move.partner_id.id,
                'analytic_account_id': self.purchase_line_id.account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, self.purchase_line_id.analytic_tag_ids.ids)],
                'display_type': self.purchase_line_id.display_type,
                'exclude_from_invoice_tab': False,
                'multi_discounts': multi_discounts,
                'discount_fixed_line': discount_fixed_line,
                'discount': discount,
                'picking_id' : self.picking_id.id,
            }