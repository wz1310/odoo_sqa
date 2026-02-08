from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class HargaDasarKonsumenReport(models.Model):
    _name = "report.summary.customer.do.new"
    _description = "Summary Customer DO Report"
    _auto = False
    _order = "id ASC"

    partner_id = fields.Many2one('res.partner', string='Customer')
    date = fields.Char('Order Date', readonly=True)
    price_total = fields.Float('Total Amount', readonly=True)
    untaxed_amount_invoiced = fields.Float('Paid', readonly=True)
    amount_residual = fields.Float('Amount Due', readonly=True)
    company_id = fields.Many2one('res.company', string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                select 
                       CONCAT(t.partner_id, t.bulan_tahun) as id,
                       t.partner_id, 
                       t.bulan_tahun as date, 
                       t.total_amount as price_total,
                       t.company_id,
                    (select sum(aml.credit) 
                        from account_move_line aml 
                        left join account_journal journal on journal.id = aml.journal_id
                        where aml.partner_id = t.partner_id 
                            and journal.is_down_payment = True
                            and to_char(aml.date, 'Mon YYYY') = t.bulan_tahun) as untaxed_amount_invoiced,
                    coalesce((select sum(aml.credit) 
                        from account_move_line aml 
                        left join account_journal journal on journal.id = aml.journal_id
                        where aml.partner_id = t.partner_id 
                            and journal.is_down_payment = True
                            and to_char(aml.date, 'Mon YYYY') = t.bulan_tahun), 0) - t.total_amount as amount_residual
                    from (select am.partner_id,
                    sum(am.amount_total) as total_amount,
                    am.company_id as company_id,
                    to_char(am.date_order, 'Mon YYYY') as bulan_tahun
    
                from sale_order am
                LEFT JOIN account_payment_term apt ON apt.id = am.payment_term_id
                where am.state in ('sale', 'done', 'force_locked') and apt.name = 'DO'
                group by am.company_id, am.partner_id, to_char(am.date_order, 'Mon YYYY')
                ) t
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())