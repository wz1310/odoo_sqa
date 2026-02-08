from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class ListDetailPenerimaanReport(models.Model):
    _name = "list.detail.penerimaan"
    _description = "List Detail Penerimaan Report"
    _auto = False
    _order = "id DESC"

    vendor_id = fields.Many2one('res.partner', string='Vendor')
    no_sj_vendor = fields.Char(string='Nomor SJ Vendor')
    receive_date_sj = fields.Datetime(string='Receive Date')
    picking_id = fields.Many2one('stock.picking',string="Transfer Reference")
    partner_id = fields.Many2one('res.partner', string='Destination')
    origin = fields.Char(string='Source Document')
    date_expected = fields.Datetime(string='Expected Date')
    creation_date = fields.Datetime(string='Creation Date')
    location_id = fields.Many2one('stock.location',string='Source Location')
    location_dest_id = fields.Many2one('stock.location',string='Destination Address')
    product_id = fields.Many2one('product.product',string='Product')
    product_uom_qty = fields.Float(string='Initial Demand')
    qty_done = fields.Float(string='Quantity Done')
    difference_qty = fields.Float(string='Difference Quantity')
    product_uom = fields.Many2one('uom.uom',string='Unit of measure')
    state = fields.Char(string='Status')
    company_id = fields.Many2one('res.company', string='Company')
    return_qty = fields.Float(compute='find_return',string='Return Quantity')

    def find_return(self):
        for rec in self:
            if rec.picking_id:
                find = self.env['stock.picking'].search([('id','=',rec.picking_id.id)]).move_ids_without_package.filtered(lambda x:x.product_id.id==rec.product_id.id)
                r_qty = sum([x.return_qty for x in find])
                rec.return_qty = r_qty
            else:
                rec.return_qty = rec.return_qty

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT ROW_NUMBER() OVER (ORDER BY sp.id) AS "id",
                M.vendor_id AS vendor_id,
                M.picking_id AS picking_id,
                sp.date_received AS receive_date_sj,
                sp.picking_type_id,
                spt.code,
                M.partner_id AS partner_id,
                M.no_sj_vendor AS no_sj_vendor,
                M.origin AS origin,
                M.date_expected AS date_expected,
                M.DATE AS creation_date,
                M.location_id AS location_id,
                M.location_dest_id AS location_dest_id,
                M.product_id AS product_id,
                M.product_uom_qty AS product_uom_qty,
                SUM ( ml.qty_done ) AS qty_done,
                M.difference_qty AS difference_qty,
                M.product_uom AS product_uom,
                M.state AS state,
                M.company_id AS company_id
                FROM
                stock_move M
                LEFT JOIN stock_move_line ml ON ml.move_id = M.id
                LEFT JOIN stock_picking sp ON ml.picking_id = sp.id 
                LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                WHERE spt.code = 'incoming' AND spt.code IS NOT NULL
                AND sp.location_id = 4
                GROUP BY
                M.id,
                sp.date_received,
                sp.id,
                spt.code
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())