# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError,RedirectWarning,AccessError
from datetime import timedelta
import re
import datetime

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # test_column_1 = fields.Many2one('res.company',
    #                                 string="Test Column",
    #                                 required=False,
    #                                 ondelete="restrict",
    #                                 track_visibility="onchange",
    #                                 check_company=False,
    #                                 context={'all_companies':True})
    whs = fields.Many2one('stock.warehouse', string="Warehouse")


    @api.depends('partner_id')
    def _compute_partner_pricelist_ids(self):
        for rec in self:
            rec.partner_pricelist_ids = rec.partner_id.partner_pricelist_ids.filtered(lambda x:x.company_id.id==self.company_id.id)
            rec._set_status_so()

    @api.onchange('plant_id')
    def _onchange_plant(self):
        self.whs = False

    @api.onchange('date_order_mask')
    def _onchange_date_order_mask(self):
        self.ensure_one()
        date = self.date_order_mask
        if date:
            format_date = datetime.datetime(date.year, date.month, date.day, 23, 59, 59) + datetime.timedelta(hours=-7)
            self.date_order = format_date
            res = super(SaleOrder, self)._onchange_date_order_mask()
            sale_date_limit = self.sudo().env['ir.config_parameter'].search([('key','=','date_limit.sales_order')])
            if not sale_date_limit:
                self.sudo().env['ir.config_parameter'].create({'key':'date_limit.sales_order','value':3})
            limit_date = fields.datetime.now().date() - datetime.timedelta(days=int(sale_date_limit.value))
            # if date < limit_date:
            #     raise AccessError(_("Order date tidak boleh melebihi limit"))
            return res

    # def _cron_close_sjcreate(self):
    #     query="""
    #     SELECT sp.id as pick, so.id as sale, sol.id as saline
    #     FROM
    #     stock_picking sp
    #     LEFT JOIN sale_order so ON so.ID = sp.sale_id
    #     LEFT JOIN sale_order_line sol ON sol.order_id = so.id
    #     WHERE so."state" != 'forced_locked'
    #     AND so.company_id = 2
    #     AND sp.order_pickup_method_id = '1'
    #     AND (sp.create_date + INTERVAL '7 hour')::timestamp::date = ((CURRENT_DATE + INTERVAL '7 hour')- INTERVAL '1 day')::timestamp::date
    #     """
    #     self.env.cr.execute(query)
    #     result = self.env.cr.dictfetchall()
    #     if result:
    #         find_so = [x['sale'] for x in result]
    #         find_sp = [x['pick'] for x in result]
    #         find_sl = [x['saline'] for x in result]
    #         self.env.cr.execute("""
    #             UPDATE
    #             sale_order
    #             SET
    #             state='forced_locked'
    #             WHERE
    #             id in %s""",(tuple(find_so),))
    #         self.env.cr.execute("""
    #             UPDATE
    #             sale_order_line
    #             SET
    #             state='forced_locked'
    #             WHERE
    #             id in %s""",(tuple(find_sl),))
    #         self.env.cr.execute("""
    #             UPDATE
    #             stock_picking
    #             SET
    #             state='cancel'
    #             WHERE
    #             state NOT IN ( 'done', 'cancel' )
    #             AND
    #             id in %s""",(tuple(find_sp),))

    def _cron_close_so(self):
        # date = self.date_order_mask
        now_date = fields.date.today()
        query="""
        SELECT sp.id as pick,sp.state, sl.usage , so.id as sale, sol.id as saline
        FROM
        stock_picking sp
        LEFT JOIN sale_order so ON so.ID = sp.sale_id
        LEFT JOIN sale_order_line sol ON sol.order_id = so.id
        LEFT JOIN stock_location sl ON sl.ID = sp.location_dest_id
        WHERE
        so.state = 'sale'
        AND so.company_id = 2
        -- AND sp.state NOT IN ( 'done', 'cancel' )
        AND (so.validity_date + INTERVAL '7 hour')::timestamp::date = CURRENT_DATE
        AND sl.usage = 'customer'
        UNION
        SELECT sp.id as pick,sp.state, sl.usage, so.id as sale, sol.id as saline
        FROM
        stock_picking sp
        LEFT JOIN sale_order so ON so.ID = sp.sale_id
        LEFT JOIN sale_order_line sol ON sol.order_id = so.id
        LEFT JOIN stock_location sl ON sl.ID = sp.location_dest_id
        WHERE so."state" != 'forced_locked'
        AND so.company_id = 2
        AND sp.order_pickup_method_id = '1'
        AND sp.date_done is NOT NULL
        AND (sp.create_date + INTERVAL '7 hour')::timestamp::date = (CURRENT_DATE - INTERVAL '1 day')::timestamp::date
        """
        # self.env.cr.execute(query, (now_date,))
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        print("RESULT", result)
        if result:
            find_so = [x['sale'] for x in result]
            find_sp = [x['pick'] for x in result]
            find_sl = [x['saline'] for x in result]
            self.env.cr.execute("""
                UPDATE
                sale_order
                SET
                state='forced_locked'
                WHERE
                id in %s""",(tuple(find_so),))
            self.env.cr.execute("""
                UPDATE
                sale_order_line
                SET
                state='forced_locked'
                WHERE
                id in %s""",(tuple(find_sl),))
            self.env.cr.execute("""
                UPDATE
                stock_picking
                SET
                state='cancel'
                WHERE
                state NOT IN ( 'done', 'cancel' )
                AND
                location_dest_id in (SELECT sl.id FROM stock_location sl WHERE sl.usage ='customer')
                AND
                sale_id in %s""",(tuple(find_so),))

    @api.onchange('test_column_1')
    def _onchange_test_column(self):
        # show success message
        # title = _("Successfully!")
        # message = _("Your Action Run Successfully!")
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': title,
        #         'message': message,
        #         'sticky': False,
        #     }
        # }
        # _logger.error('>>> _onchange_test_column')
        print('>>> _onchange_test_column')

