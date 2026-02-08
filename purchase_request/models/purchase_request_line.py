# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = 'Purchase Request Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    purchase_request_id = fields.Many2one(
        'purchase.request', string='Purchase Request', track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('purchase_ok','=',True)]", track_visibility='onchange', required=True)
    desc = fields.Text(string='Description', track_visibility='onchange')
    qty = fields.Float(string='Qty', digits="Product Unit Of Measure",
                       required=True, track_visibility='onchange')
    qty_released = fields.Float(string='Qty Released', digits="Product Unit Of Measure",
                                compute='_compute_qty_release', store=False, track_visibility='onchange')
    uom_id = fields.Many2one(
        string='UOM', related='product_id.uom_po_id', track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved')
    ], string='State', track_visibility='onchange', required=True, default='draft')
    pr_state = fields.Char(
        string="State PR", compute="_compute_pr_state", default="draft")
    current_stock = fields.Float(
        string='Stock On Hand', related='product_id.qty_available', track_visibility='onchange', compute_sudo=False)
    incoming_stock = fields.Float(
        string='Incoming', related='product_id.incoming_qty', track_visibility='onchange', compute_sudo=False)
    purchase_line_ids = fields.One2many(
        'purchase.order.line', 'purchase_request_line_id', string='Purchase Order Line', track_visibility='onchange')
    is_editable = fields.Boolean(
        string='Editable', compute='_compute_is_editable', default=lambda self: self._default_is_editable)
    is_asset = fields.Boolean(
        string="Is Asset", related="purchase_request_id.is_asset", readonly=True)
    non_asset_type = fields.Selection(
        related="product_id.non_asset_type", readonly=True)
    last_price = fields.Float('Last Price', compute="_compute_last_price")
    price_total = fields.Float('Price Total', compute="_compute_last_price")
    _rec_name = 'product_id'

    @api.depends('product_id')
    def _compute_last_price(self):
        for each in self:
            product_ids = self.env['product.product'].search(
                [('id', '=', each.product_id.id)])
            if len(product_ids) > 0:
                for prod in product_ids:
                    supp_price = self.env['product.supplierinfo'].search(
                        [('product_tmpl_id', '=', prod.product_tmpl_id.id), ('company_id', '=', self.env.company.id)])
                    if len(supp_price) > 0:
                        each.last_price = supp_price[0].price
                        each.price_total = supp_price[0].price * each.qty
                    else:
                        each.last_price = 0.0
                        each.price_total = 0.0
            else:
                each.last_price = 0.0
                each.price_total = 0.0

    # Comment per 16/09/2021 by SanQua
    # Comment as request 7/jan/2021
    # @api.constrains('is_asset')
    # def constrains_is_asset(self):
    #     for rec in self:
    #         if rec.is_asset and rec.product_id.is_asset == False:
    #             raise UserError(_("Item %s not valid. Only Assset Product can be listed on Asset Purchase Request.") % (rec.product_id.display_name,
    #                                                                                                                     ))

    def _default_is_editable(self):
        return True

    @api.depends('purchase_request_id')
    def _compute_pr_state(self):
        for rec in self:
            rec.pr_state = rec.purchase_request_id.state

    @api.model
    def create(self, vals):
        if self.purchase_request_id.id:
            if self.purchase_request_id.state != 'draft':
                raise UserError(_("Cannot modify submited document!"))
        return super(PurchaseRequestLine, self).create(vals)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.desc = self.product_id.display_name

    @api.depends('purchase_line_ids.purchase_request_line_id')
    def _compute_qty_release(self):
        for rec in self:
            qty_released = 0

            qty_released = sum(rec.purchase_line_ids.mapped('product_qty'))
            rec.qty_released = qty_released

    def _valid_to_po(self):
        if self.state != 'approved':
            raise UserError(_("Cannot Create PO for draft Product!"))
        if self.qty_released >= self.qty:
            raise UserError(_("Over process qty on item %s!") %
                            (self.display_name))

    def _compute_is_editable(self):
        for rec in self:
            if rec.pr_state == 'draft':
                rec.is_editable = True
            else:
                if rec.purchase_request_id.user_can_approve == True:
                    rec.is_editable = True
                else:
                    rec.is_editable = False

    def approve(self):
        self.write({'state': 'approved'})

    def reject(self):
        self.write({'state': 'rejected'})
