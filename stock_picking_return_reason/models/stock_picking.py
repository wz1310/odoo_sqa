from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ["stock.picking", "approval.matrix.mixin"]

    is_return_picking = fields.Boolean(
        string="Is Return Picking", compute="_compute_is_return_picking", default=False)
    origin_returned_picking_id = fields.Many2one(
        'stock.picking', compute="_compute_is_return_picking")

    def name_get(self):
        res = []
        for rec in self:
            name = "%s" % (rec.name, )
            if rec.picking_type_code == 'outgoing' and rec.is_return_picking == False:
                name = rec.doc_name
            res += [(rec.id, name)]
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        connector = '|'
        recs = self.search([connector, ('doc_name', operator, name),
                           ('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def _compute_is_return_picking(self):
        for picking in self:
            origin_returned_picking_id = picking.move_ids_without_package.mapped(
                lambda r: r.origin_returned_move_id.picking_id)
            picking.update({
                'is_return_picking': any(picking.move_ids_without_package.mapped(lambda r: r.origin_returned_move_id.id)),
                'origin_returned_picking_id': origin_returned_picking_id.id
            })

    return_reason = fields.Text(string='Reason', readonly=False)
    return_type = fields.Selection([
        ('delivery', 'Delivery'),
        ('after_sales', 'After Sales'),
        ('internal', 'Return GR by Internal'),
        ('vendor', 'Return GR by Vendor'),
    ], string='Return Type')
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('need_approval', 'Need Approval'),
        ('approved', 'Approved'),
        ('reject', 'Reject'),
    ], string='Approval State', default='draft')

    def _create_return_move_lines(self, source_picking, active_picking):
        """
            _params self : Return picking created.
            _params source_picking : picking origin from SO/PO.
            _params active_picking : origin picking from WIM.
        """
        _logger.error('>>> stock_picking_return_reason/models/stock_picking.py def _create_return_move_lines(self, source_picking, active_picking):')
        _logger.error('----------------------------------------------------------------------------------------------------------------------------')
        _logger.error('>>> source_picking: ' + str(source_picking))
        _logger.error('>>> source_picking: ' + str(active_picking))
        # print('>>> active_picking.move_line_ids.id : ' + str(active_picking.move_line_ids.id))

        self.ensure_one()
        # self --> picking to be process
        # source_picking --> picking in intercompany on processing

        LotNotFound = []
        # for move in self.move_lines:
        #     # loop each moves
        #     # find matched move from source_picking with equal product
        #     matched = source_picking.sudo().move_lines.filtered(lambda r:r.product_id.id == move.product_id.id)
        #     if not len(matched):
        #         raise UserError(_("Failed on finding same product: %s in %s on source:%s") % (move.sudo().product_id.display_name, self.sudo().display_name, source_picking.sudo().display_name))
        #     # loop each move_line_ids in source_picking

        # loop each move_line_ids in source_picking
        if len(self.move_line_ids):
            self.move_line_ids.unlink()
        move_line_ids = []
        line_done = active_picking.move_line_ids.filtered(
            lambda r: r.qty_done > 0.0)

        _logger.error('>>> line_done : ' + str(line_done))
        if not len(line_done):
            raise UserError(_("Please set done qty at least for 1 item!"))
        for line in line_done.sorted('qty_done'):
            # matched possibilities will be not a single

            # Untuk mendapatkan stock move dari picking (SJ)
            line_source = source_picking.mapped('move_ids_without_package').filtered(
                lambda r: r.product_id == line.product_id and r.product_uom_qty == line.move_id.move_orig_ids.product_uom_qty)
            _logger.error('>>> line_source not filtered : ' + str(source_picking))
            _logger.error('>>> line_source filtered: ' + str(line_source))
            current_return_qty = line_source[0].product_uom_qty - \
                sum(line_source[0].move_dest_ids.filtered(
                    lambda r: r.state == 'done').mapped('product_uom_qty'))
            _logger.error('>>> line_source.product_uom_qty : ' + str(line_source[0].product_uom_qty))
            _logger.error('>>> sum : ' + str(sum(line_source[0].move_dest_ids.filtered(
                    lambda r: r.state == 'done').mapped('product_uom_qty'))))
            _logger.error('>>> current_return_qty : ' + str(current_return_qty))

            # Utk mendapatkan stock move GR
            matched = self.sudo().move_lines.filtered(lambda r: r.product_id.id ==
                                                      line.product_id.id and r.product_uom_qty == current_return_qty)
            _logger.error('>>> matched : ' + str(matched))
            MoveLine = self.env['stock.move.line']

            # Lot = self.env['stock.production.lot'].search([('company_id','=',self.sudo().company_id.id), ('name','=',line.sudo().lot_id.name), ('product_id','=',line.sudo().product_id.id)])
            Lot = self.env['stock.production.lot'].fetch_company_lot(
                line.sudo().lot_id, self.sudo().company_id)
            _logger.error('>>> name: ' + str(line.sudo().lot_id.name))
            _logger.error('>>> product_id: ' + str(line.sudo().lot_id.product_id.id))
            _logger.error('>>> product_id: ' + str(self.sudo().company_id.id))
            _logger.error('>>> Lot: ' + str(Lot))

            if not len(Lot):
                LotNotFound.append("%s | %s | %s" % (line.sudo(
                ).lot_id.name, line.product_id.display_name, self.sudo().company_id.display_name,))
                continue

            _logger.error('>>> Start write stock.move.line...')
            if not len(LotNotFound):
                new_mvl = dict(
                    product_id=line.sudo().product_id.id,
                    product_uom_id=line.sudo().product_id.uom_id.id,
                    picking_id=self.sudo().id,
                    move_id=line.sudo().move_id.id,
                    lot_id=Lot.sudo().id,
                    qty_done=line.sudo().qty_done,

                    # PCI Version
                    # location_dest_id=self.sudo().location_id.id,
                    # location_id=self.sudo().location_dest_id.id,

                    # MIS@SanQua Update
                    # Date: 13/10/2021
                    # Note: This update purpose is to handle journal of WIM/GR (from customer) that not correct.
                    location_dest_id=self.sudo().location_dest_id.id,
                    location_id=self.sudo().location_id.id,
                    company_id=self.sudo().company_id.id)
                # move_line_ids.append((0, 0, new_mvl))
                matched.write({'move_line_ids': [(0, 0, new_mvl)]})
            _logger.error('>>> data : ' + str(new_mvl))
            _logger.error('>>> move_line_id : ' + str(matched[0].id))
            _logger.error('>>> move_id : ' + str(line.sudo().move_id.id))
            _logger.error('>>> location_dest_id : ' + str(self.sudo().location_id.id))
            _logger.error('>>> location_id : ' + str(self.sudo().location_dest_id.id))
            _logger.error('>>> End write stock.move.line...')
        if len(LotNotFound):
            raise UserError(_("Failed to fetch Lot, please check:\n%s") % (
                "\n".join(LotNotFound)))
        _logger.error('----------------------------------------------------------------------------------------------------------------------------')

    def _return_po(self):
        self.ensure_one()
        po = self.sudo().sale_id.interco_purchase_id

        # for example
        # if WH/IN/0001 (return picking INCOMING) -> validated then system should be finding sale_id.interco_purchase_id.picking_ids
        # WICH type == 'INCOMING'
        # inverse_retur_code = 'outgoing' if self.picking_type_code=='incoming' else 'incoming'
        inverse_retur_code = self.picking_type_code

        # filter picking
        # wich picking be process is
        picking = po.picking_ids.filtered(
            lambda r: r.picking_type_code == inverse_retur_code).sorted('id', reverse=True)
        if len(picking) > 1:
            # only 1
            picking = picking[0]
        elif not len(picking):
            raise UserError(_("No Picking Found for criteria %s on Purchase Doc: %s") % (
                inverse_retur_code, po.sudo().display_name,))

        # here should be get last inversed picking

        retur = with_context(
            source_picking_id=active_picking.id).direct_return_picking()
        # browse stock picking
        return_picking = self.browse(retur.get('res_id'))
        if not len(return_picking):
            raise UserError(_("Picking not created! For Purchase %s") %
                            (po.sudo().display_name,))

        # should be return picking ready
        # handler if return code was outgoing/incoming
        # creating move_lines from reversed picking
        return_picking._create_return_move_lines(self)

        print('>>> 16...')
        validating = return_picking.button_validate()

        if type(validating) == dict:
            res_model = validating.get('res_model')
            if res_model == 'stock.immediate.transfer':
                res_id = validating.get('res_id')
                Wizard = self.env['stock.immediate.transfer'].browse(res_id)
                Wizard.process()  # process if wizard showed
            elif res_model == 'stock.overprocessed.transfer':
                raise ValidationError(_("Raise Overprocessed To Receive Qty on Validating Receive Order %s!") % (
                    picking.mapped('display_name')))
            elif res_model == 'stock.backorder.confirmation':
                res_id = validating.get('res_id')
                Wizard = self.env['stock.backorder.confirmation'].browse(
                    res_id)
                # process if wizard showed
                Wizard.with_context(cancel_backorder=True,
                                    force_validating_interco_lot=True).process()

    # find possible po pickings
    # will return non singular object

    def _fetch_possible_po_picking(self):
        self.ensure_one()
        purchase = self.sudo().sale_id.interco_purchase_ids.filtered(
            lambda r: r.interco_picking_id.id == self.origin_returned_picking_id.id)
        # incase In (from do)->will fetching incoming from po
        return purchase.picking_ids.filtered(lambda r: r.picking_type_code == self.picking_type_code and r.state == 'done')

    # find possible so pickings from plant
    # will return non singular object
    def _fetch_possible_sale_picking(self):
        self.ensure_one()
        # find sales in plant company
        # sale = self.env['sale.order'].with_context(allowed_company_ids=self.plant_id.ids).sudo().search([('')])
        sale = self.sudo().sale_id.interco_purchase_ids.filtered(lambda r: r.interco_picking_id.id ==
                                                                 self.origin_returned_picking_id.id)._find_created_interco_sale_order()

        # incase In (from do)->will fetching receive from so
        inversed_picking_type_code = 'incoming' if self.picking_type_code == 'outgoing' else 'outgoing'
        return sale.picking_ids.filtered(lambda r: r.picking_type_code == inversed_picking_type_code and r.state == 'done')

    # FIND ALL RELATED PICKINGS TROUGH INTERCOMPANY PROCESS
    # DO --> IN --> retur: Retur PO -> Out, Retur DO plan -> in
    # DO --> IN -> Out --> retur: Retur PO -> Out -> In, Retur DO plan -> in -> Out
    def get_all_related_pickings(self):
        # fetch po
        pickings = self._fetch_possible_po_picking()
        # fetch plant so
        pickings += self._fetch_possible_sale_picking()
        return pickings

    def _interco_auto_retur(self, active_picking):
        print("======================================== setelah_interco_auto_retur")
        companies = self.mapped('company_id')
        for company in companies:
            picking_in_company = self.filtered(
                lambda r: r.company_id.id == company.id)
            print("============================picking_in_company::",picking_in_company)
            passed_pickings = self.env['stock.picking']
            if len(picking_in_company) > 1:
                print("=================================== len(picking_in_company) > 1")
                # if found more than 1 pickings
                # find possibility by checking product available in moves
                # picking_in_company.mapped(lambda r:)
                product_in_active_picking = active_picking.move_lines.mapped(
                    'product_id')
                # product_in_active_picking.mapped(lambda r:r.)
                for pick in picking_in_company:
                    # if pick.move_lines.mapped()
                    if set(product_in_active_picking.ids).issubset(pick.move_lines.mapped('product_id').ids):
                        # passed_pickings |= pick
                        # active_move = active_picking.move_lines.filtered(lambda r:r.)
                        # if all(pick.move_lines.mapped(lambda r:r.quantity_done>=))
                        for move in pick.move_lines:
                            compare_move = active_picking.move_lines.filtered(
                                lambda r: r.product_id.id == move.product_id.id)
                            if move.quantity_done >= sum(compare_move.mapped('quantity_done')):
                                passed_pickings |= pick
            elif len(picking_in_company) == 1:
                print("=================================== len(picking_in_company) == 1")
                passed_pickings = picking_in_company

            for picking in passed_pickings:
                # create return
                retur = picking.with_context(
                    source_picking_id=active_picking.id, force_sent=1, intecompany_return=True).sudo().direct_return_picking()
                return_picking = self.with_context(
                    allowed_company_ids=picking.company_id.ids).sudo().browse(retur.get('res_id'))
                return_picking._create_return_move_lines(
                    source_picking=picking, active_picking=active_picking)

                print('>>> 17...')
                validating = return_picking.button_validate()
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
                    elif res_model == 'stock.backorder.confirmation':
                        res_id = validating.get('res_id')
                        Wizard = self.env['stock.backorder.confirmation'].browse(
                            res_id)
                        # process if wizard showed
                        Wizard.with_context(
                            cancel_backorder=True, force_validating_interco_lot=True).process()

    def validate_return_intercompany(self):
        self.ensure_one()

        pickings_to_retur = self.get_all_related_pickings()

        pickings_to_retur._interco_auto_retur(self)

    def button_validate(self):
        print('>>> HERE IS ORIGINAL button_validate() at stock_picking.py --> stock_picking_return_reason')
        print('>>> --- Call button_validate(self) ---')
        # Cek Receved Stock
        self.ensure_one()

        # SOT masih error, jadi Outgoing di Lepas
        if self.picking_type_id.code in ('internal', 'outgoing') and self.location_id.usage in ('internal', 'production'):

            for mov in self.move_line_ids:

                print('>>> mov_id : ' + str(mov.id))
                print('>>> mov_loct : ' + str(mov.move_id))
                print('>>> mov_product : ' + str(mov.product_id))
                print('>>> lot_id : ' + str(mov.lot_id.id))

                quant_ids = self.env['stock.quant']
                if mov.location_id.usage in ('internal', 'production'):
                    stock = 0.0
                    if mov.lot_id.id:
                        quant_ids = self.env['stock.quant'].search([('product_id', '=', mov.product_id.id),
                                                                    ('location_id', '=',
                                                                     mov.location_id.id),
                                                                    ('lot_id', '=', mov.lot_id.id)])
                    else:
                        quant_ids = self.env['stock.quant'].search([('product_id', '=', mov.product_id.id),
                                                                    ('location_id', '=', mov.location_id.id)])

                    for quant in quant_ids:
                        stock += quant.quantity
                    if stock < mov.qty_done:
                        raise UserError(_("<Z> Stock untuk Product %s \nLot : %s \nkurang dari yang dibutuhkan, Mohon periksa ketersediaan stock di %s\nStock Tersedia : %s\nAkan dikirim : %s\nKurang : %s \npicking") % (
                            mov.product_id.name, mov.lot_id.name, mov.location_id.display_name, stock, mov.qty_done, stock-mov.qty_done))
                        # continue

        if self.approval_state == 'need_approval':
            if self.approved == True:

                print('>>> 18...')
                res = super(StockPicking, self).button_validate()
                return res
            else:
                raise UserError(
                    _("You Can't Validate This Document!\nThis Document Needs to Approved!"))
        else:
            if self.sale_interco_master == True and self.is_return_picking == True:
                print(
                    '>>> self.sale_interco_master==True and self.is_return_picking==True:')
                # if return picking
                # and if interco master
                # so we will append same lot to process
                return_none = False

                print('>>> 19...')
                res = super(StockPicking, self.with_context(
                    allowed_company_ids=self.allowed_company_ids.ids).sudo()).button_validate()

                if type(res) == dict:
                    res_model = res.get('res_model')
                    if res_model == 'stock.immediate.transfer':
                        print('>>> res_model == stock.immediate.transfer:')
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.immediate.transfer'].browse(
                            res_id)
                        Wizard.with_context(allowed_company_ids=self.allowed_company_ids.ids).sudo(
                        ).process()  # process if wizard showed

                    elif res_model == 'stock.overprocessed.transfer':
                        print('>>> res_model == stock.overprocessed.transfer:')
                        raise ValidationError(_("Raise Overprocessed To Receive Qty on Validating Receive Order %s!") % (
                            self.mapped('display_name')))
                    elif res_model == 'stock.backorder.confirmation':
                        print('>>> res_model == stock.backorder.confirmation:')
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.backorder.confirmation'].browse(
                            res_id)
                        Wizard.with_context(cancel_backorder=True, force_validating_interco_lot=True, allowed_company_ids=self.allowed_company_ids.ids) \
                            .sudo().process()  # process if wizard showed
                        return_none = True
                if self.state != 'done':
                    print('>>> self.state != done:')
                    raise UserError(
                        _("Failed to validate picking sss : %s %s") % (self.name, str(self.id) ))
                if self.sale_truck_id.id:
                    print('>>> self.sale_truck_id.id:')
                    # if from sale truck
                    # only return do from so company
                    return res
                else:
                    print('>>> else: self.validate_return_intercompany()')
                    self.validate_return_intercompany()

                try:
                    if(return_none):
                        return None
                except expression as identifier:
                    return True
            elif self.is_return_picking == True:
                print('>>> self.is_return_picking==True:')

                print('>>> 20...')
                res = super(StockPicking, self.with_context(
                    allowed_company_ids=self.allowed_company_ids.ids).sudo()).button_validate()
                if type(res) == dict:
                    res_model = res.get('res_model')
                    if res_model == 'stock.immediate.transfer':
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.immediate.transfer'].browse(
                            res_id)
                        Wizard.with_context(allowed_company_ids=self.allowed_company_ids.ids).sudo(
                        ).process()  # process if wizard showed

                    elif res_model == 'stock.overprocessed.transfer':
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.overprocessed.transfer'].with_context(
                            {'default_picking_id': self.id}).browse(res_id)
                        # process if wizard showed
                        return Wizard.with_context(allowed_company_ids=self.allowed_company_ids.ids).sudo().action_confirm()
                    elif res_model == 'stock.backorder.confirmation':
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.backorder.confirmation'].browse(
                            res_id)
                        Wizard.with_context(cancel_backorder=True, force_validating_interco_lot=True, allowed_company_ids=self.allowed_company_ids.ids) \
                            .sudo().process()  # process if wizard showed
                        return None
            else:
                print('>>> else:')

                # print('>>> BEFORE VALIDATE')
                # picking_plant_wim = self.env['stock.picking'].search(
                #     [('no_sj_wim', '=', self.doc_name), ('doc_name', '!=', 'New')])
                # print('>>> picking_plant_wim : ' + str(picking_plant_wim))
                print('>>> 21...')
                res = super(StockPicking, self).button_validate()
                # print('>>> Res : ' + str(res))
                # print('>>> self.id : ' + str(self.id))
                # print('>>> self.id : ' + str(self.move_ids_without_package))

                # print('>>> AFTER VALIDATE')
                # picking_plant_wim = self.env['stock.picking'].search([('no_sj_wim','=',self.doc_name),('doc_name','!=','New')])
                # print('>>> picking_plant_wim : ' + str(picking_plant_wim))
            return res

    @api.model
    def action_create_return_picking(self, picking):
        returned_picking = self.env['stock.return.picking'].create(
            {'picking_id': picking.sudo().id})
        returned_picking.sudo()._onchange_picking_id()
        processing_picking = self.sudo().browse(self._context.get('source_picking_id'))
        # FIXME: Marked to set qty demand as souce picking
        # if len(processing_picking):
        #     for line in returned_picking.product_return_moves:
        #         #add condition based on product uom qty origin return and move id
        #         move_in_process = processing_picking.move_lines.filtered(lambda r:r.product_id.id==line.product_id.id and r.origin_returned_move_id and line.move_id\
        #             and r.origin_returned_move_id.product_uom_qty == line.move_id.product_uom_qty)
        #         print(line.quantity, move_in_process.quantity_done)
        #         if not move_in_process:
        #             move_in_process = processing_picking.move_lines.filtered(lambda r:r.product_id.id==line.product_id.id)
        #         if move_in_process and len(move_in_process) > 1:
        #             move_in_process = move_in_process[0]

        #         if line.quantity != move_in_process.quantity_done:
        #             line.quantity = move_in_process.quantity_done
        validating = returned_picking.create_returns()
        picking_id = self.env['stock.picking'].browse(validating.get('res_id'))
        # picking_id.interco_master = False
        # if picking_id.picking_type_code=='outgoing':
        #     picking_id.do_unreserve()

        ctx = validating.get('context')
        return {
            'name': _('Returned Picking'),
            'view_mode': 'form,tree,calendar',
            'res_model': 'stock.picking',
            'res_id': validating.get('res_id'),
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

    def search_related_interco_deliveries(self):
        companies = self.env['res.company'].sudo().search([])

        if self.sale_id.id:
            return self.env['stock.picking'] \
                .with_context(allowed_company_ids=companies.sudo().ids) \
                .sudo().search([
                    ('sale_id', '=', self.sudo().sale_id.id),
                    ('state', '=', 'done'),
                    ('picking_type_id.code', '=', 'outgoing')])
        return self.env['stock.picking']

    # OPEN wizard.intercompany.return form

    def _open_wizard_intercompany_return_form(self):
        self.ensure_one()
        form = self.env.ref(
            'stock_picking_return_reason.wizard_intercompany_return_form_view')
        context = dict(self.env.context or {})
        context.update({
            'default_picking_id': self.id,
        })  # uncomment if need append context
        res = {
            'name': "%s - %s" % (_('Please Select Delivery'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.intercompany.return',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def _delivery_order_can_return(self):
        self.ensure_one()

        # Update by: MIS@SanQua
        # At : 19/11/2021
        # Note: to prevent return when the GR or SJ already billedd
        # ctx_params = self._context.get('params')
        # if ctx_params:
        #     if ctx_params.get('id'):

        # print(">>> Picking ID : " + str(self.sudo().id))
        xPickingDetail = self.env['stock.picking'].search(
               [('id', '=', self.sudo().id)], limit=1)
        if xPickingDetail.invoice_id.id:
            print(">>> Picking Detail : " +
                    str(xPickingDetail.invoice_id.id) or '')
            print(">>> Picking Detail : " +
                    xPickingDetail.invoice_id.name or '')
            raise UserError(_("This GR/DO is already billed with Bill No. %s" % (
                xPickingDetail.invoice_id.name)))

        if not self._context.get('force_sent') and self._context.get('check_sent') and self.picking_type_code == 'outgoing' and self.sent == False:
            raise UserError(
                _('Only can return received Delivery Order. Ref: %s') % (self.name,))

        # if not self._context.get('force_sent') and self._context.get('check_sent') and self.picking_type_code == 'outgoing' and self.sent == False:
        #    raise UserError(
        #        _('Only can return received Delivery Order. Ref: %s') % (self.name,))

    def direct_return_picking(self):
        self.ensure_one()
        self = self.with_context(abort_lot_check=1)
        # validate is picking can return
        self._delivery_order_can_return()

        # search all companies
        companies = self.env['res.company'].search([])

        # search related outgoing picking
        # pickings = self.search_related_interco_deliveries()
        # if len(pickings)>1:
        #     self._open_wizard_intercompany_return_form()
        return self.action_create_return_picking(self)


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    reason = fields.Text(string='Reason', required=False)
    return_type = fields.Selection([
        ('delivery', 'Delivery'),
        ('after_sales', 'After Sales')
    ], string='Return Type', required=False)

    def _create_returns(self):
        picking_id, picking_type_id = super(
            StockReturnPicking, self.sudo())._create_returns()
        picking = self.env['stock.picking'].sudo().browse(picking_id)
        picking.origin = "Return of %s" % (self.picking_id.display_name,)
        picking.write({
            'vehicle_model_id': self.picking_id.vehicle_model_id.id if self.picking_id.vehicle_model_id else False,
            'fleet_vehicle_id': self.picking_id.fleet_vehicle_id.id if self.picking_id.fleet_vehicle_id else False,
            'fleet_driver_id': self.picking_id.fleet_driver_id.id if self.picking_id.fleet_driver_id else False,
            'plant_id': self.picking_id.plant_id.id if self.picking_id.plant_id else False,
        })
        return picking_id, picking_type_id

    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        quantity = stock_move.product_qty - sum(
            stock_move.move_dest_ids
            .filtered(lambda m: m.state in ['partially_available', 'assigned', 'done'])
            .mapped('move_line_ids.product_qty')
        ) - stock_move.return_qty
        quantity = float_round(
            quantity, precision_rounding=stock_move.product_uom.rounding)
        return {
            'product_id': stock_move.product_id.id,
            'quantity': quantity,
            'move_id': stock_move.id,
            'uom_id': stock_move.product_id.uom_id.id,
        }

    def _prepare_move_default_values(self, return_line, new_picking):
        move_line_ids = []
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date_expected': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
            # 'move_line_ids':[(6,0, move_line_ids)]
        }
        return vals

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        move_dest_exists = False
        product_return_moves = [(5,)]
        if self.picking_id and self.picking_id.state != 'done':
            raise UserError(_("You may only return Done pickings."))
        # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
        # default values for creation.
        line_fields = [
            f for f in self.env['stock.return.picking.line']._fields.keys()]
        product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(
            line_fields)
        # FIXME: Remove filtered product not reward product then return can return for all product
        # for move in self.picking_id.move_lines.filtered(lambda r: not r.sale_line_id.is_reward_line):
        for move in self.picking_id.move_lines:
            if move.state == 'cancel':
                continue
            if move.scrapped:
                continue
            if move.move_dest_ids:
                move_dest_exists = True
            product_return_moves_data = dict(product_return_moves_data_tmpl)
            product_return_moves_data.update(
                self._prepare_stock_return_picking_line_vals_from_move(move))
            product_return_moves.append((0, 0, product_return_moves_data))
        if self.picking_id and not product_return_moves:
            raise UserError(
                _("No products to return (only lines in Done state and not fully returned yet can be returned)."))
        if self.picking_id:
            self.product_return_moves = product_return_moves
            self.move_dest_exists = move_dest_exists
            self.parent_location_id = self.picking_id.picking_type_id.warehouse_id and self.picking_id.picking_type_id.warehouse_id.view_location_id.id or self.picking_id.location_id.location_id.id
            self.original_location_id = self.picking_id.location_id.id
            location_id = self.picking_id.location_id.id
            if self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                location_id = self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
            self.location_id = location_id