class SaleOrderInvs(models.Model):
    _inherit = 'sale.order'
    kode = fields.Char(compute='_find_kode', store=True)

    # penambahan detail promo produk pada order lines
    # def _get_reward_values_product_extended(self, program):
    #     order_lines = self.order_line.filtered(lambda line: line.product_id) - self._get_reward_lines()
    #     products = order_lines.mapped('product_id')
    #     vals = []
    #     order_lines = self.order_line.filtered(lambda r: r.product_id in program._get_valid_products(products))
    #     vals = []
    #     for rec in order_lines:
    #         if rec.product_uom_qty >= program.rule_min_quantity:
    #             if program.free_product_selection=='custom':
    #                 product = program.reward_product_id
    #                 product_uom = product.uom_id
    #             else:
    #                 product = rec.product_id
    #                 product_uom = rec.product_uom
                
    #             data =  {
    #                     'product_id': product.id,
    #                     'price_unit': 0.0,
    #                     'product_uom_qty': int(rec.product_uom_qty / program.rule_min_quantity) * program.reward_product_quantity,
    #                     'is_reward_line': True,
    #                     'name': _("Free Product") + " - " + product.name,
    #                     'product_uom': product_uom.id,
    #                     'tax_id': False,
    #                     'program_promo_id' : program.id if rec.program_promo_id == False else rec.program_promo_id,
    #                     'create_date_promo' : rec.create_date if rec.create_date_promo == False else rec.create_date_promo,
    #                     'start_date_promo' : program.rule_date_from if rec.start_date_promo == False else rec.start_date_promo,
    #                     'end_date_promo' : program.rule_date_to if rec.end_date_promo == False else rec.end_date_promo,
    #                 }
    #             vals.append(data)
    #     return vals

    @api.depends('partner_id')
    def _find_kode(self):
        for rec in self:
            if rec.partner_id.id != False and rec.partner_id.code != False:
                string = str(rec.partner_id.code)
                # rec.kode = string[0:3]
                res = re.findall('(\d+|[A-Za-z]+)', string)
                rec.kode = res[0]
            else:
                rec.kode = rec.partner_id.name    
    
    @api.depends('team_id','partner_id')
    def _compute_blacklist_partner(self):
        for rec in self:
            rec.blacklist_partner = False
            pricelist = rec.partner_id.sudo().partner_pricelist_ids.filtered(lambda r:r.team_id.id==rec.team_id.id).sorted('id', reverse=True)
            if len(pricelist)>0:
                if pricelist.black_list == 'blacklist':
                    rec.blacklist_partner = True
            # self.env.cr.execute(""" SELECT id,black_list FROM "partner_pricelist" WHERE partner_id="""+str(int(rec.partner_id.id))+""" AND team_id="""+str(int(rec.team_id.id))+ """ """)
            # sql  = self.env.cr.fetchall()
            # cal_sql = [x[0] for x in sql]
            # black_list_sql = [x[1] for x in sql]
            # if len(cal_sql)>0:
            #     if 'blacklist' in black_list_sql:
            #         rec.blacklist_partner = True
            return super(SaleOrderInvs, self)._compute_blacklist_partner()

    def _get_reward_values_discount_extended(self,program):
        order_lines = self.order_line.filtered(lambda line: line.product_id) - self._get_reward_lines()
        products = order_lines.mapped('product_id')
        vals = []
        discount_product_lines = self.order_line.filtered(lambda r: r.product_id in program._get_valid_products(products))
        for rec in discount_product_lines:
            if 'Free Product' not in rec.name:
                data = {
                'name': _("Discount: ") + program.name,
                'product_id': program.discount_line_product_id.id,
                'promotion_product_id': rec.product_id.id,
                'disc_fix_amount': program.discount_fixed_amount,
                'meth_fix_amount': program.fix_amount_method,
                'promotion_disc_type': program.discount_type,
                'price_unit': - (rec.product_uom_qty * self._get_reward_values_discount_fixed_amount(program)),
                'product_uom_qty': 1.0,
                'product_uom': program.discount_line_product_id.uom_id.id,
                'is_reward_line': True,
                'tax_id': [(4, tax.id, False) for tax in program.discount_line_product_id.taxes_id],
                }
                vals.append(data)
        return vals
        return super(SaleOrderInvs, self)._get_reward_values_discount_extended(program)

    def _get_reward_values_discount(self, program):
        products = self.order_line.mapped('product_id')
        discount_product_lines = self.order_line.filtered(lambda r: r.product_id in program._get_valid_products(products))
        if program.discount_type == 'fixed_amount' and program.fix_amount_method == 'amount_total':
            for rec in discount_product_lines:
                return [{
                'name': _("Discount: ") + program.name,
                'product_id': program.discount_line_product_id.id,
                'price_unit': - self._get_reward_values_discount_fixed_amount(program),
                'promotion_product_id': rec.product_id.id,
                'disc_fix_amount': program.discount_fixed_amount,
                'meth_fix_amount': program.fix_amount_method,
                'promotion_disc_type': program.discount_type,
                'product_uom_qty': 1.0,
                'product_uom': program.discount_line_product_id.uom_id.id,
                'is_reward_line': True,
                'tax_id': [(4, tax.id, False) for tax in program.discount_line_product_id.taxes_id],
                }]
        return super(SaleOrderInvs, self)._get_reward_values_discount(program)

    # perubahan filter free produk ketika ganti pickup methode
    @api.onchange('order_pickup_method_id')
    def onchange_pickup_method(self):
        self = self.sudo()
        res = {}
        team_id = self.team_id
        if self.sale_agreement_id.id:
            team_id = self.sale_agreement_id.team_id.id

        values = {
                    'partner_can_direct_pickup':False,
                }

        if self.order_pickup_method_id.id and self.partner_id.id:
            if self.order_pickup_method_id.id == self.env.ref('sanqua_sale_flow.order_pickup_method_take_in_plan').id:
                updated = {
                    'partner_can_direct_pickup':self.partner_id.can_direct_pickup,
                }
                values.update(updated)
            else:
                values.update({
                    'partner_can_direct_pickup':self.partner_id.can_direct_pickup,
                    })
        else:
            if self.partner_id.id==False:
                values.update({'order_pickup_method_id':False})
                if self.order_pickup_method_id.id:
                    res.update({'warning':{'title':_("Attention!"),'message':_("Please Select Customer First!")}})


        if self.order_line:
            for line in self.order_line.filtered(lambda x:x.is_reward_line==False):
                line.product_id_change()
                line.product_uom_change()
        
        self.update(values)



        res.update({'value':values})
        return res


