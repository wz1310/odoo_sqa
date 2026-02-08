# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class dn_api_13(models.Model):
#     _name = 'dn_api_13.dn_api_13'
#     _description = 'dn_api_13.dn_api_13'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
