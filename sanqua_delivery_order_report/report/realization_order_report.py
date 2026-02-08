from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class RealizationOrderReport(models.Model):
    _name = "report.realization.order"
    _description = "Realization Order Report"
    _auto = False
    _order = "id"

    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Product')
    qty_order = fields.Float(string='Qty')
    company_id = fields.Many2one('res.company', string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    ROW_NUMBER() over() AS id,
                    sp.partner_id,
                    sm.product_id, 
                    sum(sm.product_uom_qty) AS qty_order,
                    sp.company_id
                FROM stock_picking sp
                JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
				JOIN stock_move sm ON sm.picking_id = sp.id
                JOIN product_product pp ON sm.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                JOIN product_category pc ON pt.categ_id = pc.id
                WHERE 
                    pc.finish_good = TRUE AND 
                    sp.state = 'done' AND 
                    sm.state = 'done' AND 
                    spt.code = 'outgoing'
                GROUP BY sp.partner_id,sm.product_id,sp.company_id
                ORDER BY sp.partner_id,sm.product_id,sp.company_id;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())