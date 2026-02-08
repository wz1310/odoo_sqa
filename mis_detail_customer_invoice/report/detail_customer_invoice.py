from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)


class DetailCustomerInvoice(models.Model):
    _name = "mis.detail.customer.invoice"
    _description = "Detail Customer Invoice"
    _auto = False

    partner_code = fields.Char(string='Customer Code')
    partner_name = fields.Char(string='Customer Name')
    area = fields.Char(string='Area')
    company_name = fields.Char(string='Company')
    company_id = fields.Integer(string='Company Id')
    sales_person = fields.Char(string='Sales Person')
    sales_admin = fields.Char(string='Sales Admin')
    invoice_no = fields.Char(string='Invoice No')
    invoice_date = fields.Date(string='Invoice Date')
    product_code = fields.Char(string='Product Code')
    category_name = fields.Char(string='Category Name')
    product_name = fields.Char(string='Product Name')
    quantity = fields.Float(string='Qty')
    product_uom_name = fields.Char(string='Uom')
    price_unit = fields.Float(string='Price Unit')
    total_discount = fields.Float(string='Discount')
    tax = fields.Char(string='Taxes')
    price_subtotal = fields.Float(string='Subtotal')
    invoice_origin = fields.Char(string='DO No')
    pickup_method = fields.Char(string='Pickup Method')
    cn_no = fields.Char(string='CN No.')
    cn_date = fields.Date(string='CN Date')
    cn_qty = fields.Float(string='CN Qty')


    def get_main_request(self):
        # request = """
        # CREATE or REPLACE VIEW %s AS
        #     SELECT ROW_NUMBER() OVER (ORDER BY aml.id) AS "id", p.code AS "partner_code", p.name AS "partner_name", rm.name AS "area", c.id AS "company_id", c.name AS "company_name",
        #             sales_person.name AS "sales_person", sales_admin.name AS "sales_admin",
        #             am.name "invoice_no", am.date AS "invoice_date",
        #             ptm.default_code AS "product_code", pc.name AS "category_name", ptm.name AS "product_name",
        #             aml.quantity, uom.name AS "product_uom_name", aml.price_unit AS "price_unit", aml.display_discount AS "total_discount",
        #             at.name AS "tax", at.amount AS "amount_tax", aml.price_subtotal,
        #             am.invoice_origin,
        #             opm.name AS "pickup_method"
        #
        #     FROM account_move_line aml INNER JOIN account_move am ON aml.move_id = am.id
        #         LEFT JOIN stock_picking sp ON sp.doc_name = am.invoice_origin
        #             LEFT JOIN sale_order so ON so.id = sp.sale_id
        #                 LEFT JOIN order_pickup_method opm ON opm.id = so.order_pickup_method_id
        #                     LEFT JOIN res_partner p ON am.partner_id = p.id
        #                         LEFT JOIN res_company c ON c.id = am.company_id
        #                             LEFT JOIN product_product pp ON pp.id = aml.product_id
        #                                 LEFT JOIN product_template ptm ON ptm.id = pp.product_tmpl_id
        #                                     LEFT JOIN product_category pc ON pc.id = ptm.categ_id
        #                                         LEFT JOIN uom_uom uom ON uom.id = aml.product_uom_id
        #                                             LEFT JOIN account_move_line_account_tax_rel amltax ON amltax.account_move_line_id = aml.id
        #                                                 LEFT JOIN account_tax at ON at.id = amltax.account_tax_id
        #                                                     LEFT JOIN region_master rm ON rm.id = p.region_master_id
        #                                                         LEFT JOIN partner_pricelist ppl ON ( ppl.partner_id = p.id AND ppl.team_id = am.team_id)
        #                                                             --LEFT JOIN res_users u1 ON u1.id = ppl.user_id
        #                                                                 --LEFT JOIN res_users u2 ON u2.id = ppl.sales_admin_id
        #                                                             LEFT JOIN (
        #                                                                 SELECT ru.id, rp.name
        #                                                                 FROM res_users ru LEFT JOIN res_partner rp ON ru.partner_id = rp.id
        #                                                             ) as sales_person ON sales_person.id = ppl.user_id
        #                                                                 LEFT JOIN (
        #                                                                 SELECT ru.id, rp.name
        #                                                                 FROM res_users ru LEFT JOIN res_partner rp ON ru.partner_id = rp.id
        #                                                             ) as sales_admin ON sales_admin.id = ppl.sales_admin_id
        #     WHERE am.type = 'out_invoice'
        #             AND aml.exclude_from_invoice_tab = false
        #             AND am.state != 'cancel'
        # """ % (self._table)

        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT ROW_NUMBER() OVER (ORDER BY a.am_id) AS "id", a.*
                        , cn.*
                        FROM (
                            SELECT am.id AS "am_id", aml.product_id AS "aml_product_id", aml.name AS "aml_name", p.code AS "partner_code", p.name AS "partner_name", rm.name AS "area", c.id AS "company_id", c.name AS "company_name", 
                                                    sales_person.name AS "sales_person", sales_admin.name AS "sales_admin",
                                                    am.name "invoice_no", am.date AS "invoice_date", 
                                                    ptm.default_code AS "product_code", pc.name AS "category_name", ptm.name AS "product_name",
                                                    aml.quantity, uom.name AS "product_uom_name", aml.price_unit AS "price_unit", aml.display_discount AS "total_discount",
                                                    at.name AS "tax", at.amount AS "amount_tax", aml.price_subtotal
                                                    ,am.invoice_origin,
                                                    opm.name AS "pickup_method"
                        
                                            FROM account_move_line aml INNER JOIN account_move am ON aml.move_id = am.id
                                                LEFT JOIN stock_picking sp ON sp.doc_name = am.invoice_origin
                                                    LEFT JOIN sale_order so ON so.id = sp.sale_id
                                                        LEFT JOIN order_pickup_method opm ON opm.id = so.order_pickup_method_id
                                                            LEFT JOIN res_partner p ON am.partner_id = p.id
                                                                LEFT JOIN res_company c ON c.id = am.company_id
                                                                    LEFT JOIN product_product pp ON pp.id = aml.product_id              
                                                                        LEFT JOIN product_template ptm ON ptm.id = pp.product_tmpl_id
                                                                            LEFT JOIN product_category pc ON pc.id = ptm.categ_id           
                                                                                LEFT JOIN uom_uom uom ON uom.id = aml.product_uom_id
                                                                                    LEFT JOIN account_move_line_account_tax_rel amltax ON amltax.account_move_line_id = aml.id
                                                                                        LEFT JOIN account_tax at ON at.id = amltax.account_tax_id
                                                                                            LEFT JOIN region_master rm ON rm.id = p.region_master_id
                                                                                                LEFT JOIN partner_pricelist ppl ON ( ppl.partner_id = p.id AND ppl.team_id = am.team_id)
                                                                                                    --LEFT JOIN res_users u1 ON u1.id = ppl.user_id
                                                                                                        --LEFT JOIN res_users u2 ON u2.id = ppl.sales_admin_id
                                                                                                    LEFT JOIN (
                                                                                                        SELECT ru.id, rp.name
                                                                                                        FROM res_users ru LEFT JOIN res_partner rp ON ru.partner_id = rp.id
                                                                                                    ) as sales_person ON sales_person.id = ppl.user_id
                                                                                                        LEFT JOIN (
                                                                                                        SELECT ru.id, rp.name
                                                                                                        FROM res_users ru LEFT JOIN res_partner rp ON ru.partner_id = rp.id
                                                                                                    ) as sales_admin ON sales_admin.id = ppl.sales_admin_id
                        
                        
                                WHERE am.type = 'out_invoice'
                                        AND aml.exclude_from_invoice_tab = false
                                        AND am.state != 'cancel'
                        ) a 
                        LEFT JOIN (
                            SELECT am.id AS "cn_id", am.name AS "cn_no", am.invoice_date AS "cn_date", aml.quantity  AS "cn_qty", am.reversed_entry_id, aml.product_id AS "cn_product_id", aml.name AS "cn_name"
                            FROM account_move am LEFT JOIN account_move_line aml ON am.id = aml.move_id
                            WHERE type = 'out_refund'
                                AND aml.exclude_from_invoice_tab = false    
                                -- AND reversed_entry_id = 1108281
                                AND am.state != 'cancel'
                        ) cn ON a.am_id = cn.reversed_entry_id AND a.aml_product_id = cn.cn_product_id AND a.aml_name = cn.cn_name
        """ % (self._table)

        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())