class SaleOrderInv(models.Model):
    _inherit = 'sale.order.line'

    promotion_product_id = fields.Char()
    disc_fix_amount = fields.Float()
    meth_fix_amount = fields.Char()
    promotion_disc_type = fields.Char()

    program_promo_id = fields.Char()
    create_date_promo = fields.Date()
    start_date_promo = fields.Date()
    end_date_promo = fields.Date()

class SalesAccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('picking_ids')
    def _onchange_picking_ids(self):
        print("JALAN _onchange_picking_ids VER 1")
        self = self.with_context(onchange_pickings=True)
        self.line_ids = [(5,0)]

        if self.picking_ids:
            if not self.partner_id:
                self.partner_id = self.picking_ids.mapped('customer_id')

            picking_ids = self.picking_ids._origin
            moves_lines = self.env['stock.move'].browse(
                [rec.id for rec in picking_ids.move_ids_without_package]
                )

            new_lines = self.env['account.move.line']
            m_line = []
            for line in moves_lines:
                new_line = new_lines.new(line._prepare_picking_account_move_line(self))
                cek_sale_order_line =self.env['stock.move'].browse(
                [new.id for new in line.sale_line_id])
                print("line.sale_line_id",line.sale_line_id)
                print("cek_sale_order_line",cek_sale_order_line.id)
                cek_sale_order_line_product =self.env['sale.order.line'].search([('id','=',line.sale_line_id.id)])
                print("cek_sale_order_line_product",cek_sale_order_line_product)
                cari_promo_sale_order = self.env['sale.order.line'].search([
                    ('order_id','=',cek_sale_order_line_product.order_id.id),
                    ('promotion_product_id','=',cek_sale_order_line_product.product_id.id)])
                # print("RETURN", line.return_qty)
                for x in cari_promo_sale_order:
                    tambah_promo_per_unit ={
                    'product_id':x.product_id.id,
                    'name':x.name,
                    'quantity':line.quantity_done - line.return_qty,
                    'price_unit':-x.disc_fix_amount,
                    }
                    tambah_promo_per_total ={
                    'product_id':x.product_id.id,
                    'name':x.name,
                    'quantity':1,
                    'price_unit':(-x.disc_fix_amount/cek_sale_order_line_product.product_uom_qty)*line.quantity_done,
                    }
                    if 'Free Product' not in line.name and x.id != False and x.meth_fix_amount == 'amount_per_unit':
                        self.update({'invoice_line_ids':[(0, 0, tambah_promo_per_unit)]})
                    elif 'Free Product' not in line.name and x.id != False and x.meth_fix_amount == 'amount_total':
                        self.update({'invoice_line_ids':[(0, 0, tambah_promo_per_total)]})
                new_line.account_id = new_line._get_computed_account()
                new_line.stock_move_id = line.id
                new_line._onchange_price_subtotal()
                new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()

        # Compute ref.
        refs = self.picking_ids.mapped('display_name')
        self.ref = ', '.join(refs)

        # Compute invoice_payment_ref.
        if len(refs) == 1:
            self.invoice_payment_ref = refs[0]

        self._onchange_currency()
        return self._onchange_partner_id()
        return super(SalesAccountMove, self)._onchange_picking_ids()

