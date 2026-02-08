""" Rencana Pembelian Material """
from odoo import models, fields, _ , api
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class MrpRpm(models.Model):
    """ Define Rencana Pembelian Material """

    _name = 'mrp.rpm'
    _description = 'Mrp RPM'
    _inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', 'Company',readonly=True, required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(default='/', copy=False)
    rpb_id = fields.Many2one('mrp.rpb','RPB',domain=[('is_active','=',True)])
    rpb_bulan_berjalan = fields.Many2one('mrp.rpb','RPB Bulan Berjalan',domain=[('is_active','=',True)])
    date = fields.Date('Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
        ('done', 'Done')
    ], string='State',default='draft',required=True)
    mrp_rpm_line = fields.One2many('mrp.rpm.line','rpm_id','Lines')
    pr_count = fields.Integer(compute='_compute_pr', string='RPM count', default=0, store=True)
    pr_ids = fields.One2many('purchase.request', 'rpm_id', string='RPM', copy=False, store=True)


    @api.depends('pr_ids', 'pr_ids.rpm_id')
    def _compute_pr(self):
        print("RPMMMMMMMMMMMMMMMMMMMMMM")
        for record in self:
            record.pr_count = len(record.pr_ids)

    @api.model
    def create(self, values):
        res = super(MrpRpm, self).create(values)
        sequence = self.env.ref('mrp_shift.sequence_mrp_rpm')

        if sequence:
            name = self.env['ir.sequence'].next_by_code(sequence.code)
            res.name = name
        return res




    def update_data(self):
        rpm_line_obj = self.env['mrp.rpm.line']
        self.ensure_one()
        line_record_ids = self.env['mrp.rpm.line'].search([('rpm_id','=',self.id)])
        line_record_ids.sudo().unlink()
        #rpb_id = self.env['mrp.rpb'].search([('date_start','<=',self.date),('date_end','>=',self.date),('is_active','=',True)])
        rpb_id = self.env['mrp.rpb'].search([('id','=',self.rpb_bulan_berjalan.id)])
        if len(rpb_id) > 1:
            print ("TEST")
        else:
            rph_ids = self.env['mrp.rph'].search([('rpb_id','=',rpb_id.id),
                                                  ('company_id','=',self.company_id.id),
                                                  ('state','=','approved')])
            if rph_ids:
                for each in rph_ids:
                    total_qty = 0
                    next_month_rph = self.env['mrp.rph'].search([('rpb_id','=',self.rpb_id.id),
                                                                 ('product_id','=',each.product_id.id),
                                                                 ('company_id','=',self.company_id.id),
                                                                 ('state','=','approved')])
                    current_move_finished_production_ids = self.env['stock.move'].search([('product_id','=',each.product_id.id),
                                                                                          ('date_expected','>=',rpb_id.date_start),
                                                                                          ('date_expected','<=',rpb_id.date_end),
                                                                                          ('company_id','=',self.company_id.id),
                                                                                          ('location_id.usage','=','production'),
                                                                                          ('state','=','done')])
                    for datas in current_move_finished_production_ids:
                        total_qty += datas.product_uom_qty
                    bom_id = self.env['mrp.bom'].search([('product_tmpl_id','=',each.product_id.product_tmpl_id.id),
                                                          ('company_id','=',self.company_id.id),
                                                          ('type','=','normal')])
                    if not bom_id:
                        raise ValidationError('RPH %s, SKU doesnt have Bill Of Material %s' % (each.name, each.product_id.name))

                    total_qty_planning = (each.total_qty_by_manager - total_qty) + next_month_rph.total_qty_by_manager 
                    vals = {
                        'rpm_id' : self.id,
                        'product_id' : each.product_id.id,
                        'current_month_production_plan' : each.total_qty_by_manager,
                        'next_month_production_plan' : next_month_rph.total_qty_by_manager,
                        'current_month_realization_production' : total_qty,
                        'current_month_not_realization' : each.total_qty_by_manager - total_qty,
                        'bom_id' : bom_id[0].id,
                        #'qty_bom' : bom_id[0].product_qty,
                        'qty_bom' :  total_qty_planning,
                        'qty_bom_uom' : bom_id[0].product_uom_id.id,
                    }
                    rpm_line_id = rpm_line_obj.create(vals)

                    for detail in bom_id[0]:
                        for bom_line in detail.bom_line_ids:
                            #qty_request = ((bom_line.product_qty / detail.product_qty) * total_qty_planning) - bom_line.product_id.qty_available - bom_line.product_id.incoming_qty
                            qty_request = bom_line.product_id.qty_available + bom_line.product_id.incoming_qty - ((bom_line.product_qty / detail.product_qty) * total_qty_planning)
                            vals_material = {
                                'line_id' : rpm_line_id.id,
                                'product_id' : bom_line.product_id.id,
                                'uom_id': bom_line.product_uom_id.id,
                                'qty_bom': (bom_line.product_qty / detail.product_qty) * total_qty_planning,
                                'qty_on_hand': bom_line.product_id.qty_available,
                                'qty_outstanding_po': bom_line.product_id.incoming_qty,
                                'qty_request' : qty_request,
                                'tolerance' : (qty_request * 20) / 100,
                                'qty_to_pr' : qty_request + ((qty_request * 20)/100),
                            }
                            rpm_line_raw_material_id = self.env['mrp.rpm.line.raw.material'].create(vals_material)
            else:
                raise ValidationError('No Data Updated')


    def button_confirm(self):
        self.checking_approval_matrix(add_approver_as_follower=True, data={'state':'waiting_approval'})
        return self.write({
            'state':'waiting_approval'
        })

    def button_approve(self):
        self.approving_matrix(post_action='action_approve')

    def action_approve(self):
        return self.write({
            'state' : 'approved'
        })

    def button_reject(self):
        self.rejecting_matrix()
        self.state = 'reject'

    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Rencana Pembelian Material</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'mrp.rpm'})
        res = {
            'name': "%s - %s" % (_('Rejecting Rencana Pembelian Material'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def button_done(self):
        return self.write({
            'state' : 'done'
        })

    def button_set_draft(self):
        return self.write({
            'state':'draft'
        })

    def create_pr(self):
        self.ensure_one()
        vals = {
                'user_id': self.env.user.id,
                'name': False,
                'rpm_id': self.id,
                'company_id': self.company_id.id,
                }
        pr_id = self.env['purchase.request'].create(vals)
        for each in self.mrp_rpm_line:
            for detail in each.line_detail:
                line_vals = {
                    'purchase_request_id' : pr_id.id,
                    'product_id' : detail.product_id.id,
                    'uom_id' : detail.uom_id.id,
                    'qty': detail.qty_to_pr,
                }
                pr_line_id = self.env['purchase.request.line'].create(line_vals)
        # for each in self.mrp_rpm_line:
        #     for detail in each.line_detail:
        #         vals = {
        #             'user_id': self.env.user.id,
        #             'name': False,
        #             'rpm_id': self.id,
        #             'company_id': self.company_id.id,
        #             'line_ids': [(0, 0, {
        #                             'product_id': detail.product_id.id,
        #                             'qty': detail.qty_to_pr,
        #                             'uom_id': detail.uom_id.id,
        #                         })]
        #         }
        #         pr_id = self.env['purchase.request'].create(vals)
        #         return True

    def action_view_pr(self):
        self.ensure_one()
        action = self.env.ref('purchase_request.purchase_request_action').read()[0]
        pr_ids = self.mapped('pr_ids')
        if len(pr_ids) > 1:
            action['domain'] = [('id', 'in', pr_ids.ids)]
        elif pr_ids:
            form_view = [(self.env.ref('purchase_request.purchase_request_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pr_ids.id
        return action


class MrpRpmLine(models.Model):
    _name = 'mrp.rpm.line'
    _description = 'RPM Line'



    rpm_id = fields.Many2one('mrp.rpm','RPM')
    product_id = fields.Many2one('product.product','Product')
    bom_id = fields.Many2one('mrp.bom','Bill of Material')
    qty_bom = fields.Float('Qty Needed')
    qty_bom_uom = fields.Many2one('uom.uom','Unit of Measure')
    current_month_production_plan = fields.Float('Current Month Production Plan')
    current_month_realization_production = fields.Float('Current Month Relization Production')
    current_month_not_realization = fields.Float('Current Month Not Realization')
    next_month_production_plan = fields.Float('Next Month Production Plan')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
        ('done', 'Done')
    ], string='State',default='draft',required=True, related="rpm_id.state")
    line_detail = fields.One2many('mrp.rpm.line.raw.material','line_id')


    # def unlink(self):
    #     for rec in self:
    #         if rec.rpm_id.state !-:
    #             raise ValidationError(_("Can't deleting record!"))


class MrpRpmLineRawMaterial(models.Model):
    _name = 'mrp.rpm.line.raw.material'
    _description = 'RPM Line Raw Material'



    line_id = fields.Many2one('mrp.rpm.line','RPM Line')
    product_id = fields.Many2one('product.product','Product')
    uom_id = fields.Many2one('uom.uom','UoM')
    qty_bom = fields.Float('Qty BoM')
    qty_on_hand = fields.Float('Qty on Hand')
    qty_outstanding_po = fields.Float('OS PO')
    tolerance = fields.Float('Tolerance')
    qty_request = fields.Float('Qty Request')
    qty_to_pr = fields.Float('Qty to PR')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
        ('done', 'Done')
    ], string='State',default='draft',required=True, related="line_id.state")

    
