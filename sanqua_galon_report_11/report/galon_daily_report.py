from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class DailyGalonReport(models.Model):
    _name = "report.galon.daily"
    _description = "Galon Daily Report"
    _auto = False
    _order = "id DESC"

    picking_id = fields.Many2one('stock.picking', string='NO SJ')
    date_done = fields.Date(string='Date')
    partner_code = fields.Char('Partner Code', related='partner_id.code', store=True)
    partner_name = fields.Char('Partner Name', related='partner_id.name', store=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    order_pickup_method_id = fields.Many2one('order.pickup.method', string='AS/K')
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    vehicle_model_id = fields.Many2one('fleet.vehicle.model', related='fleet_vehicle_id.model_id', string='Vehicle Model')
    plat_license = fields.Char(related='fleet_vehicle_id.license_plate',string='Plat License')
    product_id = fields.Many2one('product.product', string='Product')
    price_subtotal_sale = fields.Float(string='Sale Amount')
    invoice_id = fields.Many2one('account.move',string='Invoice')
    price_unit = fields.Float(string='Price Unit')
    price_subtotal_invoice = fields.Float(string='Invoice Amount')
    company_id = fields.Many2one('res.company', string='Company')


    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
					CONCAT(lpad(sp.id::TEXT, 5,'0'),rpad(sp.partner_id::TEXT,5,'0'),rpad(sp.order_pickup_method_id::TEXT,2,'0'),rpad(sm.product_id::TEXT,4,'0'))::BIGINT as id,
                    sp.id as picking_id,
                    sp.date_done, 
                    sp.partner_id,
                    sp.order_pickup_method_id,
                    sp.fleet_vehicle_id,
                    sm.product_id,
					sp.invoice_id,
					aml.price_unit,
                    sum(sol.price_total) as price_subtotal_sale,
                    sum(aml.credit) as price_subtotal_invoice,
                    sp.company_id
                FROM stock_picking AS sp
                JOIN stock_picking_type AS spt ON spt.id = sp.picking_type_id and spt.code = 'outgoing'
                JOIN stock_move sm ON sm.picking_id = sp.id and sm.state = 'done'
                JOIN sale_order_line sol ON sol.id = sm.sale_line_id and sol.order_id = sp.sale_id and sol.is_reward_line = False and sm.product_id = sol.product_id
                LEFT JOIN account_move am ON sp.invoice_id = am.id
                LEFT JOIN account_move_line aml ON aml.move_id = am.id and sm.product_id = aml.product_id and aml.exclude_from_invoice_tab = False 
                WHERE sp.state = 'done' and aml.price_unit > 0
				GROUP BY
					sp.id,
					sp.date_done, 
                    sp.partner_id,
                    sp.order_pickup_method_id,
                    sp.fleet_vehicle_id,
                    sm.product_id,
                    sp.invoice_id,
					aml.price_unit,
					sp.company_id;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
