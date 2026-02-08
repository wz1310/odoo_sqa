from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)

class MISDeliveryOrder(models.Model):
    _name = "mis.report.delivery.order"
    _description = "WIM Delivery Order Report"
    _auto = False

    picking_no = fields.Char(string='No. Picking')
    sj_no = fields.Char(string='No. SJ')
    contact_code = fields.Char(string='Customer Code')
    contact = fields.Char(string='WIM Customer')
    sub_contact = fields.Char(string='Sub Contact')
    do_date = fields.Date(string='Delivery Date')
    do_receive_date = fields.Datetime(string='Receive Date')
    so_no = fields.Char(string='SO No.')
    plant_id = fields.Many2one('res.company', string='Plant')
    company_id = fields.Many2one('res.company', string='Company')
    product_code = fields.Char(string='Product Code')
    desc_product = fields.Char(string='Product')

    qty_demand = fields.Float(string='Demand')
    qty_done = fields.Float(string='Done')
    qty_return = fields.Float(string='Return')
    qty_net = fields.Float(string='Net')
    state = fields.Char(string='State')
    uom_name = fields.Char(string='Unit')
    location_id = fields.Many2one('stock.location', string='Source Location')

    invoice_no = fields.Char(string='No. Invoice')
    invoice_date = fields.Char(string='Tanggal Invoice')
    price_pfi = fields.Float(string='Price Subtotal')
    invoice_commercial_no = fields.Char(string='No. Invoice Commerical')
    price_before_tax = fields.Float(string='DPP')
    e_tax_invoice_id = fields.Many2one('etax.invoice', string="E-Tax")

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    fleet_driver_id = fields.Many2one('res.partner', string='Driver')

    invoice_id = fields.Integer(string='Invoice Id')

    sales_team_id = fields.Many2one('crm.team', string='Division')


    def get_main_request(self):
            request = """
                CREATE or REPLACE VIEW %s AS
                    SELECT  ROW_NUMBER() OVER (ORDER BY sm.id) AS "id",
                            sm.id AS "move_id",
                            sm.state AS "sm_state", 
                            pick.id AS "picking_id", 
                            pick.name AS "picking_no", 
                            pick.doc_name as "sj_no",
                            partner.code AS "contact_code",
                            partner.name AS "contact",
                            partner_picking_2.name AS "sub_contact",
                            pick.date_done AS "do_date",
                            pick.date_received AS "do_receive_date",
                            so.name AS "so_no",
                            pick.plant_id AS "plant_id",
                            company.id AS "company_id",
                            company.name AS "company",
                            sol.name AS "desc_product",
                            pt.default_code AS "product_code",
                            pt.name AS "product_name",      
                            coalesce(sm.product_uom_qty,0) AS "qty_demand",
                            SUM(sl.qty_done) AS "qty_done",
                            coalesce(sm_return.product_uom_qty, 0) AS "qty_return",
                            ( SUM(coalesce(sl.qty_done,0)) - coalesce(sm_return.product_uom_qty,0) ) AS "qty_net",
                            pick.state AS "state",
                            uom.name AS "uom_name",
                            pick.location_id AS "location_id",
                            
                            pick.invoice_id AS "invoice_id",
                            am.id AS "account_move_id",
                            am.name AS "invoice_no",
                            am.invoice_date AS "invoice_date",
                            amls.price_pfi AS "price_pfi",
                            etax.name AS "invoice_commercial_no",
                            aml.price_subtotal AS "price_before_tax",
                            etax.e_tax_invoice_id AS "e_tax_invoice_id",
                            
                            pick.sales_team_id AS "sales_team_id",
                            
                            ( CASE WHEN pick_interco.fleet_vehicle_id IS NOT NULL THEN pick_interco.fleet_vehicle_id ELSE pick.fleet_vehicle_id END ) AS "fleet_vehicle_id",
                            ( CASE WHEN pick_interco.fleet_driver_id IS NOT NULL THEN pick_interco.fleet_driver_id ELSE pick.fleet_driver_id END ) AS "fleet_driver_id"
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
                        LEFT JOIN res_partner as partner_picking_2 ON pick.partner_id = partner_picking_2.id
                        LEFT JOIN uom_uom as uom ON sl.product_uom_id = uom.id
                        LEFT JOIN (
                        SELECT name,partner_ref, interco_sale_id, picking_type_id
                            FROM purchase_order
                        ) po ON po.name = so.client_order_ref
                        LEFT JOIN sale_order so_interco ON so_interco.id = po.interco_sale_id
                        LEFT JOIN res_partner partner_interco ON partner_interco.id = so_interco.partner_id
                        LEFT JOIN account_move am ON am.id = pick.invoice_id
    --                  LEFT JOIN account_move_line aml ON ( ( aml.move_id = am.id ) AND ( CONCAT(pick.name,':',sol.name) = aml.name ) AND aml.exclude_from_invoice_tab = false )
                        LEFT JOIN (
                            SELECT product_id,move_id,sum(price_subtotal) AS price_pfi
                            FROM account_move_line
                            WHERE exclude_from_invoice_tab = false
                            GROUP BY move_id,product_id
                        ) amls ON ( amls.move_id = am.id and amls.product_id = pp.id and sol.name NOT LIKE '%s')
                        LEFT JOIN (
                            SELECT move_id, price_subtotal, exclude_from_invoice_tab, name, product_id
                            FROM account_move_line
                            WHERE exclude_from_invoice_tab = false
                        ) aml ON ( aml.move_id = am.id AND aml.name = CONCAT(pick.name,': ',sol.name) )
                        LEFT JOIN account_move_etax_invoice_merge_rel etax_account_move_rel ON am.id = etax_account_move_rel.account_move_id
                        LEFT JOIN etax_invoice_merge etax ON etax.id = etax_account_move_rel.etax_invoice_merge_id
                        LEFT JOIN (
                            SELECT fleet_vehicle_id, fleet_driver_id, doc_name
                            FROM stock_picking

                        ) pick_interco ON pick_interco.doc_name = pick.no_sj_wim
                    WHERE pick_type.code IN ('outgoing') and pick.state != 'cancel'
                        AND company.id = 2
                        AND pick.picking_type_id IN (
                            select id from stock_picking_type where company_id = 2 and code like 'outgoing'
                        )
                        AND pick.location_dest_id = 5
                        -- AND pick.doc_name like 'WIM-SJ/22/01/003588'
                    GROUP BY sm.id, sm.state, pick.id, pick.name, pick.doc_name, partner.name, partner_picking_2.name, pick.date_done, pick.date_received,
                            so.name, pick.plant_id, company.id, company.name, sol.name, pt.name, pick.state, uom.name, pick.location_id, sm_return.product_uom_qty,
                            partner.code, pick_interco.fleet_vehicle_id, pick_interco.fleet_driver_id, am.id, etax.name,aml.price_subtotal,
                            etax.e_tax_invoice_id, pt.default_code,amls.price_pfi
                    ORDER BY pick.scheduled_date DESC
            """ % (self._table,'Free Product -%',)
            return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())