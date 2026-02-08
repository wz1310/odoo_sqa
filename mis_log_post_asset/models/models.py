# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date
import calendar


class MisLogPost(models.Model):
    _name = 'log.post.asset'

    start_time = fields.Datetime()
    end_time = fields.Datetime()
    logs = fields.Text()