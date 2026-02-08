# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import timedelta
import re
import json
import requests

import logging
_logger = logging.getLogger(__name__)

class PurchaseRequestInherit(models.Model):
    _inherit = 'purchase.request'

    @api.model
    def domain_whs(self):
        users = self.env['res.users'].search([('id', '=', self.env.user.id)]).warehouse_ids.ids
        return [('id','in',users)]

    status_pr = fields.Selection(
        [("open", "In Progress"), ("done", "Done"), ("close", "Close"), ("cancel", "Cancel")], default='open', track_visibility='onchange')
    close_reason = fields.Text(string='Reason')
    cancel_details = fields.Text(string='Cancel detail')
    openpr_reason = fields.Text(string='Open detail')
    cek_close = fields.Boolean()
    whs = fields.Many2one('stock.warehouse',string='Warehouse',domain=lambda x: x.domain_whs())

    # @api.onchange('whs')
    # def _on_change_whs(self):
    #     print("WARE")
    #     users = self.env['res.users'].search([('id', '=', self.env.user.id)])
    #     return {'domain': {'whs':[('id','in', users.warehouse_ids.ids)]}}

    def _api_validate(self):
        self.validate_item()
        self.validate_department()

    def _cek_close(self):
        self.cek_close = False
        po_done = self.purchase_ids.filtered(lambda x:x.state in ['purchase','done'] and x.status_po != 'close')
        jum_line = sum([x.qty for x in self.line_ids]) or 0.0
        jum_rel = sum([x.product_qty for x in po_done.order_line]) or 0.0
        if jum_line == jum_rel:
            self.cek_close = True
            self.close_reason = 'Auto close based qty released'
            self.status_pr = 'close'

    def btn_draft(self):
        self.state = 'draft'
        self.status_pr = ''

    def bton_cancel(self):
        akses =  self.approval_ids.approver_ids.ids
        user_crn = self.env.user.id
        if user_crn in akses and not any([x.qty_released>0 for x in self.line_ids]):
            self.ensure_one()
            view = self.env.ref('mis_purchase_request.cancel_wizards_view_form')
            return {
            'name': _('Cancel detail'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.request',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id
            }
        else:
            raise UserError(_('You are not allowed to cancel this \nplease contact administrator'))

    def btn_close(self):
        akses =  self.approval_ids.approver_ids.ids
        user_crn = self.env.user.id
        if user_crn in akses:
            self.ensure_one()
            view = self.env.ref('mis_purchase_request.close_wizard_view_form')
            return {
            'name': _('Close Reason'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.request',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id
            }
        else:
            raise UserError(_('You are not allowed to cancel this \nplease contact administrator'))

    def btn_openpr(self):
        akses =  self.approval_ids.approver_ids.ids
        user_crn = self.env.user.id
        if user_crn in akses and any([x.qty_released<x.qty for x in self.line_ids]):
            self.ensure_one()
            view = self.env.ref('mis_purchase_request.openpr_wizards_view_form')
            return {
            'name': _('Open Reason'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.request',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id
            }
        elif user_crn in akses and not any([x.qty_released<x.qty for x in self.line_ids]):
            raise UserError(_('You are not allowed to open this \n qty released is not available..'))
        else:
            raise UserError(_('You are not allowed to open this \nplease contact administrator'))

    def my_reason(self):
        if self.close_reason:
            self.status_pr = 'close'
        else:
            raise UserError(_('Please fill in the reason first'))

    def btn_cancel_detail(self):
        if self.cancel_details:
            self.status_pr = 'cancel'
        else:
            raise UserError(_('Please fill in the detail first'))

    def btn_openpr_detail(self):
        if self.openpr_reason:
            self.status_pr = 'open'
        else:
            raise UserError(_('Please fill in the detail first'))

    @api.model_create_multi
    def create(self, vals):
        print('>>> call create on mis_purchase_request')
        res = super().create(vals)
        for data in res.line_ids:
            print('>>> data: ' + str(data.last_price))
            print('>>> data: ' + str(data.qty))
            print('>>> data: ' + str(data.price_total))
        return res

    def write(self,vals):
        res = super(PurchaseRequestInherit,self).write(vals)
        return res

class CancelWizards(models.TransientModel):
    _name = 'cancel.wizards'

    cancel_details = fields.Text(string='Cancel detail')

class CloseWizard(models.TransientModel):
    _name = 'close.wizard'

    close_reason = fields.Text(string='Reason')

class OpenprWizard(models.TransientModel):
    _name = 'openpr.wizards'

    openpr_reason = fields.Text(string='Reason')

class PurchaseRequestLineInherit(models.Model):
    _inherit = 'purchase.request.line'

    last_price = fields.Float('Last Price', store=True)
    price_total = fields.Float('Price Total', store=True)
    fpb_not = fields.Text()
    fpb_uom = fields.Many2one('uom.uom')

    @api.depends('purchase_line_ids.purchase_request_line_id')
    def _compute_qty_release(self):
        for rec in self:
            # qty_released = 0
            qty_released = rec.qty
            new_qty = sum(rec.purchase_line_ids.filtered(lambda x: x.state not in ['cancel','done'] and x.order_id.status_po not in ['close','done'] ).mapped('product_qty'))
            in_qty = sum(rec.purchase_line_ids.filtered(lambda x: x.state in ['purchase'] and x.order_id.status_po in ['open'] ).mapped('qty_received'))
            qty_received = sum(x.qty_received for x in rec.purchase_line_ids)
            qty_received_over = sum(x.qty_received - x.product_qty if x.qty_received > x.product_qty and x.order_id.status_po in ['close','done'] and x.state in ['done','purchase'] else 0 for x in rec.purchase_line_ids)
            # qty_received = sum(x.qty_received if x.qty_received <= x.product_qty else x.product_qty for x in rec.purchase_line_ids)
            # qty_received = sum(x.qty_received if x.qty_received <= x.product_qty and x.qty_received != 0 and x.order_id.status_po in ['close','done'] else 0 for x in rec.purchase_line_ids)
            # print("new_qty",new_qty)
            # print("in_qty",in_qty)
            # print("qty_released",qty_released)
            # print("qty_received",qty_received)
            # print("qty_received_over",qty_received_over)

            # rec.qty_released = (0 + qty_released) - (qty_released - qty_received) + (0 + new_qty) - (0 + in_qty)
            rec.qty_released = (0 + qty_released) - (qty_released - qty_received) + (0 + new_qty) - (0 + in_qty)- (0 + qty_received_over)

class InherPurchaseRequestToOrder(models.TransientModel):
    _inherit = 'purchase.request.to.order'
    
    def btn_confirm(self):
        if len(self.line_ids.item_id) == 0:
            raise UserError(_("This action can not process \nproduct in line does not exist "))
        # self.validate_non_asset_type()
        for line in self.line_ids:
            line.item_id._valid_to_po()
            line.validity_qty()
            
        purchase_id = self.env['purchase.order'].create({
                                'partner_id':self.supplier_id.id,
                                'user_id': self.request_id.user_id.id,
                                'asset' : self.request_id.is_asset,
                                'purchase_order_type' : self.request_id.purchase_order_type
                            })
        if purchase_id:
            vals = []
            for line in self.line_ids:
                data = {
                    'product_id': line.item_id.product_id.id,
                    'name' : line.item_id.desc if line.item_id.desc else '['+line.item_id.product_id.default_code+']' +' '+line.item_id.product_id.name,
                    # 'name' : line.item_id.product_id.display_name,
                    'product_qty': line.qty,
                    'product_uom' : line.uom_id.id,
                    'fpb_uom' : line.item_id.fpb_uom.id,
                    'fpb_not' : line.item_id.fpb_not,
                    'price_unit' : line.item_id.product_id.lst_price,
                    'order_id': purchase_id.id,
                    'date_planned': fields.Date.from_string(purchase_id.date_order),
                    'purchase_request_line_id' : line.item_id.id,
                    # 'name' : line.item_id.desc
                }
                vals.append(data)
        new_po = self.env['purchase.order.line'].with_context(active_model='purchase.requisition').create(vals)
        if new_po:
            try:
                self.send_stat_po()
            except:
                None
        
        form = self.env.ref('purchase.purchase_order_form')
        context = dict(self.env.context or {})
        # pr_id = self._context['_default_request_id']
        # pr_data = self.env['purchase.request'].browse(pr_id)
        # if not any([x.qty_released<x.qty for x in pr_data.line_ids]) and pr_data.status_pr not in ['close','cancel'] and pr_data.state == 'approved':
        #     pr_data.close_reason = 'Auto close based qty released'
        #     pr_data.status_pr = 'close'
        # context.update({}) #uncomment if need append context
        res = {
            'name': "%s - %s" % (_('Purchase Order - '), self.request_id.name),
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': form.id,
            'views':[(form.id,'form')],
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'current',
            'res_id':purchase_id.id,
            'res_ids':purchase_id.ids,
        }
        return res

    def send_stat_po(self):
        mis_api = self.env['ir.config_parameter'].sudo().search([('key','=','api_send_stat_po')])
        url = mis_api.value
        payload = json.dumps({
            "pr_no":self.request_id.name,
            "is_po_created": True
            })
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)