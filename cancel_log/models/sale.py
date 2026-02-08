"""File Sale Order"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """class inherit sale.order"""
    _inherit = 'sale.order'

    cancel_note = fields.Text()

    def action_cancel(self):
        """extend function cancel for show wizard log reason"""
        if self.env.context.get('show_wizard_reason'):
            view = self.env.ref('cancel_log.sale_log_cancel_form_view')
            wiz = self.env['sale.log.cancel'].create({'sale_ids': [(6, 0, self.ids)]})
            return {
                'name': _('Reason Cancellation?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.log.cancel',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }
        else:
            return super(SaleOrder, self).action_cancel()
