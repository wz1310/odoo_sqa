# -*- coding: utf-8 -*-
from odoo import models, fields, api,SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import datetime, timedelta, date
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class InheritPicking(models.Model):
    _inherit = "stock.picking"

    def open_mutasi(self):
        return self.open_mutasi_gln_wizard()

    def open_mutasi_gln_wizard(self,datas=None):
        # all_partner = False
        form = self.env.ref('mis_mutasi_galon.open_mutasi_wizard')
        self.ensure_one()
        context = dict(self.env.context or {})
        partner_id = self.sudo().env['res.partner'].search([('id','=',self.partner_id.id)]).id
        # all_partner = partner_id
        # print("000000000000000",partner_id)
        cd_prd = self.sudo().env['ir.config_parameter'].search([('key','=','galon_kosong')]).value
        done_qty = self.move_ids_without_package.filtered(lambda x:x.product_id.default_code ==cd_prd).product_uom_qty
        ret_qty = self.move_ids_without_package.filtered(lambda x:x.product_id.default_code ==cd_prd).return_qty
        move = self.move_ids_without_package.filtered(lambda x:x.product_id.default_code ==cd_prd)
        m_line = self.env['stock.move.line'].search([('move_id','=',move.id)])
        m_interco_line = self.env['stock.interco.move.line'].search([('move_id','=',move.id)])
        # print("LOTTTTTTTTTTTT",lot_id.name)
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'default_no_sj':self.id,
            'default_partner_id':partner_id,
            'default_done_qty':sum([done_qty])-sum([ret_qty]),
            'default_lot_id':m_interco_line.lot_id.ids if self.interco_master else m_line.lot_id.ids,
            })
        res = {
            'name': "Mutasi Galon",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'show.mutasi.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def button_validates(self):
        print("button_validate picking-=-=-=-=-=-=-")
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # add user as a follower
        self.message_subscribe([self.env.user.partner_id.id])

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        # Propose to use the sms mechanism the first time a delivery
        # picking is validated. Whatever the user's decision (use it or not),
        # the method button_validate is called again (except if it's cancel),
        # so the checks are made twice in that case, but the flow is not broken
        sms_confirmation = self._check_sms_confirmation_popup()
        if sms_confirmation:
            return sms_confirmation

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }
        self.action_dones()
        return

    def action_dones(self):
        """Changes picking state to done by processing the Stock Moves of the Picking

        Normally that happens when the button "Done" is pressed on a Picking view.
        @return: True
        """
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        # Check if there are ops not linked to moves yet
        for pick in self:
            if pick.owner_id:
                pick.move_lines.write({'restrict_partner_id': pick.owner_id.id})
                pick.move_line_ids.write({'owner_id': pick.owner_id.id})

            # # Explode manually added packages
            # for ops in pick.move_line_ids.filtered(lambda x: not x.move_id and not x.product_id):
            #     for quant in ops.package_id.quant_ids: #Or use get_content for multiple levels
            #         self.move_line_ids.create({'product_id': quant.product_id.id,
            #                                    'package_id': quant.package_id.id,
            #                                    'result_package_id': ops.result_package_id,
            #                                    'lot_id': quant.lot_id.id,
            #                                    'owner_id': quant.owner_id.id,
            #                                    'product_uom_id': quant.product_id.uom_id.id,
            #                                    'product_qty': quant.qty,
            #                                    'qty_done': quant.qty,
            #                                    'location_id': quant.location_id.id, # Could be ops too
            #                                    'location_dest_id': ops.location_dest_id.id,
            #                                    'picking_id': pick.id
            #                                    }) # Might change first element
            # # Link existing moves or add moves when no one is related
            for ops in pick.move_line_ids.filtered(lambda x: not x.move_id):
                # Search move with this product
                moves = pick.move_lines.filtered(lambda x: x.product_id == ops.product_id)
                moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
                if moves:
                    ops.move_id = moves[0].id
                else:
                    new_move = self.env['stock.move'].create({
                                                    'name': _('New Move:') + ops.product_id.display_name,
                                                    'product_id': ops.product_id.id,
                                                    'product_uom_qty': ops.qty_done,
                                                    'product_uom': ops.product_uom_id.id,
                                                    'description_picking': ops.description_picking,
                                                    'location_id': pick.location_id.id,
                                                    'location_dest_id': pick.location_dest_id.id,
                                                    'picking_id': pick.id,
                                                    'picking_type_id': pick.picking_type_id.id,
                                                    'restrict_partner_id': pick.owner_id.id,
                                                    'company_id': pick.company_id.id,
                                                   })
                    ops.move_id = new_move.id
                    new_move._action_confirm()
                    todo_moves |= new_move
                    #'qty_done': ops.qty_done})
        todo_moves._action_done(cancel_backorder=True)
        self.write({'date_done': fields.Datetime.now()})
        self._send_confirmation_email()
        return True


