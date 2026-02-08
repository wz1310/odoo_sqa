from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResGroups(models.Model):
    _inherit = "res.groups"


    @api.model
    def _account_billing_user(self):
        # update account.group_account_invoice set implied to pci_efaktur_13.group_etax_user
        account_invoice = self.env.ref('account.group_account_invoice')
        account_invoice.write({'implied_ids':[(4,self.env.ref('pci_efaktur_13.group_e_tax_user').id)]})