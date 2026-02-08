from odoo import models, fields, _ , api
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError

class MisTest(models.Model):
    _name = 'mis.test'
    _description = 'MIS test'

    compay