from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ModelName(models.Model):
    _inherit = "res.partner"
    

    # counter team_ids from partner_pricelist
    team_ids = fields.Many2many('crm.team', compute="_compute_team_ids", string="Divisions")

    @api.depends('partner_pricelist_ids')
    def _compute_team_ids(self):
        for rec in self:
            rec.team_ids = rec.partner_pricelist_ids.mapped('team_id')