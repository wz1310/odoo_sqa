from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class PlantDeliveryOrderReport(models.Model):
    _name = "plant.delivery.order.report"
    _description = "Plant Delivery Order Report"
    _auto = False
    #
    # destination_location = fields.Selection([('wim_warehouse','Gudang WIM'),('wim_customer', 'Konsumen WIM'), ('internal', 'Internal')], string="Tujuan Pengiriman")
    #
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

    qty_demand = fields.Float(string='Demand')
    qty_done = fields.Float(string='Done')
    qty_return = fields.Float(string='Return')
    qty_net = fields.Float(string='Net')
    state = fields.Char(string='State')
    uom_name = fields.Char(string='Unit')
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    # invoice_id = fields.Many2one('account.move', string='No. Invoice')
    invoice_no = fields.Char(string='No. Invoice')
    invoice_commercial_no = fields.Char(string='No. Invoice Commerical')
    price_before_tax = fields.Float(string='DPP')
    e_tax_invoice_id = fields.Many2one('etax.invoice', string="E-Tax")

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    fleet_driver_id = fields.Many2one('res.partner', string='Driver')

    # move_id = fields.Many2one('stock.move', string='Move ID')
    # lot_ids = fields.Many2many('stock.production.lot', compute='_compute_lot_ids', string='Lot/Serial')

    # def _get_lot_ids(self):
    #     query = """
    #         select lot_id from stock_move_line where move_id = %s
    #     """
    #     self.env.cr.execute(query, (str(self.move_id.id),))
    #     res = [x.get('lot_id') for x in self.env.cr.dictfetchall()]
    #     return res
    #
    # @api.depends('move_id')
    # def _compute_lot_ids(self):
    #     for rec in self:
    #         rec.lot_ids = [(6, 0, rec._get_lot_ids())]

    def get_main_request(self):
