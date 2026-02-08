# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, timedelta

class MRPKwH(models.Model):
    _name = "mrp.kwh"
    _description = "KwH"
    _order = 'name, id'


    name = fields.Char('Description', required=True)
    date = fields.Date('Date', default=fields.Date.today())
    lwbp = fields.Float('KwH Tercatat di Meteran(LWBP)')
    bwp = fields.Float('KwH Tercatat di Meteran (BWP)')
    kvarh = fields.Float('KVarh')
    lwbp_bwp = fields.Float('LWBP + BWP + Kvarh', compute="_compute_lwbp_bwp", store=True)
    kwh_terpakai_di_meteran_pln = fields.Float('KwH Terpakai di Meteran PLN',compute="_compute_lwbp_bwp",store=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 readonly=True, index=True, default=lambda self: self.env.company)

    state = fields.Selection([('draft','Draft'),('submit','Submitted')],default='draft',string='State')




    def btn_submit(self):
        self.state = 'submit'


    @api.depends('lwbp','bwp','kvarh')
    def _compute_lwbp_bwp(self):
        for each in self:
            each.lwbp_bwp = each.lwbp + each.bwp + each.kvarh
            yesterday = self.date - timedelta(days=1)
            yesterday_data = self.env['mrp.kwh'].search([('date','=',yesterday),
                                                         ('company_id','=',each.company_id.id),
                                                         ('state','=','submit')])

            if not yesterday_data:
                each.kwh_terpakai_di_meteran_pln = 0.0
            else:
                for detail in yesterday_data[0]:
                    each.kwh_terpakai_di_meteran_pln = each.lwbp_bwp - detail.lwbp_bwp
