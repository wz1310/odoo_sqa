from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_repr
from odoo.exceptions import ValidationError
from collections import defaultdict
from datetime import date, datetime
import time

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _change_standard_price(self, new_price, counterpart_account_id=False):
        diff = 0
        print(">>> Hello, this override yeah...")
        print('>>> New Price : ' + str(new_price))
        print('>>> counterpart_account_id : ' + str(counterpart_account_id))
        # super(ProductProduct, self)._change_standard_price(new_price, counterpart_account_id)

        # Origin code for _change_standard_price
        """Helper to create the stock valuation layers and the account moves
                after an update of standard price.

                :param new_price: new standard price
                """
        # Handle stock valuation layers.
        svl_vals_list = []
        company_id = self.env.company
        for product in self:
            if product.cost_method not in ('standard', 'average'):
                continue
            quantity_svl = product.sudo().quantity_svl
            # print('>>> Quantity SVL : ' + str(quantity_svl))
            if float_is_zero(quantity_svl, precision_rounding=product.uom_id.rounding):
                continue
            diff = new_price - product.standard_price
            value = company_id.currency_id.round(quantity_svl * diff)
            if company_id.currency_id.is_zero(value):
                continue

            svl_vals = {
                'company_id': company_id.id,
                'product_id': product.id,
                'description': _('Product value manually modified (from %s to %s)') % (
                product.standard_price, new_price),
                'value': value,
                'quantity': 0,
            }
            svl_vals_list.append(svl_vals)
        stock_valuation_layers = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

        # Handle account moves.
        product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in self}
        am_vals_list = []
        for stock_valuation_layer in stock_valuation_layers:
            product = stock_valuation_layer.product_id
            value = stock_valuation_layer.value

            if product.type != 'product' or product.valuation != 'real_time':
                continue

            # Sanity check.
            if counterpart_account_id is False:
                raise UserError(_('You must set a counterpart account.'))
            if not product_accounts[product.id].get('stock_valuation'):
                raise UserError(
                    _('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))

            if value < 0:
                debit_account_id = counterpart_account_id
                credit_account_id = product_accounts[product.id]['stock_valuation'].id
            else:
                debit_account_id = product_accounts[product.id]['stock_valuation'].id
                credit_account_id = counterpart_account_id

            move_vals = {
                'journal_id': product_accounts[product.id]['stock_journal'].id,
                'company_id': company_id.id,
                'ref': product.default_code,
                'stock_valuation_layer_ids': [(6, None, [stock_valuation_layer.id])],
                'line_ids': [(0, 0, {
                    'name': _('%s changed cost from %s to %s - %s') % (
                    self.env.user.name, product.standard_price, new_price, product.display_name),
                    'account_id': debit_account_id,
                    'debit': abs(value),
                    'credit': 0,
                    'product_id': product.id,
                }), (0, 0, {
                    'name': _('%s changed cost from %s to %s - %s') % (
                    self.env.user.name, product.standard_price, new_price, product.display_name),
                    'account_id': credit_account_id,
                    'debit': 0,
                    'credit': abs(value),
                    'product_id': product.id,
                })],
            }
            am_vals_list.append(move_vals)
        account_moves = self.env['account.move'].create(am_vals_list)
        if account_moves:
            account_moves.post()

        print('>>> Account Move Id : ' + str(account_moves.id))
        if diff < 0 :
            self.env['account.move.line'].search([('move_id','=',account_moves.id)]).write({'quantity':-1})
        else:
            self.env['account.move.line'].search([('move_id', '=', account_moves.id)]).write({'quantity': 1})

        # Actually update the standard price.
        self.with_context(force_company=company_id.id).sudo().write({'standard_price': new_price})

        # Force create
        xStockInventoryVal = {
            'name': 'Inventory',
            'date': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'state': 'done',
            'company_id': company_id.id,
            'prefill_counted_quantity': 'counted',
            'create_date': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'write_date': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'accounting_date': time.strftime('%Y-%m-%d', time.gmtime())
        }
        xCreatedStockInventory = self.env['stock.inventory'].create(xStockInventoryVal)
        if xCreatedStockInventory:
            # Force creaate stock_move
            print('>>> Time : ' + str(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())))
            print('>>> Product Id : ' + str(product.id))

            xProductDetail = self.env['product.product'].search([('id','=', product.id)])
            print('>>> Product Detail : ' + str(xProductDetail  ))

            xUomId = 0
            if( xProductDetail ):
                xUomId = xProductDetail.product_tmpl_id.uom_id
            xLocation = self.env['stock.location'].search(
                ['&','|',
                    ('complete_name','ilike','%adjustment%'),
                    ('complete_name','ilike','%adjust opname%'),
                  '&',
                    ('company_id','=',company_id.id),('usage','=','inventory')
                ]
            )

            print('>>> Company Id : ' + str(company_id.id))
            print('>>> Location Id : ' + str(xLocation.id))
            if company_id.id != 2:
                xLocationDest = self.env['stock.location'].search([('company_id','=',company_id.id),('complete_name','ilike','%stock%')])
                print('>>> 1 Location Dest : ' + str(xLocationDest))
                if len(xLocationDest)>1:
                    xDest = xLocationDest[0].id
                else:
                    xDest = xLocationDest.id
            else:
                xDest = 1135


            xStockMoveVal = {
                'name': 'INV:Inventory',
                'sequence': 10,
                'priority': '1',
                'create_date': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'date': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'company_id': company_id.id,
                'date_expected': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product.id,
                # 'product_qty': 1,
                'product_uom_qty': 1,
                'product_uom': xUomId.id,
                'location_id': xLocation.id,
                'location_dest_id': xDest,
                'state': 'done',
                'procure_method': 'make_to_stock',
                'scrapped': False,
                'propagate_cancel': True,
                'inventory_id': xCreatedStockInventory.id,
                'additional': False,
                'reference': 'INV:Inventory',
                'is_done': True,
                'unit_factor': True,
                'to_backorder': True,
                'available_to_invoice': True,
                'difference_qty': 0
            }
            print('>>> Param Stock Move: ' + str(xStockMoveVal))
            xCreatedStockMove = self.env['stock.move'].create(xStockMoveVal)

            # Update account_move with stock_move_id
            self.env['account.move'].search([('id','=',account_moves.id)]).write({'stock_move_id': xCreatedStockMove.id})