#         request = """
#             CREATE or REPLACE VIEW %s AS
#                 SELECT  ROW_NUMBER() OVER (ORDER BY sm.id) AS "id",
#                         so.id AS "so_id",
#                         sm.id AS "move_id",
#                         sm.state AS "sm_state",
#                         pick.id AS "picking_id",
# --                         pick.name AS "internal_transfer",
#                         pick.doc_name as "sj_no",
#                         pick.no_sj_wim as "sj_wim_no",
#                         partner.id AS "partner_id",
#                         partner.name AS "contact",
#                         partner_interco.name AS "customer_wim",
#                         pick.date_done AS "do_date",
#                         pick.date_received AS "do_receive_date",
#                         so.name AS "so_no",
#                         po.partner_ref AS "so_wim_no",
#                         po.name AS "po_wim_no",
#                         company.id AS "company_id",
#                         company.name AS "company",
#                         sol.name AS "desc_product",
#                       sm.product_id,
#                         pt.name AS "product_name",
#                         (sm.product_uom_qty) AS "qty_demand",
#                         SUM(sl.qty_done) AS "qty_done",
#                         sm_return.product_uom_qty AS "qty_return",
#                         ( SUM(sl.qty_done) - sm_return.product_uom_qty ) AS "qty_net",
#                         pick.state AS "state",
#                         uom.name AS "uom_name",
#                         pick.location_id AS "location_id",
#                         pick.location_dest_id as "location_dest_id",
#                         po.picking_type_id AS "gudang_wim",
#                       am.id AS "account_move_id",
#                         am.name AS "invoice_no",
#                       etax.name AS "invoice_commercial_no",
#                       aml.price_subtotal AS "price_before_tax",
#                       etax.e_tax_invoice_id AS "e_tax_invoice_id",
#                       ( CASE WHEN pick_interco.fleet_vehicle_id IS NOT NULL THEN pick_interco.fleet_vehicle_id ELSE pick.fleet_vehicle_id END ) AS "fleet_vehicle_id",
#                       ( CASE WHEN pick_interco.fleet_driver_id IS NOT NULL THEN pick_interco.fleet_driver_id ELSE pick.fleet_driver_id END ) AS "fleet_driver_id"
#
#                 FROM stock_picking AS pick
#                     LEFT JOIN stock_picking_type AS pick_type ON pick.picking_type_id = pick_type.id
#                     LEFT JOIN sale_order AS so ON so.id = pick.sale_id
#                     LEFT JOIN stock_move AS sm ON pick.id = sm.picking_id
#                     LEFT JOIN stock_move_line AS sl ON sl.move_id = sm.id
#                     LEFT JOIN res_company as company ON pick.company_id = company.id
#                     LEFT JOIN res_partner as partner ON so.partner_id = partner.id
#                     LEFT JOIN res_users as users ON users.id = so.user_id
#                     LEFT JOIN res_partner as partner_user ON users.partner_id = partner_user.id
#                     LEFT JOIN res_partner as partner_picking ON so.partner_shipping_id = partner_picking.id
#                     LEFT JOIN partner_pricelist as p_list ON p_list.id = so.partner_pricelist_team_id
#                     LEFT JOIN region_group as reg on reg.id = partner_picking.region_group_id
#                     LEFT JOIN customer_group as cg on cg.id = p_list.customer_group
#                     LEFT JOIN fleet_vehicle_model as model on model.id = so.vehicle_model_id
#                     LEFT JOIN fleet_vehicle as vehicle on vehicle.id = pick.fleet_vehicle_id
#                     LEFT JOIN res_partner as partner_driver ON partner_driver.id = pick.fleet_driver_id
#                     LEFT JOIN product_product pp ON sm.product_id = pp.id
#                     LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
#                     LEFT JOIN sale_order_line sol ON sm.sale_line_id = sol.id
#                     LEFT JOIN stock_move sm_return ON ( sm.id = sm_return.origin_returned_move_id AND sm_return.state = 'done' )
#                     LEFT JOIN uom_uom as uom ON sl.product_uom_id = uom.id
#                     LEFT JOIN (
#                         SELECT name,partner_ref, interco_sale_id, picking_type_id
#                         FROM purchase_order
#                     ) po ON po.name = so.client_order_ref
#                     LEFT JOIN sale_order so_interco ON so_interco.id = po.interco_sale_id
#                     LEFT JOIN res_partner partner_interco ON partner_interco.id = so_interco.partner_id
#                     LEFT JOIN account_move am ON am.id = pick.invoice_id
# --                    LEFT JOIN account_move_line aml ON ( ( aml.move_id = am.id ) AND ( CONCAT(pick.name,':',sol.name) = aml.name ) AND aml.exclude_from_invoice_tab = false )
#                   LEFT JOIN (
#                       SELECT move_id, price_subtotal, exclude_from_invoice_tab, name, product_id
#                       FROM account_move_line
#                       WHERE exclude_from_invoice_tab = false
#                   ) aml ON ( aml.move_id = am.id AND aml.name = CONCAT(pick.name,': ',sol.name) )
#                   LEFT JOIN account_move_etax_invoice_merge_rel etax_account_move_rel ON am.id = etax_account_move_rel.account_move_id
#                   LEFT JOIN etax_invoice_merge etax ON etax.id = etax_account_move_rel.etax_invoice_merge_id
#                   LEFT JOIN (
#                       SELECT fleet_vehicle_id, fleet_driver_id, doc_name
#                       FROM stock_picking
#
#                   ) pick_interco ON pick_interco.doc_name = pick.no_sj_wim
#                 WHERE pick_type.code IN ('outgoing') and pick.state != 'cancel'
#                     AND company.id <> 2
#                     AND pick.picking_type_id IN (
#                         select id from stock_picking_type where company_id <> 2 and code like 'outgoing'
#                     )
#                     AND pick.location_dest_id = 5
#                   -- AND pick.name = 'IMP/SJ/21/06/03734'
#                   -- AND pick.no_sj_wim = 'WIM-SJ/22/01/000449'
#               GROUP BY so.id, sm.id, sm.state, pick.id, pick.name, pick.doc_name, pick.no_sj_wim, partner.id, partner.name, partner_interco.name,
#               pick.date_done, pick.date_received, so.name, po.partner_ref, po.name, company.id, company.name, sol.name, sm.product_id,
#               pt.name, pick.state, uom.name, pick.location_id, pick.location_dest_id, po.picking_type_id, am.id, am.name, etax.name,
#               sm_return.product_uom_qty,aml.price_subtotal, etax.e_tax_invoice_id, pick_interco.fleet_vehicle_id, pick_interco.fleet_driver_id
#                 ORDER BY pick.scheduled_date DESC
#         """ % (self._table)

        request = """
        CREATE or REPLACE VIEW %s AS
            SELECT ROW_NUMBER() OVER (ORDER BY a.move_id) AS "id",
                    a.so_id,
                    a.move_id,
                    a.sm_state,
                    a.picking_id,
                    a.sj_no,
                    a.sj_wim_no,
                    a.partner_id,
                    a.contact,
                    a.customer_wim,
                    a.do_date,
                    a.do_receive_date,
                    a.so_no,
                    a.so_wim_no,
                    a.po_wim_no,
                    a.company_id,
                    a.company,
                    a.desc_product,
                    a.product_id,
                    a.product_name,
                    a.qty_demand,
                    a.qty_done,
                    SUM(coalesce( a.qty_return,0)) as "qty_return",
                    (a.qty_done - SUM(coalesce(a.qty_return,0))) as "qty_net",
                    a.state,
                    a.uom_name,
                    a.location_id,
                    a.location_dest_id,
                    a.gudang_wim,
                    a.account_move_id,
                    a.invoice_no,
                    a.invoice_commercial_no,
                    a.price_before_tax,
                    a.e_tax_invoice_id,
                    a.fleet_vehicle_id,
                    a.fleet_driver_id
                    FROM 
                    (
                    SELECT  
                                            so.id AS "so_id",
                                            sm.id AS "move_id",
                                            sm.state AS "sm_state",
                                            pick.id AS "picking_id",
                    --                         pick.name AS "internal_transfer",
                                            pick.doc_name as "sj_no",
                                            pick.no_sj_wim as "sj_wim_no",                        
                                            partner.id AS "partner_id",
                                            partner.name AS "contact",
                                            partner_interco.name AS "customer_wim",
                                            pick.date_done AS "do_date",
                                            pick.date_received AS "do_receive_date",
                                            so.name AS "so_no",
                                            po.partner_ref AS "so_wim_no",
                                            po.name AS "po_wim_no",
                                            company.id AS "company_id",
                                            company.name AS "company",
                                            sol.name AS "desc_product",
                                            sm.product_id,
                                            pt.name AS "product_name",
                                            (sm.product_uom_qty) AS "qty_demand",
                                            SUM(sl.qty_done) AS "qty_done",
                                            coalesce(sm_return.product_uom_qty, 0) AS "qty_return",
                                            pick.state AS "state",
                                            uom.name AS "uom_name",
                                            pick.location_id AS "location_id",
                                            pick.location_dest_id as "location_dest_id",
                                            po.picking_type_id AS "gudang_wim",
                                            am.id AS "account_move_id",
                                            am.name AS "invoice_no",
                                            etax.name AS "invoice_commercial_no",
                                            aml.price_subtotal AS "price_before_tax",
                                            etax.e_tax_invoice_id AS "e_tax_invoice_id",
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
                                            SELECT move_id, price_subtotal, exclude_from_invoice_tab, name, product_id, quantity
                                            FROM account_move_line
                                            WHERE exclude_from_invoice_tab = false
                                        ) aml ON ( aml.move_id = am.id AND aml.name = CONCAT(pick.name,': ',sol.name) AND aml.quantity = sm.product_uom_qty )
                                        LEFT JOIN account_move_etax_invoice_merge_rel etax_account_move_rel ON am.id = etax_account_move_rel.account_move_id
                                        LEFT JOIN etax_invoice_merge etax ON etax.id = etax_account_move_rel.etax_invoice_merge_id
                                        LEFT JOIN (
                                            SELECT fleet_vehicle_id, fleet_driver_id, doc_name
                                            FROM stock_picking
                    
                                        ) pick_interco ON pick_interco.doc_name = pick.no_sj_wim
                                    WHERE pick_type.code IN ('outgoing') and pick.state != 'cancel'
                                        AND company.id <> 2
                                        AND pick.picking_type_id IN (
                                            select id from stock_picking_type where company_id <> 2 and code like 'outgoing'
                                        )
                                        AND pick.location_dest_id = 5
                                        AND sm.origin_returned_move_id IS NULL -- This filter is takeout SJ that comes from retur to retur
                                        -- AND pick.name = 'IMP/SJ/21/06/03734'
                                        -- AND pick.no_sj_wim = 'WIM-SJ/22/01/002941'
                                        -- AND pick.no_sj_wim = 'WIM-SJ/22/01/000290'
                                    GROUP BY so.id, sm.id, sm.state, pick.id, pick.name, pick.doc_name, pick.no_sj_wim, partner.id, partner.name, partner_interco.name,
                                    pick.date_done, pick.date_received, so.name, po.partner_ref, po.name, company.id, company.name, sol.name, sm.product_id,
                                    pt.name, pick.state, uom.name, pick.location_id, pick.location_dest_id, po.picking_type_id, am.id, am.name, etax.name,
                                    sm_return.product_uom_qty,aml.price_subtotal, etax.e_tax_invoice_id, pick_interco.fleet_vehicle_id, pick_interco.fleet_driver_id
                                    ORDER BY pick.scheduled_date DESC
                    ) a
                    GROUP BY
                    a.so_id,
                    a.move_id,
                    a.sm_state,
                    a.picking_id,
                    a.sj_no,
                    a.sj_wim_no,
                    a.partner_id,
                    a.contact,
                    a.customer_wim,
                    a.do_date,
                    a.do_receive_date,
                    a.so_no,
                    a.so_wim_no,
                    a.po_wim_no,
                    a.company_id,
                    a.company,
                    a.desc_product,
                    a.product_id,
                    a.product_name,
                    a.qty_demand,
                    a.qty_done,
                    a.state,
                    a.uom_name,
                    a.location_id,
                    a.location_dest_id,
                    a.gudang_wim,
                    a.account_move_id,
                    a.invoice_no,
                    a.invoice_commercial_no,
                    a.price_before_tax,
                    a.e_tax_invoice_id,
                    a.fleet_vehicle_id,
                    a.fleet_driver_id
        """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())

