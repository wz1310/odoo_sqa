# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
import logging
_logger = logging.getLogger(__name__)



class StockPickingSubstitute(models.TransientModel):
    _name = "stock.picking.substitute"
    _description = "Substitution of Unpredicted Availability Goods"

    picking_id = fields.Many2one(
        'stock.picking',
        string="Stock Picking", 
        default=lambda self:self.env.context.get('active_id'))
    line_ids = fields.One2many(
        'stock.picking.substitute.line',
        'substitute_id',
        string="Substitute Items")
    move_ids = fields.One2many(
        'stock.move',
        related='picking_id.move_ids_without_package')
    product_ids = fields.Many2many('product.product', compute='_compute_product_ids', store=True)

    @api.depends('picking_id')
    def _compute_product_ids(self):
        for data in self:
            # picking = stock_picking_obj.browse(self.env.context.get('active_id'))
            sale = data.picking_id.sale_agreement_id
            data.product_ids = [(6, 0, sale.agreement_line_ids.mapped('product_id').ids)]

    @api.onchange('picking_id')
    def _onchange_picking(self):
        res = []
        if self.picking_id.id:
            lines = []
            for move in self.picking_id.move_lines.filtered(lambda r:r.sale_line_id.id and r.sale_line_id.is_reward_line==False):
                
                lines.append((0,0,{
                    'move_id':move.id,
                    # 'product_id':move.product_id.id,
                    'qty':move.product_uom_qty,
                }))
            self.line_ids = lines

    def btn_confirm(self):
        stock_picking_obj = self.env["stock.picking"]
        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']
        user = self.env.user
        picking = stock_picking_obj.browse(self.env.context.get('active_id'))
        if picking.sale_substitute_id:
            raise UserError(_('You have already created Sale Order for Substitute Items.'))
        else:
            if self.line_ids:
                sale = picking.sale_id.sudo()
                so_dict = {
                    'partner_id': picking.sudo().sale_id.partner_id.id,
                    'user_id': picking.user_id.id,
                    'team_id': picking.sudo().sale_id.team_id.id,
                    'sale_agreement_id':sale.sale_agreement_id.id,
                    'payment_term_id':sale.payment_term_id.id,
                    'priority_type':sale.priority_type,
                    'company_id': picking.sudo().company_id.id,
                    'currency_id':picking.sudo().sale_id.currency_id.id,
                    'date_order': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'partner_invoice_id': picking.sudo().sale_id.partner_invoice_id.id,
                    'partner_shipping_id': picking.sudo().sale_id.partner_shipping_id.id,
                    'picking_policy': 'direct',
                    'pricelist_id':picking.sudo().sale_id.pricelist_id.id,
                    'warehouse_id': sale.warehouse_id.id,
                    # 'team_id': picking.sales_team_id,
                    'plant_id': picking.plant_id.id,
                    'vehicle_model_id': picking.vehicle_model_id.id,
                    'order_pickup_method_id': picking.order_pickup_method_id.id,
                    'is_substitute_order':True,
                    'substitute_order_id':picking.sale_id.id,
                    'interco_master':sale.interco_master,
                    'validity_date':picking.sudo().sale_id.validity_date,
                    'limit_approval_state':'need_approval_request',
                }
                so_id = sale_order_obj.with_user(picking.sudo().company_id.intercompany_user_id.id).with_context(substituting_item=True).create(so_dict)
                if not len(so_id):
                    raise UserError(_("Failed to Create new Sale Order!\nPlease call Administrator!"))
                for line in self.line_ids:
                    if line.qty > 0 and line.product_id and line.move_id:
                        
                        
                        # so_id = sale_order_obj.with_user(user.id).create(so_dict)
                        if so_id:
                            
                            soline_dict = {
                                'order_id': so_id.sudo().id,
                                'product_id': line.product_id.id,
                                'name' : line.product_id.display_name,
                                'product_uom_qty': line.qty,
                                'product_uom' : line.product_id.uom_id.id,
                                'price_unit' : picking.sudo().sale_id.pricelist_id.get_product_price(line.product_id, line.qty, False),
                            }
                            soline_id = sale_order_line_obj.with_user(picking.company_id.intercompany_user_id.id).with_context(substituting_item=True).create(soline_dict)
                # soline_id = sale_order_line_obj.with_user(user.id).create(soline_dict)
                so_id.with_user(picking.sudo().company_id.intercompany_user_id.id).message_post(body=_("Permohonan penggantian barang %s oleh (%s)") % (picking.name,user.name))
                # so_id.with_user(user.id).message_post(body=_("Permohonan penggantian barang dari Delivery Order %s oleh (%s)") % (picking.name,user.name))
                picking.with_user(picking.company_id.sudo().intercompany_user_id.id).write({'sale_substitute_id':so_id.sudo().id})
                # picking.with_user(user.id).write({'sale_substitute_id':so_id.id})
                form = self.env.ref('sale.view_order_form')
                context = dict(self.env.context or {})
                context.update({'create':False}) #uncomment if need append context
                msgs = _("%s Submiting subtitute item(s) on %s") % (self.env.user.display_name, so_id.sudo().display_name,)
                picking.sudo().message_post(body=msgs)
                
                #Remove by ADI, SO must Draft
                #so_id.sudo().with_context(cancel_action_assign=True).action_confirm()
                
                so_id.sudo().with_context(force_approval=False).btn_request_approval_limit()
                picking.sale_id.write({'substitute_with_order_id':so_id.id})
                if so_id.state=='draft':
                    # if not success confirming so will still in draft
                    # then show message
                    return {
                        'effect': {
                            'fadeout': 'slow',
                            'message': _("Subtitute Item Submited and Sales Order (%s) Need to be Approval!") % (so_id.display_name,),
                            'img_url': '/sanqua_sale_flow/static/src/img/wow.png',
                            'type': 'rainbow_man',
                        }
                    }
                form = self.env.ref('stock.view_picking_form')
                context = dict(self.env.context or {})
                # context.update({}) #uncomment if need append context
                res = {
                    'name': "%s %s %s" % (_('Subtitution for '), self.picking_id.display_name, so_id.picking_ids.display_name,),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.picking',
                    'view_id': form.id,
                    'res_id':so_id.picking_ids.id,
                    'res_ids':so_id.picking_ids.ids,
                    'type': 'ir.actions.act_window',
                    'context': context,
                    'target': 'current'
                }
                return res
            else:
                raise UserError(_('You have empty line in substitute order line. Click button "Cancel" if you dont have any substitution'))