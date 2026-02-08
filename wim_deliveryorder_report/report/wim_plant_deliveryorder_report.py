from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)

class MISPlantDeliveryOrder(models.Model):
    _name = "mis.plant.report.delivery.order"
    _description = "WIM Delivery Order Report"

    sj_no = fields.Char(string='No. SJ Plant')
    sj_wim_no = fields.Char(string='No. SJ WIM')
    contact = fields.Char(string='Customer')
    customer_wim = fields.Char(string='Customer WIM')
    do_date = fields.Datetime(string='Delivery Date')
    do_receive_date = fields.Datetime(string='Receive Date')
    so_no = fields.Char(string='SO No.')
    so_wim_no = fields.Char(string='SO WIM No.')
    company_id = fields.Many2one('res.company', string='Company')
    desc_product = fields.Char(string='Product')

    qty_demand = fields.Float(string='Demand')
    qty_done = fields.Float(string='Done')
    qty_return = fields.Float(string='Return')
    state = fields.Char(string='State')
    uom_name = fields.Char(string='Unit')
    location_id = fields.Many2one('stock.location', string='Source Location')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT  ROW_NUMBER() OVER (ORDER BY sm.id) AS "id",
                        so.id AS "so_id",
                        sm.id AS "move_id",
                        sm.state AS "sm_state", 
                        pick.id AS "picking_id", 
                        pick.name AS "sj_no", 
                        pick.doc_name as "sj_wim_no",
                        partner.name AS "contact",
                        partner_interco.name AS "customer_wim",
                        pick.scheduled_date AS "do_date",
                        pick.date_received AS "do_receive_date",
                        so.name AS "so_no",
                        po.partner_ref AS "so_wim_no",
                        company.id AS "company_id",
                        company.name AS "company",
                        sol.name AS "desc_product",
                        pt.name AS "product_name",		
                        (sm.product_uom_qty) AS "qty_demand",
                        (sl.qty_done) AS "qty_done",
                        sm_return.product_uom_qty AS "qty_return",
                        pick.state AS "state",
                        uom.name AS "uom_name",
                        pick.location_id AS "location_id",
                        'wim_warehouse' AS "destination_location"
                FROM stock_picking AS pick
                    LEFT JOIN stock_picking_type AS pick_type ON pick.picking_type_id = pick_type.id
                    LEFT JOIN sale_order AS so ON so.id = pick.sale_id
                    LEFT JOIN stock_move AS sm ON pick.id = sm.picking_id
                    LEFT JOIN stock_move_line AS sl ON sl.move_id = sm.id
                    LEFT JOIN res_company as company ON pick.company_id = company.id
                    LEFT JOIN res_partner as partner ON so.partner_id = partner.id
                    LEFT JOIN res_users as users ON users.id = so.user_id
                    LEFT JOIN res_partner as partner_user ON users.partner_id = partner_user.id
                    LEFT JOIN res_partner as partner_picking ON so.partner_shipping_id = partner_picking.id
                    LEFT JOIN partner_pricelist as p_list ON p_list.id = so.partner_pricelist_team_id
                    LEFT JOIN region_group as reg on reg.id = partner_picking.region_group_id
                    LEFT JOIN customer_group as cg on cg.id = p_list.customer_group
                    LEFT JOIN fleet_vehicle_model as model on model.id = so.vehicle_model_id
                    LEFT JOIN fleet_vehicle as vehicle on vehicle.id = pick.fleet_vehicle_id
                    LEFT JOIN res_partner as partner_driver ON partner_driver.id = pick.fleet_driver_id
                    LEFT JOIN product_product pp ON sm.product_id = pp.id
                    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    LEFT JOIN sale_order_line sol ON sm.sale_line_id = sol.id
                    LEFT JOIN stock_move sm_return ON ( sm.id = sm_return.origin_returned_move_id AND sm_return.state = 'done' )
                    LEFT JOIN uom_uom as uom ON sl.product_uom_id = uom.id
                    LEFT JOIN (
                        SELECT name,partner_ref, interco_sale_id
                        FROM purchase_order
                    ) po ON po.name = so.client_order_ref
                    LEFT JOIN sale_order so_interco ON so_interco.id = po.interco_sale_id
                    LEFT JOIN res_partner partner_interco ON partner_interco.id = so_interco.partner_id
                WHERE pick_type.code IN ('outgoing') and pick.state != 'cancel'
                    AND company.id <> 2
                    AND pick.picking_type_id IN (
                        select id from stock_picking_type where company_id <> 2 and code like 'outgoing'
                    )
                    AND pick.location_dest_id = 5
                ORDER BY pick.scheduled_date DESC
        """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())


