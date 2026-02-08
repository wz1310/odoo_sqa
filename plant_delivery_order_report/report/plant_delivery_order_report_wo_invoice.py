from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)


class PlantDeliveryOrderReportWoInvoice(models.Model):
    _name = "plant.delivery.order.wo.invoice.report"
    _description = "Plant Delivery Order Report (Logistic)"
    _auto = False

    sj_no = fields.Char(string='No. SJ Plant')
    sj_wim_no = fields.Char(string='No. SJ WIM')
    po_wim_no = fields.Char(string='No. PO WIM')
    partner_id = fields.Integer(string='Customer Plant ID')
    contact = fields.Char(string='Customer Plant')
    customer_wim = fields.Char(string='Customer WIM')
    gudang_wim = fields.Many2one('stock.picking.type', string='Gudang')
    do_date = fields.Datetime(string='Delivery Date')
    do_receive_date = fields.Datetime(string='Receive Date')
    so_no = fields.Char(string='SO No.')
    so_wim_no = fields.Char(string='SO WIM No.')
    company_id = fields.Many2one('res.company', string='Company')
    desc_product = fields.Char(string='Product')


    internal_sale_notes = fields.Char(string='Internal Sale Notes')

    qty_demand = fields.Float(string='Demand')
    qty_done = fields.Float(string='Done')
    qty_return = fields.Float(string='Return')
    qty_net = fields.Float(string='Net')
    state = fields.Char(string='State')
    uom_name = fields.Char(string='Unit')
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    fleet_driver_id = fields.Many2one('res.partner', string='Driver')
    destination = fields.Many2one('res.partner', string='Destination')
    region_group_id = fields.Many2one('region.group',string='Area')
    customer_wim_reg = fields.Many2one('region.group',string='Area Customer Wim')
    order_pickup_method_id = fields.Many2one('order.pickup.method', string='AS / K')

    def get_main_request(self):

        request = """
        CREATE or REPLACE VIEW %s AS
            SELECT ROW_NUMBER
                    ( ) OVER ( ORDER BY A.move_id ) AS "id",
                    A.so_id,
                    A.move_id,
                    A.sm_state,
                    A.picking_id,
                    A.sj_no,
                    A.sj_wim_no,
                    A.partner_id,
                    A.contact,
                    A.customer_wim,
                    A.customer_wim_reg,
                    A.do_date,
                    A.do_receive_date,
                    A.so_no,
                    A.so_wim_no,
                    A.po_wim_no,
                    A.company_id,
                    A.company,
                    A.desc_product,
                    A.product_id,
                    A.product_name,
                    A.qty_demand,
                    A.qty_done,
                    SUM ( COALESCE ( A.qty_return, 0 ) ) AS "qty_return",
                    ( A.qty_done - SUM ( COALESCE ( A.qty_return, 0 ) ) ) AS "qty_net",
                    A.STATE,
                    A.uom_name,
                    A.location_id,
                    A.location_dest_id,
                    A.gudang_wim,
                    A.fleet_vehicle_id,
                    A.fleet_driver_id,
                    A.internal_sale_notes,
                    A.destination,
                    A.region_group_id,
                    A.order_pickup_method_id
                FROM
                    (
                    SELECT
                        so.ID AS "so_id",
                        sm.ID AS "move_id",
                        sm.STATE AS "sm_state",
                        pick.ID AS "picking_id",
                --                         pick.name AS "internal_transfer",
                        pick.doc_name AS "sj_no",
                        pick.no_sj_wim AS "sj_wim_no",
                        partner.ID AS "partner_id",
                        partner.NAME AS "contact",
                        partner_interco.NAME AS "customer_wim",
                        partner_interco.region_group_id AS "customer_wim_reg",
                        pick.date_done AS "do_date",
                        pick.date_received AS "do_receive_date",
                        pick.partner_id AS "destination",
                        so.NAME AS "so_no",
                        po.partner_ref AS "so_wim_no",
                        po.NAME AS "po_wim_no",
                        company.ID AS "company_id",
                        company.NAME AS "company",
                        sol.NAME AS "desc_product",
                        sm.product_id,
                        pt.NAME AS "product_name",
                        ( sm.product_uom_qty ) AS "qty_demand",
                        SUM ( sl.qty_done ) AS "qty_done",
                        COALESCE ( sm_return.product_uom_qty, 0 ) AS "qty_return",
                        pick.STATE AS "state",
                        uom.NAME AS "uom_name",
                        pick.location_id AS "location_id",
                        pick.location_dest_id AS "location_dest_id",
                        po.picking_type_id AS "gudang_wim",
                        ( CASE WHEN pick_interco.fleet_vehicle_id IS NOT NULL THEN pick_interco.fleet_vehicle_id ELSE pick.fleet_vehicle_id END ) AS "fleet_vehicle_id",
                        ( CASE WHEN pick_interco.fleet_driver_id IS NOT NULL THEN pick_interco.fleet_driver_id ELSE pick.fleet_driver_id END ) AS "fleet_driver_id",
                        pick.internal_sale_notes,
                        reg.id AS region_group_id,
                        so.order_pickup_method_id AS order_pickup_method_id
                    FROM
                        stock_picking AS pick
                        LEFT JOIN stock_picking_type AS pick_type ON pick.picking_type_id = pick_type.
                        ID LEFT JOIN sale_order AS so ON so.ID = pick.sale_id
                        LEFT JOIN stock_move AS sm ON pick.ID = sm.picking_id
                        LEFT JOIN stock_move_line AS sl ON sl.move_id = sm.
                        ID LEFT JOIN res_company AS company ON pick.company_id = company.
                        ID LEFT JOIN res_partner AS partner ON so.partner_id = partner.
                        ID LEFT JOIN res_users AS users ON users.ID = so.user_id
                        LEFT JOIN res_partner AS partner_user ON users.partner_id = partner_user.
                        ID LEFT JOIN res_partner AS partner_picking ON so.partner_shipping_id = partner_picking.
                        ID LEFT JOIN partner_pricelist AS p_list ON p_list.ID = so.partner_pricelist_team_id
                        LEFT JOIN region_group AS reg ON reg.ID = partner_picking.region_group_id
                        LEFT JOIN customer_group AS cg ON cg.ID = p_list.customer_group
                        LEFT JOIN fleet_vehicle_model AS model ON model.ID = so.vehicle_model_id
                        LEFT JOIN fleet_vehicle AS vehicle ON vehicle.ID = pick.fleet_vehicle_id
                        LEFT JOIN res_partner AS partner_driver ON partner_driver.ID = pick.fleet_driver_id
                        LEFT JOIN product_product pp ON sm.product_id = pp.
                        ID LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.
                        ID LEFT JOIN sale_order_line sol ON sm.sale_line_id = sol.
                        ID LEFT JOIN (
                            SELECT origin_returned_move_id, SUM(COALESCE ( product_uom_qty, 0 )) AS product_uom_qty
                            FROM stock_move 
                            WHERE state = 'done'
                            GROUP BY origin_returned_move_id
                        )  sm_return ON ( sm.ID = sm_return.origin_returned_move_id )
                        LEFT JOIN uom_uom AS uom ON sl.product_uom_id = uom.
                        ID LEFT JOIN ( SELECT NAME, partner_ref, interco_sale_id, picking_type_id FROM purchase_order ) po ON po.NAME = so.client_order_ref
                        LEFT JOIN sale_order so_interco ON so_interco.ID = po.interco_sale_id
                        LEFT JOIN res_partner partner_interco ON partner_interco.ID = so_interco.partner_id
                        
                        LEFT JOIN ( SELECT fleet_vehicle_id, fleet_driver_id, doc_name FROM stock_picking ) pick_interco ON pick_interco.doc_name = pick.no_sj_wim 
                    WHERE
                        pick_type.code IN ( 'outgoing' ) 
                        AND pick.STATE != 'cancel' 
                        AND company.ID <> 2 
                        AND pick.picking_type_id IN ( SELECT ID FROM stock_picking_type WHERE company_id <> 2 AND code LIKE'outgoing' ) 
                        AND pick.location_dest_id = 5
                        -- AND pick.company_id = 6
                        -- AND pick.date_done BETWEEN '2022-10-31 17:00:00' AND '2022-11-02 16:59:59'
                        AND sm.origin_returned_move_id IS NULL -- This filter is takeout SJ that comes from retur to retur
                    GROUP BY
                        so.ID,
                        sm.ID,
                        sm.STATE,
                        pick.ID,
                        pick.NAME,
                        pick.doc_name,
                        pick.no_sj_wim,
                        partner.ID,
                        partner.NAME,
                        partner_interco.NAME,
                        partner_interco.region_group_id,
                        pick.date_done,
                        pick.date_received,
                        so.NAME,
                        po.partner_ref,
                        po.NAME,
                        company.ID,
                        company.NAME,
                        sol.NAME,
                        sm.product_id,
                        pt.NAME,
                        pick.STATE,
                        uom.NAME,
                        pick.location_id,
                        pick.location_dest_id,
                        po.picking_type_id,
                        sm_return.product_uom_qty,
                        pick_interco.fleet_vehicle_id,
                        pick_interco.fleet_driver_id,
                        pick.internal_sale_notes,
                        reg.id,
                        so.order_pickup_method_id
                    ORDER BY
                        pick.scheduled_date DESC 
                    ) A 
                GROUP BY
                    A.so_id,
                    A.move_id,
                    A.sm_state,
                    A.picking_id,
                    A.sj_no,
                    A.sj_wim_no,
                    A.partner_id,
                    A.contact,
                    A.customer_wim,
                    A.customer_wim_reg,
                    A.do_date,
                    A.do_receive_date,
                    A.so_no,
                    A.so_wim_no,
                    A.po_wim_no,
                    A.company_id,
                    A.company,
                    A.desc_product,
                    A.product_id,
                    A.product_name,
                    A.qty_demand,
                    A.qty_done,
                    A.STATE,
                    A.uom_name,
                    A.location_id,
                    A.location_dest_id,
                    A.gudang_wim,
                    A.fleet_vehicle_id,
                    A.fleet_driver_id,
                    A.internal_sale_notes,
                    A.destination,
                    A.region_group_id,
                    A.order_pickup_method_id
        """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
