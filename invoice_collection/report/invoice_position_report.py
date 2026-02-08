from odoo import api, fields, models, tools


class InvoicePositionReport(models.Model):
    _name = "report.invoice.position"
    _description = "Invoice Position Report"
    _auto = False

    invoice_id = fields.Many2one('account.move', string='Invoice')
    partner_id = fields.Many2one('res.partner', string='Customer')
    activity_id = fields.Many2one('collection.activity',string='Collection')
    collector_id = fields.Many2one('res.partner', string='Collector')
    line_id = fields.Many2one('collection.activity.line', string='Collection Line')
    amount_total = fields.Monetary(related='line_id.amount_total', string='Total Amount')
    amount_residual = fields.Monetary(related='line_id.amount_residual', string='Residual Amount')
    currency_id = fields.Many2one(related='line_id.currency_id', string='Currency')
    payment_status = fields.Selection(related='line_id.payment_status', string='Last Payment Status')
    doc_status = fields.Selection(related='line_id.doc_status', string='Last Doc Status')
    state = fields.Selection(related='line_id.activity_id.state',string='Last Collection Status')
    activity_date = fields.Date(related='line_id.activity_id.activity_date',string='Last Collection Date')
    company_id = fields.Many2one('res.company', string='Company')

    collection_activity_line_ids = fields.Many2many('collection.activity.line', 'invoice_report_id_line_id_rel', 'invoice_report_id', 'line_id', string='Lines',compute='_compute_collection_activity_line_ids')


    def _compute_collection_activity_line_ids(self):
        for rec in self:
            rec.collection_activity_line_ids = self.env['collection.activity.line'].search([('invoice_id','=',rec.invoice_id.id)]) if rec.invoice_id else False
            

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT 
                    inv.id as id
                ,inv.id as invoice_id
                ,inv.partner_id as partner_id
				,cal_s.activity_id as activity_id
                , cal_s.line_id as line_id
                , cal_s.collector_id as collector_id
                ,inv.company_id as company_id
                FROM account_move as inv
                -- LEFT JOIN collection_activity_line cal ON cal.invoice_id = inv.id
                LEFT JOIN(
                    SELECT DISTINCT ON (cal.invoice_id)
                    cal.id as line_id
					,ca.id as activity_id
					,ca.collector_id
                    ,cal.invoice_id
                FROM collection_activity_line cal
                JOIN collection_activity ca on ca.id = cal.activity_id
                ORDER BY cal.invoice_id,ca.activity_date DESC
                ) cal_s on cal_s.invoice_id = inv.id
                """ % (self._table)
        
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())