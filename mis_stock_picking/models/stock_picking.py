# -*- coding: utf-8 -*-
from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date
import json
import requests

class StockPicking(models.Model):
    _inherit = ['stock.picking']
    cek_akses = fields.Boolean(compute='open_spicks')
    sync_btn = fields.Boolean(string='Sync')
    replace_from_do = fields.One2many('stock.picking', string='Replace From Do',inverse_name="invoice_id", domain="[('state', '!=', 'draft'),('picking_type_id.code','=','outgoing')]")
    cust_street = fields.Char(string='Street')

    def _create_backorder(self):
        """ This method is called when the user chose to create a backorder. It will create a new
        picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
        """
        res = super(StockPicking, self)._create_backorder()
        res.update({
            'plant_id': res.plant_id.id,
            'warehouse_plant_id': res.warehouse_plant_id.id,
            'is_locked': False,
            'note': '',
            'internal_sale_notes': ''
        })
        res.do_unreserve()
        return res

    def create_invoice(self):
        print('>>> create_invoice(self) here...')
        if self.env.company.id != self.company_id.id:
            raise UserError(_("You cannot create invoice with this current company active"))
        
        # Warning Jika masih ada DO return yg masing gantung
        # origin = "Return of %s" % (self.doc_name,)
        # return_ids = self.env['stock.picking'].search([('sale_id','=', self.sale_id.id),('state','not in',['done','cancel','rejected']),('picking_type_id.code','=','incoming')])
        # if return_ids:
        #     raise UserError(_("You cannot create invoice because you have return not yet validate"))

        origin = "Return of %s" % (self.doc_name,)
        return_ids = self.env['stock.picking'].search([('origin','=', origin),('state','not in',['done','cancel'])])
        if return_ids:
            raise UserError(_("You cannot create invoice because you have return %s not yet validate") % [x.name for x in return_ids])

        # Add validation when invoice can process only when DO already receive
        # Updated By: MIS@SanQua
        # At: 29/12/2021
        # if not self.sent:
        #     raise UserError(_("You can't create invoice because DO not received yet"))
        # If user plant want create invoice of DO Plant to WIM, it must be :
        # 1. check DO WIM to Customer already receive or not.
        # 2. check DO Plant to WIM already receive or not

        if not self.sent:
            raise UserError(_("You can not create invoice because DO not received yet"))

        if self.no_sj_wim:
            if self.env.company.id != self.company_id.id:
                raise UserError(_("You can not create invoice with this current company active"))
            else:
        #       Check if DO Plant to WIM already receive or not
                if not self.sent:
                    raise UserError(_("You can not create invoice because DO not received yet"))
                else:
                    xWIMDO = self.env['stock.picking'].search([('doc_name','=',self.no_sj_wim)])
                    if xWIMDO:
                        if not xWIMDO.sent:
                            raise UserError(_("You can not create invoice because DO WIM to customer not received yet"))
                    else:
                        raise UserError(_("SJ WIM not found"))
        # End Edit by MIS@SanQua

        self = self.filtered(lambda r:r.picking_type_code=='outgoing')
        self.ensure_one()
        self._check_create_invoice()
        
        invoice_id = self.env['account.move'].with_context(default_user_id=self.sale_id.user_id.id).create(self._prepare_invoice(self))
        self.invoice_id = invoice_id
        view = self.env.ref('account.view_move_form')
        return {
            'name': _('Customer Invoice'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'res_id': invoice_id.id,
        }

    # ////////////////////////dipindah ke mis_stock_picking_v1///////////////////////////////
    # print_pick_op_count = fields.Integer(copy=False, default=1)
    # print_int_tf_count = fields.Integer(copy=False, default=1)
    # print_rcv_itm_count = fields.Integer(copy=False, default=1)
    # print_po_rtr_count = fields.Integer(copy=False, default=1)
    # ////////////////////////////////////////////////////////////////////////
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('waiting_approval', 'Waiting Approval'),
    #     ('waiting', 'Waiting Another Operation'),
    #     ('confirmed', 'Waiting'),
    #     ('assigned', 'Ready'),
    #     ('plant-confirmed', 'Confirmed'),
    #     ('done', 'Done'),
    #     ('cancel', 'Cancelled'),
    # ], string='Status', compute='_compute_state',
    #     copy=False, index=True, readonly=True, store=True, tracking=True,
    #     help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
    #          " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
    #          " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
    #          " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
    #          " * Done: The transfer has been processed.\n"
    #          " * Cancelled: The transfer has been cancelled.")

    state = fields.Selection([('draft', 'Draft'),('waiting_approval', 'Waiting Approval'), ('waiting', 'Waiting Another Operation'), ('confirmed', 'Waiting'), (
        'assigned', 'Ready'), ('plant-confirmed', 'Confirmed'), ('done', 'Done'), ('cancel', 'Canceled'), ('rejected', 'Rejected')])

    next_loading_plant_id = fields.Many2one('res.company',string='Next Loading', store=True)

    def action_done(self):
        res = super(StockPicking, self).action_done()
        self.write({'date_received': fields.Datetime.now()})
        return res

    # ////////////////////////dipindah ke mis_stock_picking_v1///////////////////////////////
    # def printing_po_rtr(self):
    #     msgs = []
    #     msgs.append("Purchase Return has printed in %s times"%(self.print_po_rtr_count))
    #     self.message_post(body=msgs[0])
    #     self.print_po_rtr_count += 1

    # def printing_rcv_itm(self):
    #     msgs = []
    #     msgs.append("Receive Items in has printed %s times"%(self.print_rcv_itm_count))
    #     self.message_post(body=msgs[0])
    #     self.print_rcv_itm_count += 1

    # def printing_int_tf(self):
    #     msgs = []
    #     msgs.append("Internal Transfer has printed in %s times"%(self.print_int_tf_count))
    #     self.message_post(body=msgs[0])
    #     self.print_int_tf_count += 1

    # def printing_slip_constrains(self):
    #     msgs = []
    #     msgs.append("Delivery Slips has printed in %s times"%(self.print_count))
    #     self.message_post(body=msgs[0])
    #     self.print_count += 1
    #     if self.print_count > 1:
    #         self.allow_print = False

    # def printing_pick_opr(self):
    #     msgs = []
    #     msgs.append("Picking Operations has printed in %s times"%(self.print_pick_op_count))
    #     self.message_post(body=msgs[0])
    #     self.print_pick_op_count += 1
    # //////////////////////////////////////////////////////////////////////////////////

    # penambahan onchange untuk alamat customer
    @api.onchange('partner_id')
    def _onchange_cust_street(self):
        if self.partner_id:
            self.cust_street = self.partner_id.street
        else:
            self.cust_street = False

    def open_spicks(self):
        for rec in self:
            if rec.company_id.id != self.env.company.id and rec.plant_id.id != self.env.company.id and rec.partner_id != self.env.company.id:
                self.cek_akses = True
                raise UserError(_('You are not allowed to access ! Please check your company  before.'))
            else:
                self.cek_akses = False
                # if self.cek_akses == False and self.location_id.warehouse_id.id not in self.env.user.warehouse_ids.ids and self.location_id.usage not in ('customer','view','supplier','transit','inventory'):
                #     raise UserError(_('You are not allowed to access ! Please check your allowed warehouse before.'))

    def action_confirm(self):

        #Add approval matrix
        for rec in self:
            if rec.location_dest_id.apv_for_matrix:
                self.checking_approval_matrix(add_approver_as_follower=True, data={
                    'state': 'waiting_approval'})
            else:
                self.mark_as_todo()

        return True

    def btn_approve(self):
        print('>>> call btn_approve')
        # raise UserError(_('Click btn_approve'))
        for rec in self:
            rec.approving_matrix(post_action='action_approve_it')

    def btn_reject(self):
        self.rejecting_matrix()
        self.state = 'rejected'

    def action_approve_it(self):
        print('>>> call action_approve_it')
        # raise UserError(_('Click action_approve_it'))
        for rec in self:
            rec.state = 'confirmed'
            rec.mark_as_todo()

    def mark_as_todo(self):
        print('>>> call mark_as_todo')
        # raise UserError(_('Click mark_as_todo'))
        self.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
        # call `_action_confirm` on every draft move
        self.mapped('move_lines') \
            .filtered(lambda move: move.state == 'draft') \
            .sudo()._action_confirm()
        # call `_action_assign` on every confirmed move which location_id bypasses the reservation
        self.filtered(lambda picking: picking.location_id.usage in (
        'supplier', 'inventory', 'production') and picking.state == 'confirmed') \
            .sudo().mapped('move_lines')._action_assign()
        return True

    def sync_api(self,mss=None):
        # print("JALANNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN")
        end_hasil = []
        mss = False
        for x in self.move_ids_without_package:
            hasil = {
            "product_code": x.product_id.code,
            "product_name": x.product_id.name,
            "qty": x.quantity_done,
            "uom_name": x.product_uom.name
            }
            end_hasil.append(hasil)
        ex_type = ['internal','external']
        # print("CARRIER TYPE", self.carrier_type)
        if self.state == 'done' and self.carrier_type in ex_type:
            # print("33333333333333333333333333333333333",",".join(str(e) for e in [x['name'] for x in self.sale_mix_ids]))
            try:
                s_code = [rec.doc_name for rec in self]
                eks_api = self.env['ir.config_parameter'].sudo().search([('key','=','api_ekspedisi')])
                url = eks_api.value
                # print("urlurlurlurl",url)
                # url = "http://10.10.20.5:1196/api/esanqua/expedition/v1/transaction/add_from_external"
                payload = json.dumps({
                    "odoo_order_no": s_code[0],
                    "order_date": str(datetime.strptime(str(self.date_done), '%Y-%m-%d %H:%M:%S').date()),
                    "company_id": self.plant_id.code_plant,
                    "company_name": self.plant_id.name,
                    "expedition_company_id": self.plant_id.code_plant,
                    "expedition_company_name": self.plant_id.name,
                    "sub_customer_odoo_id": self.sudo().partner_id.id,
                    "customer_address": self.sudo().partner_id.street,
                    "loading_from_company_id": self.plant_id.code_plant,
                    "loading_from_company_name": self.plant_id.name,
                    "license_plate": self.fleet_vehicle_id.license_plate,
                    "driver_id": int(self.fleet_driver_id.sanqua_nik),
                    "driver_name": self.fleet_driver_id.name,
                    "carrier_type": self.carrier_type,
                    "so_mix_ref": ",".join(str(e) for e in [x['name'] for x in self.sale_mix_ids]),
                    "so_no": self.sale_id.name,
                    "order_details": end_hasil,
                    "partner_location_id": self.warehouse_plant_id.id,
                    "partner_location_name": self.warehouse_plant_id.name,
                    "other_loading_from_company_id": self.next_loading_plant_id.code_plant,
                    "other_loading_from_company_name": self.next_loading_plant_id.name,
                    "other_loading_res_partner_id": self.sudo().next_loading_plant_id.partner_id.id
                    })
                headers = {'Content-Type': 'application/json'}
                response = requests.request("POST", url,headers=headers, data=payload)
                print('>>>>>>>>>>>>>>>>>>>>>> Response : ' + str(response))
                stat_respon = json.loads(response.text)
                status_respon = stat_respon['status_code']
                status_msg = stat_respon['status_msg']
                # print("STATE NOTE",s_code[0])
                if status_respon == '00':
                    self.sync_btn = False
                else:
                    self.sync_btn = True
                    mss = status_msg
                    print("STATUEEEEEEEEEEEE",mss)
            except Exception as e:
                print('>>> Excep : ' + str(e))
                print('>>> Date: ' + str(datetime.strptime(str(self.scheduled_date), '%Y-%m-%d %H:%M:%S').date()))
                #pass
        return mss

    def btn_plant_confirm(self):
        res = super(StockPicking, self).btn_plant_confirm()
        ex_type = ['internal','external']
        self.sudo().sync_api()
        if self.carrier_type in ex_type:
            print("Disable Notification")
            # if self.sync_btn == True:
            #     message_id = self.env['mymodule.message.wizard'].create({'message': "Sync to expedition failed"+'\n'+"Please sync manually.."})
            #     return {
            #     'name': 'Message',
            #     'type': 'ir.actions.act_window',
            #     'view_mode': 'form',
            #     'res_model': 'mymodule.message.wizard',
            #     'res_id': message_id.id,
            #     'target': 'new'
            #     }
            # else:
            #     message_id = self.env['mymodule.message.wizard'].create({'message': "Congratulations"+'\n'+"Sync to expedition success"})
            #     return {
            #     'name': 'Message',
            #     'type': 'ir.actions.act_window',
            #     'view_mode': 'form',
            #     'res_model': 'mymodule.message.wizard',
            #     'res_id': message_id.id,
            #     'target': 'new'
            #     }
        return res

    def btn_change_partner(self):
        context = dict(self.env.context or {})
        context.update({'active_id':self.id})
        return {
        'name': 'Message',
        'type': 'ir.actions.act_window',
        'res_model': 'query.view.res.partner',
        'view_mode': 'tree',
        'context': context,
        'target': 'new',
        'domain': ['|',('id_rp', '=', self.customer_id.id),('parent', '=', self.customer_id.id)]
        }

    def btn_sync(self):
        # print("999999999999999999999999999",self._butt_dom())
        # self._butt_dom()
        # raise UserError(_("This button still in development"))
        # self.sync_api()
        notes = self.sudo().sync_api()
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        ex_type = ['internal','external']
        if self.carrier_type not in ex_type:
            raise UserError(_("Expedition must Internal or External"))
        # else:
        #     if self.sync_btn == True:
        #         message_id = self.env['mymodule.message.wizard'].create({'message': "Sync to expedition failed"+'\n'+notes+'\n'+"Please try again.."})
        #         return {
        #         'name': 'Message',
        #         'type': 'ir.actions.act_window',
        #         'view_mode': 'form',
        #         'res_model': 'mymodule.message.wizard',
        #         'res_id': message_id.id,
        #         'target': 'new'
        #         }
        #     else:
        #         message_id = self.env['mymodule.message.wizard'].create({'message': "Congratulations"+'\n'+"Sync to expedition success"})
        #         return {
        #         'name': 'Message',
        #         'type': 'ir.actions.act_window',
        #         'view_mode': 'form',
        #         'res_model': 'mymodule.message.wizard',
        #         'res_id': message_id.id,
        #         'target': 'new'
        #         }


class MyModuleMessageWizard(models.TransientModel):
    _name = 'mymodule.message.wizard'
    _description = "Show Message"

    message = fields.Text('Message', required=True)

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}

class DoneAccountMoveLine(models.Model):
    _inherit = 'stock.move'

    @api.onchange('move_line_ids')
    def _qty_done(self):
        count = []
        for data in self.move_line_ids:
            count.append(data.qty_done)
            total_done = sum(count)
            if round(total_done,2) > self.product_uom_qty:
                raise UserError(_('Quantity Done can not more than quantity on SO/PO'))


# class InherQueryResPartner(models.Model):
#     _inherit = 'query.view.res.partner'

#     def cek_id(self):
#         find_p = self.env['stock.picking']
#         for rec in self:
#             act_id = self.env.context.get('active_id')
#             find_p.search([('id','=',act_id)]).partner_id = rec.id_rp
            # print("ID NYAAA", self.env.context.get('active_id'))