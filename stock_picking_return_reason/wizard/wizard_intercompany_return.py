from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class WizardIntercompanyReturn(models.TransientModel):
    _name = 'wizard.intercompany.return'
    _description = 'Wizard Intercompany Return'


    picking_id = fields.Many2one('wizard.intercompany.return', string="Picking", required=True)
    # sale_id = fiedls.Many2one('sale.order', related="picking_id.sale_id")
    delivery_picking_ids = fields.Many2many('stock.picking', string="Delivery Order(s)")


    @api.onchange('picking_id','sale_id')
    def _onchange_picking_id(self):
        # companies = self.env['res.company'].search([])
        if self.picking_id.sale_id.id:
            # pickings = self.env['stock.picking'].with_context(allowed_company_ids=companies.ids).sudo().search([('sale_id', '=', self.picking_id.sale_id.id), ('state','=','done'), ('picking_type_id.code','=','outgoing')])
            # only non return
            pickings = self.picking_id.search_related_interco_deliveries()
            self.delivery_picking_ids = [(6, 0, pickings.ids)]