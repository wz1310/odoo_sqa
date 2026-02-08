from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseRequestToOrder(models.TransientModel):
    _inherit = 'purchase.request.to.order'

    def btn_confirm(self):
        res = super(PurchaseRequestToOrder, self).btn_confirm()
        po_id = res.get('res_id')
        purchase_id = self.env['purchase.order'].browse(po_id)
        bahan_baku = False
        # purchase_id.onchange_order_line()
        return res
    
    #     self.validate_non_asset_type()
    #     for line in self.line_ids:
    #         line.item_id._valid_to_po()
    #         line.validity_qty()
    #     purchase_id = self.create_purchase_order_from_wizard()
    #     form = self.env.ref('purchase.purchase_order_form')
    #     context = dict(self.env.context or {})
    #     # context.update({}) #uncomment if need append context
    #     res = {
    #         'name': "%s - %s" % (_('Purchase Order - '), self.request_id.name),
    #         'view_mode': 'tree,form',
    #         'res_model': 'purchase.order',
    #         'view_id': form.id,
    #         'views':[(form.id,'form')],
    #         'type': 'ir.actions.act_window',
    #         'context': context,
    #         'target': 'current',
    #         'res_id':purchase_id.id,
    #         'res_ids':purchase_id.ids,
    #     }
    #     return res

    # def create_purchase_order_from_wizard(self):
    #     vals_po = self.prepare_value_po()
    #     purchase_id = self.env['purchase.order'].create(vals_po)
    #     if purchase_id:
    #         check_bahan_baku = False
    #         line_vals = self.prepare_purchase_line(purchase_id)
    #     new_po = self.env['purchase.order.line'].create(line_vals)
    #     return purchase_id

    # def prepare_value_po(self):
    #     vals_po =  {
    #                 'partner_id':self.supplier_id.id,
    #                 'user_id': self.request_id.user_id.id,
    #                 'asset' : self.request_id.is_asset,
    #                 }
    #     return vals_po

    # def prepare_purchase_line(self, purchase_id):
    #     vals = []
    #     for line in self.line_ids:
    #         data = {
    #             'product_id': line.item_id.product_id.id,
    #             'name' : line.item_id.product_id.display_name,
    #             'product_qty': line.qty,
    #             'product_uom' : line.uom_id.id,
    #             'price_unit' : line.item_id.product_id.lst_price,
    #             'order_id': purchase_id.id,
    #             'date_planned': fields.Date.from_string(purchase_id.date_order),
    #             'purchase_request_line_id' : line.item_id.id,
    #         }
    #         vals.append(data)
    #     return vals
