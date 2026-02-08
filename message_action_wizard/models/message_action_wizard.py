# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MessageActionWizard(models.TransientModel):
    _name = 'message.action.wizard'
    _description = "Message Action Wizard"

    res_model_id = fields.Many2one('ir.model', 'Document Model', index=True, ondelete='cascade', required=True)
    res_model = fields.Char('Related Document Model', index=True, related='res_model_id.model', compute_sudo=True, store=True, readonly=True)
    res_id = fields.Many2oneReference(string='Related Document ID', index=True, required=True, model_field='res_model')
    messages = fields.Html(string='Message',required=True)
    action_confirm = fields.Char(string='Action')

    def btn_confirmed(self):
        doc = self.env[self.res_model].browse(self.res_id)
        if doc and self.action_confirm:
            getattr(doc, self.action_confirm)()