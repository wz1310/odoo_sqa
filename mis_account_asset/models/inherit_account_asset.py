# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date

class InheritAsset(models.Model):
    _inherit = "account.asset"

    @api.onchange('model_id')
    def _onchange_model_id(self):
        res =  super(InheritAsset, self)._onchange_model_id()
        model = self.model_id
        if model:
            self.account_asset_id = model.account_asset_id
        return res