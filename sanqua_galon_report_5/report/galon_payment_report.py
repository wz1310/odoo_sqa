from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class PaymentGalonReport(models.Model):
    _name = "report.galon.payment"
    _description = "Payment Galon Report"
    _auto = False
    _order = "id DESC"

    code = fields.Char('Partner Code')
    partner_name = fields.Char('Partner Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    receive_date = fields.Date(string='Receive Date')
    confirm_date = fields.Date(string='Confirm Date')
    amount_paid = fields.Float(string='Amount Paid')
    company_id = fields.Many2one('res.company', string='Company')
    


    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT ap.partner_id as id,ap.partner_id,srl.date as receive_date,srl.date as confirm_date,srl.pay_amount as amount_paid, sr.company_id,rp.code, rp.name as partner_name
                FROM account_payment ap
                JOIN settlement_request sr ON sr.id = ap.settlement_request_id and sr.state = 'done'
                JOIN settlement_request_line srl ON srl.settlement_id = sr.id
                JOIN account_move am ON am.id = srl.invoice_id
                LEFT JOIN account_move_line aml ON aml.move_id = am.id and aml.exclude_from_invoice_tab = False
                JOIN product_product p_p ON p_p.id = aml.product_id
                JOIN product_template pt ON pt.id = p_p.product_tmpl_id
                JOIN product_category pc ON pc.id = pt.categ_id and pc.report_category = 'gln'
                LEFT JOIN res_partner rp ON rp.id = ap.partner_id

                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
