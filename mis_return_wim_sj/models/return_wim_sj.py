from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)

class ReturnWIMSJ(models.Model):
    _inherit = 'stock.picking'

    def btn_repair_sj(self):
        print('>>> DO Number : ' + str(self.origin_returned_picking_id.doc_name))
        sql = "SELECT func_repair_sj_plant_wim(%s)"
        self.env.cr.execute(sql, (self.origin_returned_picking_id.doc_name,))
        result = self.env.cr.dictfetchall()
        print('>>> Result repair : ' + str(result))