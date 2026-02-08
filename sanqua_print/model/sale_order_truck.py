# -*- coding: utf-8 -*-

import logging
import math
import pytz

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.addons.sanqua_print.helpers import amount_to_text,\
    format_local_currency,\
    format_local_datetime
from datetime import date, datetime

_logger = logging.getLogger(__name__)

class SaleOrderTruck(models.Model):
    _inherit = 'sale.order.truck'

    material_print = fields.Boolean(string='Print Materials', default=True)
    sequence_sj_ids = fields.One2many('sale.order.truck.surat.jalan.sequence', 'sale_truck_id', string='Delivery Number')

    def _generate_sequence_delivery(self):
        for line in self.order_line_ids.mapped('partner_id'):
            self.env['sale.order.truck.surat.jalan.sequence'].create({
                'sale_truck_id' : self.id,
                'partner_id' : line.id,
                # 'name' : self.env['ir.sequence'].next_by_code('seq.delivery.order.doc.name')
            })
    
    def btn_confirm(self):
        res = super(SaleOrderTruck, self).btn_confirm()
        self._generate_sequence_delivery()
        return res

    @staticmethod
    def get_format_currency(value,total=False):
        """ Get format currency with rule: thousand -> (.) and no decimal place.
        :param value: Float. Value that need to be formatting.
        :return: String. Format currency result.
        """
        return format_local_currency(value,total)

    def get_format_datetime(self, datetime_value, only_date=False):
        """ Get format datetime as string.
        :param datetime_value: Datetime. Datetime that need to be formatting.
        :param only_date: Boolean. If 'True' then value will be return as Date.
        :return: String. Format datetime result.
        """
        user_tz = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')

        datetime_value = datetime.combine(datetime_value.today(), datetime.min.time())

        return format_local_datetime(user_tz, datetime_value, only_date=True)

    def get_blank_space(self,line_ids):
        return math.ceil(line_ids/5) * 5 - line_ids


class SaleOrderTruckSuratJalanSequence(models.Model):
    _name = 'sale.order.truck.surat.jalan.sequence'
    _description = 'Sequence for Surat Jalan'

    partner_id = fields.Many2one('res.partner', string='Customer')
    name = fields.Char(string='Deliver Number',compute='_get_no_sj_wim')
    sale_truck_id = fields.Many2one('sale.order.truck', string='Sale Truck')

    def _get_no_sj_wim(self):
        """get delivery number based on partner"""
        for rec in self:
            rec.name = ''
            sale_id = rec.sale_truck_id.sale_ids.filtered(lambda r:r.id != rec.sale_truck_id.plant_sale_id.id)
            if sale_id:
                picking_id = sale_id.picking_ids.filtered(lambda r:r.picking_type_code == 'outgoing' and r.partner_id and r.partner_id.id == rec.partner_id.id)
                if picking_id:
                    rec.name  = picking_id[0].display_name
