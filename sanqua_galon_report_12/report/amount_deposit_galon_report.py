from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class AmountDepositGalonReport(models.Model):
    _name = "report.amount.deposit.galon"
    _description = "Amount Deposit Galon Report"
    _auto = False
    _order = "id DESC"

    partner_code = fields.Char()
    partner_name = fields.Char()
    partner_id = fields.Many2one('res.partner', string='Partner')
    nilai = fields.Float(string='Nilai')
    qty = fields.Float(string='Qty')
    amount = fields.Float(string='Amount')
    date_deposito = fields.Date(string='Date')


    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT st.id,st.partner_id,st.amount, st.qty, 30000 as nilai, st.date_deposito, rp.code as partner_code, rp.name as partner_name
                FROM sales_truck_item_adjustment st
                    LEFT JOIN res_partner rp on st.partner_id = rp.id
                WHERE st.adjustment_type = 'deposit' and st.state = 'done';
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
