from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class HargaDasarKonsumenReport(models.Model):
    _name = "report.sale.summary.sku"
    _description = "Sale Summary SKU Report"
    _auto = False
    _order = "id ASC"

    categ_id = fields.Many2one('product.category', string='Category')
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    date = fields.Datetime('Order Date', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    price_total = fields.Float('Total', readonly=True)
    company_id = fields.Many2one('res.company', string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    am.id,
                    pt.categ_id,
                    aml.product_id,
                    aml.quantity,
                    am.date,
                    aml.price_total,
                    am.company_id
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                JOIN product_product pp ON pp.id = aml.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE am.state = 'posted' and am.type = 'out_invoice' and aml.exclude_from_invoice_tab = False;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())