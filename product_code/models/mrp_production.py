"""File Account Payment"""
import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """class inherit mrp.production
    replace field location dest_is and location_scr_id because hard to inherit function private,
    """
    _inherit = 'mrp.production'

    # @api.model
    # def _get_default_location_dest_id(self):
    #     location = self.env['stock.location']
    #     res = super(MrpProduction, self)._get_default_location_dest_id()
    #     company_id = self.env.user.company_id.id
    #     domain = [('company_id', '=', company_id), ('check_active', '=', True)]
    #     location_dest_id = location.search(domain, limit=1)
    #     if location_dest_id:
    #         res = location_dest_id.id or res
    #     return res

    @api.model
    def _get_default_location_src_id(self):
        location = False
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        if self.env.context.get('default_picking_type_id'):
            location = self.env['stock.picking.type'].browse(self.env.context['default_picking_type_id']).default_location_src_id
        if not location:
            location = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1).lot_stock_id
        return location and location.id or False

    @api.model
    def _get_default_location_dest_id(self):
        location = False
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        if self._context.get('default_picking_type_id'):
            location = self.env['stock.picking.type'].browse(self.env.context['default_picking_type_id']).default_location_dest_id
        if not location:
            location = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1).lot_stock_id
        return location and location.id or False

    code_production = fields.Char(sting="Kode Produksi")
    shift_id = fields.Many2one('mrp.shift', string="Shift", required=True)
    note = fields.Text('Description')
    #replace base
    location_src_id = fields.Many2one(
        'stock.location', 'Components Location',
        default=_get_default_location_src_id,
        readonly=True, required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        states={'draft': [('readonly', False)]}, check_company=True,
        help="Location where the system will look for components.")
    location_dest_id = fields.Many2one(
        'stock.location', 'Finished Products Location',
        default=_get_default_location_dest_id,
        readonly=True, required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        states={'draft': [('readonly', False)]}, check_company=True,
        help="Location where the system will stock the finished products.")
    state = fields.Selection(selection_add=[('to_close', 'Finished')])
    date_deadline = fields.Datetime(
        'Deadline', default=fields.Datetime.now, index=True, required=True,
        help="Informative date allowing to define when the manufacturing"\
            " order should be processed at the latest to fulfill delivery on time.")

    # @api.onchange('picking_type_id')
    # def onchange_picking_type(self):
    #     location = self.env.ref('stock.stock_location_stock')
    #     res = super(MrpProduction, self).onchange_picking_type()
    #     m_location = self.env['stock.location']
    #     company_id = self.company_id.id
    #     domain = [('company_id', '=', company_id), ('usage', '=', 'production')]
    #     location_src_id = m_location.search(domain, limit=1)
    #     self.location_src_id = location_src_id.id or self.picking_type_id.default_location_src_id.id or location.id
    #     return res
    def create_lot_number_production(self):
        cd_plant = self.company_id.code_plant
        cd_mesin = self.mesin_id.kode_mesin
        cd_shift = self.shift_id.code_shift
        tmp = self.date_deadline+relativedelta(hours=7, months=(self.product_id.exp_date or 0))
        dd = tmp.day
        mm = tmp.month
        yy = tmp.year
        tgl = str(dd)+' '+str(mm)+' '+str(yy)[-2:]
        code = str(cd_plant)+' '+tgl+' '+str(cd_mesin)+' '+str(cd_shift)

        return code

    @api.onchange('date_deadline','date_planned_start','date_planned_finished')
    def onchange_date_mo(self):
        today = datetime.datetime.now()
        if self.date_deadline and self.date_planned_start and self.date_planned_finished:
            deadline = self.date_deadline.month
            date_planned_start = self.date_planned_start.month
            date_planned_finished = self.date_planned_finished.month
            mm = today.month
            if deadline > mm:
                raise UserError(_("Bulan Deadline tidak sama dengan bulan berjalan. mohon cek kembali tanggal Deadline yang diinput"))
            elif date_planned_start > mm:
                raise UserError(_("Bulan Planned Date Start tidak sama dengan bulan berjalan. mohon cek kembali tanggal Deadline yang diinput"))
            elif date_planned_finished > mm:
                raise UserError(_("Bulan Planned Date End tidak sama dengan bulan berjalan. mohon cek kembali tanggal Deadline yang diinput"))
    
    # @api.onchange('shift_id')
    # def onchange_shift(self):
    #     raise UserError(_("OOOODDDD"))
    #     code = self.create_lot_number_production()
    #     self.code_production = code

    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        #check date
        self.onchange_date_mo()
        code = self.create_lot_number_production()
        self.code_production = code
        return res

    @api.onchange('mesin_id')
    def _onchange_mesin_id(self):
        if self.mesin_id and self.state == 'done':
            raise UserError(_('machine can not be change again'))
        return super(MrpProduction, self)._onchange_mesin_id()
