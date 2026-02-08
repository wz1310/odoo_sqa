# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    interco_sale_ids = fields.One2many(
        'sale.order', 'interco_purchase_id', string="Interco Sales")
    interco_sale_id = fields.Many2one(
        'sale.order', string="Origin SO", compute="_compute_interco_sale_id", store=True)
    interco_sale_agreement_id = fields.Many2one(
        'sale.agreement', related="interco_sale_id.sale_agreement_id", string="SA", readonly=True)
    interco_ref_picking_ids = fields.Many2many(
        'stock.picking', compute='_compute_interco_ref_picking_ids', string='Interco Ref Picking', search="_search_interco_ref_picking_ids")
    interco_picking_id = fields.Many2one('stock.picking', string="Origin DO")
    validity_date = fields.Date(
        string='Expiration Original SO', related="interco_sale_id.validity_date")
    validity_so_date = fields.Date(string='Expiration SO Interco')

    @api.depends('interco_sale_id')
    def _compute_interco_ref_picking_ids(self):
        for rec in self:
            rec.interco_ref_picking_ids = rec.interco_sale_id.picking_ids.filtered(
                lambda r: r.picking_type_id.code == 'outgoing' and r.state == 'done' and r.is_return_picking == False).ids if rec.interco_sale_id else False

    def _search_interco_ref_picking_ids(self, operator, value):
        so_domain = self.env['sale.order'].search_interco_ref_picking_ids(
            operator, value)
        so = self.env['sale.order'].search(so_domain)
        return [('interco_sale_id', 'in', so.ids)]

    @api.depends('interco_sale_ids')
    def _compute_interco_sale_id(self):
        for rec in self:
            try:
                rec.interco_sale_id = rec.interco_sale_ids[0].id
            except Exception as e:
                pass

    def _get_default_sales_line_account(self, company):
        print("JALANKKKKAH ACCOUNT NYA")
        # self.env['account.account'].sudo().search([('company_id','=',company.id, '')])
        try:
            generic = self.env.ref('l10n_generic_coa.6_income')
            if len(generic):
                generic_in_company = self.env['account.account'].search(
                    [('code', '=', generic.code), ('company_id', '=', company.id)])
                return generic_in_company.id
        except Exception as e:
            return False

    def _prepare_sale_invoice_line(self, account_move, product, qty, tax_ids, price_unit, company):
        new_data = {
            'move_id': account_move.id,
            'product_id': product.id,
            'name': product.display_name,
            'price_unit': price_unit,
            'quantity': qty,
            'tax_ids': tax_ids,

        }

        new_obj = self.env['account.move.line'].new(new_data)

        for field_name, methods in new_obj._onchange_methods.items():
            new_obj._onchange_eval(field_name, '1', {})
        new_obj_data = new_obj._convert_to_write(
            {name: new_obj[name] for name in new_obj._cache})
        account_id = self._get_default_sales_line_account(company)
        new_obj_data.update({'account_id': account_id})

        return new_obj_data

    def _find_created_interco_sale_order(self):
        self.ensure_one()
        Sale = self.env['sale.order']
        order = Sale.with_user(self.company_id.intercompany_user_id.id).search(
            [('auto_purchase_order_id', '=', self.id)])
        return order

    def _create_auto_invoice(self):
        self.ensure_one()
        self = self.with_user(1)
        # find sale_order wich interco_purchase_id = self.auto_purchase_order_id.id
        order = self._find_created_interco_sale_order()
        if not len(order):
            raise ValidationError(
                _("No Sale Found on finding Origin Sale for Creating Auto Invoice!\nPlease Contact System Administrator!"))

        assert len(order) == 1, "Found %s Sale when Running Auto Invoice!" % (
            len(order))

        invoices = order.with_context(dict(
            default_company_id=order.company_id.id, allowed_company_ids=order.company_id.ids))._create_invoices()

        lines = invoices.mapped('line_ids')

        return invoices

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):

        res = super()._prepare_sale_order_data(
            name, partner, company, direct_delivery_address)
        intercompany_pricelist = self.env['inter.company.pricelist'].get_intercompany_pricelist(
            company=company, partner=self.company_id.partner_id)
        if len(intercompany_pricelist):
            res.update(
                {'pricelist_id': intercompany_pricelist.pricelist_id.id})
        return res

    """Override origin of inter_company_create_sale_order on intercompany_rules module
	
	Override origin of inter_company_create_sale_order on intercompany_rules module
	When origin rules finished, will create sale order on target company
	Validate its Picking then validate receiving for self purchase order
	"""

    def inter_company_create_sale_order(self, company):
        _logger.info('>>> START : sanqua_sale_flow/models/purchase_order.py def inter_company_create_sale_order(self, company):')
        _logger.info('-------------------------------------------------------------------------------------------------')
        self.ensure_one()

        def validating_pickings(pickings):

            _logger.info('>>> pickings : ' + str(pickings))

            for picking in pickings:

                _logger.info('>>> picking : ' + str(picking))

                qtys = {}
                products = picking.move_lines.mapped('product_id').with_user(1).with_context(force_company=self.sudo(
                ).company_id.id, location=picking.location_id.id, allowed_company_ids=self.sudo().company_id.ids, test="111")

                # for p in products:
                # 	qtys.update({p.id:p.free_qty})
                # 	# pp = self.env['product.product'].with_context(force_company=5,location=52,allowed_company_ids=[5]).browse(p.id) #tmp
                # 	# pp = self.env['product.product'].with_context(force_company=6,location=62,allowed_company_ids=[6]).browse(p.id) # imp
                # 	# pp = self.env['product.product'].with_context(force_company=2,location=22,allowed_company_ids=[2]).browse(p.id) # wim
                # 	pp = self.env['product.product'].with_context(force_company=self.sudo().company_id.id,location=picking.location_dest_id.id,allowed_company_ids=self.company_id.ids).browse(p.id) # wim

                po = picking.purchase_id
                sale = po.interco_sale_id

                _logger.info('>>> sale : ' + str(sale))

                # unlink if exist, when receive picking, odoo  will set move_line_ids with lot=0 and qty done = 0
                # so delete it

                picking.move_line_ids.unlink()
                # to fill it with same on WIM interco plant
                processed_moves = {}
                skipped_moves = self.env['stock.move']

                _logger.info('>>> picking.move_lines : ' + str(picking.move_lines))

                _logger.info('>>> sale.picking_ids.mapped(lambda r: r.move_lines) : ' + str(sale.picking_ids.mapped(lambda r: r.move_lines)))
                _logger.info('>>> sale.picking_ids : ' + str(sale.picking_ids))

                # Loop based on WIM GR
                for move in picking.move_lines:
                    # why filter ?r.product_uom_qty>=move.product_uom_qty
                    # cause maybe the original demand move bigger than qty should be send
                    # but have effect when there is same product more than 1 addition interco_move_line_qty_done = product_uom_qty

                    _logger.info('-------------------------------------------------')
                    _logger.info('>>> move.product_id.id : ' + str(move.product_id.id))
                    _logger.info('>>> move.product_uom_qty : ' + str(move.product_uom_qty))
                    matched_moves = sale.picking_ids.mapped(lambda r: r.move_lines).filtered(lambda r:
                                                                                             r.product_id.id == move.product_id.id and
                                                                                             r.id not in skipped_moves.ids and
                                                                                             r.product_uom_qty >= move.product_uom_qty and
                                                                                             r.interco_move_line_qty_done == move.product_uom_qty and
                                                                                             r.state not in ['done', 'cancel'])

                    _logger.info('>>> matched_moves : ' + str(matched_moves))
                    _logger.info('>>> len(matched_moves) : ' + str(len(matched_moves)))

                    if len(matched_moves) > 1:
                        gap = sorted(matched_moves.mapped(
                            lambda r: r.product_uom_qty - move.product_uom_qty))
                        _logger.info('>>> gap : ' + str(gap))
                        _logger.info('>>> gap[0] : ' + str(gap[0]))
                        matched_moves = matched_moves.filtered(lambda r: (
                            r.product_uom_qty - move.product_uom_qty) == gap[0])
                        _logger.info('>>> matched_moves : ' + str(matched_moves))

                    for source_sale_move in matched_moves:
                        # origin_interco_move_line_ids = sale.picking_ids.mapped('interco_move_line_ids').filtered(lambda r:r.product_id.id==move.product_id.id)
                        origin_interco_move_line_ids = source_sale_move.interco_move_line_ids
                        _logger.info('>>> origin_interco_move_line_ids : ' + str(origin_interco_move_line_ids))

                        for selected in origin_interco_move_line_ids:
                            company_lot = self.env['stock.production.lot'].fetch_company_lot(
                                selected.lot_id, self.company_id)

                            _logger.info('>>> company lot : ' + str(company_lot))
                            _logger.info('>>> selected.lot_id : ' + str(selected.lot_id))
                            _logger.info('>>> self.company_id : ' + str(self.company_id))

                            _logger.info('>>> Start: Create Move Line....')
                            _logger.info('move_id : ' + str(move.id))
                            _logger.info('location_id: ' +
                                  str(selected.picking_id.location_id.id))
                            _logger.info('location_dest_id: ' +
                                  str(selected.picking_id.location_dest_id.id))

                            _logger.info('new location_id: ' +
                                  str(move.location_id.id))
                            _logger.info('new location_dest_id: ' +
                                  str(move.location_dest_id.id))

                            _logger.info('>>> START create stock.move.line')
                            _logger.info('--------------------------------')
                            _logger.info('>>> product_id: ' + str(selected.product_id.id))
                            _logger.info('>>> product_uom_id: ' + str(selected.product_id.uom_id.id))
                            _logger.info('>>> picking_id: ' + str(picking.id))
                            _logger.info('>>> move_id: ' + str(move.id))
                            _logger.info('>>> lot_id: ' + str(company_lot.id))
                            _logger.info('>>> qty_done: ' + str(selected.qty))
                            _logger.info('>>> location_id: ' + str(move.location_id.id))
                            _logger.info('>>> location_dest_id: ' + str(move.location_dest_id.id))
                            _logger.info('>>> company_id: ' + str(self.company_id.id))
                            new_mvl = self.env['stock.move.line'].create(dict(
                                product_id=selected.product_id.id,
                                product_uom_id=selected.product_id.uom_id.id,
                                picking_id=picking.id,
                                move_id=move.id,
                                lot_id=company_lot.id,
                                qty_done=selected.qty,

                                # PCI Version
                                # location_id=selected.picking_id.location_id.id,
                                # location_dest_id=selected.picking_id.location_dest_id.id,

                                # MIS@SanQua Update
                                # Date: 13/10/2021
                                # Note: This update purpose is to handle journal of WIM/OUT and WIM/GR that not correct.
                                location_id=move.location_id.id,
                                location_dest_id=move.location_dest_id.id,
                                company_id=self.company_id.id))
                            _logger.info('>>> End: Create Move Line....')
                    skipped_moves += matched_moves

                validating = picking.button_validate()
                if type(validating) == dict:
                    res_model = validating.get('res_model')
                    if res_model == 'stock.immediate.transfer':
                        res_id = validating.get('res_id')
                        Wizard = self.env['stock.immediate.transfer'].browse(
                            res_id)
                        Wizard.process()  # process if wizard showed
                    elif res_model == 'stock.overprocessed.transfer':
                        raise ValidationError(_("Raise Overprocessed To Receive Qty on Validating Receive Order %s!") % (
                            picking.mapped('display_name')))
            checking_done_picking = pickings.mapped(
                lambda r: r.state == 'done')

            # assert all(checking_done_picking), "Some receive order not Validated(done)!"

            print(
                '>>> END : sanqua_sale_flow/models/purchase_order.py def inter_company_create_sale_order(self, company):')
            print('-------------------------------------------------------------------------------------------------')

        try:
            super(PurchaseOrder, self.with_context(no_reward=True)
                  ).inter_company_create_sale_order(company)
        except Warning as w:
            intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
            company_partner = self.mapped(
                lambda r: r.company_id.partner_id.with_user(intercompany_uid))
            if company_partner.property_product_pricelist.id == False:
                raise UserError(_("Please Define Pricelist in %s contact!") % (
                    company_partner.mapped('display_name')))

        Order = self.with_user(
            self.sudo().company_id.intercompany_user_id.id)._find_created_interco_sale_order()
        assert Order.id, "No Created Sale Order Defined When Confirming Interco PO!"
        assert Order.company_id.id != self.sudo().company_id.id
        assert Order.partner_id.id == self.sudo().company_id.partner_id.id

        # SENDING CREATED SO->PICKING_IDS #
        Order._copy_selected_interco_move_line()

        # save current free_qty on Company for each product in lines
        products = Order.order_line.mapped('product_id')

        # call button_validate() without res handler --> on validate_pickings()
        # PLANT TO ORIGIN
        if self.interco_sale_id:
            Order.picking_ids.button_validate()
        # after validate shouldbe:
        # picking done
        # qty reduced
        # assert all(Order.picking_ids.mapped(lambda r:r.state=='done')), 'Picking State not changed to Draft.'

        # RECEIVING CREATED PICKING PO #
        receiving_pickings = self.sudo().mapped('picking_ids')

        assert len(receiving_pickings) > 0, "No Receive Picking Defined!"

        # assert all(receiving_pickings.mapped(lambda r: r.state ==
        #            'assigned')), "There's 1 or more picking not Ready!"

        # must ready
        # call validating_pickings()
        # assumed receiving will assigned, so will force qty_done
        # RECEIVE ON ORIGIN
        if self.interco_sale_id:
            validating_pickings(receiving_pickings)

        # COMMENTED IMPROVEMENT
        # new_invoices = self._create_auto_invoice()
        # assert all(new_invoices.mapped(lambda r:r.state=='draft')), "Some invoice created with status != Draft!Please Contact System Administrator!"
        print('-------------------------------------------------------------------------------------------------')
