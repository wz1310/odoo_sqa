from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResGroups(models.Model):
    _inherit = "res.groups"


    @api.model
    def _internal_user_sales_product_target(self):
        # update internal user set implied to sales_product_target.group_sales_user_target_user
        internal_user = self.env.ref('base.group_user')
        internal_user.write({'implied_ids':[(4,self.env.ref('sales_product_target.group_sales_user_target_user').id)]})