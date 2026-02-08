from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class RealizationOrderDriverReport(models.Model):
    _name = "report.realization.order.driver"
    _description = "Realization Order Driver Report"
    _auto = False
    _order = "id"

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    fleet_driver_id = fields.Many2one('res.partner', string='Driver')
    product_id = fields.Many2one('product.product', string='Product')
    qty_delivered = fields.Float(string='Qty Delivered')
    company_id = fields.Many2one('res.company', string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    ROW_NUMBER() over() AS id,
                    sp.fleet_vehicle_id,
                    sp.fleet_driver_id,
                    sml.product_id, 
                    sum(sml.qty_done) AS qty_delivered,
                    sp.company_id
                FROM stock_picking sp
                JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
				JOIN stock_move_line sml ON sml.picking_id = sp.id
                JOIN product_product pp ON sml.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                JOIN product_category pc ON pt.categ_id = pc.id
                WHERE 
                    pc.finish_good = TRUE AND 
                    sp.state = 'done' AND 
                    sml.state = 'done' AND 
                    spt.code = 'outgoing'
                GROUP BY sp.fleet_vehicle_id,sp.fleet_driver_id,sml.product_id,sp.company_id
                ORDER BY sp.fleet_vehicle_id,sp.fleet_driver_id,sml.product_id,sp.company_id;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())