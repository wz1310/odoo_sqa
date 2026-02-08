from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class DailyCustomerReport(models.Model):
    _name = "report.daily.customer"
    _description = "Daily Customer Report"
    _auto = False
    _order = "id DESC"

    sj_no = fields.Char(string='No. SJ')
    do_date = fields.Datetime(string='Date')
    contact = fields.Char(string='Customer')
    contact_code = fields.Char(string='Kode Customer')
    sub_contact = fields.Char(string='Customer Delivery')
    product_name = fields.Char(string='Product')
    product_code = fields.Char(string='Kode Product')
    price_unit = fields.Float(string='Price unit')
    qty_done = fields.Float(string='Qty')
    uom_name = fields.Char(string="Satuan")
    # price_before_tax = fields.Float(string='Total')
    take_in_plant_disc_nom = fields.Float(string='Disc. Take in Plant')
    discount_fixed_line = fields.Float(string='Disc. Program')
    invoice_no = fields.Char(string='Invoice')
    price_before_tax = fields.Float(string='Amount Total')
    amount_paid = fields.Float(string='Amount Paid')
    payment_date = fields.Date(string='Paid Date')
    pickup_method = fields.Char(string='AS / K')
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    contact_address_complete = fields.Char(string='Destination')
    company_id = fields.Many2one('res.company', string='Company')

    # def _compute_destination(self):
    #     for rec in self:
    #         res = False
    #         if rec.partner_shipping_id:
    #             res = ("%s - %s")%(rec.partner_shipping_id.display_name, rec.partner_shipping_id.contact_address_complete)
    #         rec.destination_address = res


    def get_main_request(self):
        # request = """
        #     CREATE or REPLACE VIEW %s AS
        #         SELECT
        #             CONCAT(lpad(sm.id::TEXT, 5,'0'),rpad(so_line.id::TEXT,5,'0'),rpad(aml.id::TEXT,6,'0'))::BIGINT as id,
        #             sp.date_done,
        #             sp.id as picking_id,
        #             sp.partner_id,
        #             rp.code as partner_code,
        #             rp.name as partner_name,
        #             sm.product_id,
        #             pp.default_code as product_code,
        #             pt.name as product_name,
        #             sm.product_uom as product_uom_id,
        #             so_line.price_unit,
        #             so_line.qty_delivered,
        #             so_line.price_unit * so_line.qty_delivered as nilai,
        #             so_line.take_in_plant_disc_nom,
        #             aml.discount_fixed_line,
        #             sp.invoice_id,
        #             am.amount_total,
        #             am.currency_id,
        #             sp.company_id,
        #             sp.order_pickup_method_id,
        #             so.partner_shipping_id,
        #             sp.fleet_vehicle_id,
        #             fv.model_id,
        #             line_promo.price_subtotal,
        #             ap.payment_date,
        #             ap.amount as amount_paid,
        #             ap.communication,
        #             CASE WHEN ap.state = 'draft' THEN 'N' ELSE 'Y' END as approved
        #         FROM stock_picking sp
        #         LEFT JOIN stock_move sm ON sm.picking_id = sp.id
        #         LEFT JOIN res_partner rp ON sp.partner_id = rp.id
        #         LEFT JOIN product_product pp ON sm.product_id = pp.id
        #         LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        #         LEFT JOIN sale_order so ON sp.sale_id = so.id
        #         LEFT JOIN fleet_vehicle fv ON fv.id = sp.fleet_vehicle_id
        #         LEFT JOIN sale_order_line so_line ON sm.sale_line_id = so_line.id
        #         JOIN account_move am ON sp.invoice_id = am.id
		# 		JOIN account_move_line aml ON aml.move_id = sp.invoice_id and aml.product_id = sm.product_id and exclude_from_invoice_tab = False and so_line.price_unit = aml.price_unit
        #         JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
        #         LEFT JOIN (
        #                     SELECT so_line.id, so_line.order_id,so_line.product_id,so_line.product_uom_qty * ppl_item.fixed_price as price_subtotal
        #                     FROM sale_order_line so_line
        #                     JOIN sale_order so ON so_line.order_id = so.id
        #                     JOIN product_pricelist_item ppl_item ON ppl_item.pricelist_id = so.pricelist_id AND ppl_item.product_id = so_line.product_id
        #                     WHERE so_line.is_reward_line = True
        #                 ) AS line_promo ON line_promo.id = sm.sale_line_id AND line_promo.product_id = sm.product_id
        #         LEFT JOIN account_invoice_payment_rel invoice_payment_rel ON invoice_payment_rel.invoice_id = sp.invoice_id
        #         LEFT JOIN account_payment ap ON ap.id = invoice_payment_rel.payment_id
        #         WHERE spt.code = 'outgoing' AND sp.state = 'done';
        #         """ % (self._table)

        request = """
                CREATE or REPLACE VIEW %s AS
                    	SELECT ROW_NUMBER() OVER (ORDER BY a.move_id) AS "id", 
                                a.move_id,
                                a.sm_state,
                                a.picking_id,
                                a.picking_no,
                                a.sj_no,
                                a.contact_code,
                                a.contact,
                                a.sub_contact,
                                a.contact_address_complete,
                                a.do_date,
                                a.do_receive_date,
                                a.so_no,
                                a.pickup_method,
                                a.plant_id,
                                a.company_id,
                                a.company,
                                a.product_code,
                                a.product_name,
                                a.price_unit,
                                a.take_in_plant_disc_nom,
		                        a.discount_fixed_line,
                                a.qty_demand,
                                a.qty_done,
                                a.qty_return,
                                a.qty_net,
                                a.state,
                                a.uom_name,
                                a.location_id,
                                a.invoice_id,
                                a.account_move_id,
                                a.account_move_line_id,
                                a.invoice_no,
                                a.invoice_commercial_no,
                                a.price_before_tax,
                                SUM(a.amount_paid) AS amount_paid,
                                a.payment_date,
                                a.e_tax_invoice_id,
                                a.sales_team_id,
                                a.fleet_vehicle_id,
                                a.fleet_driver_id
                            FROM (
                            SELECT  
                                                        sm.id AS "move_id",
                                                        sm.state AS "sm_state", 
                                                        pick.id AS "picking_id", 
                                                        pick.name AS "picking_no", 
                                                        pick.doc_name as "sj_no",
                                                        partner.code AS "contact_code",
                                                        partner.name AS "contact",
                                                        partner_picking_2.name AS "sub_contact",
                                                        partner_picking_2.contact_address_complete,
                                                        pick.date_done AS "do_date",
                                                        pick.date_received AS "do_receive_date",
                                                        so.name AS "so_no",
                                                        opm.name AS "pickup_method",
                                                        pick.plant_id AS "plant_id",
                                                        company.id AS "company_id",
                                                        company.name AS "company",
                                                        pt.default_code AS "product_code",
                                                        pt.name AS "product_name",		
                                                        sol.price_unit AS "price_unit",
                                                        coalesce(sm.product_uom_qty,0) AS "qty_demand",
                                                        SUM(sl.qty_done) AS "qty_done",
                                                        coalesce(sm_return.product_uom_qty, 0) AS "qty_return",
                                                        ( SUM(coalesce(sl.qty_done,0)) - coalesce(sm_return.product_uom_qty,0) ) AS "qty_net",
                                                        pick.state AS "state",
                                                        uom.name AS "uom_name",
                                                        pick.location_id AS "location_id",
                                                        sol.take_in_plant_disc_nom,
							                            aml.discount_fixed_line,
                        
                                                        pick.invoice_id AS "invoice_id",
                                                        am.id AS "account_move_id",
                                                        am.name AS "invoice_no",
                                                        etax.name AS "invoice_commercial_no",
                                                        aml.id AS "account_move_line_id",
                                                        aml.price_subtotal AS "price_before_tax",
                                                        ap.amount as amount_paid,
                                                        ap.payment_date as payment_date,
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
                                -- 					LEFT JOIN account_move_line aml ON ( ( aml.move_id = am.id ) AND ( CONCAT(pick.name,':',sol.name) = aml.name ) AND aml.exclude_from_invoice_tab = false )
                                                    LEFT JOIN (
                                                        SELECT id, move_id, price_subtotal, exclude_from_invoice_tab, name, product_id, discount_fixed_line
                                                        FROM account_move_line
                                                        WHERE exclude_from_invoice_tab = false
                                                    ) aml ON ( aml.move_id = am.id AND aml.name = sol.name )
                                                    LEFT JOIN account_move_etax_invoice_merge_rel etax_account_move_rel ON am.id = etax_account_move_rel.account_move_id
                                                    LEFT JOIN etax_invoice_merge etax ON etax.id = etax_account_move_rel.etax_invoice_merge_id
                                                    LEFT JOIN (
                                                        SELECT fleet_vehicle_id, fleet_driver_id, doc_name
                                                        FROM stock_picking
                        
                                                    ) pick_interco ON pick_interco.doc_name = pick.no_sj_wim
                                                    LEFT JOIN account_invoice_payment_rel invoice_payment_rel ON invoice_payment_rel.invoice_id = pick.invoice_id
                                                    LEFT JOIN account_payment ap ON ap.id = invoice_payment_rel.payment_id
                                                    LEFT JOIN order_pickup_method opm ON opm.id = so.order_pickup_method_id
                                                WHERE pick_type.code IN ('outgoing') and pick.state != 'cancel'
                                                    AND company.id = 2
                                                    AND pick.picking_type_id IN (
                                                        select id from stock_picking_type where company_id = 2 and code like 'outgoing'
                                                    )
                                                    AND pick.location_dest_id = 5
                                                    -- AND pick.doc_name like 'WIM-SJ/22/01/003588'
                                                    -- AND am.name like 'WIM/PFI/22/01/000974'
                                                    AND sol.name not like %s
                                                    AND pick.doc_name not like 'New'
                                                GROUP BY sm.id, sm.state, pick.id, pick.name, pick.doc_name, partner.name, partner_picking_2.name, pick.date_done, pick.date_received,
                                                        so.name, pick.plant_id, company.id, company.name, pt.name, pick.state, uom.name, pick.location_id, sm_return.product_uom_qty,
                                                        partner.code, pick_interco.fleet_vehicle_id, pick_interco.fleet_driver_id, am.id, etax.name,aml.price_subtotal,
                                                        etax.e_tax_invoice_id, pt.default_code, aml.id, ap.amount, ap.payment_date, sol.price_unit,
                                                        sol.take_in_plant_disc_nom,aml.discount_fixed_line, opm.name, partner_picking_2.contact_address_complete
                                                ORDER BY pick.scheduled_date DESC
                            ) a
                            GROUP BY a.move_id,
                                a.sm_state,
                                a.picking_id,
                                a.picking_no,
                                a.sj_no,
                                a.contact_code,
                                a.contact,
                                a.sub_contact,
                                a.do_date,
                                a.do_receive_date,
                                a.so_no,
                                a.plant_id,
                                a.company_id,
                                a.company,
                                a.product_code,
                                a.product_name,
                                a.qty_demand,
                                a.qty_done,
                                a.qty_return,
                                a.qty_net,
                                a.state,
                                a.uom_name,
                                a.location_id,
                                a.invoice_id,
                                a.account_move_id,
                                a.account_move_line_id,
                                a.invoice_no,
                                a.invoice_commercial_no,
                                a.price_before_tax,
                                a.e_tax_invoice_id,
                                a.sales_team_id,
                                a.fleet_vehicle_id,
                                a.fleet_driver_id,
                                a.payment_date,
                                a.price_unit,
                                a.take_in_plant_disc_nom,
		                        a.discount_fixed_line,
		                        a.pickup_method,
		                        a.contact_address_complete

        """ % (self._table,'\'%Free%\'')
        return request


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
