""" RPB """
from odoo import models, fields, _ , api
from datetime import datetime


class MrpRpb(models.Model):
    """ Define Rencana Pembelian Material """

    _name = 'mrp.rpb'
    _description = 'Mrp RPB'

    is_active = fields.Boolean()
    date_start = fields.Date()
    date_end = fields.Date()
    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')], 
                            string='Month')
    name = fields.Char(required=True)
    year = fields.Selection([(str(num), str(num)) for num in range(2018, (datetime.now().year)+20 )])
