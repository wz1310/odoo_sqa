# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_ids = fields.One2many('stock.picking', 'invoice_id', string='Receipts')
    company_id = fields.Many2one('res.company', deafult=lambda self:self._default_company())
    interco_ref_picking_ids = fields.Many2many('stock.picking',compute='_compute_interco_ref_picking_ids', string='Interco Ref Picking', search="_search_interco_ref_picking_ids")
    cek_user = fields.Boolean(string="check field", compute='cek_users')

    def cek_users(self):
        for x in self:
            x.cek_user = False
            if x.user_has_groups("picking_to_invoice.group_acess_qty_pfi"):
                x.cek_user = True

    @api.depends('picking_ids')
    def _compute_interco_ref_picking_ids(self):
        print("_compute_interco_ref_picking_ids")
        for rec in self:
            picking = False
            if rec.picking_ids:
                # self.env.cr.execute(""" SELECT id FROM stock_picking WHERE id in %s and invoice_id = %s""", (tuple(rec.picking_ids.ids),rec.id,))
                # res = self.env.cr.fetchall()
                # print("RESSSSSSSSSSSSSS1",rec.picking_ids.ids)
                # print("RESSSSSSSSSSSSSS2",res)
                picking = rec.picking_ids.sudo().interco_ref_picking_ids.ids
                # print("rec.picking_ids", rec.picking_ids)
            print("interco_ref_picking_ids",picking)
            rec.interco_ref_picking_ids = picking

    def _search_interco_ref_picking_ids(self, operator, value):
        print("_search_interco_ref_picking_ids==================",value)
        invoice_ids = self.env['account.move'].sudo().search([])
        invoice_ids = invoice_ids.filtered(lambda r: r.interco_ref_picking_ids.filtered(lambda f: f.doc_name == value))
        return [('id','in',invoice_ids.ids)]

    @api.model
    def search_interco_ref_picking_ids(self, operator, value):
        print("search_interco_ref_picking_ids==================",value)
        return self._search_interco_ref_picking_ids(operator, value)

    def _default_company(self):
        # print(self.env.company.id,'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxx')
        return self.env.company.id

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):

        res = super(AccountMove, self)._onchange_partner_id()
        code = ''
        if self.type == 'in_invoice':
            code = 'incoming'
        elif self.type == 'out_invoice':
            code = 'outgoing'

        if not self._context.get('onchange_pickings'):
            self.picking_ids = [(5,0)]
        if self.partner_id:
            picking_ids_domain = [('partner_id','=',self.partner_id.id),('invoice_id','=',False),('picking_type_code','=', code),('state','in',['done'])]
            if self.type == 'out_invoice':
                # Change by: MIS@SanQua
                # At: 29/12/2021
                # Description: Add filter when dropdown at invoice form sent=True to check wether the DO already received or not
                picking_ids_domain = [('customer_id','=',self.partner_id.id),('invoice_id','=',False),('picking_type_code','=', code),('state','in',['done']),('sent','=','True')]

            if res:
                if type(res)==dict and res.get('domain'):
                    domain = res.get('domain')
                    new_domain = domain.update({'picking_ids':picking_ids_domain})
                    res.update({'domain':new_domain})
                else:
                    return {'domain':{'picking_ids':picking_ids_domain}}
            return {'domain':{'picking_ids':picking_ids_domain}}
        else:
            return {'domain':{'picking_ids':[('invoice_id','=',False),('picking_type_code','=', code),('state','in',['done'])]}}

    @api.onchange('picking_ids')
    def _onchange_picking_ids(self):
        print('>>> _onchange_picking_ids')
        self = self.with_context(onchange_pickings=True)
        self.line_ids = [(5,0)]

        if self.picking_ids:
            if not self.partner_id:
                self.partner_id = self.picking_ids.mapped('customer_id')

            picking_ids = self.picking_ids._origin
            moves_lines = self.env['stock.move'].browse(
                [rec.id for rec in picking_ids.move_ids_without_package]
                )

            new_lines = self.env['account.move.line']
            for line in moves_lines:
                new_line = new_lines.new(line._prepare_picking_account_move_line(self))
                new_line.account_id = new_line._get_computed_account()
                new_line.stock_move_id = line.id
                new_line._onchange_price_subtotal()
                new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()

        # Compute ref.
        refs = self.picking_ids.mapped('display_name')
        self.ref = ', '.join(refs)

        # Compute invoice_payment_ref.
        if len(refs) == 1:
            self.invoice_payment_ref = refs[0]

        self._onchange_currency()
        return self._onchange_partner_id()


    @api.onchange('purchase_vendor_bill_id')
    def _onchange_picking_purchase_vendor_bill_id(self):
        self._onchange_purchase_auto_complete()
        return self._onchange_partner_id()

    def button_cancel(self):
        res = super(AccountMove,self).button_cancel()
        if self.picking_ids:
            for picking in self.picking_ids:
                picking.old_invoice_id = self.id
                picking.invoice_id = False
        return res

    def button_draft(self):
        res = super(AccountMove,self).button_draft()
        picking_ids = self.env['stock.picking'].search([('old_invoice_id','=',self.id)])
        for picking in picking_ids:
            if picking.old_invoice_id:
                picking.invoice_id = picking.old_invoice_id.id
        return res

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    stock_move_id = fields.Many2one('stock.move', string='Stock Moves', ondelete='set null', index=True, readonly=True,store=True)
    no_sj_wim = fields.Char(related="stock_move_id.picking_id.no_sj_wim", string="No SJ WIM")
    no_sj_plan = fields.Char(related="stock_move_id.picking_id.name", string="No SJ Plan")