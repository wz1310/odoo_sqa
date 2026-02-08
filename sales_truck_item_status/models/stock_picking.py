# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    sale_truck_status_ids = fields.Many2many('sale.truck.item.status', string='Sales Truck Status',compute='_compute_field_sale_truck_status_ids', track_visibility='onchange')
    sale_truck_id = fields.Many2one('sale.order.truck', string="Sale Truck", track_visibility='onchange', related=False, store=True, compute="_compute_sale_truck_id", inverse="_inverse_true")
    is_fetch_borrow = fields.Boolean(string='Fetch Borrow',default=False, track_visibility='onchange')
    is_fetch_dispenser = fields.Boolean(string='Fetch Dispenser',default=False, track_visibility='onchange')

    @api.depends('sale_id')
    def _compute_sale_truck_id(self):
        for rec in self:
            res = False
            if rec.sale_id.id:
                res = rec.sale_id.sale_truck_id.id
                if rec.sale_id.sale_truck_id:
                    rec.write({'origin': rec.sale_id.sale_truck_id.sequence_sj_ids.filtered(lambda r: r.partner_id.id == rec.partner_id.id).name})                    
            rec.sale_truck_id = res

    def _inverse_true(self):
        return True

    @api.onchange('sale_truck_id','state')
    def _onchange_sale_truck_id(self):
        if self.sale_truck_id:
            self.fleet_vehicle_id = self.sale_truck_id.vehicle_id
            self.fleet_driver_id = self.sale_truck_id.vehicle_driver_id
            # virtual_location = self.env.ref('stock.stock_location_locations_virtual')
            # transit_location_id = self.env['stock.location'].with_user(self.env.user.company_id.intercompany_user_id.id).search([('usage','=','transit'),('company_id','=',False),('location_id','=',virtual_location.id)])	
            # raise UserError (_(transit_location_id.name))
            # self.location_id = transit_location_id.id
    
    
    @api.depends('move_ids_without_package.sale_truck_status_id')
    def _compute_field_sale_truck_status_ids(self):
        for rec in self:
            rec.sale_truck_status_ids = False
            sale_truck_status_ids = rec.move_ids_without_package.mapped('sale_truck_status_id')
            if len(sale_truck_status_ids) > 0:
                rec.sale_truck_status_ids = [(6,0,sale_truck_status_ids.ids)]


class StockPicking(models.Model):
    _inherit = 'stock.move'
    
    sale_truck_status_id = fields.Many2one('sale.truck.item.status', string='Sales Truck Status', track_visibility='onchange')
    sale_truck_dispenser_id = fields.Many2one('sale.truck.dispenser.status', string='Sales Truck Dispenser', track_visibility='onchange')
    sale_truck_id = fields.Many2one('sale.order.truck', string="Sale Truck", related="picking_id.sale_truck_id", track_visibility='onchange')

