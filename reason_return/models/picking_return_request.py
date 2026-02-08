# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

    
class PickingReturnRequest(models.Model):
    _name = "picking.return.request"
    _inherit = ['mail.thread', 'mail.activity.mixin', "approval.matrix.mixin"]
    _description = "Form Return Barang"

    def _domain_sale_id(self):
        order_ids = self.env['sale.order'].search([('order_promotion_id','=',False),('state','=','done'),('sale_truck_id','=',False)])
        sale_ids = order_ids.filtered(lambda r: r.picking_ids and any(r.picking_ids.mapped(lambda p: p.state == 'done')))
        return [('id','in',sale_ids.ids)]

    name = fields.Char(string='Name', track_visibility="onchange", unique=True, required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    user_id = fields.Many2one('res.users', track_visibility="onchange", string="Salesman", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', track_visibility="onchange", string="Company", required=True, default=lambda self: self.env.company.id, domain=False)
    
    sale_id = fields.Many2one('sale.order', track_visibility="onchange", string="SO Number", required=True, default=False, domain=_domain_sale_id)
    partner_id = fields.Many2one('res.partner',related='sale_id.partner_id', string='Customer')
    sale_company_id = fields.Many2one('res.company', compute="_compute_sale", store=True)
    team_id = fields.Many2one('crm.team', track_visibility="onchange", string="Division", required=True, default=False, domain=False)
    reason = fields.Text('Reason', required=True, track_visibility="onchange")

    picking_id = fields.Many2one('stock.picking', string="Delivery Number", domain=[('picking_type_code','=','outgoing'),('state','=','done'),('is_return_picking','=',False)], track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('need approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft', track_visibility="onchange")
    return_type = fields.Selection([
        ('delivery', 'Delivery'),
        ('after_sales', 'After Sale'),
        ], string='Return Type', required=True, default="after_sales", invisible=True, track_visibility="onchange")
    item_ids = fields.One2many('picking.return.request.line', 'request_id', string="Item Return")
    line_ids = fields.One2many('sale.order.line', compute="_compute_sale")
    return_picking_id = fields.Many2one('stock.picking', string="Returned Picking", readonly=True, track_visibility="onchange")
    total_qty_return = fields.Float('Total Qty Returned', compute="_get_total_qty_return", store=True)



    @api.depends('sale_id','picking_id','item_ids')
    def _get_total_qty_return(self):
        for rec in self:
            total = 0.0
            for each in rec.item_ids:
                total += each.qty
            rec.total_qty_return = total


    @api.depends('sale_id')
    def _compute_sale(self):
        for rec in self:
            res = {
                'sale_company_id':rec.sudo().sale_id.company_id.id if rec.sudo().sale_id.id else False,
                'line_ids':rec.sudo().sale_id.order_line
            }
            rec.update(res)

    def btn_submit(self):
        self.checking_approval_matrix()
        self.state = 'need approval'

    def _create_return(self):
        Wiz = self.env['stock.return.picking']
        # _logger.info((Wiz._fields))
        defaultGet = Wiz.with_context(dict(active_id=self.picking_id.id,active_model='stock.picking')).default_get(['product_return_moves','picking_id','move_dest_exists','original_location_id','parent_location_id','company_id','location_id'])
        
        newWiz = Wiz.new(defaultGet)
        newWiz._onchange_picking_id()
        
        new_data = newWiz._convert_to_write({name: newWiz[name] for name in newWiz._cache})

        new_data.update({
            'reason':self.reason,
            'return_type':self.return_type,
        })
        
        created_obj = Wiz.create(new_data)

        new_picking = created_obj.sudo().create_returns()
        if type(new_picking) == dict:
            return_picking_id = new_picking.get('res_id')
            self.return_picking_id = return_picking_id
            self._confirm_picking(return_picking_id)
            return new_picking
        
        raise UserError(_("Failed to create new returned picking"))

    def _confirm_picking(self,picking_id):
        picking_id = self.env['stock.picking'].browse(picking_id)
        picking_id.return_reason = self.reason
        picking_id.return_type = self.return_type
        for picking in picking_id.move_line_ids:
            line_id = self.item_ids.filtered(lambda r: r.product_id == picking.product_id)
            picking.lot_id = line_id.lot_id.id
            picking.qty_done = line_id.qty
        # picking_id.button_validate()


    def btn_approve(self):
        self.approving_matrix()
        if self.approved:
            self._create_return()
            self.state = 'approved'

    def btn_draft(self):
        self.state = 'draft'

    def btn_reject(self):
        self.state = 'rejected'
        self.rejecting_matrix()

    @api.onchange('sale_id')
    def _onchange_sale_id(self):
        list_pick_id = []
        list_line_id = []
        res = {}
        if self.sale_id.id:
            self.picking_id = False
            if len(self.sale_id.picking_ids.filtered(lambda r:r.picking_type_code=='outgoing'))==1:
                picking_id = self.sale_id.picking_ids[0].id
            else:
                picking_id = False
            self.update({
                'picking_id':picking_id,
                'team_id':self.sale_id.team_id.id,
            })
            res['domain'] = {'picking_id':[('id','in',self.sale_id.picking_ids.filtered(lambda r: r.is_return_picking == False).ids),('picking_type_code','=','outgoing'),('state','=','done')]}
        else:
            self.update({'picking_id':False})
        return res

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('picking.return.request')
        result = super(PickingReturnRequest, self).create(vals)
        return result
