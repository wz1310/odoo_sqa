# -*- coding: utf-8 -*-
import logging
import pytz

from odoo import fields, models, api, _
from odoo.addons.sanqua_print.helpers import amount_to_text,\
    format_local_currency,\
    format_local_datetime
from num2words import num2words

_logger = logging.getLogger(__name__)


class SettlementRequest(models.Model):
    _name = 'settlement.request'
    _inherit = 'settlement.request'
    _description = 'Settlement request for printing'

    @staticmethod
    def get_format_currency(value, total=False):
        """ Get format currency with rule: thousand -> (.) and no decimal place.
        :param value: Float. Value that need to be formatting.
        :return: String. Format currency result.
        """
        return format_local_currency(value, total)

    def get_format_datetime(self, datetime_value, only_date=False):
        """ Get format datetime as string.
        :param datetime_value: Datetime. Datetime that need to be formatting.
        :param only_date: Boolean. If 'True' then value will be return as Date.
        :return: String. Format datetime result.
        """
        user_tz = pytz.timezone(self._context.get(
            'tz') or self.env.user.tz or 'UTC')
        return format_local_datetime(user_tz, datetime_value, only_date=True)

    def get_terbilang(self, amount):
        return num2words(amount, lang="id")
