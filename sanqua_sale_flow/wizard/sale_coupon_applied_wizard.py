# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError,ValidationError

_logger = logging.getLogger(__name__)

class SaleCouponAppliedWizard(models.TransientModel):
    _name = 'sale.coupon.applied.wizard'
    _description = 'Sale Coupon Applied Wizard'

    sale_id = fields.Many2one('sale.order', string='Order')
    line_ids = fields.One2many('sale.coupon.applied.wizard.line', 'wizard_id', string='Lines')


    @api.model
    def default_get(self,  default_fields):
        res = super(SaleCouponAppliedWizard, self).default_get(default_fields)

        sale_coupon_ids = self.env['sale.coupon.program'].browse(self._context.get('line_ids',[]))

        vals = []
        for record in sale_coupon_ids:
            vals.append((0,0,{
                            'wizard_id':self.id,
                            'sale_coupon_program_id' : record.id,
                            'applied':True
                            }))
        res.update({'line_ids':vals})
        
        return res
    
    def btn_confirm(self):
        self._check_valid_promotions()
        for line in self.line_ids:
            if line.applied == True:
                self.sale_id._create_reward_line(line.sale_coupon_program_id)

    def btn_confirm_all(self):
        for line in self.line_ids:
            self.sale_id._create_reward_line(line.sale_coupon_program_id)

    def _check_valid_promotions(self):
        if len(self.line_ids.filtered(lambda r: r.applied == True)) > 1:
            # raise UserError(_('Cannot applied promotion program more than 1.'))
            pass

class SaleCouponAppliedWizardLine(models.TransientModel):
    _name = 'sale.coupon.applied.wizard.line'
    _description = 'Sale Coupon Applied Wizard Line'

    wizard_id = fields.Many2one('sale.coupon.applied.wizard', string='Sale Coupon Applied Wizard')
    sale_coupon_program_id = fields.Many2one('sale.coupon.program', string='Program Promotion')
    applied = fields.Boolean(string='Applied')