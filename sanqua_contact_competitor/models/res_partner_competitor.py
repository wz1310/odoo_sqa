from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResPartnerCompetitor(models.Model):
    _name = 'res.partner.competitor'
    _description = 'Partner Competitor'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Contact',required=False, track_visibility='onchange')
    brand = fields.Char(string='Brand',required=True, track_visibility='onchange')
    product_volume = fields.Char(string='Prod. Vol.',required=True, track_visibility='onchange')
    description = fields.Char(string='Description',required=True, track_visibility='onchange')
    qty = fields.Float(string='Qty', digits="Product Unit of Measure", track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id, track_visibility='onchange')
    base_price = fields.Monetary(string='Base Price', track_visibility='onchange')
    double_price = fields.Monetary(string='Double Price', track_visibility='onchange')
    medium_truck_price = fields.Monetary(string='Engkel Price', track_visibility='onchange')
    retail_price = fields.Monetary(string='Retail Price', track_visibility='onchange')
    warehouse_capacity = fields.Float(string='WH Capacity', digits="Volume", track_visibility='onchange')
    company_id = fields.Many2one('res.company', related='partner_id.company_id',string='Company', track_visibility='onchange')
    competitor_name = fields.Char(compute='_compute_competitor_name', inverse='inverse_competitor',store=True, track_visibility='onchange')
    date = fields.Date(string='Date', track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='State',default='draft', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id, track_visibility='onchange')
    sales_id = fields.Many2one('res.partner','Sales')
    external_customer = fields.Char('External Customer')


    @api.depends('partner_id')
    def _compute_competitor_name(self):
        for rec in self:
            rec.competitor_name = rec.partner_id.display_name if rec.partner_id else False

    def inverse_competitor(self):
        for rec in self:
            return True

    def btn_post(self):
        self.ensure_one()
        self.state = 'done'

    def name_get(self):
        result = []
        for rec in self:
            partner = rec.partner_id.name or ''
            brand = rec.brand or ''
            result.append((rec.id, partner + ' - ' + brand))
        return result

    def unlink(self):
        not_draft = self.filtered(lambda r:r.state!='draft')
        if len(not_draft):
            raise UserError(_("Couldn't deleting competitor docs %s") % (", ".join(not_draft.mapped('display_name')), ))
        
        return super(ResPartnerCompetitor, self).unlink()