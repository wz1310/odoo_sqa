from odoo import api, fields, models, _

# MONTH_SELECTION = [
#     ('1', 'Januari'),
#     ('2', 'Februari'),
#     ('3', 'Maret'),
#     ('4', 'April'),
#     ('5', 'Mei'),
#     ('6', 'Juni'),
#     ('7', 'Juli'),
#     ('8', 'Agustus'),
#     ('9', 'September'),
#     ('10', 'Oktober'),
#     ('11', 'November'),
#     ('12', 'Desember'),
# ]

class SaleAnnualForecast(models.Model):
    """ Create new model Sale Forecast """
    _name = "sale.annual.forecast"
    _description = "Sale Annual Forecast"
    _rec_name = "product_id"


    def get_years():
        """ Function to get list of years """
        year_list = []
        for i in range(2021, 2100):
            selection_string = str(i)
            year_list.append((selection_string, str(i)))
        return year_list

    product_category_id = fields.Many2one('product.category')
    product_id = fields.Many2one('product.template')
    year = fields.Selection(get_years())    
    # month = fields.Selection(MONTH_SELECTION)
    forecast_qty = fields.Float(string='Total Value')
    forecast_value = fields.Float()
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id)


    @api.onchange('product_category_id')
    def _onchange_product_category_id(self):
        """ Function to dynamically change domain for product_id value based on product category """
        for rec in self:
            domain = {}
            if rec.product_category_id:
                domain = {'domain': {'product_id': [('categ_id', '=', rec.product_category_id.id)]}}
                return domain
