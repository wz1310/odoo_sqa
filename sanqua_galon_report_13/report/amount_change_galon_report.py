from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class AmountChangeGalonReport(models.Model):
    _name = "report.amount.change.galon"
    _description = "Amount Change Galon Report"
    _auto = False
    _order = "id DESC"

    code = fields.Char('Code')
    partner_name = fields.Char('Partner Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    nilai = fields.Float(string='Nilai')
    amount = fields.Float(string='Amount')
    qty = fields.Float(string='Qty')
    date = fields.Date(string='Date')


    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT a.id, rp.name as partner_name, rp.code, b.partner_id,(a.qty * 30000) as amount, a.qty, 30000 as nilai, a.create_date as date
                FROM sales_truck_item_adjustment a
                LEFT JOIN sale_truck_item_status b on b.id = a.sale_truck_status_id
                LEFT JOIN res_partner rp on rp.id = b.partner_id
                WHERE a.adjustment_type = 'to_bill' and a.state = 'done';
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