# class DoneAccountMoveLine(models.Model):
#     _inherit = 'stock.move'

#     @api.onchange('move_line_ids')
#     def _qty_done(self):
#         count = []
#         for data in self.move_line_ids:
#             count.append(data.qty_done)
#             total_done = sum(count)
#             if total_done > self.product_uom_qty:
#                 raise UserError(_('Quantity not available'))

class SaleStockPick(models.Model):
    _inherit = 'stock.picking'

    def _prepare_invoice(self,picking):
        invoice_vals = {
            'type': 'out_invoice',
            'invoice_origin': picking.name,
            'invoice_user_id': picking.sale_id.user_id.id,
            # Updated by : MIS@SanQua
            # At: 12/01/2022
            # Description: The date default is not include timezone.
            'invoice_date': (picking.date_done + timedelta(hours=7)),
            'invoice_origin': picking.doc_name,
            'narration': picking.note,
            'partner_id': picking.sale_id.partner_invoice_id.id,
            'partner_shipping_id': picking.partner_id.id,
            'team_id': picking.sales_team_id.id,
            'warehouse_id': picking[0].picking_type_id.warehouse_id if picking else False,
            # 'source_id': self.id,
            'invoice_line_ids':[],
            'invoice_payment_term_id':picking.sudo().sale_id.payment_term_id.id,
            'locked': False
        }
        for rec in picking.move_ids_without_package.filtered(lambda r:r.qty_to_invoice>0.0 and r.available_to_invoice and not r.product_id.reg_in_customer_stock_card):
            invoice_vals['invoice_line_ids'].append(
                    (0, 0, self._prepare_vals_move(rec))
                )
        for d in picking.move_ids_without_package:
            if 'Free Product' not in d.name:
                print("d.name",d.name)
            free_p = False
            dis_p = False
            # print("REC",rec)
            for d in self.sale_id.order_line:
                # print("ID SALE", d.id)
                if 'Discount' in d.name:
                    dis_p = True
                    # print("dis_p",dis_p)
                else:
                    dis_p = False
                    # print("dis_p",dis_p)
        tot_ret = sum([x.return_qty for x in self.move_ids_without_package])
        if dis_p == True:
            invoice_vals['invoice_line_ids'].append(
                (0, 0, self._prepare_vals_promo(rec)))
            # print("INSERTS")
        
        # if picking.sale_id:
        #     reward_so_product = picking.sale_id._get_reward_lines().filtered(lambda r: r.qty_invoiced != r.product_uom_qty).mapped('product_id')
        #     reward_move_product = picking.move_ids_without_package.filtered(lambda r:r.qty_to_invoice>0.0).mapped('product_id')
        #     rewards_product = reward_so_product - reward_move_product
        #     for line in picking.sale_id._get_reward_lines().filtered(lambda r: r.product_id in rewards_product):
        #         invoice_vals['invoice_line_ids'].append(
        #                 (0, 0, self._prepare_vals_sale_order_line(line))
        #             )
        return invoice_vals
        return super(SaleStockPick, self)._prepare_invoice()

    def _prepare_vals_promo(self,line):
        cari_produk_promo = self.env['sale.order.line'].search([('order_id','=',line.sale_line_id.order_id.id),('promotion_product_id','=',line.product_id.id)])
        income_acc = self.env['product.category'].search([('id','=',cari_produk_promo.product_id.categ_id.id)])
        # print("NAME PROMO",cari_produk_promo.name)
        # print("LINE")
        # if 'Free Product' not in line.name:
        #     print("LINE NAME",line.name)
        #     print("LINE quantity",line.quantity_done)
        if cari_produk_promo.meth_fix_amount == 'amount_per_unit':
            # print("AMOUNT PER UNIT")
            return {
            'name': cari_produk_promo.name,
            'price_unit': -cari_produk_promo.disc_fix_amount,
            'quantity': line.quantity_done,
            'product_id': cari_produk_promo.product_id.id,
            'account_id': income_acc.property_account_income_categ_id.id,
            }
        elif cari_produk_promo.meth_fix_amount == 'amount_total':
            # print("AMOUNT TOTAL")
            return {
            'name': cari_produk_promo.name,
            'price_unit': (-cari_produk_promo.disc_fix_amount/line.sale_line_id.product_uom_qty)*line.quantity_done,
            'quantity': 1,
            'product_id': cari_produk_promo.product_id.id,
            'account_id': income_acc.property_account_income_categ_id.id,
            }
        return True

