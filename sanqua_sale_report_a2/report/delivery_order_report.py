from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class DeliveryOrderReport(models.Model):
    _name = "report.delivery.order"
    _description = "Delivery Order Report"
    _auto = False
    _order = "picking_id DESC"

    display_name = fields.Text(string='Display Name',store=True)
    picking_id = fields.Many2one('stock.picking', string='Delivery Order')
    plant_id = fields.Many2one('res.company', string='Plant')
    # date_done = fields.Datetime(string='DO Date')
    date = fields.Date(string='Date')
    state = fields.Char(string='State')

    sale_id = fields.Many2one('sale.order', string='No. Sale Order')
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_code = fields.Char(string='Outlet Code')
    partner_name = fields.Char(string='Outlet Name')
    user_id = fields.Many2one('res.users', string='Sales')
    sales_ref = fields.Char(string='Sales Id')
    region_group_id = fields.Many2one('region.group',string='Area')
    customer_group_id = fields.Many2one('customer.group',string='Class Outlet')
    order_pickup_method_id = fields.Many2one('order.pickup.method', string='AS / K')
    vehicle_model_id = fields.Many2one('fleet.vehicle.model', string='Car Type')
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='No. Plat')
    driver_id = fields.Many2one('res.partner', string='Driver')
    partner_tujuan_id = fields.Many2one('res.partner', string='Destination')
    destination_address = fields.Char(compute='_compute_destination', string='Destination')
    move_id = fields.Many2one('stock.move', string='Move ID')
    product_id = fields.Many2one('product.product', string='Product ID')
    product_code = fields.Char('Kode Product')
    product_name = fields.Text('Nama Product',compute='_compute_product_name')
    quantity_done = fields.Float(string='Quantity')
    company_id = fields.Many2one('res.company', string='Company')
    lot_ids = fields.Many2many('stock.production.lot',compute='_compute_lot_ids',string='Lot/Serial')
    warehouse_plant_id = fields.Many2one('stock.warehouse', string='Source Location')

    def _get_lot_ids(self):
        query = """ 
            select lot_id from stock_move_line where move_id = %s
        """
        self.env.cr.execute(query, (str(self.move_id.id),))
        res = [x.get('lot_id') for x in self.env.cr.dictfetchall()]
        return res
    
    @api.depends('move_id')
    def _compute_lot_ids(self):
        for rec in self:
            rec.lot_ids = [(6,0,rec._get_lot_ids())]


    def _compute_product_name(self):
        for rec in self:
            desc = rec.move_id.desc_product
            if desc and desc[:14] == 'Free Product -':
                rec.product_name = rec.move_id.desc_product
            else:
                rec.product_name = rec.product_id.name


    def _compute_destination(self):
        for rec in self:
            res = False
            if rec.partner_tujuan_id:
                res = ("%s - %s")%(rec.partner_tujuan_id.display_name, rec.partner_tujuan_id.contact_address_complete)
            rec.destination_address = res

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT main.*, CONCAT( main.so_name,
                            ' | ', main.date::timestamp::date,
                            ' | ', main.pick_name,
                            ' | ', main.partner_code,
                            ' | ', main.partner_name,
                            ' | ', main.sales_ref,
                            ' | ', main.region_name,
                            ' | ', main.user_name,
                            ' | ', main.customer_group_name,
                            ' | ', main.vehicle_model_name,
                            ' | ', main.fleet_vehicle_name,
                            ' | ', main.driver_name,
                            ' | ', main.warehouse_plant_id,
                            ' | ', main.id) as display_name
                FROM (
                    SELECT 
                                    sm.id AS id,
                                    so.name as so_name,
                                    pick.name as pick_name,
                                    pick.sale_id as sale_id,
                                    pick.date_done as date,
                                    pick.id AS picking_id,
                                    pick.plant_id AS plant_id,
                                    pick.state AS state,
                                    partner.code as partner_code,
                                    so.partner_id as partner_id,
                                    partner.name as partner_name,
                                    partner_user.ref as sales_ref,
                                    partner_picking.region_group_id as region_group_id,
                                    reg.name as region_name,
                                    so.user_id as user_id,
                                    partner_user.name as user_name,
                                    p_list.customer_group as customer_group_id,
                                    cg.name as customer_group_name,
                                    so.order_pickup_method_id as order_pickup_method_id,
                                    so.vehicle_model_id as vehicle_model_id,
                                    model.name as vehicle_model_name,
                                    pick.fleet_vehicle_id as fleet_vehicle_id,
                                    vehicle.name as fleet_vehicle_name,
                                    pick.fleet_driver_id as driver_id,
                                    partner_driver.name as driver_name,
                                    pick.partner_id as partner_tujuan_id,
                                    sm.product_id AS product_id,
                                    pp.default_code as product_code,
                                    sm.name as product_name,
                                    sm.id as move_id,
                                    sum(sl.qty_done) as quantity_done,
                                    company.id as company_id,
                                    pick.warehouse_plant_id as warehouse_plant_id
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
                                WHERE pick_type.code = 'outgoing' and pick.state != 'cancel'
                                GROUP BY sm.id, pick.id,pick.plant_id,pick.name,sm.product_id,pp.default_code,pt.name,company.id,so.name,
                                so.partner_id,so.partner_shipping_id,partner.code,partner_user.ref,so.user_id,partner.name,
                                partner_picking.region_group_id,p_list.customer_group,
                                so.order_pickup_method_id,so.vehicle_model_id,reg.name,partner_user.name,
                                cg.name,model.name,vehicle.name,partner_driver.name
                                ORDER BY pick.id DESC
                ) AS main
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())