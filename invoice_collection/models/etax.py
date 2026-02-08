from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class CollectionActivityETax(models.Model):
    _name = 'collection.activity.etax'

    activity_id = fields.Many2one('collection.activity', string='Activity',required=True)
    e_tax_id = fields.Many2one('etax.invoice', string='Tax Id',required=True)
    partner_id = fields.Many2one(related='e_tax_id.invoice_id.partner_id', string='Customer')
    doc_status = fields.Selection([
        ('on_accountant', 'On Accountant'),
        ('on_collector', 'On Collector'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], string='Doc. State',default='on_accountant',required=True)

    _sql_constraints = [
        ('activity_etax_uniq', 'unique (activity_id,e_tax_id)', 'Cannot fill same Collection and E-Tax !'),
    ]

    def post(self):
        if self.e_tax_id:
            self.e_tax_id.doc_status = 'on_collector'


class CollectionActivityETaxWizard(models.TransientModel):
    _name = 'collection.activity.etax.wizard'

    partner_id = fields.Many2one('res.partner', string='Customer')
    etax_ids = fields.Many2many('etax.invoice', string='Tax Invoices')

    def confirm(self):
        if self.etax_ids:
            vals = []
            activity_id = self._context.get('activity_id') if self._context.get('activity_id') else False
            for tax in self.etax_ids:
                data = {
                    'activity_id':activity_id,
                    'e_tax_id':tax.id
                }
                vals.append(data)
            self.env['collection.activity.etax'].create(vals)
        return {'type': 'ir.actions.act_window_close'}

class ETaxInvoice(models.Model):
    _inherit = 'etax.invoice'

    doc_status = fields.Selection([
        ('on_accountant', 'On Accountant'),
        ('on_collector', 'On Collector'),
        ('customer', 'Customer')
    ], string='Doc. State',default='on_accountant',required=True)