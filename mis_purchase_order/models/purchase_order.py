# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import timedelta
import re
from odoo.tools.float_utils import float_compare

import logging
_logger = logging.getLogger(__name__)


class MessagePostWiz(models.TransientModel):
    _name = 'message.post.wiz'

    messages = fields.Text(required=False)

    def confirm(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        if not res_id or not model:
            raise UserError("Require to get context active id and active model!")
        
        if not self.messages:
            raise ValidationError(_("Please Fill Message first"))
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)

        if len(Record):
            
            # msgs = "%s%s" % (self.prefix_message+"<br/>" if self.prefix_message else "", self.messages)
            msgs = []            
            if self.messages:
                msgs.append(self.messages)

            msgs = "<br/>".join(msgs)
            Record.message_post(body=msgs)
            Record.update({'close_reason':msgs,'status_po':'close'})
            picking_ids = self.env['stock.picking'].search([('purchase_id','=',res_id),('state','not in',['cancel','done'])])
            for picking in picking_ids:
                picking.action_cancel()
            Record.update({'state':'done'})
            Record.update({'status_po':'close'})


class MessageOpenWiz(models.TransientModel):
    _name = 'message.open.wiz'

    messages = fields.Text(required=False)

    def confirm(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        if not res_id or not model:
            raise UserError("Require to get context active id and active model!")
        
        if not self.messages:
            raise ValidationError(_("Please Fill Message first"))
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)

        if len(Record):
            
            # msgs = "%s%s" % (self.prefix_message+"<br/>" if self.prefix_message else "", self.messages)
            msgs = []            
            if self.messages:
                msgs.append(self.messages)

            msgs = "<br/>".join(msgs)
            Record.message_post(body=msgs)
            Record.update({'open_reason':msgs,'state':'purchase','status_po':'open'})
            Record._create_picking()

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    close_reason = fields.Text(string='Reason')
    open_reason = fields.Text(string='Open reason')

    def closed_picking_new(self):
        picking_ids = self.env['stock.picking'].search([('purchase_id','=',self.id),('state','not in',['cancel','done'])])
        for picking in picking_ids:
            picking.action_cancel()
        self.close_reason = "Auto close by PO received"
        self.state = 'done'
    
    def btn_approve(self, force=False):
        res = super(PurchaseOrderInherit, self).btn_approve()
        if self.request_id:
            self.request_id._cek_close()
        return res

    @api.depends('order_line.move_ids.returned_move_ids',
                'order_line.move_ids.state',
                'order_line.move_ids.picking_id')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)
            id_order = False
            try:
                id_order = self.id
            except:
                id_order = self._origin.id
            idsk = self.env['stock.picking'].search([('purchase_id','=', id_order),('state','not in',['done','cancel'])])
            order.sisa_picking = len(idsk)
            if len(idsk) == 0 and order.status_po == 'open':
                order.status_po = 'done'
            elif len(idsk) > 0:
                order.status_po = 'open'

        def button_confirm(self):
            res = super(PurchaseOrderInherit,self).button_confirm()
            if not len(self.order_line.mapped('id'))>0:
                raise UserError(_('Product in order lines can not be empty..'))
            return res
        
    def btn_close(self):
        self.ensure_one()
        
        form = self.env.ref('mis_purchase_order.message_post_wiz_form_view')
        context = dict(self.env.context or {})
        # context.update({'default_prefix_message':"<h4>Rejecting Purchase Order</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'active_model':'purchase.order'
            })
        res = {
            'name': "%s - %s" % (_('Rejecting Purchase'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wiz',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res
        
    def btn_open(self):
        self.ensure_one()
        akses =  self.approval_ids.approver_ids.ids
        user_crn = self.env.user.id
        if user_crn not in akses:
            raise UserError(_('You are not allowed to cancel this \nplease contact PO approvers'))        
        form = self.env.ref('mis_purchase_order.message_open_wiz_form_view')
        context = dict(self.env.context or {})
        # context.update({'default_prefix_message':"<h4>Rejecting Purchase Order</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'active_model':'purchase.order'
            })
        res = {
            'name': "%s - %s" % (_('Open Purchase'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.open.wiz',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def copy(self, default=None):
        ctx = dict(self.env.context)
        ctx.pop('default_product_id', None)
        self = self.with_context(ctx)
        if self.request_id.status_pr == 'close':
            raise UserError(_('Cannot Create PO because status pr in Purchase Request closed'))
        for x in self.request_id.line_ids.filtered(lambda x:x.product_id.id in [y.product_id.id
            for y in self.order_line]):
            if x.qty_released >= x.qty:
                raise UserError(_('Cannot Create Product Qty of PO greather than Qty of Purchase Request : %s')%(x.product_id.name))
                # print("LINE PRODUCT",x.product_id.name)
        new_po = super(PurchaseOrderInherit, self).copy(default=default)
        new_po.status_po = ''
        for line in new_po.order_line:
            line.product_qty = 0
            if new_po.date_planned and not line.display_type:
                line.date_planned = new_po.date_planned
            elif line.product_id:
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id, quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(), uom_id=line.product_uom)
                line.date_planned = line._get_date_planned(seller)
        return new_po

    @api.constrains('validity_so_date')
    def check_validity(self):
        print("self.env.context",self.env.context)
        if self.validity_so_date:
            if self.validity_so_date < self.date_order.date():
                raise UserError(_('Validity date cannot be smaller from order date..'))

    def _cron_close_po(self):
        # date = self.date_order_mask
        now_date = fields.date.today()
        query="""
        SELECT po.id id_po,sp.id id_sp
        FROM
        purchase_order po
        LEFT JOIN purchase_order_line po_line ON po_line.order_id = po.id
        LEFT JOIN stock_move sm ON sm.purchase_line_id = po_line.id
        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
        WHERE
        po.validity_so_date :: DATE = CURRENT_DATE :: DATE
        AND po.state NOT IN ( 'done', 'cancel' )
        AND sp.state NOT IN ( 'done', 'cancel' )
        AND sp.origin NOT LIKE %s
        """
        self.env.cr.execute(query,('Return %',))
        result = self.env.cr.dictfetchall()
        if result:
            find_po = [x['id_po'] for x in result]
            find_sp = [x['id_sp'] for x in result]
            self.env.cr.execute("""
                UPDATE
                purchase_order
                SET
                state='done',
                status_po = 'close',
                close_reason = 'Closed by expired date'
                WHERE
                id in %s""",(tuple(find_po),))
            self.env.cr.execute("""
                UPDATE
                stock_picking
                SET
                state='cancel'
                WHERE
                id in %s""",(tuple(find_sp),))

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'
    
    detail_project = fields.Many2one('detail.project.po',string='Project')
    desc = fields.Text(string='Details')
    fpb_not = fields.Text()
    fpb_uom = fields.Many2one('uom.uom')

    def write(self,vals):
        # print("PRD QTY NOW",vals.get('product_qty'))
        # print("PRD QTY BEFORE",self.product_qty )
        # print("PRD QTY",vals.get('product_qty'))
        # print("PRD QTY PR",self.purchase_request_line_id.qty_released)
        if vals.get('product_qty'):
            fins = (self.purchase_request_line_id.qty_released - self.product_qty) + vals.get('product_qty')
            use = vals.get('product_qty') - ( fins - self.purchase_request_line_id.qty)
            # print("Prod qty",self.product_qty)
            # print("Use",use)
            # print("FINS",fins)
            # update rounding untuk nilai sisa pakai qty
            if round(fins,2) > self.purchase_request_line_id.qty:
                raise UserError(_('Cannot Create Product Qty of PO greather than Qty of Purchase Request : %s \nyou can use : %s of product qty')%(self.product_id.name, use))
        self._check_request_qty()
        self._check_request_product()
        return super(PurchaseOrderLineInherit,self).write(vals)

    def _prepare_stock_moves(self, picking):
        # rex = super(PurchaseOrderLineInherit,self)._prepare_stock_moves(picking)
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        for move in incoming_moves:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        description_picking = self.product_id.with_context(lang=self.order_id.dest_address_id.lang or self.env.user.lang)._get_description(self.order_id.picking_type_id)
        description_picking = self.name
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'propagate_date': self.propagate_date,
            'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
            'description_picking': description_picking,
            'propagate_cancel': self.propagate_cancel,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
            po_line_uom = self.product_uom
            quant_uom = self.product_id.uom_id
            product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
            template['product_uom_qty'] = product_uom_qty
            template['product_uom'] = product_uom.id
            res.append(template)
        return res


class DetailProjectPO(models.Model):
    _name = 'detail.project.po'

    name = fields.Char(strin="Name")
    company_id = fields.Many2one('res.company',string="Company")