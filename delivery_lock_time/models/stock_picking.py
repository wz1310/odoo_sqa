# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    lock_datetime = fields.Datetime(compute='_compute_lock_datetime',store=True, string='Lock Time', track_visibility='onchange')
    
    @api.depends('scheduled_date')
    def _compute_lock_datetime(self):
        for rec in self:
            res = (rec.scheduled_date + timedelta(days=1)).strftime('%Y-%m-%d 23:59:59')
            # rec.lock_datetime = rec.scheduled_date
            if rec.sale_id.id and not rec.is_return_picking:
                if rec.sale_id.validity_date:
                    res = rec.sale_id.validity_date.strftime('%Y-%m-%d 23:59:59')
            rec.lock_datetime = res

    def validate_lock_datetime(self):
        if datetime.now() > self.lock_datetime:
            raise ValidationError(_("%s was Overdue based on Scheduled date: %s.") % (self.display_name, self.lock_datetime.strftime('%d-%m-%Y')))

    def btn_plant_confirm(self):
        self.validate_lock_datetime()
        return super(StockPicking,self).btn_plant_confirm()

    # def action_assign(self):
    #     self.validate_lock_datetime()
    #     return super(StockPicking,self).action_assign()

#Request by Bu Vita, Schedule Date Bisa di Edit
    # @api.depends('move_lines.date_expected')
    # def _compute_scheduled_date(self):
    #     sales_pickings = self.filtered(lambda r: r.sale_id.id)
    #     for picking in sales_pickings:
    #         if picking.picking_type_code == 'outgoing' and picking.sale_id and not picking.is_return_picking:
    #             if picking.sale_id.commitment_date:
    #                 picking.scheduled_date = picking.sale_id.commitment_date
    #             else:
    #                 #days = picking.partner_id.delivery_lead_time
    #                 #Request by bu Novita 
    #                 days = 0.0
    #                 picking.scheduled_date = picking.create_date + timedelta(days=days)

    #     non_sales_pickings = self.filtered(lambda r: r.sale_id.id == False)
    #     if len(non_sales_pickings):
    #         return super(StockPicking, non_sales_pickings)._compute_scheduled_date()

    def _cronjob_lock_datetime(self):
        picking_ids = self.env['stock.picking'].search([('lock_datetime','<',datetime.now()),('picking_type_code','=','outgoing'),('state','in',['draft','waiting','confirmed'])])
        for picking in picking_ids:
            makloon_product_ids = picking.move_ids_without_package.mapped('product_id').filtered(lambda r: r.makloon == True)
            if len(makloon_product_ids) > 0 and picking.sale_id.id:
                so = picking.sale_id.copy()
                days = so.company_id.customer_lead_time
                so.update({'commitment_date':datetime.now() + timedelta(days=days)})
                for line in so.order_line:
                    if line.product_id.id not in makloon_product_ids.ids:
                        line.unlink()
                    else:
                        for move in picking.move_ids_without_package:
                            if line.product_id.id == move.product_id.id:
                                line.product_uom_qty = move.product_uom_qty - move.quantity_done
                    
            picking.action_cancel()
            so = self.env['sale.order'].search([('id','=', picking.sale_id.id)])
            if not picking.backorder_id:
                so = self.env['sale.order'].search([('id','=', picking.sale_id.id)])
                so.sudo().with_context(force_approval=True).action_cancel()
            else:  
                sale_ids = self.env['sale.order.line'].search([('order_id','=', picking.sale_id.id)])
                for sale in sale_ids:
                    if so.state == 'done':
                        so.sudo().action_unlock()
                        sale.product_uom_qty = sale.qty_delivered
                        so.sudo().action_done()
                    else:
                        sale.product_uom_qty = sale.qty_delivered

    def _cronjob_run_cancel(self):
        picking_ids = self.env['stock.picking'].search([('picking_type_code','=','outgoing'),('state','=','cancel')])
        for picking in picking_ids:
            # makloon_product_ids = picking.move_ids_without_package.mapped('product_id').filtered(lambda r: r.makloon == True)
            # if len(makloon_product_ids) > 0 and picking.sale_id.id:
            #     so = picking.sale_id.copy()
            #     days = so.company_id.customer_lead_time
            #     so.update({'commitment_date':datetime.now() + timedelta(days=days)})
            #     for line in so.order_line:
            #         if line.product_id.id not in makloon_product_ids.ids:
            #             line.unlink()
            #         else:
            #             for move in picking.move_ids_without_package:
            #                 if line.product_id.id == move.product_id.id:
            #                     line.product_uom_qty = move.product_uom_qty - move.quantity_done
                    
            # picking.action_cancel()
            so = self.env['sale.order'].search([('id','=', picking.sale_id.id)])
            if not picking.backorder_id:
                so = self.env['sale.order'].search([('id','=', picking.sale_id.id)])
                so.sudo().with_context(force_approval=True).action_cancel()
            else:  
                sale_ids = self.env['sale.order.line'].search([('order_id','=', picking.sale_id.id)])
                for sale in sale_ids:
                    if so.state == 'done':
                        so.sudo().action_unlock()
                        sale.product_uom_qty = sale.qty_delivered
                        so.sudo().action_done()
                    else:
                        sale.product_uom_qty = sale.qty_delivered