# class MyAccountMovePopup(models.Model):
#     _inherit = 'account.move'

#     pick_method = fields.Char(compute="_pick_method")

#     def _pick_method(self):
#         for rec in self:
#             find_pick = self.env['stock.picking'].search([('doc_name','=',rec.invoice_origin)])
#             rec.pick_method = find_pick.order_pickup_method_id.name

# class SaleCouponsProgram(models.Model):
#     _inherit = 'sale.coupon.program'

    # Rubah filter promotion berdasarkan tanggal create
#     @api.model
#     def _filter_on_validity_dates(self, order):
        # print("SALEESALEEEEEEEEEEEEEE",order.date_order)
#         return self.filtered(lambda program:
#             program.rule_date_from and program.rule_date_to and
#             program.rule_date_from <= order.create_date and program.rule_date_to >= order.create_date or
# #             not program.rule_date_from or not program.rule_date_to)

# class SaleOrderLineInher(models.Model):
#     _inherit = 'sale.order.line'

#     def write(self, values):
#         previous_product = self.product_id
#         previous_price = self.price_unit
#         rex =  super(SaleOrderLineInher, self).write(values)
#         uprice = 'price_unit' in values
#         if uprice:
#             new_price = values.get('price_unit')
#             msgs = []
#             msgs.append("Change %s %s price %s --> %s"%(previous_product.code if previous_product.code else '',
#                 previous_product.name,previous_price,new_price))
#             self.order_id.message_post(body=msgs[0])
#         return rex