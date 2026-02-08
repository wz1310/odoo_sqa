"""File Account Payment"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    """class inherit res.company"""
    _inherit = 'res.company'

    code_plant = fields.Char(sting="Kode Plant")
