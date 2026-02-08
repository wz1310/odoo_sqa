from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class MISReceiveReport(models.Model):
    _name = "mis.receive.report"
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
    bill_no = fields.Char(string='Bill No.')
    etax_no = fields.Char(string='eTax')
    bill_ref_no = fields.Char(string='Ref')
    accounting_date = fields.Char(string='Acc. Date')
    amount_untaxed = fields.Float(string='Untaxed Amount')
    company_id = fields.Many2one('res.company', string='Company Id')
    company_name = fields.Char(string='Company Name')
    date_done = fields.Datetime(string='Tgl. Penerimaan')

    def get_main_request(self):
        # request = """
        # CREATE or REPLACE VIEW %s AS
        # SELECT ROW_NUMBER() OVER (ORDER BY a.po_id) AS "id",
        #         a.vendor_name,
        #         a.vendor_code,
        #         a.po_no,
        #         a.po_date,
        #         a.gr_no,
        #         a.product_category,
        #         a.product_name,
        #         a.product_code,
        #         a.qty_done,
        #         a.qty_return,
        #         a.qty_net,
        #         a.uom,
        #         -- a.bill_no,
        #         -- a.etax_no,
        #         -- a.bill_ref_no,
        #         -- a.accounting_date,
        #         -- a.amount_untaxed,
        #         a.company_id,
        #         CAST(a.date_received AS DATE) as "date_received"
        # FROM (
        #     SELECT  po.id AS "po_id",
        #             rp.name AS "vendor_name",
        #             rp.code AS "vendor_code",
        #             po.name AS "po_no",
        #             po.date_order AS "po_date",
        #             sp.name AS "gr_no",
        #             pc.name AS "product_category",
        #             pt.name AS "product_name",
        #             pt.default_code AS "product_code",
        #             --TRIM(spl.name) AS "lot_no",
        #             coalesce(sml.qty_done,0) AS "qty_done",
        #             coalesce(sm_return.product_uom_qty,0) AS "qty_return",
        #             (coalesce(sml.qty_done,0) - coalesce(sm_return.product_uom_qty,0)) AS "qty_net",
        #             uom.name AS "uom",
        #             -- am.name AS "bill_no",
        #             -- am.e_tax_vendor_bill AS "etax_no",
        #             -- am.ref AS "bill_ref_no",
        #             -- am.date AS "accounting_date",
        #             -- am.amount_untaxed,
        #             po.company_id,
        #             rc.name AS "company_name",
        #             sp.scheduled_date,
        #             TO_CHAR(sp.date_received,'YYYY-MM-DD') AS "date_received"
        #     FROM purchase_order po LEFT JOIN purchase_order_stock_picking_rel posp ON po.id = posp.purchase_order_id
        #         LEFT JOIN purchase_order_line pol ON pol.order_id = po.id
        #             LEFT JOIN stock_picking sp ON sp.id = posp.stock_picking_id
        #                 LEFT JOIN stock_move sm ON sm.picking_id = sp.id
        #                     LEFT JOIN stock_move_line sml ON sml.move_id = sm.id
        #                         LEFT JOIN product_product pp ON pp.id = sml.product_id
        #                             LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
        #                                 --LEFT JOIN stock_production_lot spl ON spl.id = sml.lot_id
        #                                     LEFT JOIN product_category pc ON pc.id = pt.categ_id
        #                                         -- LEFT JOIN account_move am ON am.id = sp.invoice_id
        #                                             -- LEFT JOIN (
        #                                             --    SELECT move_id, price_subtotal, exclude_from_invoice_tab, name, product_id
        #                                             --    FROM account_move_line
        #                                             --    WHERE exclude_from_invoice_tab = false
        #                                             -- ) aml ON ( aml.move_id = am.id AND aml.name = CONCAT(sp.name,': ',pol.name) )
        #                                                 LEFT JOIN uom_uom uom ON uom.id = sml.product_uom_id
        #                                                     LEFT JOIN stock_picking_type AS spt ON sp.picking_type_id = spt.id
        #                                                         LEFT JOIN stock_move sm_return ON ( sm.id = sm_return.origin_returned_move_id AND sm_return.state = 'done' )
        #                                                             LEFT JOIN res_partner rp ON rp.id = po.partner_id
        #                                                                 LEFT JOIN res_company rc ON rc.id = po.company_id
        #     WHERE sp.state = 'done'
        #         AND spt.code IN ('incoming') and sp.state != 'cancel'
        # ) a
        # """ % (self._table)

        # Version Old
        request = """
                CREATE or REPLACE VIEW %s AS
                    SELECT  ROW_NUMBER() OVER (ORDER BY po.id, sp.id) AS "id", po.id AS "po_id",
                            rp.name AS "vendor_name",
                            rp.code AS "vendor_code",
                            po.name AS "po_no",
                            po.date_order AS "po_date",
                            sp.name AS "gr_no",
                            pc.name AS "product_category",
                            pt.name AS "product_name",
                            pt.default_code AS "product_code",
                            --TRIM(spl.name) AS "lot_no",
                            coalesce(sml.qty_done,0) AS "qty_done",
                            coalesce(sm_return.product_uom_qty,0) AS "qty_return",
                            (coalesce(sml.qty_done,0) - coalesce(sm_return.product_uom_qty,0)) AS "qty_net",
                            uom.name AS "uom",
                            am.name AS "bill_no",
                            am.e_tax_vendor_bill AS "etax_no",
                            am.ref AS "bill_ref_no",
                            am.date AS "accounting_date",
                            am.amount_untaxed,
                            po.company_id,
                            rc.name AS "company_name",
                            sp.scheduled_date,
                            sp.date_done
                    FROM purchase_order po LEFT JOIN purchase_order_stock_picking_rel posp ON po.id = posp.purchase_order_id
                        LEFT JOIN purchase_order_line pol ON pol.order_id = po.id
                            LEFT JOIN stock_picking sp ON sp.id = posp.stock_picking_id
                                LEFT JOIN stock_move sm ON sm.picking_id = sp.id
                                    LEFT JOIN stock_move_line sml ON sml.move_id = sm.id
                                        LEFT JOIN product_product pp ON pp.id = sml.product_id
                                            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                                --LEFT JOIN stock_production_lot spl ON spl.id = sml.lot_id
                                                    LEFT JOIN product_category pc ON pc.id = pt.categ_id
                                                        LEFT JOIN account_move am ON am.id = sp.invoice_id
                                                            LEFT JOIN (
                                                                SELECT move_id, price_subtotal, exclude_from_invoice_tab, name, product_id
                                                                FROM account_move_line
                                                                WHERE exclude_from_invoice_tab = false
                                                            ) aml ON ( aml.move_id = am.id AND aml.name = CONCAT(sp.name,': ',pol.name) )
                                                                LEFT JOIN uom_uom uom ON uom.id = sml.product_uom_id
                                                                    LEFT JOIN stock_picking_type AS spt ON sp.picking_type_id = spt.id
                                                                        LEFT JOIN stock_move sm_return ON ( sm.id = sm_return.origin_returned_move_id AND sm_return.state = 'done' )
                                                                            LEFT JOIN res_partner rp ON rp.id = po.partner_id
                                                                                LEFT JOIN res_company rc ON rc.id = po.company_id
                    WHERE sp.state = 'done'
                        AND spt.code IN ('incoming') and sp.state != 'cancel'
                """ % (self._table)
        # return request

        request = """
                    CREATE or REPLACE VIEW %s AS
                        SELECT ROW_NUMBER() OVER (ORDER BY a.po_id, a.picking_id) AS "id",
                            a.vendor_name,
                            a.vendor_code,
                            a.po_no,
                            a.po_date,
                            a.gr_no,
                            a.product_category,
                            a.product_name,
                            a.product_code,
                            a.qty_done,
                            SUM(coalesce( a.qty_return,0)) as "qty_return",
                            (a.qty_done - SUM(coalesce(a.qty_return,0))) as "qty_net",
                            a.uom,
                            a.bill_no,
                            a.etax_no,
                            a.bill_ref_no,
                            a.accounting_date,
                            a.amount_untaxed,
                            a.company_id,
                            a.company_name,
                            a.scheduled_date,
                            a.date_done
                        FROM (
                            SELECT  sm.id AS "move_id",
                                    sp.id AS "picking_id",
                                    po.id AS "po_id",
                                    rp.name AS "vendor_name",
                                    rp.code AS "vendor_code",
                                    po.name AS "po_no",
                                    po.date_order AS "po_date",
                                    sp.name AS "gr_no",
                                    pc.name AS "product_category",
                                    pt.name AS "product_name",
                                    pt.default_code AS "product_code",
                                    --TRIM(spl.name) AS "lot_no",
                                    SUM(sml.qty_done) AS "qty_done",
                                    coalesce(sm_return.product_uom_qty, 0) AS "qty_return",
                                    uom.name AS "uom",
                                    am.name AS "bill_no",
                                    am.e_tax_vendor_bill AS "etax_no",
                                    am.ref AS "bill_ref_no",
                                    am.date AS "accounting_date",
                                    am.amount_untaxed,
                                    po.company_id,
                                    rc.name AS "company_name",
                                    sp.scheduled_date,
                                    sp.date_done
                            FROM purchase_order po LEFT JOIN purchase_order_stock_picking_rel posp ON po.id = posp.purchase_order_id
                                LEFT JOIN purchase_order_line pol ON pol.order_id = po.id
                                    LEFT JOIN stock_picking sp ON sp.id = posp.stock_picking_id
                                        LEFT JOIN stock_move sm ON ( sm.picking_id = sp.id AND pol.product_id = sm.product_id)
                                            LEFT JOIN stock_move_line sml ON sml.move_id = sm.id
                                                LEFT JOIN product_product pp ON pp.id = sml.product_id
                                                    LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                                        --LEFT JOIN stock_production_lot spl ON spl.id = sml.lot_id
                                                            LEFT JOIN product_category pc ON pc.id = pt.categ_id
                                                                LEFT JOIN account_move am ON am.id = sp.invoice_id
                                                                    LEFT JOIN (
                                                                        SELECT move_id, price_subtotal, exclude_from_invoice_tab, name, product_id
                                                                        FROM account_move_line
                                                                        WHERE exclude_from_invoice_tab = false
                                                                    ) aml ON ( aml.move_id = am.id AND aml.name = CONCAT(sp.name,': ',pol.name) )
                                                                        LEFT JOIN uom_uom uom ON uom.id = sml.product_uom_id
                                                                            LEFT JOIN stock_picking_type AS spt ON sp.picking_type_id = spt.id
                                                                                LEFT JOIN stock_move sm_return ON ( sm.id = sm_return.origin_returned_move_id AND sm_return.state = 'done' )
                                                                                    LEFT JOIN res_partner rp ON rp.id = po.partner_id
                                                                                        LEFT JOIN res_company rc ON rc.id = po.company_id
                            WHERE sp.state = 'done'
                            AND spt.code IN ('incoming') and sp.state != 'cancel'
                            AND pp.id IS NOT null
                            GROUP BY sm.id,
                                    po.id,
                                    rp.name,
                                    rp.code,
                                    po.name ,
                                    po.date_order,
                                    sp.name ,
                                    pc.name ,
                                    pt.name ,
                                    pt.default_code ,
                                    coalesce(sm_return.product_uom_qty, 0),
                                    uom.name,
                                    am.name ,
                                    am.e_tax_vendor_bill,
                                    am.ref ,
                                    am.date ,
                                    am.amount_untaxed,
                                    po.company_id,
                                    rc.name ,
                                    sp.scheduled_date,
                                    sp.date_done,
                                    sp.id
                        ) a
                        GROUP BY
                        a.po_id,
                        a.picking_id,
                                a.vendor_name,
                                a.vendor_code,
                                a.po_no,
                                a.po_date,
                                a.gr_no,
                                a.product_category,
                                a.product_name,
                                a.product_code,
                                a.qty_done,
                                a.uom,
                                a.bill_no,
                                a.etax_no,
                                a.bill_ref_no,
                                a.accounting_date,
                                a.amount_untaxed,
                                a.company_id,
                                a.company_name,
                                a.scheduled_date,
                                a.date_done
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = self.get_main_request()
        print('>>> sql: ' + sql)
        self.env.cr.execute(sql)