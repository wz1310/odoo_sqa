from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)

class MISReportMO(models.Model):
    _name = "mis.report.mo"
    _description = "MIS Report MO"
    _auto = False

    name = fields.Char(string='Reference')
    code_production = fields.Char(string='Code Production')
    date_planned_start = fields.Char(string='Planned Date')
    product_id = fields.Many2one('product.product',string='Product')
    product_uom_id = fields.Many2one('uom.uom',string='Unit of Measure')
    bom_id = fields.Many2one('mrp.bom',string='Bill of Materials')
    origin = fields.Char(string='Source')
    product_qty = fields.Float(string='Quantity')
    produktivitas_mesin = fields.Float(string='Produktivitas mesin')
    consumption = fields.Float(string='Consumption')
    reject_produksi_persen = fields.Float(string='Reject produksi')
    status = fields.Char(string='State')
    date_done = fields.Datetime(string='QC Date')
    it_qty = fields.Float(string='IT Quantity')
    company_id = fields.Many2one('res.company',string='Company')


    def get_main_request(self):
            request = """
                CREATE or REPLACE VIEW %s AS
                    SELECT DISTINCT ON (mp.name) ROW_NUMBER() OVER (ORDER BY mp.name ASC) AS "id",
                            mp.name AS "name",
                            mp.code_production AS "code_production",
                            mp.date_planned_start AS "date_planned_start",
                            mp.product_id AS "product_id",
                            mp.product_uom_id AS "product_uom_id",
                            mp.bom_id AS "bom_id",
                            mp.origin AS "origin",
                            mp.product_qty AS "product_qty",
                            mp.produktivitas_mesin AS "produktivitas_mesin",
                            mp.consumption AS "consumption",
                            mp.reject_produksi_persen AS "reject_produksi_persen",
                            mp.state AS "state",
                            sp.date_done AS "date_done",
                            mp.company_id AS "company_id",
                            (CASE
                            WHEN mp.state = 'draft' THEN 'Draft'
                            WHEN mp.state = 'confirmed' THEN 'Confirmed'
                            WHEN mp.state = 'planned' THEN 'Planned'
                            WHEN mp.state = 'progress' THEN 'In Progress'
                            WHEN mp.state = 'to_close' THEN 'Finished'
                            WHEN mp.state = 'done' THEN 'Done'
                            WHEN mp.state = 'cancel' THEN 'Cancelled'
                            WHEN mp.state = 'waiting_qc' THEN 'Waiting QC'
                            WHEN mp.state = 'qc_done' THEN 'QC Done' End) AS status,
                            (CASE WHEN sp.id is not null THEN
                            (SELECT sum(product_qty) FROM stock_move WHERE picking_id = sp.id)
                            End) AS it_qty
                            FROM
                            mrp_production mp
                            LEFT JOIN stock_picking sp on sp.group_id = mp.procurement_group_id
                            AND sp.group_id IS NOT NULL
                            AND sp.location_dest_id = mp.finished_location_qc_id
                            AND sp.state = 'done'
            """ % (self._table)
            return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())