""" Rencana Produksi Harian """
from odoo import models, fields, _ , api
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class MrpRph(models.Model):
    """ Define Rencana Produksi Harian """

    _name = 'mrp.rph'
    _description = 'Mrp RPH'
    _inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 required=True, index=True, default=lambda self: self.env.company)
    create_date_rph = fields.Date(string='Create Date', required=True, copy=False,
                              default=fields.Datetime.now, track_visibility='onchange')
    mrp_rph_line_ids = fields.One2many('mrp.rph.line', 'mrp_rph_id', store=True)
    name = fields.Char(default='/', copy=False, track_visibility='onchange')
    product_ids = fields.Many2many('product.product')
    product_id = fields.Many2one('product.product', string="SKU", required=True,
                                 track_visibility='onchange')
    product_tmpl_id = fields.Many2one('product.template')
    rpb_id = fields.Many2one('mrp.rpb',string="RPB", required=True,
                             track_visibility='onchange')
    production_schedule_id = fields.Many2one('mrp.production.schedule')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled')
    ], string='State', track_visibility='onchange', default='draft', required=True)
    total_qty_by_manager = fields.Float(compute='_compute_total_qty',store=True, help="Total Qty set by manager", track_visibility='onchange')
    total_qty = fields.Float(compute='_compute_total_qty',store=True, track_visibility='onchange')
    bom_id = fields.Many2one('mrp.bom', 'Bill of Material', track_visibility='onchange')
    rph_count = fields.Integer(compute="_compute_rph", string='RPH Count', copy=False, default=0, store=True)
    pbbh_ids = fields.One2many('mrp.pbbh', 'rph_id', copy=False, store=True)

    @api.model
    def default_get(self, fields):
        """set product_ids based on production schedule"""
        res = super(MrpRph, self).default_get(fields)
        product_schedule_ids = self.env['mrp.production.schedule'].search([])
        res['product_ids'] = [(6, 0, product_schedule_ids.mapped('product_id').ids)]
        return res

    @api.depends('pbbh_ids')
    def _compute_rph(self):
        """count rph"""
        for data in self:
            data.rph_count = len(data.pbbh_ids)

    def action_view_tree_pbbh(self):
        '''
        This function returns an action that display existing PBBH
        '''
        action = self.env.ref('mrp_shift.mrp_pbbh_action')
        result = action.read()[0]
        result['context'] = {'default_rph_id': self.id}
        pbbh_ids = self.mapped('pbbh_ids')
        result['domain'] = "[('id','in', %s)]" % (pbbh_ids.ids)
        return result

    @api.onchange('product_id', 'rpb_id')
    def ochange_product_per_month(self):
        if self.product_id:
            self.product_tmpl_id = self.product_id.product_tmpl_id
            if self.product_tmpl_id:
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)], limit=1)
                # bom_id = self.product_tmpl_id.bom_ids[0] if self.product_tmpl_id.bom_ids else False
                self.bom_id = bom_id 
        if self.product_id and self.rpb_id:
            production_schedule_id = self.env['mrp.production.schedule'].search([('product_id', '=', self.product_id.id)], limit=1)
            self.production_schedule_id = production_schedule_id.id
            if production_schedule_id:
                new_lines = self.env['mrp.rph.line']
                forecast_ids = self.env['mrp.product.forecast'].search([('production_schedule_id', '=', production_schedule_id.id),
                                                                        ('date', '>=', self.rpb_id.date_start),
                                                                        ('date', '<=', self.rpb_id.date_end)])
                if forecast_ids:
                    for forecast_daily in forecast_ids.sorted('date'):
                        vals = {'date': forecast_daily.date,
                                'hari' : forecast_daily.date.strftime("%A"),
                                'mrp_product_forecast_id': forecast_daily.id,
                                'qty_forecast': forecast_daily.forecast_qty,
                                'qty':forecast_daily.forecast_qty}
                        new_lines += new_lines.new(vals)
                self.mrp_rph_line_ids = new_lines
            else:
                raise ValidationError('There is no production schedule for this proudct')

    @api.model
    def create(self, values):
        res = super(MrpRph, self).create(values)
        sequence = self.env.ref('mrp_shift.sequence_mrp_rph')
        if sequence:
            name = self.env['ir.sequence'].next_by_code(sequence.code)
            res.name = name
        return res

    
    
    def action_view_pbbh(self):
        action = self.env.ref('mrp_shift.mrp_pbbh_action')
        result = action.read()[0]
        result['context'] = {
            'default_rph_id': self.id,
            'default_product_id' : self.product_id.id,
            'default_product_tmpl_id' : self.product_tmpl_id.id,
            'default_bom_id' : self.bom_id.id,
        }
        res = self.env.ref('mrp_shift.mrp_pbbh_view_form', False)
        form_view = [(res and res.id or False, 'form')]
        if 'views' in result:
            result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            result['views'] = form_view
        return result
    
    def action_view_rpm(self):
        action = self.env.ref('mrp_shift.mrp_rpm_action')
        result = action.read()[0]
        res = self.env.ref('mrp_shift.mrp_rpm_view_form', False)
        form_view = [(res and res.id or False, 'form')]
        if 'views' in result:
            result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            result['views'] = form_view
        return result

    @api.depends('rpb_id', 'product_id', 'mrp_rph_line_ids', 'mrp_rph_line_ids.qty')
    def _compute_total_qty(self):
        for data in self:
            total = 0
            total_line = 0
            for line in data.mrp_rph_line_ids:
                total += line.qty_forecast
                total_line += line.qty
            self.total_qty_by_manager = total
            self.total_qty = total_line
            if total < total_line:
                raise ValidationError('You cannot set qty more than qty that already set by manager')


    def button_confirm(self):
        self.checking_approval_matrix(add_approver_as_follower=True, data={'state':'waiting_approval'})
        return self.write({
            'state':'waiting_approval'
        })

    def button_approve(self):
        self.approving_matrix(post_action='action_approve')

    def action_approve(self):
        for data in self.mrp_rph_line_ids:
            if data.qty != data.qty_forecast:
                data.mrp_product_forecast_id.forecast_qty = data.qty
        self.state = 'approved'

    def button_reject(self):
        self.rejecting_matrix()
        self.state = 'reject'
        for data in self.mrp_rph_line_ids:
            if data.qty != data.qty_forecast:
                data.mrp_product_forecast_id.forecast_qty = data.qty_forecast

    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Rencana Pembelian Harian</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'mrp.rph'})
        res = {
            'name': "%s - %s" % (_('Rejecting Rencana Pembelian Harian'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res
    
    def button_set_draft(self):
        return self.write({
            'state':'draft'
        })
    
    def button_cancel(self):
        return self.write({
            'state':'cancel'
        })

    @api.constrains('company_id', 'product_id', 'rpb_id', 'state')
    def constrains_forecast_product(self):
        for data in self:
            if data.product_id and data.rpb_id:
                mrp_rph_ids = self.env['mrp.rph'].search([('product_id', '=', data.product_id.id),
                                                            ('rpb_id', '=', data.rpb_id.id),
                                                            ('state', '!=', 'cancel'),
                                                            ('company_id','=',data.company_id.id)])
                if len(mrp_rph_ids) > 1:
                     raise ValidationError(_("You should cancel other RPH before you can create new RPH with same SKU and same RPB"))

    def unlink(self):
        for rph in self:
            if rph.state == 'approved':
                raise UserError(_('You cannot delete data that already Approved'))
            elif rph.state in ('waiting_approval', 'reject'):
                raise UserError(_('You only can delete data in state Draft or Cancel'))
        return super(MrpRph, self).unlink()
    
class MrpRphLine(models.Model):
    """ Define Rencana Produksi Harian Line """

    _name = 'mrp.rph.line'
    _description = 'Mrp RPH line'
    _order = 'date asc'

    mrp_rph_id = fields.Many2one('mrp.rph',ondelete='cascade',index=True)
    product_id = fields.Many2one('product.product','Product', related="mrp_rph_id.product_id", store=True)
    company_id = fields.Many2one('res.company',related="mrp_rph_id.company_id")
    date = fields.Date(string="Tgl",required=True)
    hari = fields.Char()
    mesin = fields.Char()
    qty = fields.Float()
    mrp_product_forecast_id = fields.Many2one('mrp.product.forecast')
    qty_forecast = fields.Float()
    qty_produce = fields.Float(string='Qty Realisasi',compute='_qty_realisasi')
    qty_produce_save = fields.Float(string='Qty Realisasi',compute='_qty_realisasi',store=True)
    qty_do = fields.Float(string='Qty Penjualan',compute='_qty_do')

    def _qty_realisasi(self):
        for this in self:
            mrp_ids = self.env['mrp.production'].search([('company_id','=', this.company_id.id),('product_id','=',this.product_id.id),('state','in',['done','waiting_qc','qc_done'])])
            mrp_ids = mrp_ids.filtered(lambda x : (x.date_planned_start + timedelta(hours=7)).date() == this.date)
            if mrp_ids:
                qty = sum(mrp_ids.mapped('product_qty'))
                this.qty_produce = qty
                this.qty_produce_save = qty
            else:
                this.qty_produce = 0
                this.qty_produce_save = 0
    
    def _qty_do(self):
        for this in self:
            mrp_ids = self.env['stock.move'].search([('company_id','=', this.company_id.id),
                                ('product_id','=',this.product_id.id),('state','=',['done']),
                                ('sale_line_id','!=',False)])
            mrp_ids = mrp_ids.filtered(lambda x : (x.date + timedelta(hours=7)).date() == this.date)
            if mrp_ids:
                qty = sum(mrp_ids.mapped('quantity_done'))
                this.qty_do = qty
                # this.qty_produce_save = qty
            else:
                this.qty_do = 0
                # this.qty_produce_save = 0
