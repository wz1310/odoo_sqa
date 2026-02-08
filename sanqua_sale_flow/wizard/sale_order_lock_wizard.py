# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class SaleOrderLockWizard(models.Model):
    _name = 'sale.order.lock.wizard'
    _description = 'Sale Order Lock Wizard'

    order_ids = fields.Many2many('sale.order', string='Agreements')
    line_ids = fields.One2many('sale.order.lock.line.wizard', 'wizard_id', string='Lines')


    @api.model
    def default_get(self,  default_fields):
        
        active_ids = self._context.get('active_ids')
        if not len(active_ids):
            raise UserError(_("Must select at last 1 Order!"))
        orders = self.env['sale.order'].search([('id','in',active_ids), ('state','in',['sale','done'])])

        # if len(orders):
        #     has_invoice = orders.invoice_ids.filtered(lambda r:r.state not in ['draft','cancel'])
        #     if len(has_invoice):
        #         raise UserError(_("Order %s has posted invoice") % (", ".join(orders.mapped('name'))))

        
        if not len(orders):
            raise UserError(_("No Confirmation Order was selected!\nAction can't be done!"))

        res = super(SaleOrderLockWizard, self).default_get(default_fields)

        # sale_ids = self.env['sale.order'].browse(self._context.get('line_ids',[]))
        # sale_ids = orders._get_sales_can_be_cancel()
        sale_ids = orders

        vals = []
        for record in sale_ids:
            vals.append((0,0,{
                            'wizard_id':self.id,
                            'sale_id' : record.id,
                            'currency_id' : record.currency_id.id,
                            'sale_team_id' : record.team_id.id,
                            'sale_amount_total' : record.amount_total,
                            'sale_picking_ids' : [(6,0, record.picking_ids.ids)],
                            'sale_state' : record.state,
                            'cancel':True
                            }))

        order_ids = [(6,0,orders.ids)]
        res.update({'order_ids':order_ids,'line_ids':vals})
        
        return res
        
    def btn_confirm(self):
        for line in self.line_ids:
            if line.cancel == True:
                if line.sale_id.id in line.wizard_id.order_ids.ids:
                    for picking in line.sale_id.picking_ids.filtered(lambda r:r.state not in ['done','cancel']):
                        picking.action_cancel()
                    for invoice in line.sale_id.invoice_ids.filtered(lambda r: r.picking_ids == False):
                        invoice.button_cancel()
                    line.sale_id.write({'state':'forced_locked'})
        # self.order_ids.filtered(lambda r:r.state=='approve').write({'state': 'locked'})

class SaleOrderLockLineWizard(models.Model):
    _name = 'sale.order.lock.line.wizard'
    _description = 'Sale Order Lock Line Wizard'

    wizard_id = fields.Many2one('sale.order.lock.wizard', string='Wizard Cancel')
    sale_id = fields.Many2one('sale.order', string='Order',required=True)
    sale_team_id = fields.Many2one('crm.team', related="sale_id.team_id", readonly=True)
    currency_id = fields.Many2one('res.currency', related="sale_id.currency_id", readonly=True)
    sale_amount_total = fields.Monetary(related="sale_id.amount_total", readonly=True)
    sale_state = fields.Selection(related="sale_id.state", readonly=True)
    sale_picking_ids = fields.One2many(related="sale_id.picking_ids")
    cancel = fields.Boolean(string='Cancel')