from odoo import models, fields, api


class RunQuery(models.Model):
    _name='run.query'

    name = fields.Char(string='Query')
    result = fields.Char(string='Name')


    def execute(self):
        '''Button to run Query'''
        if self.name:
            self.env.cr.execute(self.name)
        return True
