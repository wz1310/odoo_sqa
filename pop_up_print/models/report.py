from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'
    @api.model
    def _get_rendering_context_model(self):
        res = super()._get_rendering_context_model()
        return res

    @api.model
    def _get_report_from_name(self, report_name):
        res = super()._get_report_from_name(report_name)
        
        return res
    def render_template(self, template, values=None):
        res = super().render_template(template, values)
        
        return res

    def render(self, res_ids, data=None):
        res = super(res_ids, data)
        
        return res

    def report_action(self, docids, data=None, config=True):
        res = super().report_action(docids=docids, data=data, config=config)
        
        return res

