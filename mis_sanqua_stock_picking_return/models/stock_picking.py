from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _delivery_order_can_return(self):
        self.ensure_one()

        # print(">>> Context : " + str(self._context))
        ctx_params = self._context.get('params')
        print(">>> Picking ID : " + str(ctx_params))
        if ctx_params:
            if ctx_params.get('id'):
                print(">>> Picking ID : " + str(ctx_params.get('id')))
                xPickingDetail = self.env['stock.picking'].search(
                    [('id', '=', ctx_params.get('id'))], limit=1)
                if xPickingDetail:
                    print(">>> Picking Detail : " +
                          str(xPickingDetail.invoice_id.id) or '')
                    print(">>> Picking Detail : " +
                          xPickingDetail.invoice_id.name or '')
                    super(StockPicking, self)._delivery_order_can_return()
                    raise Warning(_("This GR is already billed with Bill No. %s" % (
                        xPickingDetail.invoice_id.name)))
                else:
                    super(StockPicking, self)._delivery_order_can_return()
                    if not self._context.get('force_sent') and self._context.get('check_sent') and self.picking_type_code == 'outgoing' and self.sent == False:
                        raise UserError(
                            _('Only can return received Delivery Order. Ref: %s') % (self.name,))

        # If GR :
        # if not self._context.get('force_sent') and self._context.get('check_sent') and self.picking_type_code == 'outgoing' and self.sent == False:
        #     raise UserError(_('Only can return received Delivery Order. Ref: %s') % (self.name,))
