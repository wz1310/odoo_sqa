# """ Rencana Pembelian Material """
# from odoo import models, fields, _ , api
# from datetime import datetime


# class MrpRph(models.Model):
#     """ Define Rencana Pembelian Material """

#     _name = 'mrp.rpm'
#     _description = 'Mrp RPM'
#     _inherit = ["approval.matrix.mixin",'mail.thread', 'mail.activity.mixin']

#     company_id = fields.Many2one('res.company', 'Company',readonly=True, required=True, index=True, default=lambda self: self.env.company)
#     date_start = fields.Date(default=fields.Datetime.now)
#     date_end = fields.Date()
#     name = fields.Char(default='/', copy=False)
#     material_id = fields.Many2one('product.product')
#     product_id = fields.Many2one('product.product')
#     product_uom = fields.Many2one('uom.uom', string="Uom")
#     qty = fields.Float()
#     rph_id = fields.Many2one('mrp.rph', string="RPH")
#     # pbbh_idzz = fields.Many2one('mrp.pbbh', string="PBBH")
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('waiting_approval', 'Waiting Approval'),
#         ('approved', 'Approved'),
#         ('reject', 'Rejected'),
#         ('done', 'Done')
#     ], string='State',default='draft',required=True)
#     picking_count = fields.Integer(compute='_compute_picking', string='Picking count', default=0, store=True)
#     picking_ids = fields.One2many('stock.picking', 'mrp_pbbh_id', string='Internal Transfer', copy=False, store=True)
    
#     pr_count = fields.Integer(compute='_compute_pr', string='RPM count', default=0, store=True)
#     pr_ids = fields.One2many('purchase.request', 'rpm_id', string='RPM', copy=False, store=True)

#     @api.depends('picking_ids', 'picking_ids.mrp_pbbh_id')
#     def _compute_picking(self):
#         for record in self:
#             record.picking_count = 0

#     @api.depends('pr_ids', 'pr_ids.rpm_id')
#     def _compute_pr(self):
#         for record in self:
#             record.pr_count = len(record.pr_ids)

#     @api.model
#     def create(self, values):
#         res = super(MrpRph, self).create(values)
#         sequence = self.env.ref('mrp_shift.sequence_mrp_rpm')

#         if sequence:
#             name = self.env['ir.sequence'].next_by_code(sequence.code)
#             res.name = name
#         return res

#     def create_pr(self):
#         self.ensure_one()
#         values = {
#             'user_id': self.env.user.id,
#             'name': False,
#             'rpm_id': self.id,
#             'company_id': self.company_id.id,
#             'line_ids': [(0, 0, {
#                 'product_id': self.material_id.id,
#                 'qty': self.qty,
#                 'uom_id': self.product_uom.id
#             })]
#         }
#         pr_id = self.env['purchase.request'].create(values)
#         return True

#     def action_view_pr(self):
#         self.ensure_one()
#         action = self.env.ref('purchase_request.purchase_request_action').read()[0]
#         pr_ids = self.mapped('pr_ids')
#         if len(pr_ids) > 1:
#             action['domain'] = [('id', 'in', pr_ids.ids)]
#         elif pr_ids:
#             form_view = [(self.env.ref('purchase_request.purchase_request_view_form').id, 'form')]
#             if 'views' in action:
#                 action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
#             else:
#                 action['views'] = form_view
#             action['res_id'] = pr_ids.id
#         return action

#     def action_view_receipt(self):
#         return

#     def button_confirm(self):
#         self.checking_approval_matrix(add_approver_as_follower=True, data={'state':'waiting_approval'})
#         return self.write({
#             'state':'waiting_approval'
#         })

#     def button_approve(self):
#         self.approving_matrix(post_action='action_approve')

#     def action_approve(self):
#         return self.write({
#             'state' : 'approved'
#         })

#     def button_reject(self):
#         self.rejecting_matrix()
#         self.state = 'reject'

#     def open_reject_message_wizard(self):
#         self.ensure_one()
        
#         form = self.env.ref('approval_matrix.message_post_wizard_form_view')
#         context = dict(self.env.context or {})
#         context.update({'default_prefix_message':"<h4>Rejecting Rencana Pembelian Material</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
#         context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'mrp.rpm'})
#         res = {
#             'name': "%s - %s" % (_('Rejecting Rencana Pembelian Material'), self.name),
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'message.post.wizard',
#             'view_id': form.id,
#             'type': 'ir.actions.act_window',
#             'context': context,
#             'target': 'new'
#         }
#         return res

#     def button_done(self):
#         return self.write({
#             'state' : 'done'
#         })

#     def button_set_draft(self):
#         return self.write({
#             'state':'draft'
#         })
