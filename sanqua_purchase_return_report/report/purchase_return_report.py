from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class PurchaseReturnReport(models.Model):
    _name = "report.purchase.return"
    _description = "Purchase Return Report"
    _auto = False
    _order = "id ASC"

    return_number = fields.Text(string='Return No.')
    return_date = fields.Date(string='Return Date')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    product_id = fields.Many2one('product.product', string='Product')
    move_id = fields.Many2one('account.move', string='Product')
    qty_done = fields.Float(string='Return Qty')
    product_uom = fields.Many2one('uom.uom', string='UoM')
    price_unit = fields.Float(string='Price Unit')
    untaxed_amount = fields.Float(string='Untaxed')
    tax_amount = fields.Float(string='Tax')
    total_amount = fields.Float(string='Sub Total')
    amount_change = fields.Float(string='Amount Change')
    tax_change = fields.Float(string='Tax Change')
    status = fields.Text(string='Status')
    company_id = fields.Many2one('res.company', string='Company')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT rec.*, 
                    sum((rec.qty_done * rec.price_unit) * atx.amount/ 100) AS tax_amount,
                    untaxed_amount + sum((rec.qty_done * rec.price_unit) * atx.amount/ 100) AS total_amount
                FROM account_tax_purchase_order_line_rel atpol_rel
                LEFT JOIN account_tax atx ON atpol_rel.account_tax_id = atx.id
                JOIN
                    (
                        SELECT 
                            po_line.id AS id,
                            CONCAT(sp.name,' ',sp.origin) AS return_number,
                            sp.date_done AS return_date, 
                            aml.move_id as move_id,
                            sp.partner_id AS partner_id,
                            po_line.product_id AS product_id,
                            sml.qty_done AS qty_done,
                            po_line.product_uom AS product_uom,
                            po_line.price_unit AS price_unit,
                            (sml.qty_done * po_line.price_unit) AS untaxed_amount,
                            1 AS amount_change,
                            1 AS tax_change,
                            'Diluar Pajak' AS status,
                            po_line.company_id as company_id
                        FROM purchase_order_line po_line
                        JOIN stock_move sm ON sm.purchase_line_id = po_line.id
                        JOIN stock_move_line sml ON sml.move_id = sm.id
                        JOIN stock_picking sp ON sm.picking_id = sp.id
                        JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                        LEFT JOIN account_move_line aml ON aml.purchase_line_id = po_line.id
                        WHERE spt.code = 'outgoing' AND sp.state = 'done'
                    ) AS rec ON atpol_rel.purchase_order_line_id = rec.id
				GROUP BY rec.id,rec.return_number,rec.return_date, rec.return_number, rec.move_id
				, rec.partner_id
				, rec.product_id
				, rec.qty_done
				, rec.product_uom
				, rec.price_unit
				, rec.untaxed_amount
				, rec.amount_change
				, rec.tax_change
				, rec.status
				, rec.company_id
				ORDER BY rec.return_number,rec.company_id ASC;
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())