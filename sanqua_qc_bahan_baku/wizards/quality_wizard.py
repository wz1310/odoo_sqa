from odoo import models, api, _
from odoo.exceptions import UserError


class QualityWizard(models.TransientModel):
    _inherit = 'quality.wizard'

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(QualityWizard, self).default_get(fields_list)
    #     if self._context and self._context.get('active_id') and self._context.get('active_model'):
    #         if self._context.get('active_model') == 'stock.move':
    #             move = self.env['stock.move'].browse(self._context['active_id'])
    #             if 'product_qty' in fields_list:
    #                 res['product_qty'] = move.product_uom_qty
    #     return res

    @api.onchange('pass_qty')
    def onchange_qc(self):
        self.fail_qty = self.product_qty - self.pass_qty
        super(QualityWizard, self).onchange_qc()
        if self.quality_line_ids:
            line = self.quality_line_ids[0]
            line.qty_done = self.pass_qty
            line.fail_qty = self.fail_qty
        else:
            self.quality_line_ids.new({
                'quality_id': self.id,
                'qty_done': self.pass_qty,
                'fail_qty': self.fail_qty
            })

    # def do_quality_check(self):
    #     if self._context and self._context.get('active_id') and self._context.get('active_model'):
    #         if self._context.get('active_model') == 'stock.move':
    #             move = self.env['stock.move'].browse(self._context['active_id'])
    #             move.pass_qty = self.pass_qty
    #             move.fail_qty = self.fail_qty
    #             move.fail_reason = self.fail_reason
    #             move.quantity_done = self.pass_qty
    #             stock_total = move.pass_qty + move.fail_qty
    #             if stock_total != move.product_uom_qty:
    #                 raise UserError(_('Sum of Pass and Quarantine Qty '
    #                                   'should be equal to the Product Qty.'))
    #             for line in self.quality_line_ids:
    #                 if line.fail_qty > 0:
    #                     line.move_line_id.write({'fail_qty': line.fail_qty,
    #                                              'is_fail': True})
    #                 else:
    #                     line.move_line_id.write({'fail_qty': 0.0,
    #                                              'is_fail': False})
    #     return True
