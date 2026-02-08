from odoo import api, fields, models, _

class CRMTeam(models.Model):
    _inherit = 'crm.team'

    user_id = fields.Many2one('res.users', string='Supervisor')
    sales_admin_ids = fields.Many2many('res.users','crm_team_sales_admin_rel','crm_team_id', 'user_id',string='Sales Admin')
