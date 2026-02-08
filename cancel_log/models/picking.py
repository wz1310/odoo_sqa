"""File Sale Order"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    """class inherit StockPicking"""
    _inherit = 'stock.picking'

    cancel_note = fields.Text()

    def action_cancel(self):
        """extend function cancel for show wizard log reason"""
        if self.env.context.get('show_wizard_reason'):
            view = self.env.ref('cancel_log.picking_log_cancel_form_view')
            wiz = self.env['picking.log.cancel'].create({'picking_ids': [(6, 0, self.ids)]})
            return {
                'name': _('Reason Cancellation?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'picking.log.cancel',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }
        else:
            return super(StockPicking, self).action_cancel()
