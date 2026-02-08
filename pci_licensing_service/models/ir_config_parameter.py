# -*- coding: utf-8 -*-
"""Ir Config Parameter"""
from datetime import datetime, timedelta
import random
from odoo import api, models, release
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as SDTF

PATCHED_KEY = [
    'database.expiration_date', 
    'database.expiration_reason', 
    'database.enterprise_code'
]


class IrConfigParameter(models.Model):
    """Ir Config Parameter"""
    _inherit = 'ir.config_parameter'

    def _get_code(self):
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        chars += 'abcdefghijklmnopqrstuvwxyz'
        chars += '0123456789'
        return ''.join(random.choice(chars) for i in range(16))

    def _set_config(self):
        if '+e' in release.version:
            Config = self.env['ir.config_parameter'].sudo()
            exp_date = datetime.now() + timedelta(days=180)
            Config.set_param('database.expiration_date', exp_date.strftime(SDTF))
            Config.set_param('database.expiration_reason', 'trial')
            Config.set_param('database.enterprise_code', self._get_code())
            Config.set_param('database.patched_licensing_service', True)

    @api.model
    def get_param(self, key, default=False):
        if key in PATCHED_KEY:
            self._set_config()
        return super(IrConfigParameter, self).get_param(key, default)
