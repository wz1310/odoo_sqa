from ast import literal_eval
from datetime import date
from itertools import groupby
from operator import itemgetter
import time

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    avail_to_cancel = fields.Boolean(
        string="Can Cancel", compute="_compute_avail_to_cancel")
    interco_master = fields.Boolean(
        string="Intercompany Master", compute="_compute_sale_interco", readonly=True, store=True)
    sale_interco_master = fields.Boolean(
        string="Sales is Intercompany Master", related='sale_id.interco_master', readonly=True)

    vehicle_model_id = fields.Many2one(
        'fleet.vehicle.model', string="Vehicle Model", related="sale_id.vehicle_model_id", readonly=True, copy=False)
    plant_id = fields.Many2one('res.company', string="Plant", required=False, ondelete="restrict",
                               onupdate="restrict", compute="_compute_picking_sale_intercompany", store=True, inverse="_inverse_plant")
    warehouse_plant_id = fields.Many2one('stock.warehouse', string="Partner Location", required=False, ondelete="restrict",
                                         onupdate="restrict", compute="_compute_picking_sale_intercompany", store=True, inverse="_inverse_plant")
    sales_team_id = fields.Many2one('crm.team', string="Division", ondelete="restrict",
                                    onupdate="restrict", compute="_compute_picking_sale_intercompany", store=True)
    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting Another Operation'), ('confirmed', 'Waiting'), (
        'assigned', 'Ready'), ('plant-confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Canceled')])
    sale_agreement_id = fields.Many2one(
        'sale.agreement', compute="_compute_picking_sale_intercompany", store=True, required=False)
    order_pickup_method_id = fields.Many2one(
        'order.pickup.method', string="Pickup Method", required=False, compute="_compute_picking_sale_intercompany", store=True)

    interco_move_line_ids = fields.One2many(
        'stock.interco.move.line', compute="_compute_interco_move_line_ids")

    other_wh_can_read = fields.Boolean(
        related="picking_type_id.other_wh_can_read", readonly=True, store=True)
    allow_print = fields.Boolean(readonly=True, default=True, copy=False)
    print_count = fields.Integer(string="Print Count", copy=False, default=1)
    internal_sale_notes = fields.Text(readonly=False, store=True)
    carrier_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
        ('partner', 'Partner')
    ], string='Expedition', required=False, copy=False)
    fleet_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle', copy=False)
    fleet_driver_id = fields.Many2one('res.partner', string="Driver", domain=[
                                      ('customer', '=', False), ('supplier', '=', False)], copy=False)

    sale_mix_ids = fields.Many2many(
        'sale.order', related="sale_id.sale_mix_ids", readonly=True)

    allowed_company_ids = fields.Many2many('res.company', 'stock_picking_allowed_company_rel', 'picking_id',
                                           'allowed_company_id', compute="_compute_allowed_company_ids", store=True, string="Allowed Companies")
    interco_ref_picking_ids = fields.Many2many(
        'stock.picking', compute='_compute_interco_ref_picking_ids', string='Interco Ref Picking', search="_search_interco_ref_picking_ids")
    sent = fields.Boolean(string='Sent', default=False, copy=False)
    doc_name = fields.Char(string='Doc. Name', readonly=True,
                           required=False, default='New', copy=False)
    customer_id = fields.Many2one(
        'res.partner', string="Customer SO", related="sale_id.partner_id", store=True)

    def _fetch_sequence(self):
        print('==========================================')
        print('>>> _fetch_sequence(self) : WIM')
        for rec in self:
            print('>>> rec : ' + str(rec))
            if rec.doc_name == 'New':
                rec.doc_name = self.env['ir.sequence'].next_by_code(
                    'seq.delivery.order.doc.name')
                print('>>> rec.doc_name : ' + str(rec.doc_name))
                print('==========================================')

    # Added by: MIS@SanQua
    # At: 19/12/2021
    # Description: When intercompany transaction, DO Number formula plant must be use its owned. Before use WIM formula.
    def _fetch_sequence_plant(self, company_id):
        print('==========================================')
        print('>>> _fetch_sequence(self) : PLANT')
        print('>>> company_id : ' + str(company_id))
        sequence_obj = self.env['ir.sequence']
        for rec in self:
            print('>>> rec : ' + str(rec))
            if rec.doc_name == 'New':

                sj_sequence = sequence_obj.search([('company_id','=',company_id.id),('code','=','seq.delivery.order.doc.name')])
                if sj_sequence:
                    print('>>> sj_sequence : ' + str(sj_sequence._get_prefix_suffix()))

                code = sequence_obj.with_context(force_company=company_id.id).next_by_code(
                    'seq.delivery.order.doc.name')
                print('>>> code : ' + str(code))
                rec.doc_name = code
                print('==========================================')

    def action_done(self):
        # print('>>> START def action_done...')
        # i = 0
        for rec in self.filtered(lambda r: r.doc_name == 'New' and r.picking_type_code == 'outgoing'):
            # print('>>> i : ' + str(i))
            # print('>>> Source Location Company : ' + str(rec.location_id.company_id)

            # Added by: MIS@SanQua
            # At: 19/12/2021
            # Description: When intercompany transaction, DO Number formula plant must be use its owned. Before use WIM formula.
            rec._fetch_sequence_plant(rec.location_id.company_id)
            # i = i + 1

            # By PCI
            rec._fetch_sequence()
        res = super().action_done()
        return res

    def btn_sent(self):
        if self.plant_id:
            if self.env.company.id != self.plant_id.id:
                raise UserError(
                    _("With your current status company, you can not do this process"))

        if any(self.mapped(lambda r: r.state != 'done')):
            raise UserError(_("Only can processing done document(s)!"))

        # Added by: MIS@SanQua
        # At: 29/12/2021
        # Description: Auto received when DO WIM -> Customer received
        if self.interco_master:
            plant_picking_ids = self.env['stock.picking'].search([('no_sj_wim','=',self.doc_name), ('company_id','=',self.env.company.id)])
            if plant_picking_ids:
                plant_picking_ids.write({'sent': True})

        self.sent = True

    @api.depends('sale_id')
    def _compute_interco_ref_picking_ids(self):
        print("START CONFIRM INTERCO REF PICKING",fields.Datetime.now())
        for rec in self:
            picking = False
            if rec.sale_id:
                picking = rec.sudo().sale_id.auto_purchase_order_id.interco_ref_picking_ids.ids
            rec.interco_ref_picking_ids = picking
        print("END CONFIRM INTERCO REF PICKING",fields.Datetime.now())

    def _search_interco_ref_picking_ids(self, operator, value):
        print("SEARCH START CONFIRM INTERCO REF PICKING",fields.Datetime.now())
        picking_ids = self.env['stock.picking'].sudo().search([])
        picking_ids = picking_ids.filtered(
            lambda r: r.interco_ref_picking_ids.filtered(lambda f: f.doc_name == value))
        print(" SEARCH END CONFIRM INTERCO REF PICKING",fields.Datetime.now())
        return [('id', 'in', picking_ids.ids)]

    def _compute_avail_to_cancel(self):
        res = False
        diff = self
        incoming = self.filtered(lambda r: r.picking_type_code == 'incoming' and r.state in [
                                 'draft', 'waiting', 'confirmed', 'assigned'])
        if len(incoming):
            incoming.update({'avail_to_cancel': True})
            diff = diff - incoming

        outging = self.filtered(lambda r: r.picking_type_code ==
                                'outgoing' and r.state in ['draft', 'confirmed'])
        if len(outging):
            outging.update({'avail_to_cancel': True})
            diff = diff - outging

        elsetype = self.filtered(lambda r: r.picking_type_code not in [
                                 'outgoing', 'incoming'] and r.state in ['draft', 'confirmed', 'waiting'])
        if len(elsetype):
            elsetype.update({'avail_to_cancel': True})
            diff = diff - elsetype

        if len(diff):
            diff.update({'avail_to_cancel': res})

    # allowed company will append from company_id+plant_id+sale_id.allowed_company_ids
    @api.depends('sale_id', 'picking_type_id', 'plant_id')
    def _compute_allowed_company_ids(self):
        print("None")
        for rec in self:
            allowed_companies = rec.company_id + rec.plant_id
            if rec.sale_id.id:
                allowed_companies += rec.sale_id.allowed_company_ids

            rec.allowed_company_ids = [(6, 0, allowed_companies.ids)]

    @api.depends('sale_id')
    def _compute_sale_interco(self):
        for rec in self:
            res = False
            if rec.sale_id.id and rec.picking_type_code == 'outgoing':
                res = rec.sudo().sale_id.interco_master

            rec.interco_master = res

    def write(self, vals):
        Env = self
        if self.picking_type_id.other_wh_can_read:
            context = self._context.copy()
            context.update(allowed_company_ids=self.mapped('company_id').ids)
            Env = self.with_user(
                self.env.company.intercompany_user_id.id).with_context(context)

        return super(StockPicking, Env).write(vals)

    @api.onchange('fleet_vehicle_id')
    def onchange_fleet_vehicle_id(self):
        driver_id = False
        if self.fleet_vehicle_id.id:
            driver_id = self.fleet_vehicle_id.driver_id.id

        self.fleet_driver_id = driver_id

    def check_access_rule(self, operation):
        origin = True
        for rec in self:
            if self.env.user.company_id.id == rec.plant_id.id:
                origin = False
        if origin:
            return super().check_access_rule(operation)

    def action_toggle_is_locked(self):
        stock_warehouses = self.env['stock.warehouse'].with_context(
            allowed_company_ids=self.env.user.company_id.ids).search([])
        for rec in self:
            if rec.is_locked == False and rec.interco_master and rec.picking_type_code == 'outgoing':
                if not rec.plant_id.id:
                    rec.plant_id = self.env.user.company_id.id
                if not rec.warehouse_plant_id.id:
                    # if only 1 warehouse
                    if len(stock_warehouses) == 1:
                        rec.warehouse_plant_id = stock_warehouses.id
                    else:
                        raise UserError(_("Please Select Plant and Location!"))

                msg_body = _("Locked for %s") % (rec.plant_id.display_name,)
                rec.message_post(body=msg_body)
        return super().action_toggle_is_locked()

    def _compute_interco_move_line_ids(self):
        for rec in self:
            rec.interco_move_line_ids = rec.move_lines.mapped(
                'interco_move_line_ids')

    """ compute check_availability button on form
        @override from stock
        @return True or False
    """

    def _compute_show_check_availability(self):

        if self.user_has_groups('base.group_system,stock.group_stock_manager'):
            super()._compute_show_check_availability()
        else:
            for picking in self:
                if picking.interco_master:
                    picking.show_check_availability = False
                    continue
                if picking.immediate_transfer or not picking.is_locked or picking.state not in ('confirmed', 'waiting', 'assigned'):
                    picking.show_check_availability = False
                    continue

                picking.show_check_availability = any(
                    move.state in ('waiting', 'confirmed', 'partially_available') and
                    float_compare(move.product_uom_qty, 0,
                                  precision_rounding=move.product_uom.rounding)
                    for move in picking.move_lines
                )

    def _validating_selected_lot_and_warehouse_plant(self):
        self.ensure_one()
        if self.interco_master and self.picking_type_code == 'outgoing':
            selected_warehouse_ids = self.interco_move_line_ids.mapped(
                'warehouse_id')
            if len(selected_warehouse_ids) == 0:
                raise UserError(
                    _("Please Select Warehouse on Interco Stock Lot Form"))
            elif len(selected_warehouse_ids) > 1:
                raise UserError(
                    _("Cant selecting Multiple Warehouse Source Location!"))

    def _validating_lot(self):
        self.ensure_one()
        checkLot = not self._context.get('abort_lot_check')

        if checkLot and self.interco_master and self.picking_type_code == 'outgoing':
            # if product tracking is not none (lot / unique)
            # then must required to fill interco_move_line_ids
            for move in self.move_lines.filtered(lambda r: r.product_id.tracking not in ['none']):
                if not len(move.interco_move_line_ids):
                    raise ValidationError(_("Please Select Lot Number for product %s!") % (
                        move.product_id.display_name,))
            self._validating_selected_lot_and_warehouse_plant()

    def action_assign(self):
        if self._context.get('cancel_action_assign'):
            return False
        if not self._context.get('force_validating_interco_lot', False):
            interco_pickings = self.filtered(
                lambda r: r.interco_master == True and r.picking_type_code == 'outgoing')
            if len(interco_pickings):
                for picking in interco_pickings:
                    picking._validating_lot()
        return super(StockPicking, self).action_assign()

    @api.depends('state', 'is_locked')
    def _compute_show_validate(self):
        interco_picking = self.filtered(
            lambda r: r.sale_id.id and r.interco_master == True and r.picking_type_code == 'outgoing')
        for rec in interco_picking:
            if rec.sale_id.interco_master:
                if rec.state in ['plant-confirmed']:
                    rec.show_validate = True
                else:
                    rec.show_validate = False
        # non interco
        non_interco = self - interco_picking
        if len(non_interco):
            super(StockPicking, non_interco)._compute_show_validate()

    """Creating Purchase Order to Plant Company (intercompany process)
    
    Creating Purchase Order to Plant Company (intercompany process)
    After Purchase Order created, it will run rule on intercompany_rules module
    will creating SaleOrder in Plant Company wich Customer = PurchaseOrder Company
    will run (purchase.order).inter_company_create_sale_order()
    """

    def _procure_inter_company(self):
        self.with_user(self.env.company.intercompany_user_id.id).with_context(force_company=self.sale_id.sudo().company_id.id).sale_id.write({
            'interco_company_id': self.plant_id.id,
        })

        def del_context(ctx, keys):
            for key in keys:
                if ctx.get(key):
                    del ctx[key]
            return ctx

        to_del = [
            'default_partner_id',
            'default_picking_id',
            'default_picking_type_id',
            'default_origin',
            'default_group_id']
        new_context = del_context(self._context.copy(), to_del)
        new_context['picking_id'] = self.id
        new_context['validity_date'] = self.sale_id.validity_date
        print("MEW CONTEXT", new_context)

        self.sale_id.with_context(new_context).create_interco_purchase_order()

    def _assign_interco_move_line_availability(self):
        self.ensure_one()
        MoveLine = self.env['stock.move.line']
        if self.interco_master == True and self.picking_type_code == 'outgoing':
            for line in self.interco_move_line_ids:

                company_lot_id = self.env['stock.production.lot'].fetch_company_lot(lot=line.with_user(
                    self.company_id.intercompany_user_id.id).lot_id, company=self.company_id)
                assert len(company_lot_id) == 1, "Should only 1 Lot found! But found %s lot within name:%s" % (
                    len(company_lot_id), line.lot_id.name)

                # available = self.env['stock.quant'].with_user(SUPERUSER_ID)._get_available_quantity(line.move_id.product_id, self.location_id, package_id=None, owner_id=None, strict=True)
                available = line.product_id.with_context(
                    force_company=2, allowed_company_ids=[2]).with_user(1).free_qty

                print('>>> _assign_interco_move_line_availability(self)')
                print('------------------------------------------------')
                print('picking_id : ' + str(line.move_id.picking_id.id))
                print('location_id : ' +
                      str(line.picking_id.location_id.id))
                print('location_dest_id : ' +
                      str(line.picking_id.location_dest_id.id))

                # PCI Version
                new_mvl = MoveLine.create(dict(product_id=line.product_id.id, product_uom_id=line.product_id.uom_id.id, picking_id=line.move_id.picking_id.id, move_id=line.move_id.id,
                                          lot_id=company_lot_id.id, qty_done=line.qty, location_dest_id=line.picking_id.location_id.id, location_id=line.picking_id.location_dest_id.id, company_id=self.company_id.id))
                print('>>> New_Mvl_ID!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! : ' + str(new_mvl.id))
                # MIS@SanQua Update
                # Date: 13/10/2021
                # Note: This update purpose is to handle journal of WIM/OUT that not correct.
                update_mvl = self.env['stock.move.line'].search([('id', '=', new_mvl.id)]).write(
                    {'location_id': line.picking_id.location_id.id, 'location_dest_id': line.picking_id.location_dest_id.id})
                # print('>>> update_mvl : ' + str(update_mvl))

    def validate_interco_move_lines(self):
        self.ensure_one()
        for move in self.move_lines:
            if not len(move.interco_move_line_ids) and not move.to_backorder:
                raise UserError(_("Please select Lot for %s") %
                                (move.product_id.display_name,))

        if all(self.move_lines.mapped(lambda r: r.to_backorder)):
            raise UserError(
                _("No Moves would be process.\nAll moves was no backorder!"))

    def btn_plant_confirm(self):
        self.ensure_one()
        self = self.with_context(plant_confirm=1)
        print("XXX LOCATION||||||||||||",[x.location_id.display_name for x in self.move_line_ids])
        if self.env.company.id != self.plant_id.id:
            raise UserError(
                _('Your Active company can not do this process, please re-check'))

        if self.warehouse_plant_id.id == False:
            raise UserError(_("Please fill Warehouse Plant!"))

        if self.interco_master and self.picking_type_code == 'outgoing':
            print('>>> 1. Statement 1...')
            print('>>> self.picking_type_code : ' + str(self.picking_type_code))
            print('>>> self.interco_master : ' + str(self.interco_master))
            # force intercompany rules
            company = self.with_user(SUPERUSER_ID).company_id
            print('>>> company : ' + str(company))
            print('>>> self.env.user.company_id.ids : ' + str(self.env.user.company_id.ids))

            self = self.with_context(
                force_company=company.id, allowed_company_ids=company.ids+self.env.user.company_id.ids)

        if self.sudo().sale_id.id and self.sudo().sale_id.interco_master == True and self.picking_type_code == 'outgoing':
            print('>>> 2. validate_interco_move_lines() : Checking lot already choosen or not')
            self.validate_interco_move_lines()

            assert self.state in (
                'confirmed', 'assigned'), "State must be start with confirmed to confirming Delivery Order. Current State: %s" % self.state
            products = self.move_lines.mapped('product_id')
            current_qty = {}

            self._fetch_sequence()
            # After create Doc Name, will be created PO internal
            self.with_context(force_request=1)._procure_inter_company()
            self._assign_interco_move_line_availability()
            self.state = 'plant-confirmed'
            validating = self.button_validate()

            if type(validating) == dict:
                res_model = validating.get('res_model')
                if res_model == 'stock.immediate.transfer':
                    print('>>> 1...')
                    res_id = validating.get('res_id')
                    Wizard = self.env['stock.immediate.transfer'].browse(
                        res_id)
                    Wizard.process()  # process if wizard showed
                elif res_model == 'stock.overprocessed.transfer':
                    print('>>> 2...')
                    raise ValidationError(_("Raise Overprocessed To Receive Qty on Validating Receive Order %s!") % (
                        picking.mapped('display_name')))
                elif res_model == 'stock.backorder.confirmation':
                    print('>>> 3...')
                    res_id = validating.get('res_id')
                    Wizard = self.env['stock.backorder.confirmation'].browse(
                        res_id)
                    # process if wizard showed
                    Wizard.with_context(
                        force_validating_interco_lot=True).process()

    def btn_plant_refuse(self):
        self.is_locked = False
        self.warehouse_plant_id = False
        self.plant_id = False
        self.message_post(body=_('Document Refused'))

    @api.model
    def _get_active_warehouses_in_all_company(self):
        return self.env['stock.warehouse'].with_user(1).search([('active', '=', True)])

    def _inverse_plant(self):
        warehouses = self._get_active_warehouses_in_all_company()
        for rec in self:
            res = {}
            plant_id = rec.plant_id.id

            if rec.plant_id.id and not rec.warehouse_plant_id.id:
                warehouse_plant_id = rec.plant_id.id
                wh_in_company = warehouses.filtered(
                    lambda r: r.company_id.id == rec.plant_id.id)
                # if  warehouse_plant_id not filed
                if not rec.warehouse_plant_id.id:
                    # only auto filled when result lenght == 1 if more than 1 user must select from ui
                    if len(wh_in_company):
                        if len(wh_in_company) == 1:
                            warehouse_plant_id = wh_in_company.id
                            res.update({
                                'warehouse_plant_id': warehouse_plant_id
                            })
            res.update({
                'plant_id': plant_id
            })
            rec.update(res)
        return True

    @api.depends('group_id.sale_id')
    def _compute_picking_sale_intercompany(self):
        warehouses = self._get_active_warehouses_in_all_company()
        for rec in self:
            wh_in_company = warehouses.filtered(
                lambda r: r.company_id.id == rec.sale_id.plant_id.id)
            if len(wh_in_company) == 1:
                wh_in_company = wh_in_company
            elif len(wh_in_company) > 1:
                wh_in_company = self.env['stock.warehouse']
            res = {
                'plant_id': rec.sale_id.plant_id.id,
                'warehouse_plant_id': wh_in_company.id,
                'sales_team_id': rec.sale_id.team_id.id,
                'sale_agreement_id': rec.sale_id.sale_agreement_id.id,
                'order_pickup_method_id': rec.sale_id.order_pickup_method_id.id,
            }
            rec.update(res)

    def printing_slip_constrains(self):
        self.print_count += 1
        if self.print_count > 1:
            self.allow_print = False

    def btn_allow_print(self):
        self.allow_print = True

    def _create_backorder(self):
        """ This method is called when the user chose to create a backorder. It will create a new
        picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
        """
        res = super(StockPicking, self)._create_backorder()
        res.update({
            'plant_id': res.plant_id.id,
            'warehouse_plant_id': res.warehouse_plant_id.id,
            'is_locked': False
        })
        res.do_unreserve()
        return res

    # def button_validate(self):
    # 	self.ensure_one()
    # 	if not self.move_lines and not self.move_line_ids:
    # 		raise UserError(_('Please add some items to move.'))

    # 	# If no lots when needed, raise error
    # 	picking_type = self.picking_type_id
    # 	precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    # 	no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))

    # 	no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
    # 	if no_reserved_quantities and no_quantities_done:
    # 		raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

    # 	if picking_type.use_create_lots or picking_type.use_existing_lots:
    # 		lines_to_check = self.move_line_ids
    # 		if not no_quantities_done:
    # 			lines_to_check = lines_to_check.filtered(
    # 				lambda line: float_compare(line.qty_done, 0,
    # 										   precision_rounding=line.product_uom_id.rounding)
    # 			)

    # 		for line in lines_to_check:
    # 			product = line.product_id
    # 			if product and product.tracking != 'none':
    # 				if not line.lot_name and not line.lot_id:
    # 					raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

    # 	# Propose to use the sms mechanism the first time a delivery
    # 	# picking is validated. Whatever the user's decision (use it or not),
    # 	# the method button_validate is called again (except if it's cancel),
    # 	# so the checks are made twice in that case, but the flow is not broken
    # 	sms_confirmation = self._check_sms_confirmation_popup()
    # 	if sms_confirmation:
    # 		return sms_confirmation

    # 	if no_quantities_done:
    # 		view = self.env.ref('stock.view_immediate_transfer')
    # 		wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
    # 		return {
    # 			'name': _('Immediate Transfer?'),
    # 			'type': 'ir.actions.act_window',
    # 			'view_mode': 'form',
    # 			'res_model': 'stock.immediate.transfer',
    # 			'views': [(view.id, 'form')],
    # 			'view_id': view.id,
    # 			'target': 'new',
    # 			'res_id': wiz.id,
    # 			'context': self.env.context,
    # 		}

    # 	if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
    # 		view = self.env.ref('stock.view_overprocessed_transfer')
    # 		wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
    # 		return {
    # 			'type': 'ir.actions.act_window',
    # 			'view_mode': 'form',
    # 			'res_model': 'stock.overprocessed.transfer',
    # 			'views': [(view.id, 'form')],
    # 			'view_id': view.id,
    # 			'target': 'new',
    # 			'res_id': wiz.id,
    # 			'context': self.env.context,
    # 		}

    # 	# Check backorder should check for other barcodes
    # 	if self._check_backorder():
    # 		return self.action_generate_backorder_wizard()
    # 	self.action_done()
    # 	return


class StockDeliverySlip(models.AbstractModel):
    _name = 'report.sanqua_print.report_deliveryslip'
    _description = 'Report Surat Jalan'

    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        for picking in docs:
            if picking.state != 'done':
                raise UserError(
                    _("You only can print this document in state 'DONE'"))
            if not picking.allow_print:
                raise UserError(
                    _("You are already print this document.\nPlease ask your Stock Manager to 'Allow Print' this document"))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'stock.picking',
            'docs': docs,
        }
