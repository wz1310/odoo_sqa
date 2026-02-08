import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

class Tes123(models.Model):
    _name = 'tes.123'

    name = fields.Char(string='Nama')