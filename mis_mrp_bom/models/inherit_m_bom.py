# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date

class InheritMbom(models.Model):
    _inherit = "mrp.bom"

    def open_bom_line(self):
        return self.open_bom_wizard()

    def open_bom_wizard(self,datas=None):
        form = self.env.ref('mis_mrp_bom.open_bom_wizard')
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids
            })
        res = {
            'name': "Line",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'show.bom.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res


class bomsline(models.TransientModel):
    _name = 'show.bom.wizard.line'


    def _get_default_product_uom_id(self):
        print("_get_default_product_uom_id")
        return self.env['uom.uom'].search([], limit=1, order='id').id

    bom_id = fields.Many2one('show.bom.wizard')
    boms_id = fields.Many2one('mrp.bom')
    product_id = fields.Many2one('product.product')
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id', readonly=False)
    company_id = fields.Many2one('res.company')
    product_qty = fields.Float(
        'Quantity', default=1.0,
        digits='Product Unit of Measure', required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        default=_get_default_product_uom_id,
        required=True,
        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control", domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    parent_product_tmpl_id = fields.Many2one('product.template', 'Parent Product Template', related='boms_id.product_tmpl_id')


class boms(models.TransientModel):
    _name = 'show.bom.wizard'

    @api.model
    def default_get(self,fields):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)


        res = super(boms,self).default_get(fields)
        b_line = []
        for x in Record.bom_line_ids:
            line = (0,0,{
                'company_id':x.company_id.id,
                'bom_id':x.bom_id.id,
                'product_id':x.product_id.id,
                'product_uom_id':x.product_uom_id.id,
                'product_qty':x.product_qty,
                'product_uom_category_id':x.product_uom_category_id.id
                })
            b_line.append(line)
        res.update({'bom_line_ids':b_line})
        return res


    bom_line_ids = fields.One2many('show.bom.wizard.line', 'bom_id')


    def confirm_reject(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)
        Record.bom_line_ids.unlink()
        update = []
        for x in self.bom_line_ids:
            update.append((0,0,{
                            'company_id' : Record.company_id.id,
                            'bom_id' : Record.id,
                            'product_id' : x.product_id.id,
                            'product_uom_id' : x.product_uom_id.id,
                            'product_qty' : x.product_qty,
                            'product_uom_category_id':x.product_uom_category_id.id
                            }))
        Record.update({'bom_line_ids':update})
        self.bom_line_ids.unlink()