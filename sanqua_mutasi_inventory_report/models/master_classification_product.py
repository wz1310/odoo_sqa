from odoo import models, fields, api

class MasterClassification(models.Model):
    _name = 'master.classification.product'
    _description = 'Classification Product'

    name = fields.Char()
    code = fields.Char()

class MasterClassificationValue(models.Model):
    _name = 'master.classification.product.value'
    _description = 'Classification Product'

    name = fields.Char()
    code = fields.Char()