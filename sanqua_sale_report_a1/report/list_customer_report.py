from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class ListCustomerReport(models.Model):
    _name = "report.list.customer"
    _description = "List Customer Report"
    _auto = False
    _order = "id DESC"

    partner_id = fields.Many2one('res.partner', string='Partner')
    tax_holder_name = fields.Char(string='Nama NPWP')
    partner_code = fields.Char(string='Kode Konsumen')
    partner_name = fields.Char(string="Nama Konsumen")
    customer_group_id = fields.Many2one('customer.group',string='Class Outlet')
    team_id = fields.Many2one('crm.team', string='Divisi')
    vat = fields.Char(string='Nomor NPWP')
    streets = fields.Text(string='Alamat')
    phone = fields.Char(string='Telepon')
    user_id = fields.Many2one('res.users', string='Salesman')
    ref = fields.Char(string='Sales ID')
    sales_admin_id = fields.Many2one('res.users', string='Admin')
    credit_limit = fields.Float(string='Limit')
    payment_term_id = fields.Many2one('account.payment.term', string='TOP')
    join_date = fields.Date(string='Tanggal Bergabung')
    nik = fields.Char(string='NIK')
    company_id = fields.Many2one('res.company', string='Company')
    owner_image = fields.Boolean(string='Owner')
    warehouse_image = fields.Boolean(string='Foto Gudang')
    lat_long = fields.Boolean(string='Maps')
    payment_method = fields.Char(string='Metode Pembayaran')
    collection_method =  fields.Char(string='Metode Penagihan')
    region_group_id = fields.Many2one('region.group', string='Region Group')
    region_master_id = fields.Many2one('region.master', string='Wilayah')
    region_id = fields.Many2one('region.region', string='Region')
    ktp_image = fields.Boolean(string='KTP')
    contact_address = fields.Text(string='Contact')

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT
                    CONCAT(lpad(rp.id::TEXT, 5,'0'),rpad(ppr.sales_admin_id::TEXT,5,'0'),rpad(ppr.team_id::TEXT,5,'0'))::BIGINT as id
                    ,rp.id AS partner_id
                    ,rp.code AS partner_code
                    ,rp.name as partner_name
                    ,ppr.customer_group AS customer_group_id
                    ,rp.vat
                    ,rp.contact_address_complete as streets
                    ,CONCAT(rp.phone,'/',rp.mobile) AS phone
                    ,ppr.user_id
                    ,user_partner.ref
                    ,ppr.sales_admin_id
                    ,ppr.credit_limit
                    ,ppr.payment_term_id
                    ,ppr.team_id
                    ,rp.join_date
                    ,ppr.company_id
                    ,rp.national_id as nik
                    ,CASE WHEN
                        rp.partner_latitude ISNULL AND rp.partner_longitude ISNULL
                    THEN FALSE
                    ELSE TRUE
                    END AS lat_long
                    ,CASE WHEN
                        rp.owner_file_name ISNULL
                    THEN FALSE
                    ELSE TRUE
                    END AS owner_image
                    ,CASE WHEN
                        rp.warehouse_file_name ISNULL
                    THEN FALSE
                    ELSE TRUE
                    END AS warehouse_image
                    ,rp.payment_method
                    ,rp.collection_method
                    ,rp.region_group_id
                    ,rp.region_master_id
                    ,rp.region_id
                    ,rp.tax_holder_name
 					,CASE WHEN
 						(
  						SELECT file from res_partner_document rp_doc
  						LEFT JOIN res_partner_document_field rp_doc_field ON rp_doc.field_id = rp_doc_field.id
  						WHERE rp_doc_field.name = 'KTP' AND rp_doc.partner_id = rp.id
  						ORDER BY partner_id
  						) ISNULL
                     THEN FALSE
                     ELSE TRUE
                     END AS ktp_image
					, (SELECT name
 					FROM res_partner WHERE parent_id = rp.id
 					ORDER BY id LIMIT 1) AS contact_address 
                FROM partner_pricelist ppr
                JOIN res_partner AS rp ON ppr.partner_id = rp.id
                JOIN res_users ru ON ru.id = ppr.user_id
                JOIN res_partner user_partner ON user_partner.id = ru.partner_id
                """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
