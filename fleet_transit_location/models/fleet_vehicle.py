"""File fleet vehicle"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class FleetVehicle(models.Model):
    _inherit  = 'fleet.vehicle'

    location_id = fields.Many2one('stock.location', string="Location")
    use_as_transit_location = fields.Boolean(string="Transit Location", default=False)
    company_id = fields.Many2one('res.company', 'Company', default=False)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        force_company = self._context.get('force_company') # int -> 3
        if force_company:
            self = self.with_user(self.env.company.intercompany_user_id.id)


        return super(FleetVehicle, self).name_search(name=name, args=args, operator=operator, limit=limit)



    @api.model
    def create(self, vals):
        vals = self._generate_location(vals)
        res = super(FleetVehicle, self).create(vals)
        if res.use_as_transit_location and res.location_id :
            if res.location_id.name != self.name:
                self.location_id.name = self.name
        return res
    
    # @api.multi
    def write(self, vals):
        vals = self._generate_location(vals)
        res = super(FleetVehicle, self).write(vals)
        if self.use_as_transit_location and self.location_id.name != self.name:
            self.location_id.name = self.name
        return res

    def _generate_location(self, vals):
        location = self.env['stock.location'].sudo()
        models = self.env['fleet.vehicle.model'].sudo()
        name = vals.get('name')
        lokasi = vals.get('location_id')
        transit_lokasi = vals.get('use_as_transit_location')
        if self.use_as_transit_location or transit_lokasi:
            if self.use_as_transit_location and self.location_id:
                if self.location_id.name != (name or self.name):
                    self.location_id.write({'name': name or self.name})
            elif self.use_as_transit_location and not self.location_id:
                model = models.search([('id', '=', vals.get('model_id'))])
                rec_name = ((model.brand_id.name or self.model_id.brand_id.name) or '') + '/' + ((model.name or self.model_id.name) or '') + '/' + ((vals.get('license_plate') or self.license_plate) or _('No Plate'))
                value = {'name': rec_name, 
                        'usage': 'transit'}
                location_id = location.create(value)
                vals['location_id'] = location_id.id
            elif transit_lokasi and self.location_id:
                if self.location_id.name != (name or self.name):
                    self.location_id.write({'name': name})
            elif transit_lokasi and not self.location_id:
                model = models.search([('id', '=', vals.get('model_id'))])
                rec_name = ((model.brand_id.name or self.model_id.brand_id.name) or '') + '/' + ((model.name or self.model_id.name) or '') + '/' + ((vals.get('license_plate') or self.license_plate) or _('No Plate'))
                value = {'name': rec_name,
                        'usage': 'transit'}
                location_id = location.create(value)
                vals['location_id'] = location_id.id
        return vals
    
    # @api.constrains('company_id')
    # def _constrains_company_id(self):
    #     if self.use_as_transit_location == True:
    #         if self.company_id != self.env.company:
    #             raise UserError(_('Cannot changes company for transit location fleet.'))

    def action_archive(self):
        res = super(FleetVehicle, self).action_archive()
        if self.use_as_transit_location == True and self.location_id :
            self.location_id.active = False
        return res

    def action_unarchive(self):
        res = super(FleetVehicle, self).action_unarchive()
        if self.use_as_transit_location == True and self.location_id :
            self.location_id.active = True
        return res

class StockLocation(models.Model):
    _inherit  = 'stock.location'

    fleet_ids = fields.One2many('fleet.vehicle', 'location_id', string='Fleet')


    def action_archive(self):
        res = super(StockLocation, self).action_archive()
        for rec in self.fleet_ids:
            rec.active = False
        return res

    def action_unarchive(self):
        res = super(StockLocation, self).action_unarchive()
        for rec in self.fleet_ids:
            rec.active = True
        return res