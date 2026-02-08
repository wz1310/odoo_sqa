from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)

class ReportEnergyConsumption(models.Model):
    _name = "report.energy.consumption"
    _description = "List Report Energy Consumption"
    _auto = False
    _order = "mm.name ASC"

    company_id = fields.Many2one('res.company', String = 'Company')
    machine_name = fields.Char(String = 'Mesin')
    date_deadline = fields.Date(String = 'Tgl. MO')
    consumption = fields.Float( String = 'Consumption' )
    total_produced = fields.Integer( String = 'Total Qty' )

    def get_main_request(self):
        request = """
            CREATE OR REPLACE VIEW %s AS
                SELECT mp.company_id, 
                       mm.name AS "machine_name", 
                       date(mp.date_deadline) AS "date_deadline", 
                       (consumption) AS "consumption", 
                       (mp.qty_produced) AS "total_produced"
                FROM mrp_production mp INNER JOIN mrp_mesin mm ON mp.mesin_id = mm.id
                WHERE mp.state in ('done', 'waiting_qc', 'qc_done')
        """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())