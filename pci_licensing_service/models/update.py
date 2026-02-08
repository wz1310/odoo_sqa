# -*- coding: utf-8 -*-
"""Publisher Warranty Contract"""
from datetime import datetime, timedelta
import logging
import random
from odoo import api, models, release
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as SDTF

_logger = logging.getLogger(__name__)


class PublisherWarrantyContract(models.AbstractModel):
    """Publisher Warranty Contract"""
    _inherit = "publisher_warranty.contract"

    @api.model
    def _get_message(self):
        res = super(PublisherWarrantyContract, self)._get_message()
        if '+e' in release.version:
            res = {}
        return res

    @api.model
    def _get_sys_logs(self):
        res = {
            'messages': []
        }
        self._get_message()
        if '+e' in release.version:
            Config = self.env['ir.config_parameter'].sudo()
            res['enterprise_info'] = {
                'expiration_date': Config.get_param('database.expiration_date'),
                'expiration_reason': Config.get_param('database.expiration_reason'),
                'enterprise_code': Config.get_param('database.enterprise_code')
            }
        return res

    @api.model
    def _update_notification(self):
        self.update_notification()


    def update_notification(self, cron_mode=True):
        _logger.info("Patched licensing service")
        return super(PublisherWarrantyContract, self).update_notification(cron_mode)
