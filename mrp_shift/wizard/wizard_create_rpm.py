"""Wizard create RPM """
from odoo import models, fields, _ , api

class WizardCreateRpmLines(models.TransientModel):
    """  create.rpm.line"""
    _name = "create.rpm.line"
    _description = 'Create RPM Lines'

    create_rpm_id = fields.Many2one('create.rpm')
    product_id = fields.Many2one('product.product')
    product_qty = fields.Float()
    product_uom = fields.Many2one('uom.uom')
    is_check = fields.Boolean(default=False, string="Choose")

class WizardCreateRPM(models.TransientModel):
    """  create.rpm"""
    _name = "create.rpm"
    _description = 'Create RPM'

    pbbh_id = fields.Many2one('mrp.pbbh', string="PBBH")
    create_rpm_line_ids = fields.One2many('create.rpm.line', 'create_rpm_id')

    @api.model
    def default_get(self, fields):
        result = super(WizardCreateRPM, self).default_get(fields)
        pbbh_id = self.env['mrp.pbbh'].browse(self._context.get('default_pbbh_id',[]))
        if pbbh_id:
            result['create_rpm_line_ids'] = [(0, 0, {
            'product_id': data.product_id.id,
            'product_qty': data.qty,
            'product_uom': data.product_uom_id.id
            }) for data in pbbh_id.mrp_pbbh_line_ids]
        return result

    def action_create_rpm(self):
        for data in self.create_rpm_line_ids.filtered(lambda x:x.is_check == True):
            values = {
                'product_id': self.pbbh_id.product_id.id,
                'material_id': data.product_id.id,
                'qty' : data.product_qty,
                'product_uom': data.product_uom.id,
                'date_start': self.pbbh_id.date,
                'date_end': self.pbbh_id.date,
                'rph_id': self.pbbh_id.rph_id.id
            }
            self.env['mrp.rpm'].create(values)
        return True
