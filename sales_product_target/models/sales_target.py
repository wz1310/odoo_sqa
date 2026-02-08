# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class SalesUserTarget(models.Model):
    _name = 'sales.user.target'
    _description = 'Sales User Target'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    MONTH = [(str(num), str(num)) for num in range(1, 13)]
    YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+1 )]

    team_id = fields.Many2one('crm.team', string='Division', check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",track_visibility='onchange', required=True)
    user_id = fields.Many2one('res.users', string='Salesperson',required=True,track_visibility='onchange')
    year = fields.Selection(YEARS, string='Year',track_visibility='onchange', required=True)
    month = fields.Selection(MONTH,string='Month',track_visibility='onchange', required=True)
    line_ids = fields.One2many('sales.user.target.line', 'target_id', string='Lines',track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='State',default='draft',track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company.id,readonly=True,track_visibility='onchange')
    hari_kerja = fields.Integer(string="Working Days",track_visibility='onchange', default=30)
    _sql_constraints = [
        ('unique_team_sale_year_month', 'unique(team_id,user_id,year,month)', 'Sales Person with same division in current year already exist!')
    ]

    def btn_draft(self):
        self.write({'state':'draft'})

    def btn_done(self):
        self.write({'state':'done'})
    

    @api.onchange('team_id')
    def onchange_team_id(self):
        res = {
            'domain':{
                'user_id':False
            }
        }
        if self.team_id.id:
            res['domain'].update({'user_id':[('id','in',self.team_id.sales_user_ids.ids)]})
            if self.user_id.id:
                # if user_id filled
                # check if on division.sales_user_ids
                if self.user_id.id not in self.team_id.sales_user_ids.ids:
                    self.user_id = False
        
        return res

class SalesUserTargetLine(models.Model):
    _name = 'sales.user.target.line'
    _description = 'Sales User Target Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    MONTH = [(str(num), str(num)) for num in range(1, 13)]
    YEARS = [(str(num), str(num)) for num in range(2020, (datetime.now().year)+1 )]

    target_id = fields.Many2one('sales.user.target', string='Target',track_visibility='onchange', required=True)
    team_id = fields.Many2one('crm.team',related='target_id.team_id', string='Division',track_visibility='onchange', readonly=True, store=True)
    user_id = fields.Many2one('res.users',compute="get_information_partner",string='Salesperson', store=True)
    product_id = fields.Many2one('product.product', string='Product',track_visibility='onchange', required=True)
    qty = fields.Float(string='Qty',track_visibility='onchange', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id,track_visibility='onchange')
    amount = fields.Float(string='Amount',track_visibility='onchange', required=True)
    company_id = fields.Many2one('res.company',related='target_id.company_id', string='Company',track_visibility='onchange', store=True)
    partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer','=',True)])
    region_master_id = fields.Many2one('region.master',compute="get_information_partner",string='Area', store=True)
    region_id = fields.Many2one('region.region',compute="get_information_partner",string='Region', store=True)
    customer_group_id = fields.Many2one('customer.group','Customer Group')
    year = fields.Selection(YEARS, related="target_id.year",string='Year',track_visibility='onchange', store=True)
    month = fields.Selection(MONTH,related="target_id.month",string='Month',track_visibility='onchange', store=True)

    @api.onchange('team_id')
    def onchange_team_id(self):
        res = {
            'domain':{
                'product_id':False
            }
        }
        if self.team_id.id:
            res['domain'].update({'product_id':[('categ_id','in',self.team_id.product_category_ids.ids)]})
        return res


    @api.depends('partner_id')
    def get_information_partner(self):
        for rec in self:
            rec.user_id = rec.target_id.user_id.id
            if rec.partner_id.region_master_id:
                rec.region_master_id = rec.partner_id.region_master_id.id
            else:
                rec.region_master_id = False

            if rec.partner_id.region_id:
                rec.region_id = rec.partner_id.region_id.id
            else:
                rec.region_id = False


    @api.onchange('partner_id')
    def onchange_team_id(self):
        pricelist_data = self.env['partner.pricelist'].search([('partner_id','=',self.partner_id.id),('team_id','=',self.target_id.team_id.id)])
        for x in pricelist_data:
            print ("zoooonkk", pricelist_data)
        if len(pricelist_data) > 1:
            raise ValidationError(_('Wrong Data'))
        else:
            self.customer_group_id = pricelist_data.customer_group.id
