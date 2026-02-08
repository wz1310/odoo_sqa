from odoo import api,fields,models,_
import time
from odoo.exceptions import UserError, RedirectWarning, ValidationError, except_orm, Warning
from datetime import datetime, date
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import odoo.addons.decimal_precision as dp


class ResPartnerFetchDispenser(models.TransientModel):
    _name = "res.partner.wizard.fetch.dispenser"


    def _get_cusutomer(self):
        partner_id = self._context.get('active_id')
        check = self.env['res.partner'].browse(partner_id)
        customer = check.id
        return customer

    def _get_company(self):
        # partner_id = self._context.get('active_id')
        # check = self.env['res.partner'].browse(partner_id)
        # company_id = check.company_id.id
        company_id = self.env.company.id
        return company_id



    brand = fields.Text(string='Brand', track_visibility='onchange')
    vendor_ids = fields.Many2many('res.partner',string='Vendor', domain=[('supplier','=',True)])
    new_brand = fields.Text(string=' New Brand', track_visibility='onchange')
    buy_date = fields.Date(string='Buy Date', track_visibility='onchange')
    serial_number = fields.Char(string='Serial Number', track_visibility='onchange')
    new_serial_number = fields.Char(string='New Serial Number', track_visibility='onchange')
    qty = fields.Integer(string='Qty', track_visibility='onchange', default="1")
    deliver_date = fields.Date(string='Date Deliver To Customer', track_visibility='onchange')
    #condition = fields.Text(string='Condition', track_visibility='onchange')
    condition = fields.Selection([('good','Good'),('broken','Broken')],'Condition')
    #type_of_lease = fields.Text(string='Type of Lease', track_visibility='onchange')
    type_of_lease = fields.Selection([('borrow','Borrow'),('rent','Rent'),
    								  ('return','Return'),
    								  ('change','Change')],'Type of Lease')
    return_date = fields.Date('Return Date')
    picking_id = fields.Many2one('stock.picking', string='Source Document', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner',default=_get_cusutomer, string='Customer',required=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company',default=_get_company, string='Company',required=True, track_visibility='onchange')
    rental_price_to_vendor = fields.Float('Rental Price to Vendor',required=True, track_visibility='onchange')
    rental_price_to_customer = fields.Float('Rental Price to Customer',required=True, track_visibility='onchange')


    def btn_confirm(self):
    	dispenser_obj = self.env['sale.truck.dispenser.status']
    	vals = {
    		'brand' : self.brand,
    		'buy_date' : self.buy_date,
    		'serial_number' : self.serial_number,
    		'qty' : self.qty,
    		'deliver_date' : self.deliver_date,
    		'condition' : self.condition,
    		'type_of_lease' : self.type_of_lease,
            'return_date' : self.return_date,
    		'picking_id' : self.picking_id.id,
    		'partner_id' : self.partner_id.id,
    		'company_id' : self.company_id.id,
            'rental_price_to_vendor' : self.rental_price_to_vendor,
            'rental_price_to_customer' : self.rental_price_to_customer,
            'vendor_ids' : self.vendor_ids.ids
    	}
    	dispenser_id = dispenser_obj.create(vals)
