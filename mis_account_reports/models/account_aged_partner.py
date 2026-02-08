# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _, api
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from datetime import date

class ReportAgedPayable(models.AbstractModel):
    """ Inherit Account Aged Payable """
    _inherit = "account.aged.payable"