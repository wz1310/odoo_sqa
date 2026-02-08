# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class mis_sanqua_print(models.Model):
#     _name = 'mis_sanqua_print.mis_sanqua_print'
#     _description = 'mis_sanqua_print.mis_sanqua_print'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
