from odoo import api, fields, models, _
from odoo.exceptions import UserError,AccessError
import logging
_logger = logging.getLogger(__name__)

class IrRule(models.Model):
    _inherit = 'ir.rule'

    def _handle_known_errors(self, operation, records, error):
        passed = False
        if records._name == 'res.company':
            if operation=='read':
                for rec in records:
                    if rec.id in self.env.user.company_ids.ids:
                        passed = True

        if not passed:
            return error
        else:
            return None
                        


    # handling with known error
    # def _make_access_error(self, operation, records):
    #     sup = super()._make_access_error(operation, records)

    #     if type(sup) == AccessError:
    #         sup = self._handle_known_errors(operation, records, sup)
        
    #     return sup
        