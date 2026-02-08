from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class KasBankReport(models.Model):
    _name = "report.kas.bank"
    _description = "Kas Bank Report"
    _auto = False
    _order = "id DESC"

    name = fields.Char(string='Code Ref')
    partner_id = fields.Many2one('res.partner', string='Partner')
    payment_term_id = fields.Many2one('account.payment.term', string='Term of Payments')
    credit_limit = fields.Float(string='Credit Limit')
    omzet_amount = fields.Float(string='Omzet')
    piutang = fields.Float(related='pricelist_id.current_credit',string='Piutang')
    company_id = fields.Many2one('res.company', string='Company')


    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    id, 
                    name, 
                    partner_id,
                    payment_method_id, 
                    amount,
                    company_id
                FROM 
                    account_payment 
                WHERE 
                    payment_type = 'inbound';
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
