# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError

class MisFleetVehicle(models.Model):
    _inherit = ['fleet.vehicle']
    expedition_app = fields.Boolean()

class MisFleetVehicleModel(models.Model):
    _inherit = ['fleet.vehicle.model']
    expedition_app = fields.Boolean()