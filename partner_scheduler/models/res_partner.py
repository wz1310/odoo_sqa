# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _cronjob_delete_partner(self):
        """Delete expired partner != approved
            create date 1 jan 2020 expired date = 11 jan 2020
            when 11 jan 2020 < date today() it will deleted
        """
        company_ids = self.env['res.company'].search([])
        for comp in company_ids:
            comp_days_to_expired_settings = comp.auto_delete_partner
            partner_ids = self.env['res.partner'].search([('company_id', '=', comp.id),
                                       ('state', 'in', ('draft', 'waiting_approval'))])
            for partner in partner_ids:
                expired_date = partner.create_date + timedelta(days=comp_days_to_expired_settings)
                if datetime.now() > expired_date:
                    check_in_move_line = self.env['account.move.line'].search([('partner_id', '=', partner.id)])
                    if check_in_move_line:
                        partner.active = False
                    else:
                        partner.unlink()
