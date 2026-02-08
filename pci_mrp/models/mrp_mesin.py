from odoo import fields,api,models,_
import odoo.addons.decimal_precision as dp

class MrpMesin(models.Model):
    _name = 'mrp.mesin'
    
    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    kode_mesin = fields.Char(string='Kode Mesin')
    sebelum_produksi = fields.Float(string='Sebelum Produksi')
    sesudah_produksi = fields.Float(string='Sesudah Produksi')
    information_ids = fields.One2many('mrp.mesin.information', 'mesin_id')
    history_mesin_ids = fields.One2many('mrp.mesin.history', 'mesin_id')
    production_id = fields.Many2one('mrp.production')
    company_id = fields.Many2one('res.company','Plant', default=lambda self:self.env.user.company_id)
    kwh_per_jam = fields.Float('KwH', default="1")
    standard_personil = fields.Integer('Standard Personil')
    type_mesin = fields.Selection([('PLASTIK','PLASTIK'),('AMDK','AMDK')], string="Tipe Mesin")


class MrpMesinInformation(models.Model):
    _name = 'mrp.mesin.information'

    mesin_id = fields.Many2one('mrp.mesin', string='Mesin')
    company_id = fields.Many2one('res.company', string='Plant', related="mesin_id.company_id")
    sku_id = fields.Many2one('product.product', string='SKU')
    kapasitas = fields.Float(string='Kapasitas')
    satuan_id = fields.Many2one('uom.uom', string='Satuan')
    target_prod = fields.Float(string='Target Produksi / jam')
    hasil_prod = fields.Float(string='Hasil Produksi / jam')
    cost = fields.Float(string='Cost / Jam')
    kwh = fields.Float(string='Kwh / Dus / Pcs',digits=dp.get_precision('kwh'))

    _sql_constraints = [('information_unique', 'unique(company_id, sku_id, mesin_id)', 'A user can only have one information plant and sku in one machine.')]


class MrpMesinHistory(models.Model):
    _name = 'mrp.mesin.history'

    mesin_id = fields.Many2one('mrp.mesin', string='Mesin')
    date = fields.Date(string='Tanggal')
    user_id = fields.Many2one('res.users', string='User')
    production_id = fields.Many2one('mrp.production', string='MO')
    history = fields.Char(string='History')