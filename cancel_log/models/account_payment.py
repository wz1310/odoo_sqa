"""File Account Payment"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    """class inherit account payment"""
    _inherit = 'account.payment'

    def cancel(self):
        """extend function cancel for show wizard log reason"""
        if self.env.context.get('show_wizard_reason'):
            view = self.env.ref('cancel_log.payment_log_cancel_form_view')
            wiz = self.env['payment.log.cancel'].create({'payment_ids': [(6, 0, self.ids)]})
            return {
                'name': _('Reason Cancellation?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.log.cancel',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }
        else:
            return super(AccountPayment, self).cancel()
