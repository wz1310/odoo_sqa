# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date
from odoo.tools import float_is_zero
import json
import requests
import xml.etree.ElementTree as ET

class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    # /////////////////tambahan field untuk menghitung jumlah print/////////////////
    # print_pick_op_count = fields.Integer(copy=False, default=1)
    # print_int_tf_count = fields.Integer(copy=False, default=1)
    # print_rcv_itm_count = fields.Integer(copy=False, default=1)
    # print_po_rtr_count = fields.Integer(copy=False, default=1)
    descript = fields.Text()
    
    def repair_return(self):
        if self.state != 'done':
            self.env.cr.execute("""DELETE FROM stock_move_line WHERE picking_id = %s""",(self.id,))
            msgs = []
            msgs.append("User has been deleted move line")
            self.message_post(body=msgs[0])
            

    @api.model
    def _get_custom_domain_location(self):

        users = self.env['res.users'].search([('id', '=', self.env.user.id)])
        xFilterTempWarehouseIds = []
        xFilterPickingCode = []
        xFilterCompanyId = self.env.company.id

        xPickingId = self.env.context.get('params', {}).get('id')
        if xPickingId:
            xPickingDetail = self.env['stock.picking'].search([('id', '=', xPickingId)])

            # Domain of location_id depends on the purpose of stock.picking
            # Purpose: DO Intercompany, DO from plant's SO, GR and Return
            # 1. DO Intercompany
            print('>>> xPickingDetail.interco_master : ' + str(xPickingDetail.interco_master))
            if xPickingDetail.interco_master:
                xFilterCompanyId = xPickingDetail.company_id.id
                # print('>>> xFilterCompanyId: ' + str(xFilterCompanyId))
                xFilterTempWarehouseIds = self.env['stock.warehouse'].search([('company_id', '=', xFilterCompanyId)])
                # print('>>> xFilterTempWarehouseIds: ' + str(xFilterTempWarehouseIds))
                return [('warehouse_id', 'in', xFilterTempWarehouseIds.ids)]
            elif not xPickingDetail.interco_master and xPickingDetail.sale_id.company_id.id == xFilterCompanyId:
                for user in users:
                    xFilterTempWarehouseIds = user.warehouse_ids
                return [('warehouse_id', 'in', xFilterTempWarehouseIds.ids)]
        else:
            return [('warehouse_id', 'in', users.warehouse_ids.ids)]

                # users = self.env['res.users'].search([('id', '=', self.env.user.id)])
                # temp_warehouse_ids = []
                # for user in users:
                #     temp_warehouse_ids = user.warehouse_ids
                #
                # if temp_warehouse_ids:
                #     return [('warehouse_id', 'in', temp_warehouse_ids.ids)]
                # else:
                #     return []

    warehouse_ids = fields.Many2many('stock.warehouse', compute='_get_warehouse', track_visibility='onchange')

    # This field replace from origin in terms of supporting filter based on allowed warehouse
    # picking_type_id = fields.Many2one(
    #     'stock.picking.type', 'Operation Type',
    #     required=True,
    #     domain=lambda self: self._get_custom_domain_picking_type_id())
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True)
    # location_id = fields.Many2one(
    #     'stock.location', "Source Location",
    #     default=lambda self: self.env['stock.picking.type'].browse(
    #         self._context.get('default_picking_type_id')).default_location_src_id,
    #     check_company=True, readonly=True, required=True,
    #     states={'draft': [('readonly', False)]},
    #     domain=_get_custom_domain_location)
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        check_company=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]})


    # New column for filtered domain
    domain_picking_type_id = fields.Many2many('stock.picking.type',compute="_compute_picking_type_id_domain", readonly=True, store=False)
    domain_location_id = fields.Many2many('stock.location', compute="_compute_location_id_domain",
                                              readonly=True, store=False)

    def _get_custom_domain_location_id(self):
        print('>>> _get_custom_domain_location_id')
        users = self.env['res.users'].search([('id', '=', self.env.user.id)])
        print('>>> warehouse_ids: ' + str(users.warehouse_ids.ids))
        return users.warehouse_ids

    def _get_custom_domain_picking_type_id(self):
        print('>>> call _get_custom_domain_picking_type_id(self)')
        users = self.env['res.users'].search([('id', '=', self.env.user.id)])
        print('>>> users : ' + str(users))
        xFilterTempWarehouseIds = []
        xFilterPickingCode = []
        xFilterCompanyId = self.env.company.id
        # print('>>> xFilterCompanyId : ' + str(xFilterCompanyId))

        # print('>>> params : ' + str(self.env.context.get('params')))
        # print('>>> self.env.context : ' + str(self.env.context))
        # print('>>> self.id : ' + str(self.id))
        xPickingId = self.env.context.get('params', {}).get('id') if self.env.context.get('params', {}).get(
            'id') else self.id
        # print('>>> xPickingId : ' + str(xPickingId))
        if xPickingId:
            xPickingDetail = self.env['stock.picking'].search([('id', '=', xPickingId)])
            if xPickingDetail.sale_id:
                xFilterPickingCode = ['outgoing']
            else:
                xFilterPickingCode = ['incoming', 'internal']

            # Domain of picking_type_id depends on the purpose of stock.picking
            # Purpose: DO Intercompany, DO from plant's SO, GR and Return
            # 1. DO Intercompany
            if xPickingDetail.interco_master:
                xFilterCompanyId = xPickingDetail.company_id.id
                xFilterTempWarehouseIds = self.env['stock.warehouse'].search([('company_id', '=', xFilterCompanyId)])
                # print('>>> temp_warehouse_ids: ' + str(temp_warehouse_ids))
            elif not xPickingDetail.interco_master and xPickingDetail.sale_id.company_id.id == xFilterCompanyId:
                for user in users:
                    xFilterTempWarehouseIds = user.warehouse_ids

            if xFilterTempWarehouseIds:

                # return [('company_id', '=', xFilterCompanyId),
                #         ('code', '=', xFilterPickingCode),
                #         ('warehouse_id', 'in', xFilterTempWarehouseIds.ids)]
                return self.env['stock.picking.type'].search(
                    [('company_id', '=', xFilterCompanyId), ('code', '=', xFilterPickingCode),
                     ('warehouse_id', 'in', xFilterTempWarehouseIds.ids)])
            else:
                return self.env['stock.picking.type'].search(
                    [('company_id', '=', self.env.company.id), ('code', '=', xFilterPickingCode)])
        else:
            print('>>> ELSE ')
            for user in users:
                xFilterTempWarehouseIds = user.warehouse_ids
                return self.env['stock.picking.type'].search(
                    [('company_id', '=', self.env.company.id),('warehouse_id', 'in', xFilterTempWarehouseIds.ids)])

    def _compute_picking_type_id_domain(self):
        print("_compute_picking_type_id_domain")
        for rec in self:
            rec.domain_picking_type_id = rec._get_custom_domain_picking_type_id()

    def _compute_location_id_domain(self):
        print('>>> _compute_location_id_domain')
        for rec in self:
            users = self.env['res.users'].search([('id', '=', self.env.user.id)])
            print('>>> users: ' + str(users))
            print('>>> warehouse_ids: ' + str(users.warehouse_ids.ids))
            rec.domain_location_id = users.warehouse_ids.ids

    @api.onchange('location_id')
    def _onchange_location_id(self):
        return {
            'domain': {
                'location_id': [('warehouse_id', 'in', self._get_custom_domain_location_id().ids)]
            }
        }

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        print('>>> call _onchange_picking_type_id()')
        users = self.env['res.users'].search([('id', '=', self.env.user.id)])
        for rec in self:
            for line_ids in rec.move_line_ids:
                if line_ids.location_id.warehouse_id not in users.warehouse_ids.ids:
                    raise UserError(_('Please delete the picking detail first when change you have change the Operation Type'))
            rec.location_id = ''
        return {
            'domain': {
                'picking_type_id': [('id','in', self._get_custom_domain_picking_type_id().ids)]
            }
        }

    # The purpose of this function is to get allowed warehouse based on setting on user module
    # This will work for user that create DO on intercompany process
    def _butt_dom(self):
        self.warehouse_ids = self.env['res.users'].search([('id','=',self.env.user.id)]).warehouse_ids
        print("INILAHHH",self.warehouse_ids)

    @api.model
    def _get_warehouse(self):
        print("START _get_warehouse>>>>>>>>>>>>>",fields.Datetime.now())
        self.warehouse_ids = self.env['res.users'].search([('id','=',self.env.user.id)]).warehouse_ids
        print("END _get_warehouse>>>>>>>>>>>>>",fields.Datetime.now())

    def btn_plant_confirm(self):
        print('>>> call btn_plant_confirm() on mis_stock_picking_v1')
        res = super(StockPickingInherit, self).btn_plant_confirm()
        if self.sale_id and self.interco_master:
            if not self.fleet_vehicle_id:
                raise UserError(_('Please fill vehicle before..'))

        # Author: Peter@MISSanQua
        # At: 26/05/2023
        # Description : Add validation to check relation between operation type, allowed user warehouse and the purpose of this DO
        # Case 1: - SO Intercompay WIM -> Plant (interco_master = True)
        #            - Validate operation type must be part of company that create the SO
        if self.interco_master:
            users = self.env['res.users'].search([('id', '=', self.env.user.id)])

        return res

    # /////////////function untuk menghitung jumlah print dan tambahan informasi pada log//////////
    def printing_po_rtr(self):
        msgs = []
        msgs.append("Purchase Return has printed")
        self.message_post(body=msgs[0])
        self.print_po_rtr_count += 1

    def printing_rcv_itm(self):
        msgs = []
        msgs.append("Receive Items in has printed")
        self.message_post(body=msgs[0])
        self.print_rcv_itm_count += 1

    def printing_int_tf(self):
        msgs = []
        msgs.append("Internal Transfer has printed")
        self.message_post(body=msgs[0])
        self.print_int_tf_count += 1

    def printing_slip_constrains(self):
        msgs = []
        msgs.append("Delivery Slips has printed")
        self.message_post(body=msgs[0])
        self.print_count += 1
        if self.print_count > 1:
            self.allow_print = False

    def printing_pick_opr(self):
        msgs = []
        msgs.append("Picking Operations has printed")
        self.message_post(body=msgs[0])
        self.print_pick_op_count += 1

    # Author : MIS@SanQua
    # Date : 26 Mei 2023
    # Description : This override write method to remove validation checking change of picking_type_id
    def write(self, vals):
        print('>>> Override write')
        # Remove this line
        # if vals.get('picking_type_id') and self.state != 'draft':
        #     raise UserError(_("Changing the operation type of this record is forbidden at this point."))
        # set partner as a follower and unfollow old partner
        if vals.get('partner_id'):
            for picking in self:
                if picking.location_id.usage == 'supplier' or picking.location_dest_id.usage == 'customer':
                    if picking.partner_id:
                        picking.message_unsubscribe(picking.partner_id.ids)
                    picking.message_subscribe([vals.get('partner_id')])

        # Change locations of moves if those of the picking change
        after_vals = {}
        if vals.get('location_id'):
            after_vals['location_id'] = vals['location_id']
        if vals.get('location_dest_id'):
            after_vals['location_dest_id'] = vals['location_dest_id']
        if after_vals:
            self.mapped('move_lines').filtered(lambda move: not move.scrapped).write(after_vals)
        if vals.get('move_lines'):
            # Do not run autoconfirm if any of the moves has an initial demand. If an initial demand
            # is present in any of the moves, it means the picking was created through the "planned
            # transfer" mechanism.
            pickings_to_not_autoconfirm = self.env['stock.picking']
            for picking in self:
                if picking.state != 'draft':
                    continue
                for move in picking.move_lines:
                    # if not super(StockPickingInherit, self).float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                    if not float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                        pickings_to_not_autoconfirm |= picking
                        break
            (self - pickings_to_not_autoconfirm)._autoconfirm_picking()
        return super(models.Model, self).write(vals)

    def validate_operation_type_location(self):
        print('>>> Call validate_operation_type_location on mis_stock_picking_v1')
        users = self.env['res.users'].search([('id', '=', self.env.user.id)])
        xCreatedSOWarehouse = self.env['stock.warehouse'].search([('company_id', '=',self.sale_id.company_id.id)])
        # Author: Peter@MISSanQua
        # At: 26/05/2023
        # Description : Add validation to check relation between operation type, allowed user warehouse and the purpose of this DO
        # Case 1: - SO Intercompay WIM -> Plant (interco_master = True)
        #            - Validate operation type must be part of company that create the SO
        # if self.interco_master:
        # Note : Case 1 no need to check since the dropdown already filtered

        # Case 2: - PO Intercompay WIM -> Plant or Plant -> Plant (interco_master = True)
        #         - Operation type must be part of allowed warehouse of the user
        #         - Location must be part of allowed warehouse of the user
        # print('>>> self.picking_type_id.warehouse_id.id : ' + str(self.picking_type_id.warehouse_id.id))
        # print('>>> users.warehouse_ids.ids : ' + str(users.warehouse_ids.ids))
        print('>>> self.id : ' + str(self.id))
        print('>>> self.interco_master: ' + str(self.interco_master))
        print('>>> self.picking_type_id : ' + str(self.picking_type_id))
        print('>>> self.doc_name : ' + str(self.doc_name))
        print('>>> self.location_id : ' + str(self.location_id))
        print('>>> self.sale_id.company_id.id : ' + str(self.sale_id.company_id.id))
        print('>>> self.location_id.warehouse_id.id : ' + str(self.location_id.warehouse_id.id))
        print('>>> xCreatedSOWarehouse : ' + str(xCreatedSOWarehouse.ids))
        if not self.interco_master and self.picking_type_id and not self.no_sj_wim:
            if self.picking_type_id.code == 'outgoing':
                if self.picking_type_id.warehouse_id.id not in users.warehouse_ids.ids:
                    self.env['stock.move.line'].search([('picking_id', '=', self.id)]).unlink()
                    raise UserError(_("Please select allowed Operation Type"))
            else:
                print('>>> Do validate here')
        # else:
        #     print('>>> self.name : ' + str(self.name))
        #     print('>>> self.no_sj_wim : ' + str(self.no_sj_wim))
        #     if not self.no_sj_wim:
        #         raise UserError(_("Operation type can not be empty"))

        # if self.picking_type_id.code == 'outgoing' and self.location_id:
        #     print('>>> 1 : ' + str(( self.location_id.warehouse_id.id not in users.warehouse_ids.ids and not self.no_sj_wim )))
        #     print('>>> 2 : ' + str((self.location_id.warehouse_id.id not in xCreatedSOWarehouse.ids)))
        #     if ( self.location_id.warehouse_id.id not in users.warehouse_ids.ids and not self.no_sj_wim ) or (self.location_id.warehouse_id.id not in xCreatedSOWarehouse.ids):
        #         raise UserError(_("Please select allowed Location"))
        #     else:
        #         print('>>> Do validate here')



    def button_validate(self):
        print('>>> Call button_validate from mis_stock_picking_v1/models.py')
        # Cek Receved Stock
        self.ensure_one()

        # At : 29/05/2023
        # By : Peter @MIS-SanQua
        # Description: This line added to validate field Operation type and location based on allowed warehouse
        # print('>>> Before call validate_operation_type_location')
        # print('>>> self.interco_master : ' + str(self.interco_master))
        self.validate_operation_type_location()
        # print('>>> After call validate_operation_type_location')

        # SOT masih error, jadi Outgoing di Lepas
        if self.picking_type_id.code in ('internal', 'outgoing') and self.location_id.usage in ('internal', 'production'):

            for mov in self.move_line_ids:

                quant_ids = self.env['stock.quant']
                if mov.location_id.usage in ('internal', 'production'):
                    stock = 0.0
                    if mov.lot_id.id:
                        quant_ids = self.env['stock.quant'].search([('product_id', '=', mov.product_id.id),
                                                                    ('location_id', '=',
                                                                     mov.location_id.id),
                                                                    ('lot_id', '=', mov.lot_id.id)])
                    else:
                        quant_ids = self.env['stock.quant'].search([('product_id', '=', mov.product_id.id),
                                                                    ('location_id', '=', mov.location_id.id)])

                    for quant in quant_ids:
                        stock += quant.quantity
                    if stock < mov.qty_done:
                        raise UserError(_("Stock untuk Product %s \nLot : %s \nkurang dari yang dibutuhkan, Mohon periksa ketersediaan stock di %s\nStock Tersedia : %s\nAkan dikirim : %s\nKurang : %s \npicking") % (
                            mov.product_id.name, mov.lot_id.name, mov.location_id.display_name, stock, mov.qty_done, stock-mov.qty_done))
                        # continue

        if self.approval_state == 'need_approval':
            if self.approved == True:
                res = super(StockPickingInherit, self).button_validate()
                return res
            else:
                raise UserError(
                    _("You Can't Validate This Document!\nThis Document Needs to Approved!"))
        else:
            if self.sale_interco_master == True and self.is_return_picking == True:
                # if return picking
                # and if interco master
                # so we will append same lot to process
                return_none = False
                res = super(StockPickingInherit, self.with_context(
                    allowed_company_ids=self.allowed_company_ids.ids).sudo()).button_validate()

                if type(res) == dict:
                    res_model = res.get('res_model')
                    if res_model == 'stock.immediate.transfer':
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.immediate.transfer'].browse(
                            res_id)
                        Wizard.with_context(allowed_company_ids=self.allowed_company_ids.ids).sudo(
                        ).process()  # process if wizard showed

                    elif res_model == 'stock.overprocessed.transfer':
                        raise ValidationError(_("Raise Overprocessed To Receive Qty on Validating Receive Order %s!") % (
                            self.mapped('display_name')))
                    elif res_model == 'stock.backorder.confirmation':
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.backorder.confirmation'].browse(
                            res_id)
                        Wizard.with_context(cancel_backorder=True, force_validating_interco_lot=True, allowed_company_ids=self.allowed_company_ids.ids) \
                            .sudo().process()  # process if wizard showed
                        return_none = True
                if self.state != 'done':
                    raise UserError(
                        _("Failed to validate picking sss : %s %s") % (self.name, str(self.id) ))
                if self.sale_truck_id.id:
                    # if from sale truck
                    # only return do from so company
                    return res
                else:
                    print('>>> else: self.validate_return_intercompany()')
                    self.validate_return_intercompany()

                try:
                    if(return_none):
                        return None
                except expression as identifier:
                    return True
            elif self.is_return_picking == True:
                res = super(StockPickingInherit, self.with_context(
                    allowed_company_ids=self.allowed_company_ids.ids).sudo()).button_validate()
                if type(res) == dict:
                    res_model = res.get('res_model')
                    if res_model == 'stock.immediate.transfer':
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.immediate.transfer'].browse(
                            res_id)
                        Wizard.with_context(allowed_company_ids=self.allowed_company_ids.ids).sudo(
                        ).process()  # process if wizard showed

                    elif res_model == 'stock.overprocessed.transfer':
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.overprocessed.transfer'].with_context(
                            {'default_picking_id': self.id}).browse(res_id)
                        # process if wizard showed
                        return Wizard.with_context(allowed_company_ids=self.allowed_company_ids.ids).sudo().action_confirm()
                    elif res_model == 'stock.backorder.confirmation':
                        res_id = res.get('res_id')
                        Wizard = self.env['stock.backorder.confirmation'].browse(
                            res_id)
                        Wizard.with_context(cancel_backorder=True, force_validating_interco_lot=True, allowed_company_ids=self.allowed_company_ids.ids) \
                            .sudo().process()  # process if wizard showed
                        return None
            else:
                res = super(StockPickingInherit, self).button_validate()



            return res

    @api.onchange('picking_type_id')
    def onc_wh(self):
        users = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if self.picking_type_id.code == 'warehouse_transfer':
            return {'domain': {'location_dest_id': [('warehouse_id', 'not in', users.warehouse_ids.ids),
            ('warehouse_id', '!=',False),('company_id', 'in', [x['id'] for x in users.company_ids])]}}
        elif self.picking_type_id.code != 'warehouse_transfer':
            return {'domain': {'location_dest_id': [('company_id', 'in', [users.company_id.id,False])]}}

    def open_bom_line(self):
        print("OPEN BOM LINE")
        # return self.open_fpm_wizard()

    # def open_fpm_wizard(self,datas=None):
    #     self.ensure_one()

    #     datas = self.action_show_fpm(datas)        
    #     form = self.env.ref('mis_faktur_pajak_masuk.open_post_wizard_fpm_view')
    #     context = dict(self.env.context or {})
    #     context.update({
    #         'active_id':self.id,
    #         'active_ids':self.ids,
    #         'default_fm':'FM',
    #         'default_kode_jenis':datas['kdJenisTransaksi'],
    #         'default_fg_pengganti':datas['fgPengganti'],
    #         'detailTransaksi': datas['detailTransaksi'],
    #         'default_no_faktur':datas['nomorFaktur'],
    #         'default_tanggal_faktur':datetime.strptime(datas['tanggalFaktur'],'%d/%m/%Y'),
    #         'default_npwp':datas['npwpPenjual'],
    #         'default_nama_vendor':datas['namaPenjual'],
    #         'default_alamat':datas['alamatPenjual'],
    #         'default_jumlah_dpp':datas['jumlahDpp'],
    #         'default_jumlah_ppn':datas['jumlahPpn'],
    #         'default_jumlah_ppnbm':datas['jumlahPpnBm'],
    #         'active_model':'account.move'})
    #     # print("context",context)
    #     res = {
    #         'name': "%s - %s" % (_('Barcode data'), self.fpm_barcode),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'show.fpm.wizard',
    #         'view_id': form.id,
    #         'type': 'ir.actions.act_window',
    #         'context': context,
    #         'target': 'new'
    #     }
    #     self.sudo().env['account.move'].browse(self.id).write({'fpm_barcode':False})
    #     # print("IDDDDDDDDDDDDDDD", self.env['account.move'].browse(self.id).fpm_barcode)
    #     return res


    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     print('>>> Call fields_view_get')
    #     sup = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form':
    #         print('>>> Sup : ' + str(sup))
    #         sup['fields']['picking_type_id']['domain'] = [('code','in',self._get_custom_domain_picking_type_id())]
    #
    #     return sup
    # //////////////////////////////////////////////////////////////////////////////////////

class StockPickingTypeInherit(models.Model):
    _inherit = 'stock.picking.type'

    code = fields.Selection(selection_add=[
        ('warehouse_transfer', 'Warehouse Transfer'),
        ('mts_transfer', 'Mutasi Transfer')
        ])
