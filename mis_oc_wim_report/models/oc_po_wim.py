from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)


class OCWIMReport(models.Model):
    _name = "oc.po.wim.report"
    _description = "OC WIM that only for WIM"
    _auto = False

    plant_id = fields.Many2one('res.company', string='Plant')
    order_pickup_method_id = fields.Many2one('order.pickup.method', string='Pickup Method')
    license_plate = fields.Char(string='No. Pol')
    fleet_model_name = fields.Char(string='Jenis Mobil')
    carrier_type = fields.Char(string='Tipe Ekspedisi')
    priority = fields.Char(string='Prioritas')
    customer_code = fields.Char(string='Kode Cust')
    region_group = fields.Char(string='Region Group')
    region_master = fields.Char(string='Area')
    region = fields.Char(string='Region')
    customer_name = fields.Char(string='Nama Cust')
    sales_name = fields.Char(string='Sales Man')
    downline_name = fields.Char(string='Nama Downline')
    destination = fields.Char(string='Alamat')
    so_no = fields.Char(string='No. SO')
    sj_no = fields.Char(string='No. SJ')
    so_sale_order_mix = fields.Char(string='SO Mix No.')
    create_date = fields.Datetime(string='Tgl. Buat SO')
    commitment_date_mask = fields.Date(string='Tgl DO')
    notes = fields.Char(string='Notes')

    product_1 = fields.Float(string='AMDK 600ml Air Alam')
    product_2 = fields.Float(string='AMDK 220ml BTV')
    product_3 = fields.Float(string='AMDK 600ml BTV')
    product_4 = fields.Float(string='AMDK 200ml BTV')

    product_5 = fields.Float(string='AMDK 220ml SQ')
    product_6 = fields.Float(string='AMDK 330ml SQ')
    product_7 = fields.Float(string='AMDK 600ml SQ')
    product_8 = fields.Float(string='AMDK 1500ml SQ @12')
    product_9 = fields.Float(string='AMDK 220ml SQ Botol')
    product_10 = fields.Float(string='AMDK 1500ml SQ @6')
    product_11 = fields.Float(string='AMDK 120ml SQ')

    product_12 = fields.Float(string='Robust Kopi Susu 160 ml')
    product_13 = fields.Float(string='Vontea 150 ml')
    product_14 = fields.Float(string='Vontea 160 ml x 48 Cup (Printing)')
    product_15 = fields.Float(string='Vontea 160 ml x 24 Cup')
    product_16 = fields.Float(string='Vontea 160 ml x 24 Cup ( Polos )')
    product_17 = fields.Float(string='Le Vontea 220 ml')
    product_18 = fields.Float(string='Vontea 160 ml x 48 Cup')

    product_19 = fields.Float(string='AMDK_Galon_SQ')
    product_20 = fields.Float(string='AMDK_Galon_VIT')

    def get_main_request(self):
        sql = """
                CREATE or REPLACE VIEW %s AS
                    SELECT  ROW_NUMBER() OVER (ORDER BY sj_no) AS "id", plant_id ,
                            license_plate ,
                            fleet_model_name ,
                            carrier_type ,
                            priority ,
                            customer_code ,
                            region_group ,
                            region_master ,
                            region ,
                            customer_name ,
                          sales_name ,
                            downline_name ,
                            destination ,
                            so_no ,
                            sj_no ,
                            so_sale_order_mix ,
                            TO_TIMESTAMP(create_date, 'YYYY-MM-DD HH24:MI:SS' ) at time zone 'UTC' AS "create_date",
                            TO_DATE(commitment_date_mask, 'YYYY-MM-DD' ) AS "commitment_date_mask"  ,
                            notes ,
                            order_pickup_method_id,

                            "AMDK_600ml_Air_Alam" AS product_1,
                            "AMDK_220ml_BTV" AS product_2,
                            "AMDK_600ml_BTV" AS product_3,
                            "AMDK_200ml_BTV" AS product_4,
                            "AMDK_220ml_SQ" AS product_5,
                            "AMDK_330ml_SQ" AS product_6,
                            "AMDK_600ml_SQ" AS product_7,
                            "AMDK_1500ml_SQ_@12" AS product_8,
                            "AMDK_220ml_SQ_Botol" AS product_9,
                            "AMDK_1500ml_SQ_@6" AS product_10,
                            "AMDK_120ml_SQ" AS product_11,

                            "Robust_Kopi_Susu_160_ml" AS product_12,
                            "Vontea_150_ml" AS product_13,
                            "Vontea_160_ml_x_24_Cup" AS product_14,
                            "Vontea_160_ml_x_48_Cup" AS product_15,
                            "Vontea_160_ml_x_48_Cup_(Printing)" AS product_16,
                            "Le_Vontea_220_ml" AS product_17,
                            "Vontea_160_ml_x_24_Cup_(_Polos_)" AS product_18,

                            "AMDK_Galon_SQ" AS product_19,
                            "AMDK_Galon_VIT" AS product_20             
                     from func_oc_po_wim() 
                """ % (self._table)
        return sql

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())

