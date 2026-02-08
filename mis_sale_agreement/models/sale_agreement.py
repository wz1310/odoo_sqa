# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import timedelta
import re
import datetime

import logging
_logger = logging.getLogger(__name__)

class InheritSaleAgreement(models.Model):
    _inherit = 'sale.agreement'

    pricelist_id = fields.Many2one('product.pricelist', store=True)

    @api.model
    def create(self, vals):
        # <penambahan warning saat create dimana user tidak pilih pricelist
        price = vals.get('pricelist_id')
        if not price and not self.pricelist_id.id:
            raise UserError(_("No Pricelist Selected!"))
            # ====================================================>
        return super(models.Model, self).create(vals)

    @api.depends('partner_id','team_id')
    def _compute_pricelist(self):
        for rec in self:
            partner_pricelist = self.env['partner.pricelist'].get_partner_pricelist(partner=rec.partner_id, team=rec.team_id, user=rec.user_id)
            rec.update({
                # 'pricelist_id':partner_pricelist.pricelist_id,
                'sales_admin_id':partner_pricelist.sales_admin_id
            })

    
    def action_confirm(self):
        res = super(InheritSaleAgreement,self).action_confirm()
        for rec in self:
            if rec.pricelist_id:
                sql = """SELECT pricelist_id FROM partner_pricelist WHERE partner_id="""+str(rec.partner_id.id)+""" AND team_id="""+str(rec.team_id.id)+""" """
                self.env.cr.execute(sql,())
                result = self.env.cr.fetchone()
                if result[0]:
                    if rec.pricelist_id.id != result[0]:
                        raise UserError(_("You cannot continue this transaction because pricelist has changed..."))
        return res


    @api.depends('team_id','partner_id')
    def _compute_partner_priceist(self):
        for rec in self:
            partner_pricelist_id = False
            pricelist_id = False
            if rec.partner_id.id:
                matched = rec.partner_id.partner_pricelist_ids.filtered(lambda r:r.team_id.id==rec.team_id.id)
                partner_pricelist_id = matched.id
                pricelist_id = matched.pricelist_id.id

            rec.update({
                'partner_pricelist_id':partner_pricelist_id,
                'pricelist_id':pricelist_id
                })
            for x in rec.agreement_line_ids:
                f_price = x.env['product.pricelist.item'].search([('pricelist_id','=',rec.pricelist_id.id),('product_id','=',x.product_id.id),('date_start','<=',fields.Date.today()),('date_end','>=',fields.Date.today())])
                if len(f_price.ids) > 1:
                    f_price = f_price[0]
                x.write({'price_unit': f_price.fixed_price or 0})