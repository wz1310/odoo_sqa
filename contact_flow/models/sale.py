from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def domain_partner(self):
    	sql = """SELECT * FROM "res_partner" WHERE "state"='approved' AND customer=True"""
    	cr= self.env.cr
    	cr.execute(sql,())
    	result= cr.fetchall()
    	find_res = [x[0] for x in result]
    	# print("find_res",find_res)
    	return [('id','in',find_res)]

    # partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer','=',True), ('state','=','approved')])
    partner_id = fields.Many2one('res.partner', string="Customer", domain=domain_partner)