class mutasiinfo(models.Model):
    _name = 'mutasi.request'
    _inherit = ["approval.matrix.mixin", 'mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    no_sj = fields.Many2one('stock.picking')
    gln_rusak = fields.Integer()
    # gln_kosong = fields.Integer()
    gln_sqa = fields.Integer()
    gln_lain = fields.Integer()
    qty_pinjam = fields.Integer()
    qty_deposit = fields.Integer()
    # qty_switch = fields.Integer()
    state_mutasi = fields.Selection([
        ('draft', 'Draft'),
        ('wait', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')],
        default='draft')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id)
    note = fields.Text()
    done_qty = fields.Integer()
    lot_id = fields.Char()

    def submit_(self):
        self.checking_approval_matrix(add_approver_as_follower=False, data={
                                      'state_mutasi': 'wait'})

    def approved_(self):
        self.approving_matrix(post_action='action_approve')

    def _fetch_next_seq(self):
        return self.env['ir.sequence'].next_by_code('seq.mutasi.request')

    def action_approve(self):
        if self.done_qty != sum([self.gln_sqa,self.gln_lain,self.qty_pinjam,self.qty_deposit]):
            remaining = self.done_qty - sum([self.gln_sqa,self.gln_lain,self.qty_pinjam,self.qty_deposit])
            raise UserError(_("Proses ini tidak bisa dilanjutkan karena masih ada Remaining Qty %s") % remaining)
        self.name = self._fetch_next_seq()
        # self.name ='MTS/GLN'+'-'+str(self.no_sj.id)
        cek_mutasi = self.sudo().env['master.mutasi'].search([('partner_id','=',self.partner_id.id)])
        dtl_mutasi = self.sudo().env['detail.master.mutasi']
        have_id = cek_mutasi.mutasi_line_ids.mts_id
        sld_awal = cek_mutasi.mutasi_line_ids.search([('state_detail_mutasi','!=','rejected')],order="id desc",limit=1).s_akhir
        if not cek_mutasi.mutasi_line_ids:
            raise UserError ("Saldo awal mutasi galon untuk customer ini belum di tambahkan..")
        dtl_mutasi.sudo().create({
            'info_mutasi':'mutasi',
            'tgl_mutasi': fields.Datetime.now(),
            'mutasi_id':cek_mutasi.id,
            'mts_id':self.id,
            's_awal':sld_awal,
            'qty_pinjam':self.qty_pinjam,
            'deposit':self.qty_deposit,
            'note':self.note,
            'qty_switch':self.gln_lain,
            'gln_rusak':self.gln_rusak,
            's_akhir':sum([sld_awal,self.qty_pinjam,self.qty_deposit]),
            'state_detail_mutasi':'approved'
            })
        # if not have_id:
        #     print("NOT IDIDIDI",len(cek_mutasi.mutasi_line_ids.mts_id.ids))
        #     if len(cek_mutasi.mutasi_line_ids.ids) == 1:
        #         cek_mutasi.mutasi_line_ids.filtered(lambda x: not x.mts_id).write({
        #             'mts_id':self.id,
        #             'qty_pinjam':self.qty_pinjam,
        #             'qty_switch':self.qty_switch,
        #             'gln_rusak':self.gln_rusak,
        #             's_akhir': cek_mutasi.mutasi_line_ids.s_awal + self.qty_pinjam,
        #             'state_detail_mutasi':'approved',
        #             'tgl_mutasi': fields.Datetime.now(),
        #             'no_sj': self.no_sj.id
        #             })
        # if have_id:
        #     print("HAVE >>>>>>>>>>>>have_id")
        #     find_mts = cek_mutasi.mutasi_line_ids.search([('mts_id','=',self.id)])
        #     sld_awal = cek_mutasi.mutasi_line_ids.search([],order="id desc",limit=1).s_akhir
        #     print("COBA CEK NOMOR ID NYA YA",sld_awal)
        #     if find_mts:
        #         find_mts.sudo().write({
        #             'qty_pinjam':self.qty_pinjam,
        #             'qty_switch':self.qty_switch,
        #             'gln_rusak':self.gln_rusak,
        #             's_akhir':find_mts.s_awal+self.qty_pinjam,
        #             'state_detail_mutasi':'approved'                    
        #             })
            # else:
                # cek_mutasi.sudo().create({
                #     'mutasi_line_ids':[(0,0,{
                #         'mutasi_id':cek_mutasi.id,
                #         'mts_id':self.id,
                #         'qty_pinjam':self.qty_pinjam,
                #         'qty_switch':self.qty_switch,
                #         'gln_rusak':self.gln_rusak,
                #         'state_detail_mutasi':'approved'
                #         }) ]
                #     })
                # print("COBA CEK NOMOR ID NYA YA",dtl_mutasi)
                # dtl_mutasi.sudo().create({
                #     'mutasi_id':cek_mutasi.id,
                #     'mts_id':self.id,
                #     's_awal':sld_awal,
                #     'qty_pinjam':self.qty_pinjam,
                #     'qty_switch':self.qty_switch,
                #     'gln_rusak':self.gln_rusak,
                #     's_akhir':sld_awal+self.qty_pinjam,
                #     'state_detail_mutasi':'approved'
                #     })

        # print("CEK MUTTTTTT",have_id)
        # if len(cek_mutasi.mutasi_line_ids.ids) == 1:
        #     have_id = cek_mutasi.mutasi_line_ids.filtered(lambda x:x.mts_id.id == self.id)
        #     if have_id:
        #         print("ADA ID>>>>>>>>>>>>",ada_id)
        #         cek_mutasi.mutasi_line_ids.write({
        #             'mts_id':self.id,
        #             'qty_pinjam':self.qty_pinjam,
        #             'qty_switch':self.qty_switch,
        #             'gln_rusak':self.gln_rusak,
        #             'state_detail_mutasi':'approved'
        #             })
        self.state_mutasi = 'approved'
        self.create_return_stock(self.no_sj)
        # move = self.no_sj.move_ids_without_package.filtered(lambda x:x.product_id.default_code ==cd_prd)
        # m_line = self.env['stock.move.line'].search([('move_id','=',move.id)])
        # interco = self.no_sj.interco_master
        # orderlines = []
        # m_orderlines = []
        # abc = self.lot_id.strip('][').split(', ')
        # if interco:
        #     pick_type = self.env['stock.picking.type'].search([('code','=','mts_transfer'),('company_id','=',self.no_sj.plant_id.id)])
        #     orderlines.append((0, 0, {
        #             'name': move.name,
        #             'product_id': move.product_id.id,
        #             'product_uom_qty': move.product_uom_qty,
        #             'product_uom': move.product_uom.id,
        #             'desc_product': move.desc_product,
        #             'description_picking': move.description_picking,
        #             }))
        #     for x in abc:
        #         m_orderlines.append((0, 0, {
        #             'product_id': move.product_id.id,
        #             'product_uom_id':move.product_uom.id,
        #             'location_id': pick_type.default_location_src_id.id,
        #             'location_dest_id': self.no_sj.warehouse_plant_id.id,
        #             'lot_id': int(x),
        #             'qty_done': sum([z.qty for z in self.no_sj.interco_move_line_ids.filtered(lambda y:y.lot_id.id == int(x))]),
        #             }))
        #     new_picking = self.env['stock.picking'].sudo().create({
        #         'picking_type_id': pick_type.id,
        #         'location_id': pick_type.default_location_src_id.id,
        #         'location_dest_id': self.no_sj.warehouse_plant_id.lot_stock_id.id,
        #         'sale_id': self.no_sj.sale_id.id,
        #         'plant_id': self.no_sj.company_id.id,
        #         'move_ids_without_package':orderlines,
        #         })
        #     new_picking.action_confirm()
        #     new_picking.move_line_ids.sudo().unlink()
        #     movex_id = new_picking.move_ids_without_package.filtered(lambda x:x.product_id.default_code ==cd_prd)
        #     for x in abc:
        #         cr_mline = self.env['stock.move.line'].create({
        #             'location_id': pick_type.default_location_src_id.id,
        #             'location_dest_id': self.no_sj.warehouse_plant_id.lot_stock_id.id,
        #             'picking_id':new_picking.id,
        #             'move_id':movex_id._origin.id,
        #             'product_id':movex_id.product_id.id,
        #             'product_uom_id':movex_id.product_uom.id,
        #             'lot_id': int(x),
        #             'qty_done':sum([z.qty for z in self.no_sj.interco_move_line_ids.filtered(lambda y:y.lot_id.id == int(x))]),
        #             })
        #         cr_mline.write({
        #             'move_id':movex_id.id
        #             })
        #     new_picking.write({
        #         'partner_id':False
        #         })
        #     new_picking.button_validate()

    def create_return_stock(self,sj_number=None):
        cd_prd = self.sudo().env['ir.config_parameter'].search([('key','=','galon_kosong')]).value
        new_data = {}
        move = sj_number.move_ids_without_package.filtered(lambda x:x.product_id.default_code ==cd_prd)
        m_line = self.env['stock.move.line'].search([('move_id','=',move.id)])
        interco = sj_number.interco_master
        orderlines = []
        MoveLine = self.env['stock.move.line']
        abc = self.lot_id.strip('][').split(', ')
        if interco:
            pick_type = self.env['stock.picking.type'].search([('code','=','mts_transfer'),('company_id','=',sj_number.plant_id.id)])
            orderlines.append((0, 0, {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'product_uom_qty': move.product_uom_qty,
                    'product_uom': move.product_uom.id,
                    'desc_product': move.desc_product,
                    'description_picking': move.description_picking,
                    'state': 'confirmed'
                    }))
            new_picking = self.env['stock.picking'].sudo().create({
                'partner_id':False,
                'picking_type_id': pick_type.id,
                'location_id': pick_type.default_location_src_id.id,
                'location_dest_id': sj_number.warehouse_plant_id.lot_stock_id.id,
                'sale_id': sj_number.sale_id.id,
                'plant_id': sj_number.company_id.id,
                'descript': "Mutasi Galon Customer :"+' '+sj_number.partner_id.name,
                'move_ids_without_package':orderlines,
                })
            new_picking.action_confirm()
            new_picking.move_line_ids.sudo().unlink()
            movex_id = new_picking.move_ids_without_package.filtered(lambda x:x.product_id.default_code ==cd_prd)
            for x in abc:
                cr_mline = self.env['stock.move.line'].create({
                    'location_id': pick_type.default_location_src_id.id,
                    'location_dest_id': new_picking.location_dest_id.id,
                    'picking_id':new_picking.id,
                    'move_id':movex_id._origin.id,
                    'product_id':movex_id.product_id.id,
                    'product_uom_id':movex_id.product_uom.id,
                    'lot_id': int(x),
                    # 'qty_done':sum([z.qty for z in sj_number.interco_move_line_ids.filtered(lambda y:y.lot_id.id == int(x))]),
                    'qty_done':sum([self.gln_sqa,self.gln_lain])
                    })
            new_picking.button_validates()
        else:
            pick_type = self.env['stock.picking.type'].search([('code','=','mts_transfer'),('company_id','=',sj_number.location_id.company_id.id)])
            orderlines.append((0, 0, {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'product_uom_qty': move.product_uom_qty,
                    'product_uom': move.product_uom.id,
                    'desc_product': move.desc_product,
                    'description_picking': move.description_picking,
                    'state': 'confirmed'
                    }))
            new_picking = self.env['stock.picking'].sudo().create({
                'picking_type_id': pick_type.id,
                'location_id': pick_type.default_location_src_id.id,
                'location_dest_id': sj_number.location_id.id,
                'sale_id': sj_number.sale_id.id,
                'plant_id': sj_number.company_id.id,
                'descript': "Mutasi Galon Customer :"+' '+sj_number.partner_id.name,
                'move_ids_without_package':orderlines,
                })
            new_picking.action_confirm()
            new_picking.move_line_ids.sudo().unlink()
            movex_id = new_picking.move_ids_without_package.filtered(lambda x:x.product_id.default_code ==cd_prd)
            for x in abc:
                cr_mline = self.env['stock.move.line'].create({
                    'location_id': pick_type.default_location_src_id.id,
                    'location_dest_id': sj_number.location_id.id,
                    'picking_id':new_picking.id,
                    'move_id':movex_id._origin.id,
                    'product_id':movex_id.product_id.id,
                    'product_uom_id':movex_id.product_uom.id,
                    'lot_id': int(x),
                    # 'qty_done':sum([z.qty_done for z in sj_number.move_line_ids.filtered(lambda y:y.lot_id.id == int(x))]),
                    'qty_done':sum([self.gln_sqa,self.gln_lain])
                    })
            new_picking.button_validate()

    def draft_(self):
        self.state_mutasi = 'draft'

    def rejected_(self):
        return self.reject_wizard()

    # def rejected_(self):
    #     self.state_mutasi = 'rejected'

    # def rejected_(self):

    #     form = self.env.ref('approval_matrix.message_post_wizard_form_view')
    #     context = dict(self.env.context or {})
    #     context.update({'default_prefix_message': "<h4>Rejecting Mutasi Galon</h4>",
    #                    "default_suffix_action": "btn_reject"})  # uncomment if need append context
    #     context.update({'active_id': self.id, 'active_ids': self.ids,
    #                    'active_model': 'mutasi.request'})
    #     res = {
    #         'name': "%s - %s" % (_('Rejecting Mutasi Galon Request'), self.name),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'message.post.wizard',
    #         'view_id': form.id,
    #         'type': 'ir.actions.act_window',
    #         'context': context,
    #         'target': 'new'
    #     }
    #     return res

    def reject_wizard(self):
        self.ensure_one()

        # datas = self.action_show_fpm(datas)        
        form = self.env.ref('mis_mutasi_galon.open_mutasi_reject_wizard')
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'active_model':'mutasi.request'})
        # print("context",context)
        res = {
            'name': "%s - %s" % (_('Reject detail'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mutasi.reject.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res


class reject(models.TransientModel):
    _name = 'mutasi.reject.wizard'

    reject_detail = fields.Text('Detail reject')


    def confirm_reject(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        if not res_id or not model:
            raise UserError("Require to get context active id and active model!")
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)

        if len(Record):
            msgs = []
            if not self.reject_detail:
                raise UserError("Please fill detail..")
            Record.sudo().write({
                'note':self.env.user.name+' : '+self.reject_detail,
                'state_mutasi':'rejected'
                })
            master_mutasi = self.env['detail.master.mutasi'].search([('mts_id','=',Record.id)])
            if master_mutasi:
                master_mutasi.write({
                    'state_detail_mutasi':'rejected',
                    'note':self.reject_detail
                    })
            msgs.append("Mutasi Galon %s Rejected"%(Record.name))
            Record.message_post(body=msgs[0])


class mutasigalon(models.TransientModel):
    _name = 'show.mutasi.wizard'
    _inherit = ["approval.matrix.mixin", 'mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self,fields):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)


        res = super(mutasigalon,self).default_get(fields)
        b_line = []
        no_mutasi = self.env['mutasi.request'].search([('no_sj','=',res_id),('state_mutasi','!=','rejected')])
        if no_mutasi:
            res.update({
                'mts_id':no_mutasi.id,
                'name':no_mutasi.name,
                'no_sj':no_mutasi.no_sj.id,
                'gln_rusak':no_mutasi.gln_rusak,
                # 'gln_kosong':no_mutasi.gln_kosong,
                'gln_sqa':no_mutasi.gln_sqa,
                'gln_lain':no_mutasi.gln_lain,
                'qty_pinjam':no_mutasi.qty_pinjam,
                'qty_deposit':no_mutasi.qty_deposit,
                'note':no_mutasi.note,
                # 'qty_switch':no_mutasi.qty_switch,
                'state_mutasi':no_mutasi.state_mutasi,
                'company_id':no_mutasi.company_id.id,
                'approved':no_mutasi.approved,
                'approval_ids':no_mutasi.approval_ids.ids,
                'user_can_approve':no_mutasi.user_can_approve
                })
        # for x in Record.bom_line_ids:
        #     line = (0,0,{
        #         'company_id':x.company_id.id,
        #         'bom_id':x.bom_id.id,
        #         'product_id':x.product_id.id,
        #         'product_uom_id':x.product_uom_id.id,
        #         'product_qty':x.product_qty,
        #         'product_uom_category_id':x.product_uom_category_id.id
        #         })
        #     b_line.append(line)
        # res.update({'bom_line_ids':b_line})
        return res


    # bom_line_ids = fields.One2many('show.bom.wizard.line', 'bom_id')
    mts_id = fields.Many2one('mutasi.request')
    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    no_sj = fields.Many2one('stock.picking')
    gln_rusak = fields.Integer()
    # gln_kosong = fields.Integer()
    gln_sqa = fields.Integer()
    gln_lain = fields.Integer()
    qty_pinjam = fields.Integer()
    qty_deposit = fields.Integer()
    # qty_switch = fields.Integer()
    state_mutasi = fields.Selection([
        ('draft', 'Draft'),
        ('wait', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')],
        default='draft')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id)
    user_can_approve = fields.Boolean(related='mts_id.user_can_approve',string="User can approve")
    approval_ids = fields.One2many(related='mts_id.approval_ids')
    note = fields.Text()
    done_qty = fields.Integer()
    lot_id = fields.Char()
    remain_qty = fields.Integer(compute='remains_qty')

    # @api.depends('gln_kosong','qty_pinjam')
    @api.onchange('gln_sqa','gln_lain','qty_pinjam','qty_deposit')
    def remains_qty(self):
        for rec in self:
            # rec.remain_qty = rec.done_qty - sum([rec.gln_kosong,rec.qty_pinjam])
            rec.remain_qty = rec.done_qty - sum([rec.gln_sqa,rec.gln_lain,rec.qty_pinjam,rec.qty_deposit])

    # @api.onchange('gln_lain')
    # def onch_gln_lain(self):
    #     self.qty_switch = self.gln_lain
    #     self.gln_kosong = self.gln_lain + self.gln_sqa
        # self.qty_pinjam = self.done_qty - (self.gln_kosong+self.gln_rusak)

    # @api.onchange('gln_sqa')
    # def onch_gln_sqa(self):
    #     self.gln_kosong = self.gln_lain + self.gln_sqa
        # self.qty_pinjam = self.done_qty - (self.gln_kosong+self.gln_rusak)

    # @api.onchange('gln_rusak')
    # def onch_gln_rusak(self):
    #     self.qty_pinjam = self.done_qty - (self.gln_kosong+self.gln_rusak)

    def get_mutasi(self):
        res_id = self._context.get('active_id')
        no_mutasi = self.sudo().env['mutasi.request'].search([('no_sj','=',res_id)])

        return no_mutasi

    def get_pre_wizard(self):
        form = self.env.ref('mis_mutasi_galon.open_mutasi_wizard')
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({
            'active_id':self.id,
            'active_ids':self.ids,
            'default_mts_id':self.mts_id.id,
            'default_name':self.mts_id.name,
            'default_no_sj':self.mts_id.no_sj.id,
            'default_partner_id':self.mts_id.partner_id.id,
            'default_gln_rusak':self.mts_id.gln_rusak,
            # 'default_gln_kosong':self.mts_id.gln_kosong,
            'default_gln_sqa':self.mts_id.gln_sqa,
            'default_gln_lain':self.mts_id.gln_lain,
            'default_qty_pinjam':self.mts_id.qty_pinjam,
            'default_qty_deposit':self.mts_id.qty_deposit,
            'default_note':self.mts_id.note,
            # 'default_qty_switch':self.mts_id.qty_switch,
            'default_state_mutasi':self.mts_id.state_mutasi,
            'default_approval_ids':self.mts_id.approval_ids.ids,
            'default_approved':self.mts_id.approved,
            'default_user_can_approve':self.mts_id.user_can_approve,
            })
        res = {
            'name': "Mutasi Galon",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'show.mutasi.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def draft_(self):
        self.mts_id.draft_()
        return self.get_pre_wizard()

    def fetch_mtx(self):
        self.mts_id.submit_()
        return self.get_pre_wizard()

    def approved_(self):
        if self.remain_qty != 0:
            raise UserError(_("Proses ini tidak bisa dilanjutkan karena masih ada Remaining Qty %s") % self.remain_qty)
        self.mts_id.write({
            'no_sj':self.no_sj.id,
            'partner_id':self.partner_id.id,
            'gln_rusak':self.gln_rusak,
            # 'gln_kosong':self.gln_kosong,
            'gln_sqa':self.gln_sqa,
            'gln_lain':self.gln_lain,
            'qty_pinjam':self.qty_pinjam,
            'qty_deposit':self.qty_deposit,
            'note':self.note,
            # 'qty_switch':self.qty_switch,
            'state_mutasi':self.state_mutasi,
            'company_id':self.company_id.id,
            })
        self.mts_id.approved_()
        return self.get_pre_wizard()

    def submit_(self):
        # if self.remain_qty > 0:
        #     raise UserError(_("Proses ini tidak bisa dilanjutkan karena masih ada Remaining Qty %s") % self.remain_qty)
        if self.remain_qty != 0:
            context = dict(self.env.context)
            context.update({
                'mts_id':self.mts_id.id,
                'lot_id':self.lot_id,
                'done_qty':self.done_qty,
                'no_sj':self.no_sj.id,
                'partner_id':self.partner_id.id,
                'gln_rusak':self.gln_rusak,
                # 'gln_kosong':self.gln_kosong,
                'gln_sqa':self.gln_sqa,
                'gln_lain':self.gln_lain,
                'qty_pinjam':self.qty_pinjam,
                'qty_deposit':self.qty_deposit,
                'note':self.note,
                # 'qty_switch':self.qty_switch,
                'state_mutasi':self.state_mutasi,
                'company_id':self.company_id.id,
                })
            message_id = self.env['info.message.wizard'].create({'message': "Masih ada remaining qty"+' '+str(self.remain_qty)+'\n'+"Apakah anda yakin untuk melanjutkan?"})
            return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'info.message.wizard',
            'context': context,
            'res_id': message_id.id,
            'target': 'new'
            }
        mts_id = False
        if not self.mts_id:
            mts_id = self.env['mutasi.request'].create(
                {
                'no_sj':self.no_sj.id,
                'partner_id':self.partner_id.id,
                'gln_rusak':self.gln_rusak,
                # 'gln_kosong':self.gln_kosong,
                'gln_sqa':self.gln_sqa,
                'gln_lain':self.gln_lain,
                'qty_pinjam':self.qty_pinjam,
                'qty_deposit':self.qty_deposit,
                'note':self.note,
                # 'qty_switch':self.qty_switch,
                'state_mutasi':self.state_mutasi,
                'company_id':self.company_id.id,
                })
            self.mts_id = mts_id.id
        self.mts_id.write({
            'no_sj':self.no_sj.id,
            'partner_id':self.partner_id.id,
            'gln_rusak':self.gln_rusak,
            # 'gln_kosong':self.gln_kosong,
            'gln_sqa':self.gln_sqa,
            'gln_lain':self.gln_lain,
            'qty_pinjam':self.qty_pinjam,
            'qty_deposit':self.qty_deposit,
            'note':self.note,
            # 'qty_switch':self.qty_switch,
            'state_mutasi':self.state_mutasi,
            'company_id':self.company_id.id,
            })
        self.mts_id.submit_()
        # return self.get_pre_wizard()

    def rejected_(self):
        return self.mts_id.rejected_()


    def confirms_(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)
        no_mutasi = self.env['mutasi.request'].search([('no_sj','=',res_id)])
        # if no_mutasi:
        if self.mts_id:
            self.mts_id.update({
                'no_sj':self.no_sj.id,
                # 'gln_kosong':self.gln_kosong,
                'gln_rusak':self.gln_rusak,
                'gln_sqa':self.gln_sqa,
                'gln_lain':self.gln_lain,
                'qty_pinjam':self.qty_pinjam,
                'qty_deposit':self.qty_deposit,
                'note':self.note,
                # 'qty_switch':self.qty_switch,
                'state_mutasi':self.state_mutasi,
                'company_id':self.company_id.id,
                })
        else:
            self.env['mutasi.request'].create(
                {
                'no_sj':self.no_sj.id,
                # 'gln_kosong':self.gln_kosong,
                'gln_rusak':self.gln_rusak,
                'gln_sqa':self.gln_sqa,
                'gln_lain':self.gln_lain,
                'qty_pinjam':self.qty_pinjam,
                'qty_deposit':self.qty_deposit,
                'note':self.note,
                # 'qty_switch':self.qty_switch,
                'state_mutasi':self.state_mutasi,
                'company_id':self.company_id.id,
                })
        self.search([('no_sj','=',self.no_sj.id)]).unlink()
        # Record.bom_line_ids.unlink()
        # update = []
        # for x in self.bom_line_ids:
        #     update.append((0,0,{
        #                     'company_id' : Record.company_id.id,
        #                     'bom_id' : Record.id,
        #                     'product_id' : x.product_id.id,
        #                     'product_uom_id' : x.product_uom_id.id,
        #                     'product_qty' : x.product_qty,
        #                     'product_uom_category_id':x.product_uom_category_id.id
        #                     }))
        # Record.update({'bom_line_ids':update})
        # self.bom_line_ids.unlink()
        # return {"type": "set_scrollTop"}


class mastermutasi(models.Model):
    _name = 'master.mutasi'
    _inherit = ["approval.matrix.mixin", 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute="onc_prt")
    partner_id = fields.Many2one('res.partner')
    code = fields.Char(compute="onc_prt", store=True)
    mutasi_line_ids = fields.One2many('detail.master.mutasi','mutasi_id')
    sum_s_awal = fields.Integer(compute='summary_mutasi')
    sum_deposit = fields.Integer(compute='summary_mutasi')
    sum_qty_pinjam = fields.Integer(compute='summary_mutasi')
    sum_qty_switch = fields.Integer(compute='summary_mutasi')
    sum_gln_rusak = fields.Integer(compute='summary_mutasi')
    sum_s_akhir = fields.Integer(compute='summary_mutasi')

    @api.depends('partner_id')
    def onc_prt(self):
        for x in self:
            if x.partner_id:
                x.code = x.partner_id.code
                x.name = 'MUTASI'+' '+'('+str(x.partner_id.code)+' '+str(x.partner_id.name)+')'
            else:
                x.code = ""
                x.name = ""
        # if self.partner_id:
        #     self.code = self.partner_id.code
        #     self.name = 'MUTASI'+' '+'('+str(self.partner_id.code)+' '+str(self.partner_id.name)+')'
        # else:
        #     self.code = ""
        #     self.name = ""

    def summary_mutasi(self):
        # saldo = self.mutasi_line_ids.search([('state_detail_mutasi','!=','rejected')],order="id desc",limit=1)
        # total_d = sum([x.deposit for x in self.mutasi_line_ids if x.state_detail_mutasi!='rejected'])
        # total_qp = sum([x.qty_pinjam for x in self.mutasi_line_ids if x.state_detail_mutasi!='rejected'])
        # total_qs = sum([x.qty_switch for x in self.mutasi_line_ids if x.state_detail_mutasi!='rejected'])
        # total_gr = sum([x.gln_rusak for x in self.mutasi_line_ids if x.state_detail_mutasi!='rejected'])

        for x in self:
            saldo = x.mutasi_line_ids.search([('state_detail_mutasi','!=','rejected'),('partner_id','=',x.partner_id.id)],order="id desc",limit=1)
            total_qp = sum([x.qty_pinjam for x in self.mutasi_line_ids.search([('partner_id','=',x.partner_id.id)]) if x.state_detail_mutasi!='rejected' and x.partner_id.id ==x.partner_id.id])
            total_d = sum([x.deposit for x in self.mutasi_line_ids.search([('partner_id','=',x.partner_id.id)]) if x.state_detail_mutasi!='rejected'])
            total_qs = sum([x.qty_switch for x in self.mutasi_line_ids.search([('partner_id','=',x.partner_id.id)]) if x.state_detail_mutasi!='rejected'])
            total_gr = sum([x.gln_rusak for x in self.mutasi_line_ids.search([('partner_id','=',x.partner_id.id)]) if x.state_detail_mutasi!='rejected'])
            x.sum_s_awal = saldo.s_awal if saldo.s_awal else x.sum_s_awal
            x.sum_deposit = total_d if total_d else x.sum_deposit
            x.sum_qty_pinjam = total_qp if total_qp else x.sum_qty_pinjam
            x.sum_qty_switch = total_qs if total_qs else x.sum_qty_switch
            x.sum_gln_rusak = total_gr if total_gr else x.sum_gln_rusak
            x.sum_s_akhir = saldo.s_akhir if saldo.s_akhir else x.sum_s_akhir
            # self.saldo_awal = self.s_awal + self.qty_pinjam


class detailmastermutasi(models.Model):
    _name = 'detail.master.mutasi'
    _inherit = ["approval.matrix.mixin", 'mail.thread', 'mail.activity.mixin']

    mts_id = fields.Many2one('mutasi.request')
    s_awal = fields.Integer()
    deposit = fields.Integer()
    qty_pinjam = fields.Integer()
    qty_switch = fields.Integer()
    s_akhir = fields.Integer()
    gln_rusak = fields.Integer()
    partner_id = fields.Many2one('res.partner',related='mutasi_id.partner_id')
    mutasi_id = fields.Many2one('master.mutasi')
    state_detail_mutasi = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected')])
    info_mutasi = fields.Selection([
        ('adjust', 'Adjustment'),
        ('sld_awl', 'Saldo awal'),
        ('mutasi', 'Mutasi')
        ], required=True, default=False)
    tgl_mutasi = fields.Datetime(default=fields.Datetime.now())
    no_sj = fields.Many2one('stock.picking')
    note = fields.Text()

    # @api.onchange('s_awal','deposit','qty_pinjam','qty_switch','gln_rusak')
    @api.onchange('s_awal','deposit','qty_pinjam','qty_switch','gln_rusak')
    def onch_gln_lain(self):
        self.s_akhir = sum([self.s_awal,self.deposit,self.qty_pinjam])


class InfoMessageWizard(models.TransientModel):
    _name = 'info.message.wizard'
    _description = "Show Message"

    message = fields.Text('Message', required=True)

    def action_close(self):
        context = dict(self.env.context)
        if not context['mts_id']:
            mts_id = self.env['mutasi.request'].create(
                {
                'no_sj':context['no_sj'],
                'partner_id':context['partner_id'],
                'gln_rusak':context['gln_rusak'],
                # 'gln_kosong':context['gln_kosong'],
                'gln_sqa':context['gln_sqa'],
                'gln_lain':context['gln_lain'],
                'qty_pinjam':context['qty_pinjam'],
                'qty_deposit':context['qty_deposit'],
                # 'qty_switch':context['qty_switch'],
                'state_mutasi':context['state_mutasi'],
                'company_id':context['company_id'],
                })
            self.mts_id = mts_id.id
            mts_id.submit_()
        else:
            f_mutasi = self.env['mutasi.request'].search([('id','=',context['mts_id'])])
            f_mutasi.write({
                'no_sj':context['no_sj'],
                'partner_id':context['partner_id'],
                'gln_rusak':context['gln_rusak'],
                # 'gln_kosong':context['gln_kosong'],
                'gln_sqa':context['gln_sqa'],
                'gln_lain':context['gln_lain'],
                'qty_pinjam':context['qty_pinjam'],
                'qty_deposit':context['qty_deposit'],
                # 'qty_switch':context['qty_switch'],
                'state_mutasi':context['state_mutasi'],
                'company_id':context['company_id'],
                })
            f_mutasi.submit_()
        return {'type': 'ir.actions.act_window_close'}


class adjustmutasiinfo(models.Model):
    _name = 'adjust.mutasi.request'
    _inherit = ["approval.matrix.mixin", 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(default="/")
    no_det_mts_gln = fields.Many2one('detail.master.mutasi')
    id_mts_customer = fields.Many2one('master.mutasi')
    deposit = fields.Integer()
    gln_rusak = fields.Integer()
    qty_pinjam = fields.Integer()
    qty_switch = fields.Integer()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wait', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')],
        default='draft')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id)
    note = fields.Text()
    lot_id = fields.Char()
    sum_s_awal = fields.Integer()
    sum_deposit = fields.Integer()
    sum_qty_pinjam = fields.Integer()
    sum_qty_switch = fields.Integer()
    sum_gln_rusak = fields.Integer()
    sum_s_akhir = fields.Integer()
    date = fields.Datetime()


    @api.onchange('id_mts_customer')
    def remains_qty(self):
        for x in self:
            if x.id_mts_customer:
                # x.partner_id = x.id_mts_customer.partner_id.id
                x.sum_s_awal = x.id_mts_customer.sum_s_awal
                x.sum_deposit = x.id_mts_customer.sum_deposit
                x.sum_qty_pinjam = x.id_mts_customer.sum_qty_pinjam
                x.sum_qty_switch = x.id_mts_customer.sum_qty_switch
                x.sum_gln_rusak = x.id_mts_customer.sum_gln_rusak
                x.sum_s_akhir = x.id_mts_customer.sum_s_akhir
            else:
                # x.partner_id = x.partner_id
                x.sum_s_awal = x.sum_s_awal
                x.sum_deposit = x.sum_deposit
                x.sum_qty_pinjam = x.sum_qty_pinjam
                x.sum_qty_switch = x.sum_qty_switch
                x.sum_gln_rusak = x.sum_gln_rusak
                x.sum_s_akhir = x.sum_s_akhir

    def submit_(self):
        self.checking_approval_matrix(add_approver_as_follower=False, data={
                                      'state': 'wait'})
        self.name = self._fetch_next_seq()

    def approved_(self):
        self.approving_matrix(post_action='action_approve')

    def _fetch_next_seq(self):
        return self.env['ir.sequence'].next_by_code('seq.adjust.mutasi.request')

    def action_approve(self):
        dt_mutasi_request = self.env['detail.master.mutasi'].sudo().create({
            'info_mutasi': 'adjust',
            'mutasi_id': self.id_mts_customer.id,
            'tgl_mutasi': fields.Datetime.now(),
            'partner_id': self.id_mts_customer.partner_id.id,
            's_awal': self.id_mts_customer.sum_s_akhir,
            'deposit': self.deposit,
            'qty_pinjam': self.qty_pinjam,
            'qty_switch': self.qty_switch,
            'gln_rusak': self.gln_rusak,
            'note': str(self.name)+'\n'+self.note if self.note else str(self.name)+'\n'+'',
            's_akhir': sum([self.id_mts_customer.sum_s_akhir,self.deposit,self.qty_pinjam]),
            'state_detail_mutasi': 'approved'
            })
        self.no_det_mts_gln = dt_mutasi_request.id
        self.date = fields.Datetime.now()
        self.state = 'approved'

    def rejected_(self):
        self.no_det_mts_gln.write({
            'state_detail_mutasi':'rejected'
            })
        self.state = 'rejected'

class StockPickingTypeInherit(models.Model):
    _inherit = 'stock.picking.type'

    code = fields.Selection(selection_add=[
        ('warehouse_transfer', 'Warehouse Transfer'),
        ('mts_transfer', 'Mutasi Transfer')
        ])


class SaleOrderMts(models.Model):
    _inherit = 'sale.order'


    def _copy_selected_interco_move_line(self):
        print("MTS SALEEEEE")
        if self.state=='draft':
            raise ValidationError(_("You should checklist automatic validation for intercompany confirmation picking %s/%s") % (self.env.company.display_name,self.sudo().company_id.display_name))
        self.ensure_one()
        self = self.with_user(SUPERUSER_ID).with_context(force_company=self.company_id.id,allowed_company_ids=self.company_id.ids+self.company_id.ids)

        self.picking_ids.filtered(lambda r:r.state=='assigned').do_unreserve()


        IntercoMoveLine = self.env['stock.interco.move.line']
        MoveLine = self.env['stock.move.line']
        skip_moves = self.env['stock.move']
        for picking in self.origin_interco_order_id.picking_ids.filtered(lambda r:r.picking_type_id.code=='outgoing' and r.state not in ['draft','cancel','done']):
            # picking = picking on source (WIM)
            # self = self order in plant
            movesstatus = {}
            for move in picking.move_lines.sorted('product_uom_qty', reverse=True):
                # move = move in picking (WIM)

                # origin_interco_move_lines = picking.interco_move_line_ids.filtered(lambda r: \
                #     r.product_id.id==move.product_id.id \
                #     and r.move_id.id == move.id)

                origin_interco_move_lines = move.interco_move_line_ids
                if len(origin_interco_move_lines):
                    for origin_interco_move_line in origin_interco_move_lines:
                        new_data = {}
                        # interco_data = origin_interco_move_line._convert_to_write({name: getattr(origin_interco_move_line, name) for name in origin_interco_move_line._fields})
                        # interco_move = stock.move() -> with company "Plant"

                        interco_move = self.picking_ids.filtered(lambda r:r.picking_type_id.code=='outgoing') \
                            .mapped('move_lines') \
                            .filtered(lambda r:r.product_id.id==move.product_id.id and r.id not in skip_moves.ids and r.sale_line_id.product_uom_qty>=origin_interco_move_line.qty).sorted('product_uom_qty', reverse=False) # find same move on interco move from origin interco move
                        if len(interco_move)>1:
                            # find move with product_uom_qty == WIM->product_uom_qty(matched)
                            new_interco_move = interco_move.filtered(lambda r:r.product_uom_qty==move.interco_move_line_qty_done)
                            if len(new_interco_move)>1:
                                # ordered = interco_move.sorted('qty')
                                interco_move = new_interco_move[0]
                                
                            elif len(new_interco_move)==0:
                                interco_move = interco_move.filtered(lambda r:r.product_uom_qty<=move.product_uom_qty)[0]
                            elif len(new_interco_move)==1:
                                interco_move = new_interco_move
                        exist_move = movesstatus.get(str(interco_move.id))
                        if not len(interco_move):
                            raise ValidationError(_("No Interco Move Reference Found:Err 2001"))

                        if exist_move:
                            after_qty = float(exist_move)+origin_interco_move_line.qty
                            movesstatus.update({str(interco_move.id):after_qty})
                            if after_qty >= interco_move.sale_line_id.product_uom_qty:
                                skip_moves += interco_move
                        else:
                            # if not registered
                            after_qty = origin_interco_move_line.qty
                            movesstatus.update({str(interco_move.id):after_qty})
                            if after_qty >= interco_move.sale_line_id.product_uom_qty:
                                skip_moves += interco_move

                        cd_prd = self.sudo().env['ir.config_parameter'].search([('key','=','galon_kosong')]).value
                        lct_gln = self.sudo().env['ir.config_parameter'].search([('key','=','transit_galon')]).value
                        new_data.update(dict(
                            product_id=interco_move.product_id.id, 
                            product_uom_id=interco_move.product_id.uom_id.id,
                            picking_id=interco_move.picking_id.id, 
                            move_id=interco_move.id, 
                            lot_id=origin_interco_move_line.lot_id.id, 
                            qty_done=origin_interco_move_line.qty,
                            # merubah default location ketika create account move line
                            location_id=interco_move.location_id.id,
                            # location_id=origin_interco_move_line.src_location_id.id,
                            location_dest_id=interco_move.location_dest_id.id if cd_prd not in interco_move.product_id.default_code else int(lct_gln),
                            company_id=self.company_id.id))
                        
                        
                        
                        mvl = MoveLine.new(new_data)
                        mvl.onchange_product_id()
                        
                        new_mvl = mvl._convert_to_write({name:mvl[name] for name in mvl._cache})
                        created_obj = MoveLine.create(new_data)

#     def _assign_interco_move_line_availability(self):
#         self.ensure_one()
#         MoveLine = self.env['stock.move.line']
#         if self.interco_master == True and self.picking_type_code == 'outgoing':
#             for line in self.interco_move_line_ids:

#                 company_lot_id = self.env['stock.production.lot'].fetch_company_lot(lot=line.with_user(
#                     self.company_id.intercompany_user_id.id).lot_id, company=self.company_id)
#                 assert len(company_lot_id) == 1, "Should only 1 Lot found! But found %s lot within name:%s" % (
#                     len(company_lot_id), line.lot_id.name)

#                 # available = self.env['stock.quant'].with_user(SUPERUSER_ID)._get_available_quantity(line.move_id.product_id, self.location_id, package_id=None, owner_id=None, strict=True)
#                 available = line.product_id.with_context(
#                     force_company=2, allowed_company_ids=[2]).with_user(1).free_qty

#                 print('>>> _assign_interco_move_line_availability(self)')
#                 print('------------------------------------------------')
#                 print('picking_id : ' + str(line.move_id.picking_id.id))
#                 print('location_id : ' +
#                       str(line.picking_id.location_id.id))
#                 print('location_dest_id : ' +
#                       str(line.picking_id.location_dest_id.id))

#                 # PCI Version
#                 cd_prd = self.sudo().env['ir.config_parameter'].search([('key','=','galon_kosong')]).value
#                 new_mvl = MoveLine.create(dict(product_id=line.product_id.id, product_uom_id=line.product_id.uom_id.id, picking_id=line.move_id.picking_id.id, move_id=line.move_id.id,
#                                           lot_id=company_lot_id.id, qty_done=line.qty,
#                                           location_dest_id=line.picking_id.location_id.id if cd_prd not in line.product_id.default_code else 8519,
#                                           location_id=line.picking_id.location_dest_id.id, company_id=self.company_id.id))
#                 print('>>> New_Mvl_ID!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! : ' + str(new_mvl.id))
#                 # MIS@SanQua Update
#                 # Date: 13/10/2021
#                 # Note: This update purpose is to handle journal of WIM/OUT that not correct.
#                 update_mvl = self.env['stock.move.line'].search([('id', '=', new_mvl.id)]).write(
#                     {'location_id': line.picking_id.location_id.id, 'location_dest_id': line.picking_id.location_dest_id.id if cd_prd not in line.product_id.default_code else 8519})
#                 # print('>>> update_mvl : ' + str(update_mvl))