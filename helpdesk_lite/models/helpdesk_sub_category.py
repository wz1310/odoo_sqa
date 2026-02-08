# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models



class Category(models.Model):
    """ Model for case stages. This models the main stages of a document
        management flow. Tickets will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "helpdesk_lite.sub.category"
    _description = "Category of case"
    _rec_name = 'name'
    _order = "sequence, name, id"

    description = fields.Char('Description of Sub Category', translate=True)
    name = fields.Char('Name Of Sub Category', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    padding = fields.Integer('Padding For Sequence', required=True)
    prefix = fields.Char('Prefix For Sequence', required=True , default="MIS%(range_y)s%(month)s")
    sequence_id = fields.Many2one('ir.sequence')


    @api.onchange('sequence_id')
    def onchange_seq(self):
        for rec in self:
            if rec.sequence_id:
                rec.padding = rec.sequence_id.padding
                rec.prefix = rec.sequence_id.prefix
            else:
                rec.padding = rec.padding
                rec.prefix = rec.prefix
                
    @api.model
    def create(self,vals):
        context = dict(self.env.context)
        res = super(Category, self.with_context(context)).create(vals)
        if res.name and not res.sequence_id:
            seq = self.env['ir.sequence'].sudo().create({
                'name':str(res.name)+' '+'Sequence',
                'code': str(res.name)+'.sequence',
                'implementation':'standard',
                'active':'t',
                'prefix':res.prefix,
                'padding':res.padding
                })
            m_data = self.env['ir.model.data'].sudo().create({
                'name':seq.code,
                'module': 'helpdesk_category_sequence',
                'res_id': seq.id,
                'model': 'ir.sequence'
                })
            res.sequence_id = seq.id
        return res

    # def domain_sequence(self):
    #     for rec in self:
    #         print("JALANNNNNNNNN")
    #         find_dom = self.env['ir.sequence'].sudo().search([('name','=',rec.name+' '+'Sequence')])
    #         print("FINDDD",find_dom)
    #         if rec.name:
    #             rec.sequence_id = find_dom.id
    #         else:
    #             rec.sequence_id = rec.sequence_id

    def unlink(self):
        ir_seq = self.env['ir.sequence']
        for rec in self:
            if rec.sequence_id:
                ir_seq.browse([rec.sequence_id.id]).unlink()
        return super(Category, self).unlink()

    def write(self,vals):
        res = super(Category, self).write(vals)
        ir_seq = self.env['ir.sequence']
        for rec in self:
            if rec.sequence_id:
                ir_seq.browse([rec.sequence_id.id]).sudo().write({
                    'padding':rec.padding,
                    'prefix':rec.prefix,
                    })
        return res


