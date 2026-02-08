# -*- coding: utf-8 -*-

import logging
import math
import pytz

from odoo import _, api, fields, models
from odoo.addons.sanqua_print.helpers import amount_to_text,\
    format_local_currency,\
    format_local_datetime

_logger = logging.getLogger(__name__)

class CollectionActivity(models.Model):
    _inherit = 'collection.activity'

    def get_blank_space(self,line_ids):
        return math.ceil(len(line_ids)/9) * 9 - len(line_ids)

    def get_blank_space_etax(self,line_ids):
        return math.ceil(len(line_ids)/10) * 10 - len(line_ids)

    @staticmethod
    def get_format_currency(value,total=False):
        """ Get format currency with rule: thousand -> (.) and no decimal place.
        :param value: Float. Value that need to be formatting.
        :return: String. Format currency result.
        """
        return format_local_currency(value,total)

    def get_format_datetime(self, datetime_value, only_date=False):
        """ Get format datetime as string.
        :param datetime_value: Datetime. Datetime that need to be formatting.
        :param only_date: Boolean. If 'True' then value will be return as Date.
        :return: String. Format datetime result.
        """
        user_tz = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        return format_local_datetime(user_tz, datetime_value, only_date=True)
