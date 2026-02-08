from odoo import api,fields,models,_
import time
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from datetime import datetime, timedelta
from dateutil.relativedelta import *
import odoo.addons.decimal_precision as dp


class WizardCreatePbbh(models.TransientModel):
    _name = "wizard.create.pbbh"

    def confirm(self):
        print (">>>>>>>>>>>>@@@@@@@@@@@@")
        rph_line_ids = self.env['mrp.rph.line'].browse(self._context.get('active_ids', []))
        print ("xxxxxxaaaa", rph_line_ids)
        for each in rph_line_ids:
            if each.mrp_rph_id.state != 'approved':
                raise Warning('RPH needs to approved first')
            else:
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id','=',each.product_id.product_tmpl_id.id),
                                                      ('company_id','=',each.company_id.id),
                                                      ('type','=','normal')])
                if not bom_id:
                    raise ValidationError('Product %s doenst have Bill of Material, please check again'  % (each.product_id.name))
            
                vals = {
                    'rph_id' : each.mrp_rph_id.id,
                    'product_id' : each.mrp_rph_id.product_id.id,
                    'company_id' : each.mrp_rph_id.company_id.id,
                    'date' : each.date,
                    'total_qty' : each.qty,
                    'bom_id' : bom_id[0].id,
                }
                pbbh_id = self.env['mrp.pbbh'].create(vals)

                for detail in bom_id:
                    for bom_line in detail.bom_line_ids:
                        qty_per_uom_finished_good = bom_line.product_qty/ detail.product_qty
                        vals_line = {
                            'mrp_pbbh_id' : pbbh_id.id,
                            'product_id' : bom_line.product_id.id,
                            'product_uom_id' : bom_line.product_uom_id.id,
                            'qty' : qty_per_uom_finished_good * each.qty,
                        }
                        pbbh_line_id = self.env['mrp.pbbh.line'].create(vals_line)

                form = self.env.ref('mrp_shift.mrp_pbbh_view_form')
                context = dict(self.env.context or {})

                res = {
                    'view_mode': 'tree,form',
                    'res_model': 'mrp.pbbh',
                    'view_id': form.id,
                    'views':[(form.id,'form')],
                    'type': 'ir.actions.act_window',
                    'context': context,
                    'target': 'current',
                    'res_id':pbbh_id.id,
                }
                return res
