from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class ReportBersih(models.AbstractModel):
    _name = "tes.report.bersih.report_my_custom_report"
    _description = "Report Penjualan Bersih"

    def render_html(self,data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('x.report_my_custom_report')

        data_array = []
        docargs = {
        'hold_data_array':data_array
        }
        return report_obj.render('tes_report_bersih.report_my_custom_report',docargs)