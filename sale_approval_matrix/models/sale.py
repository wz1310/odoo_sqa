from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ["sale.order",'mail.thread', 'mail.activity.mixin', "approval.matrix.mixin"]


    def test_approve_matrix(self):
        self.approving_matrix()

    def action_confirm(self):
        sup = super().action_confirm()
        return sup