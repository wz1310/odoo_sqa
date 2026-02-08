# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CollectionActivity(models.Model):
    _inherit = 'collection.activity'

    settlement_ids = fields.One2many('settlement.request', 'activity_id', string='Settlement Request')
    settlement_ids_count = fields.Integer(compute="_compute_settlement_ids_count", string="Settlement Count")
    

    def open_settlement_request_form(self):
        self.ensure_one()
        form = self.env.ref('settlement_request.settlement_request_view_form')
        context = dict(self.env.context or {})
        context.update({'default_activity_id':self.id}) #uncomment if need append context
        res = {
            'name': "%s - %s" % (_('Create Settlement Request from Collection'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'settlement.request',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def open_settlement(self):
        view_id = self.env.ref('settlement_request.settlement_request_view_tree').id
        return {
            'name':'Settlement Request',
            'view_mode': 'tree,form',
            'view_ids':[(False, 'tree'),(False, 'form')],
            'res_model':'settlement.request',
            'type':'ir.actions.act_window',
            'target':'current',
            'domain':[('activity_id','=',self.id)],
            'context': {
                'default_activity_id':self.id
            }
               }

    @api.depends('settlement_ids')
    def _compute_settlement_ids_count(self):
        for rec in self.sudo():
            rec.settlement_ids_count = len(rec.settlement_ids)