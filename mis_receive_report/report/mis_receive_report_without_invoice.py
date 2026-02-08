from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class MISReceiveReport(models.Model):
    _name = "mis.receive.report.without.invoice"
    _description = "Receive report for purchasing"
    _auto = False

    id = fields.Char(string='Id')
    vendor_name = fields.Char(string='Vendor Name')
    vendor_code = fields.Char(string='Vendor Code')
    po_no = fields.Char(string='PO No.')
    po_date = fields.Date(string='PO Date')
    gr_no = fields.Char(string='GR No.')
    product_category = fields.Char(string='Category')
    product_code = fields.Char(string='Product Code')
    product_name = fields.Char(string='Product Name')
    qty_done = fields.Float(string='Qty Done')
    qty_return = fields.Float(string='Qty Return')
    qty_net = fields.Float(string='Qty Net')
    uom = fields.Char(string='Uom')
    # bill_no = fields.Char(string='Bill No.')
    # etax_no = fields.Char(string='eTax')
    # bill_ref_no = fields.Char(string='Ref')
    # accounting_date = fields.Char(string='Acc. Date')
    # amount_untaxed = fields.Float(string='Untaxed Amount')
    company_id = fields.Many2one('res.company', string='Company Id')
    company_name = fields.Char(string='Company Name')
    date_received = fields.Datetime(string='Tgl. Penerimaan')
    tot_net = fields.Float(string='Jml Valas')
    price_unit = fields.Float(string='Harga Satuan')
    diskon = fields.Float(string='Diskon')

    def get_main_request(self):
        request = """
        CREATE or REPLACE VIEW %s AS
        SELECT row_number() over () as "id",
                a.tot_net,
                a.price_unit,
                a.diskon,
                a.vendor_name,
                a.vendor_code,
                a.po_no,
                a.po_date,
                a.gr_no,
                CASE WHEN a.product_category = 'bahanbaku' THEN 'Bahan Baku'
                WHEN a.product_category = 'barangsetengahjadi' THEN 'Barang 1/2 Jadi'
                WHEN a.product_category = 'barangjadi' THEN 'Barang Jadi'
                WHEN a.product_category = 'sparepart' THEN 'Sparepart'
                WHEN a.product_category = 'bahankimia' THEN 'Bahan Kimia'
                WHEN a.product_category = 'lainlain' THEN 'Lain - lain'
                END AS product_category,
                -- a.product_category,
                a.product_name,
                a.product_code,
                a.qty_done,
                a.qty_return,
                a.qty_net,
                a.uom,
                a.company_id,
                a.date_received,
                a.company_name
        FROM (
            SELECT  po.id AS "po_id",
                    pol.price_unit AS "price_unit",
                    pol.discount as "diskon",
                    (coalesce(100 - pol.discount ,0)*(coalesce(sml.qty_done,0) - coalesce(sm_return.product_uom_qty,0)) *pol.price_unit)/100 AS "tot_net",
                    rp.name AS "vendor_name",
                    rp.code AS "vendor_code",
                    po.name AS "po_no",
                    po.date_order AS "po_date",
                    sp.name AS "gr_no",
                    -- pc.name AS "product_category",
                    pt.product_classification AS "product_category",
                    pt.name AS "product_name",
                    pt.default_code AS "product_code",
                    --TRIM(spl.name) AS "lot_no",
                    coalesce(sml.qty_done,0) AS "qty_done",		
                    coalesce(sm_return.product_uom_qty,0) AS "qty_return",
                    (coalesce(sml.qty_done,0) - coalesce(sm_return.product_uom_qty,0)) AS "qty_net",
                    uom.name AS "uom",
                    po.company_id,
                    rc.name AS "company_name",
                    sp.scheduled_date,
                    sp.date_received
            FROM purchase_order po LEFT JOIN purchase_order_stock_picking_rel posp ON po.id = posp.purchase_order_id
                    LEFT JOIN stock_picking sp ON sp.id = posp.stock_picking_id
                        LEFT JOIN stock_move sm ON sm.picking_id = sp.id
                        LEFT JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
                            LEFT JOIN stock_move_line sml ON sml.move_id = sm.id
                                LEFT JOIN product_product pp ON pp.id = sml.product_id
                                    LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                        --LEFT JOIN stock_production_lot spl ON spl.id = sml.lot_id
                                            LEFT JOIN product_category pc ON pc.id = pt.categ_id
                                                        LEFT JOIN uom_uom uom ON uom.id = sml.product_uom_id
                                                            LEFT JOIN stock_picking_type AS spt ON sp.picking_type_id = spt.id
                                                                LEFT JOIN stock_move sm_return ON ( sm.id = sm_return.origin_returned_move_id AND sm_return.state = 'done' )
                                                                    LEFT JOIN res_partner rp ON rp.id = po.partner_id
                                                                        LEFT JOIN res_company rc ON rc.id = po.company_id
            WHERE sp.state = 'done'
                AND spt.code IN ('incoming') and sp.state != 'cancel'
        ) a
        """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())