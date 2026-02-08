from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']

    invoice_origin_pfi = fields.Char(related='move_id.invoice_origin', string='SJ-PFI')
    invoice_origin_ivj = fields.Char(related='move_id.stock_move_id.picking_id.doc_name', string='SJ-IVJ')
    doc_nm = fields.Char(string="Doc.Name",related='move_id.stock_move_id.picking_id.doc_name')
    ret_of = fields.Char(string="Return Of", compute='ret_off')
    # do_number = fields.Char(string='No. SJ', compute='_compute_do_number')
    #
    # def _compute_do_number(self):
    #     # print('>>> move_id : ' + str(self.move_id))
    #     if self.type == 'out_invoice':
    #         self.do_number = self.invoice_origin_pfi
    #     elif self.type == 'entry':
    #         self.do_number = self.invoice_origin_do

    # def ret_query(self,label=None):
    #     qwr = """
    #     SELECT name FROM stock_picking WHERE origin ="""+"'"+'Return of'+' '+label+"'"+"""
    #     AND state = 'done'
    #     """
    #     self.env.cr.execute(qwr,())
    #     result = self.env.cr.dictfetchall()
    #     if result:
    #         z = [x['name'] for x in result]
    #         z_list = ','.join([str(e) for e in z])
    #         return z_list

    def ret_off(self):
        for rec in self:
            rec.ret_of = ''
        # trig = 'TMP'or'IMP'or'SQA'or'KAJ'or'WIM'or'GIT'
        # for rec in self:
        #     rec.ret_of = ""
        #     rec.ret_of = rec.move_id.stock_move_id.picking_id.origin
        #     if rec.ret_of:
        #         if 'Return' in rec.ret_of:
        #             rec.ret_of = rec.move_id.stock_move_id.picking_id.origin
        #         else:
        #             rec.ret_of = ""
        #     else:
        #         if rec.name:
        #             if trig in rec.name:
        #                 rec.ret_of = rec.ret_query(rec.name)