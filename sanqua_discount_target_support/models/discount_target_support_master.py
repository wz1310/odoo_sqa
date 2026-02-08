from odoo import api, fields, models, _

class DiscountTargetSupportMixin(models.AbstractModel):
    _name = "discount.target.support.mixin"
    _description = "Discount Target Support Mixin"

    team_id = fields.Many2one('crm.team', string='Division', required=True)
    salesman_id = fields.Many2one('res.users', string='Salesman', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.user.company_id)


    @api.onchange('team_id')
    def _onchange_team_id(self):
        res = {
            'domain':{}
        }
        self.salesman_id = False
        if self.team_id.id:
            res['domain'].update({'salesman_id':[('id','in',self.team_id.sales_user_ids.ids)]})

        return res
        

class DiscountTargetSupportMaster(models.Model):
    _name = "discount.target.support.master"
    _description = "Discount Target Support Master"
    _inherit = ["discount.target.support.mixin"]

    name = fields.Char(string='No. Document')
    disc_type = fields.Selection([
        ('target', 'Target'),
        ('support', 'Support')
    ], string='Type',required=True)
    partner_ids = fields.Many2many('res.partner', string='Partner')
    disc_ids = fields.One2many('discount.target.support.customer', 'master_id', string='Discounts Customer')
    target_type = fields.Char(string='Target Type')
    allowed_partner_ids = fields.Many2many('res.partner', 'disc_support_master_allowed_partner_rel', 'disc_support_master_id', 'allowed_partner_id', string="Allowed Partner", compute="_compute_allowed_partner")

    @api.depends('salesman_id')
    def _compute_allowed_partner(self):
        for rec in self:
            allowed_customer_ids = self.env['partner.pricelist']
            if rec.salesman_id.id:
                allowed_customer_ids = self.env['partner.pricelist'].search([('team_id','=',self.team_id.id),('user_id','=',self.salesman_id.id)])
            rec.allowed_partner_ids = allowed_customer_ids.mapped('partner_id').ids
    

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('seq.discount.target.support.master.code')
        return super(DiscountTargetSupportMaster, self).create(vals_list)