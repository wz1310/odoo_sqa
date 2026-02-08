# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_truck_status_ids = fields.One2many('sale.truck.item.status', 'partner_id', string='Sale Truck Status', track_visibility='onchange')
    sale_truck_dispenser_ids = fields.One2many('sale.truck.dispenser.status', 'partner_id', string='Sale Truck Dispenser', track_visibility='onchange')
    is_readonly = fields.Boolean(compute='_compute_is_readonly', string='Is Manager', track_visibility='onchange')
    sale_truck_item_status_partner_report_ids = fields.One2many('sale.truck.item.status.partner.report', 'partner_id', string="Stock Cards (Galon)")

    final_stock = fields.Float(compute='_compute_stock_akhir', string='Final Stock')
    
    @api.depends('sale_truck_item_status_partner_report_ids',
                 'sale_truck_item_status_partner_report_ids.returned_qty',
                 'sale_truck_item_status_partner_report_ids.changed_qty',
                 'sale_truck_item_status_partner_report_ids.replaced_qty')
    def _compute_stock_akhir(self):
        for rec in self:
            sum_borrow = sum([x.borrow_qty for x in rec.sale_truck_item_status_partner_report_ids])
            sum_returned = sum([x.returned_qty for x in rec.sale_truck_item_status_partner_report_ids])
            sum_changed = sum([x.changed_qty for x in rec.sale_truck_item_status_partner_report_ids])
            rec.final_stock = sum_borrow + sum_returned + sum_changed

    def open_stock_card_moves(self):
        action = self.env['ir.actions.act_window'].for_xml_id('sales_truck_item_status', 'action_sale_truck_item_status')
        action.update({'domain':[('partner_id','in',self.ids)]})
        return action
    
    # @api.depends('')
    def _compute_is_readonly(self):
        for rec in self:
            rec.is_readonly = True
            if self.env.user.has_group('sales_truck_item_status.group_sale_truck_item_status_manager'):
                rec.is_readonly = False

    def fetch_borrow(self):
        all_companies = self.env['res.company'].search([])
        self.env['sale.truck.item.status'].sudo().with_context(allowed_company_ids=all_companies.ids).fetch_borrow(self.id)


    def fetch_dispenser(self):
        form = self.env.ref('sales_truck_item_status.view_res_partner_fetch_dispenser_view', raise_if_not_found=False)
        return {
                'name': _('Fetch Dispenser'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'res.partner.wizard.fetch.dispenser',
                #'views': [(form.id, 'form')],
                'view_id': False,
                'target': 'new',
                
            }
        # all_companies = self.env['res.company'].search([])
        # self.env['sale.truck.dispenser.status'].sudo().with_context(allowed_company_ids=all_companies.ids).fetch_borrow()
    