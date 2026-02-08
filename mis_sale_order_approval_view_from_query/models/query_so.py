from odoo import api, fields, models, tools
import logging
import datetime

_logger = logging.getLogger(__name__)

class QuerySaleOrder(models.Model):
    _name = 'query.view.sale.order'
    _description = "Query SO"
    _auto = False

    id_so = fields.Integer(string='Id So')
    payment_term_id = fields.Many2one('account.payment.term',string='Payment Terms')
    name = fields.Char(string='Name')
    create_date = fields.Char(string='Create Date')
    partner_id = fields.Many2one('res.partner',string='Customer')
    user_id = fields.Many2one('res.users',string='Salesperson')
    division = fields.Many2one('crm.team',string='Division')
    pickup_method = fields.Many2one('order.pickup.method',string='Pickup Method')
    plant = fields.Many2one('res.company',string='Plant')
    total = fields.Float(string='Total')
    delivery_address = fields.Many2one('res.partner',string='Delivery Address')
    status_so = fields.Selection([('0', 'Normal'), ('1', 'Overdue'), ('2', 'Overlimit'), ('3', 'Overdue & Overlimit'), 
                    ('4', 'Blacklist')])
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status',default='no')
    company = fields.Many2one('res.company',string='Company')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status',default='draft')
    priority_type = fields.Selection([('normal','NORMAL'), ('urgent','URGENT'), ('pending','PENDING')], default="normal")
    date_order_mask = fields.Date('Order Date', default=(datetime.datetime.now().date()))
    commitment_date_mask = fields.Date('Delivery Date', default=(datetime.datetime.now().date())+datetime.timedelta(days=1))
    validity_date = fields.Date(string='Expiration')

    def get_main_request(self):
        request = """
        CREATE or REPLACE VIEW %s AS
        SELECT row_number() over () as "id",
        so.id AS "id_so",
        so.payment_term_id AS "payment_term_id",
        so.name AS "name",so.create_date AS "create_date",
        so.partner_id AS "partner_id", so.user_id AS "user_id",
        so.team_id AS "division",so.order_pickup_method_id AS "pickup_method",
        so.plant_id AS "plant",so.amount_total AS "total",
        so.partner_shipping_id AS "delivery_address",so.status_so AS "status_so",
        so.invoice_status AS "invoice_status",
        so.company_id AS "company",
        so.priority_type AS "priority_type",
        so.date_order_mask AS "date_order_mask",
        so.commitment_date_mask AS "commitment_date_mask",
        so.validity_date AS "validity_date",
        so.state AS "state"
        FROM sale_order so
        LEFT JOIN sale_order_line sol on sol.order_id = so.id
        WHERE so."state" = 'sale'
        """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())

    def open_form(self):
        context = dict(self.env.context or {})
        for rec in self:
            context.update({
                'default_id_so': rec.id_so,
                'default_division': rec.division.id,
                'default_name': rec.name,
                'default_partner_id': rec.partner_id.id,
                'default_user_id': rec.user_id.id,
                'default_plant': rec.company.id,
                'default_pickup_method': rec.pickup_method.id,
                'default_payment_term_id': rec.payment_term_id.id,
                'default_priority_type': rec.priority_type,
                'default_date_order_mask': rec.date_order_mask,
                'default_commitment_date_mask': rec.commitment_date_mask,
                'default_validity_date': rec.validity_date,
                })
        return {
        'name': 'Message',
        'type': 'ir.actions.act_window',
        'res_model': 'query.view.sale.order',
        'res_id': self.id_so,
        'view_mode': 'form',
        'context': context,
        'target': 'current'        
        }

# class QuerySaleOrderLine(models.Model):
#     _name = 'query.view.sale.order.line'
#     _description = "Query SO Line"

#     product = fields.Many2one('product.product')
#     # name = fields.text('product.product')
#     # product_uom_qty = fields.Many2one('product.product')
#     qty_delivered = fields.Float()
#     qty_invoiced = fields.Float()
#     product_uom = fields.Many2one('uom.uom')
#     price_unit = fields.Float()