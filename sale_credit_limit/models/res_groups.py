from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResGroups(models.Model):
    _inherit = "res.groups"


    @api.model
    def _init_user_sale_credit_limit(self):
        internal = self.env.ref('base.group_user')
        internal.write({
            'implied_ids':[(4,self.env.ref('sale_credit_limit.group_customer_group_user').id)]
        })