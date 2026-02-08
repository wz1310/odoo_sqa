# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime
import logging
import base64
from odoo.addons.e_tax_invoice_merge.helpers import amount_to_text,\
    format_local_currency,\
    format_local_datetime
_logger = logging.getLogger(__name__)


class MakeObj(dict):
    """Make object"""

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    hide_commercial = fields.Boolean(string='Hide')


class AccountMove(models.Model):
    _inherit = 'account.move'
    commercial_ids = fields.Many2many('etax.invoice.merge', 'account_move_etax_invoice_merge_rel',
                                      'account_move_id', 'etax_invoice_merge_id', string="Commercial IDS")

    @api.model
    def _autopost_draft_entries(self):
        ''' This method is called from a cron job.
        It is used to post entries such as those created by the module
        account_asset.
        '''
        records = self.search([
            ('state', '=', 'draft'),
            ('date', '<=', fields.Date.today()),
            ('auto_post', '=', True),
        ], limit=500)
        records.post()


class ETaxInvoiceMerge(models.Model):
    """New Class etax_invoice_merge"""

    _name = 'etax.invoice.merge'
    _description = 'Invoice Commercial'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_invoice_date(self):
        return fields.Date.today()

    name = fields.Char(string='Number', required=True, readonly=True,
                       copy=False, default='/', track_visibility='onchange')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', track_visibility='onchange')
    partner_shipping_id = fields.Many2one(
        'res.partner',
        string='Delivery Address',
        readonly=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Delivery address for current invoice.", track_visibility='onchange')
    ref = fields.Char(string='Reference', track_visibility='onchange')
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
                               default=_get_default_invoice_date, track_visibility='onchange')
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
                                              domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                              readonly=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id, track_visibility='onchange')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', track_visibility='onchange')
    invoice_date_due = fields.Date(
        string='Due Date', readonly=True, index=True, copy=False, track_visibility='onchange')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, track_visibility='onchange',
        default='draft')

    e_tax_invoice_id = fields.Many2one(
        'etax.invoice', string="E-Tax", copy=False, track_visibility='onchange')
    e_tax_invoice_validated = fields.Boolean(string="E-faktur Uploaded Success",
                                             readonly=True, related='e_tax_invoice_id.validated', store=True, track_visibility='onchange')
    tgl_upload = fields.Date(string='Upload Date', track_visibility='onchange')
    invoice_line_ids = fields.Many2many(
        'account.move.line', compute='_compute_invoice_ids', track_visibility='onchange')
    invoice_ids = fields.Many2many('account.move', track_visibility='onchange')

    amount_undiscount = fields.Monetary(
        string='Subtotal', store=True, readonly=True, track_visibility='onchange', compute='_compute_amount')

    amount_discount = fields.Monetary(
        string='Discount Amount', track_visibility='onchange')

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True,
                                     readonly=True, track_visibility='onchange', compute='_compute_amount')

    amount_tax = fields.Monetary(string='Tax Amount', store=True, readonly=True,
                                 compute='_compute_amount', track_visibility='onchange')

    amount_total = fields.Monetary(
        string='Total', store=True, readonly=True, compute='_compute_amount', track_visibility='onchange')

    partner_tax_digit = fields.Char(
        compute='_compute_partner_tax_digit', store=True, track_visibility='onchange')
    is_replaced_e_tax = fields.Boolean(
        related='e_tax_invoice_id.is_replaced_e_tax', string='Replaced E-Tax', track_visibility='onchange')
    tax_number = fields.Char(related='e_tax_invoice_id.tax_number',
                             string="Tax Number", track_visibility='onchange')

    # Created by: PCI
    # invoice_merge_line_ids = fields.Many2many(
    #         'etax.invoice.merge.line', compute='_compute_invoice_line_ids', track_visibility='onchange', string='Summary Invoice')

    # Change by: MIS@SanQua
    # At: 13/01/2022
    # Description: This relation makes load very long and it makes unnecessary data.
    #              When make this change, we found unnecessary data rount 59.462.460.
    invoice_merge_line_ids = fields.One2many(
        'etax.invoice.merge.line', 'e_tax_invoice_merge_id', compute='_compute_invoice_line_ids', track_visibility='onchange', string='Summary Invoice', store=True)
    show_all_invoice = fields.Boolean(string="Hide Zero Price")

    def upload_etax(self):
        print('>>> upload_etax()')
        etax = self.mapped('e_tax_invoice_id')
        etax.upload_etax()

    def _fetch_sequence(self):
        print('>>> _fetch_sequence()')
        self.name = self.env['ir.sequence'].next_by_code(
            'seq.invoice.commercial')

    @api.depends('partner_id')
    def _compute_partner_tax_digit(self):
        print('>>> _compute_partner_tax_digit()')
        for rec in self:
            rec.partner_tax_digit = rec.partner_id.digit2

    @api.onchange('show_all_invoice')
    def _hide_price_nol(self):
        print('>>> _hide_price_nol()')
        for rec in self:
            ini = rec.show_all_invoice
            if len(rec.invoice_line_ids) > 1:
                for line in rec.invoice_line_ids:
                    if line.price_unit <= 0:
                        # raise UserError(_(line._origin.id))
                        move_line = self.env['account.move.line'].search(
                            [('id', '=', line._origin.id)])
                        move_line.hide_commercial = ini

    @api.depends('invoice_ids')
    def _compute_invoice_ids(self):
        print('>>> _compute_invoice_ids()')
        for rec in self:
            vals = []
            for invoice in rec.invoice_ids:
                for line in invoice.invoice_line_ids.filtered(lambda r: not r.hide_commercial):
                # for line in invoice.invoice_line_ids:
                    vals.append(line.id)
            rec.invoice_line_ids = [(6, 0, vals)]

    @api.depends('invoice_line_ids')
    def _compute_invoice_line_ids(self):
        print('>>> _compute_invoice_line_ids()')
        for rec in self:
            rec.invoice_merge_line_ids = False
            if len(rec.invoice_line_ids) > 0:
                for product in rec.invoice_line_ids.mapped('product_id'):
                    qty = sum([x.quantity * -1 if x.move_id.type in ['in_refund', 'out_refund']
                              else x.quantity for x in rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id and not r.hide_commercial)])
                    subtoal = sum([x.price_subtotal * -1 if x.move_id.type in ['in_refund', 'out_refund']
                                  else x.price_subtotal for x in rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id and not r.hide_commercial)])
                    display_discount = sum([x.display_discount * -1 if x.move_id.type in ['in_refund', 'out_refund']
                                           else x.display_discount for x in rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id and not r.hide_commercial)])
                    price_subtotal = sum([x.price_subtotal * -1 if x.move_id.type in ['in_refund', 'out_refund']
                                         else x.price_subtotal for x in rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id and not r.hide_commercial)])
                    if qty > 0:
                        print('>>> Here...')
                        data = {
                            'product_id': product.id,
                            'name': product.name,
                            'account_id': rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].account_id.id,
                            'analytic_account_id': rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].analytic_account_id.id,
                            'quantity': qty,
                            'product_uom_id': rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].product_uom_id.id,
                            'price_unit': subtoal/qty if qty > 0 else 0,
                            'display_discount': display_discount,
                            'tax_ids': [(6, 0, rec.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)[0].tax_ids.ids)],
                            'price_subtotal': price_subtotal,
                        }
                        print('>>> Start insert...')
                        print('>>> Data : ' + str(data))
                        rec.invoice_merge_line_ids = [(0, 0, data)]

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        print('>>> _onchange_partner_id()')
        # Recompute 'partner_shipping_id' based on 'partner_id'.
        addr = self.partner_id.address_get(['delivery'])
        self.partner_shipping_id = addr and addr.get('delivery')

    @api.onchange('amount_discount')
    def _onchange_amount_discount(self):
        print('>>> _onchange_amount_discount()')
        self._compute_amount()

    @api.depends('invoice_merge_line_ids', 'invoice_merge_line_ids.price_subtotal')
    def _compute_amount(self):
        print('>>> _compute_amount()')
        for rec in self:
            rec.amount_undiscount = sum(
                [line.price_subtotal for line in rec.invoice_merge_line_ids])
            rec.amount_untaxed = rec.amount_undiscount - rec.amount_discount
            # amount_tax = 0
            # for line in rec.invoice_merge_line_ids:
            #     tax_total = 0
            #     for tax in line.tax_ids:
            #         tax_total += line.price_subtotal * tax.amount / 100
            #     amount_tax += tax_total
            rec.amount_tax = rec.amount_untaxed * 10 / 100
            rec.amount_total = rec.amount_untaxed + rec.amount_tax

    def btn_cancel(self):
        print('>>> btn_cancel()')
        self.state = 'cancel'

    def btn_draft(self):
        print('>>> btn_draft()')
        self.state = 'draft'

    def btn_posted(self):
        print('>>> btn_posted()')
        # Note from MIS SanQua (07/09/2021) :
        # This self._fetch_sequence will make Invoice Commercial Number using next number
        # Request from Mae (FA Staff), it must be still same, do not changed
        print('>>> Self.name : ' + self.name)
        if self.name == '' or self.name == '/':
            self._fetch_sequence()

        self.state = 'posted'

    def action_cancel(self):
        print('>>> action_cancel()')
        """Canceling or unlink E-Faktur"""
        if self.e_tax_invoice_id:
            self.e_tax_invoice_id = False
            self.reset_efaktur()

    def name_get(self):
        print('>>> name_get()')
        """Get name"""
        result = []
        for inv in self:
            if inv.state == 'cancel':
                result.append((inv.id, "Cancelled %s %s" % ('Invoice Commercial' or '',
                                                            inv.name or '')))
            else:
                result.append((inv.id, "%s %s" %
                              ('Invoice Commercial', inv.name or '')))
        return result

    def reset_efaktur(self):
        print('>>> reset_efaktur()')
        """To reset E-Faktur, so it can be use for other invoice"""
        for faktur in self:
            obj = faktur.e_tax_invoice_id
            no_fak = faktur.e_tax_invoice_id.name
            obj.write({
                'validated': False,
                'invoice_id': False,
                'downloaded': False
            })
            faktur.message_post(
                body='e-Faktur Reset: %s ' % (no_fak,),
                subject="Reset Efaktur")
            faktur.write({'e_tax_invoice_id': False})
        return True

    def open_reset_message_wizard(self):
        print('>>> open_reset_message_wizard()')
        self.ensure_one()

        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message': "<h4>Rev-Efaktur</h4>",
                       "default_suffix_action": "replacement_efaktur"})  # uncomment if need append context
        res = {
            'name': "%s - %s" % (_('Rev-Efaktur'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def replacement_efaktur(self):
        print('>>> replacement_efaktur()')
        replaced = False
        if self.e_tax_invoice_validated == True:
            replaced = True
        self.e_tax_invoice_id.write({
            'is_replaced_e_tax': replaced
        })

    def btn_view_next_e_tax_no(self):
        print('>>> btn_view_next_e_tax_no()')
        next_e_tax_no = self.call_etax_series()
        view_id = self.env.ref(
            'pci_efaktur_13.etax_invoice_form_view_readonly')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Faktur Number'),
            'res_model': 'etax.invoice',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id.id, 'form'), (False, 'tree')],
            'view_id': view_id.id,
            'res_id': next_e_tax_no.id,
            'target': 'new',
            'flags': {'mode': 'readonly'},
            'context': {
                'e_tax_invoice_merge_id': self.id
            }
        }

    def btn_register_next_e_tax_no(self):
        print('>>> btn_register_next_e_tax_no()')
        self.e_tax_invoice_id = self.call_etax_series()

    def call_etax_series(self):
        print('>>> call_etax_series()')
        register_tax = self.env['etax.series'].search(
            [('state_number', '=', True)])
        if not register_tax:
            raise UserError(_('Not more Active Series.'))
        if not register_tax.get_avail_number():
            raise UserError(_('No more allocation faktur number.'))
        return register_tax.get_avail_number()

    @staticmethod
    def get_format_currency(value, total=False):
        print('>>> get_format_currency()')
        """ Get format currency with rule: thousand -> (.) and no decimal place.
        :param value: Float. Value that need to be formatting.
        :return: String. Format currency result.
        """
        return format_local_currency(value, total)

    def get_format_datetime(self, datetime_value, only_date=False):
        print('>>> get_format_datetime()')
        """ Get format datetime as string.
        :param datetime_value: Datetime. Datetime that need to be formatting.
        :param only_date: Boolean. If 'True' then value will be return as Date.
        :return: String. Format datetime result.
        """
        user_tz = pytz.timezone(self._context.get(
            'tz') or self.env.user.tz or 'UTC')
        return format_local_datetime(user_tz, datetime_value, only_date=True)

    def get_amount_to_text(self, amount):
        print('>>> get_amount_to_text()')
        return amount_to_text(amount)


class ETaxInvoice(models.Model):
    _inherit = 'etax.invoice'

    e_tax_invoice_merge_ids = fields.One2many(
        'etax.invoice.merge', 'e_tax_invoice_id', string='Invoices Commercial', track_visibility='onchange')
    e_tax_invoice_merge_id = fields.Many2one('etax.invoice.merge', string='Invoice Commercial',
                                             compute='_compute_e_tax_invoice_merge_id', store=True, track_visibility='onchange')

    @api.depends('e_tax_invoice_merge_ids')
    def _compute_e_tax_invoice_merge_id(self):
        print('>>> _compute_e_tax_invoice_merge_id()')
        for rec in self:
            if len(rec.e_tax_invoice_merge_ids) == 1:
                rec.e_tax_invoice_merge_id = rec.e_tax_invoice_merge_ids
            else:
                rec.e_tax_invoice_merge_id = False

    def apply_e_tax(self):
        print('>>> apply_e_tax()')
        res = super(ETaxInvoice, self).apply_e_tax()
        if self._context.get('e_tax_invoice_merge_id'):
            move_id = self.env['etax.invoice.merge'].browse(
                self._context.get('e_tax_invoice_merge_id'))
            move_id.write({
                'e_tax_invoice_id': self.id
            })
        return res

    @api.depends('invoice_id', 'is_replaced_e_tax', 'name', 'e_tax_invoice_merge_id')
    def _compute_tax_number(self):
        print('>>> _compute_tax_number()')
        for rec in self:
            res = super(ETaxInvoice, self)._compute_tax_number()
            digit_comercial = ''
            name = rec.name or ''
            if rec.e_tax_invoice_merge_id:
                digit_comercial = rec.e_tax_invoice_merge_id.partner_tax_digit or ''

                # PCI Version
                rec.tax_number = digit_comercial + \
                    str(int(rec.is_replaced_e_tax))+'.' + name

                # SanQua Version
                # rec.tax_number = '0.' + name[1:16]
            return res

    def name_get(self):
        print('>>> name_get()')
        result = []
        for efaktur in self:
            name = ''
            if efaktur.invoice_id:
                name = efaktur.tax_number
            elif efaktur.e_tax_invoice_merge_id:
                name = efaktur.tax_number
            else:
                name = efaktur.name
            result.append(
                (efaktur.id, self.format_etax(('').join(name.split('.')))))
        return result

    def format_etax(self, vals):
        print('>>> format_etax()')
        format = ""
        name = str(vals)
        text = list(name)
        for x in range(len(text)):
            if x == 2:
                format = format + text[x] + '.'
            elif x == 5:
                format = format + text[x] + '-'
            elif x == 7:
                format = format + text[x] + '.'
            else:
                format = format + text[x]
        return format


class ETaxSeries(models.Model):
    _inherit = 'etax.series'

    @api.depends('line_ids')
    def _compute_next_avail_no(self):
        print('>>> _compute_next_avail_no()')
        for rec in self:
            if len(rec.line_ids) > 0:
                query = """ 
                    SELECT ei.id FROM etax_invoice ei
                    LEFT JOIN etax_series es ON ei.e_tax_series_id = es.id
                    WHERE ei.e_tax_series_id = %s AND ei.invoice_id IS NULL AND ei.e_tax_invoice_merge_id IS NULL AND NOW() <= es.end_date AND es.state_number = True
                    ORDER BY ei.name ASC LIMIT 1
                """
                self.env.cr.execute(query, (rec.id,))
                res = self.env.cr.fetchall()
                if res:
                    rec.next_avail_no = res[0][0]
                else:
                    rec.next_avail_no = False
            else:
                rec.next_avail_no = False


class ReexportEFaktur(models.TransientModel):
    _inherit = 'reexport.efaktur'

    def get_active_ids(self):
        print('>>> get_active_ids()')
        active_ids = ''
        context = self.env.context
        model_name = context.get('active_model')
        if model_name == 'etax.invoice':
            active_ids = context.get('active_ids')
        if model_name == 'account.move':
            move_id = self.env[model_name].browse(context.get('active_ids'))
            active_ids = move_id.mapped('e_tax_invoice_id').ids
        if model_name == 'etax.invoice.merge':
            move_id = self.env[model_name].browse(context.get('active_ids'))
            active_ids = move_id.mapped('e_tax_invoice_id').ids
        return active_ids

    def reexport_efaktur(self):
        print('>>> reexport_efaktur()')
        """Collect the data and execute function _generate_efaktur"""

        data = {}

        tax_ids = self.env['etax.invoice'].browse(self.get_active_ids())

        if not tax_ids:
            raise UserError(
                _('Not found faktur number in selected documents.'))
        delimiter = self.delimiter

        # From Invoice of Customer
        invoice_ids = [inv.invoice_id.id for inv in tax_ids
                       if inv.invoice_id.id and not inv.is_vendor]
        # From Invoice of Supplier
        vendor_bill_ids = [inv.invoice_id.id for inv in tax_ids
                           if inv.invoice_id.id and inv.is_vendor]
        # From Invoice Merge
        e_tax_invoice_merge_ids = [inv.e_tax_invoice_merge_id.id for inv in tax_ids
                                   if inv.e_tax_invoice_merge_id.id]

        data.update({
            'e_tax_invoice_merge_ids': e_tax_invoice_merge_ids,
            'invoice_ids': invoice_ids,
            'vendor_bill_ids': vendor_bill_ids,
        })
        return self._generate_efaktur(data, delimiter)

    def _generate_efaktur(self, data, delimiter):
        print('>>> _generate_efaktur()')
        """Main function of generate E-Faktur from wizard"""

        filename = 'reexport_efaktur.csv'

        efaktur_values = self._prepare_efaktur_csv(delimiter)

        output_head = '%s\n%s\n%s' % (
            efaktur_values.get('fk_head'),
            efaktur_values.get('lt_head'),
            efaktur_values.get('of_head'),
        )

        output_head = self._generate_efaktur_invoice(
            data, delimiter, output_head).replace('False', '')

        output_head2 = ''
        output_head2 = self._generate_efaktur_purchase(
            data, delimiter, output_head2)
        if data['vendor_bill_ids']:
            my_utf8 = output_head2.encode("utf-8")
        else:
            my_utf8 = output_head.encode("utf-8")
        out = base64.b64encode(my_utf8)

        self.write({'state_x': 'get', 'data_x': out, 'name': filename})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=reexport.efaktur&field=data_x&filename_field=name&id=%s&download=true&filename=%s' % (self.id, filename,),
            'target': 'self',
        }

    def _generate_efaktur_invoice(self, data, delimiter, output_head):
        print('>>> _generate_efaktur_invoice()')
        """Generate E-Faktur for customer invoice"""

        # Invoice of Customer
        obj_invs = ''
        if data['e_tax_invoice_merge_ids']:
            obj_invs = self.env['etax.invoice.merge'].browse(
                data['e_tax_invoice_merge_ids'])
        if data['invoice_ids']:
            obj_invs = self.env['account.move'].browse(data['invoice_ids'])
        company_id = self.env.ref('base.main_company')
        eTax = MakeObj(self._prepare_etax())
        efaktur_values = self._prepare_efaktur_csv(delimiter)

        for obj_inv in obj_invs:
            # If state open then print invoice line
            if obj_inv.state in ['posted']:
                npwp = ''
                # if obj_inv.partner_id.vat and not obj_inv.partner_id.vat_child:
                if obj_inv.partner_id.vat:
                    npwp = obj_inv.partner_id.vat
                # if obj_inv.partner_id.vat_child:
                #     npwp = obj_inv.partner_id.vat_child
                invoice_date = datetime.strptime(
                    str(obj_inv.invoice_date), "%Y-%m-%d") or False
                invoice_npwp = nik = street = street2 = number_ref = ''
                if not npwp or self.npwp_o:
                    nik = str(obj_inv.partner_id.citizen_id_no)

                # set value referensi
                # no invocie
                # if obj_inv.replace_invoice_id:
                #     number_ref = "NO FAKTUR PENJUALAN : "+str(obj_inv.replace_invoice_id.name)+" replaced by "+str(obj_inv.name)
                # else:
                number_ref = "NO FAKTUR PENJUALAN : "+str(obj_inv.name)

                # kode pelanggan
                if obj_inv.partner_id:
                    partner_ref = ''
                    if obj_inv.partner_id.parent_id:
                        partner_ref = obj_inv.partner_id.parent_id.ref
                    if not obj_inv.partner_id.parent_id:
                        partner_ref = obj_inv.partner_id.ref

                    if number_ref == '':
                        number_ref = "KODE PELANGGAN : "+str(partner_ref)
                    else:
                        number_ref = number_ref + \
                            ", KODE PELANGGAN : "+str(partner_ref)

                # no do / pikcing
                # if obj_inv.picking_id:
                #     sales_name = ""
                #     if obj_inv.user_id:
                #         sales_name = " ("+obj_inv.user_id.name+")"
                #     if number_ref == '':
                #         number_ref = "NO SURAT JALAN : "+str(obj_inv.picking_id.name) + str(sales_name)
                #     else:
                #         number_ref = number_ref+", NO SURAT JALAN : "+str(obj_inv.picking_id.name) + str(sales_name)

                # no do / pikcing
                # if obj_inv.total_delivery_price:
                #     total_delivery = "{:,.2f}".format(obj_inv.total_delivery_price)
                #     if number_ref == '':
                #         number_ref = "ONGKOS TRANSPORTASI : "+str(obj_inv.currency_id.symbol)+". "+str(total_delivery)
                #     else:
                #         number_ref = number_ref+", ONGKOS TRANSPORTASI : "+str(obj_inv.currency_id.symbol)+". "+str(total_delivery)

                # if obj_inv.total_delivery_price <= 0:
                #     total_delivery = "Rp. 0.00"
                #     if number_ref == '':
                #         number_ref = "ONGKOS TRANSPORTASI : "+str(total_delivery)
                #     else:
                #         number_ref = number_ref+", ONGKOS TRANSPORTASI : "+str(total_delivery)

                if not invoice_date:
                    raise UserError(_("Invoice %s no date", (obj_inv.name)))

                if not obj_inv.partner_id.street:
                    street = ''
                else:
                    street = "" + obj_inv.partner_id.street

                if not obj_inv.partner_id.street2:
                    street2 = ''
                else:
                    street2 = " " + obj_inv.partner_id.street2

                basic_address = ("" + street + street2) or '' \
                    if eTax.fields.npwp.value == '000000000000000' else \
                    obj_inv.partner_id.tax_holder_address \
                    or ("" + street + street2) or ''
                city = " " + obj_inv.partner_id.city if obj_inv.partner_id.city else ''
                state = " " + obj_inv.partner_id.state_id.name or '' \
                    if eTax.fields.npwp.value == '000000000000000' and obj_inv.partner_id.state_id.name else ''
                zip_code = " " + obj_inv.partner_id.zip or '' \
                    if eTax.fields.npwp.value == '000000000000000' and obj_inv.partner_id.zip else ''
                country = " " + obj_inv.partner_id.country_id.name or '' \
                    if eTax.fields.npwp.value == '000000000000000' and obj_inv.partner_id.country_id.name else ''

                if self.npwp_o:
                    invoice_npwp = '000000000000000'
                else:
                    invoice_npwp = '000000000000000'
                    if npwp and len(npwp) >= 12:
                        invoice_npwp = npwp
                    elif not npwp or (npwp and
                                      len(npwp) < 12) and npwp:
                        invoice_npwp = obj_inv.partner_id.citizen_id_no
                    if invoice_npwp:
                        invoice_npwp = invoice_npwp.replace('.', '')
                        invoice_npwp = invoice_npwp.replace('-', '')
                '''
                    Here all fields or columns based on eTax Invoice Third Party
                '''
                eTax.fields.kd_jenis_transaksi.value = obj_inv.tax_number[0:2] or ''
                eTax.fields.fg_pengganti.value = obj_inv.tax_number[2] or ''
                eTax.fields.nomor_faktur.value = obj_inv.tax_number[4:] or ''
                eTax.fields.masa_pajak.value = datetime.strptime(str(obj_inv.invoice_date),
                                                                 "%Y-%m-%d").month or False
                eTax.fields.tahun_pajak.value = datetime.strptime(str(obj_inv.invoice_date),
                                                                  "%Y-%m-%d").year or False
                eTax.fields.tgl_faktur.value = '{0}/{1}/{2}'.format(invoice_date.day,
                                                                    invoice_date.month,
                                                                    invoice_date.year) or ''
                eTax.fields.npwp.value = invoice_npwp
                eTax.fields.nama.value = obj_inv.partner_id.name if \
                    eTax.fields.npwp.value == '000000000000000' else obj_inv.partner_id.tax_holder_name \
                    or obj_inv.partner_id.name or ''
                eTax.fields.alamat_lengkap.value = '%s%s%s%s%s' % (
                    basic_address,
                    city,
                    state,
                    zip_code,
                    country,
                )
                eTax.fields.alamat_lengkap.value.replace(',', '.')
                amount_nontax = sum(
                    [line.price_subtotal if not line.tax_ids else 0 for line in obj_inv.invoice_line_ids])
                eTax.fields.jumlah_dpp.value = int(
                    round(obj_inv.amount_untaxed - amount_nontax, 0)) or 0.0
                eTax.fields.jumlah_ppn.value = int(
                    round(obj_inv.amount_tax, 0)) or 0.0
                eTax.fields.id_keterangan_tambahan.value = '1' if \
                    obj_inv.partner_id.digit2 == '07' else ''
                eTax.fields.referensi.value = number_ref

                company_npwp = ''
                if company_id.partner_id.vat:
                    company_npwp = company_id.partner_id.vat
                else:
                    company_npwp = '000000000000000'
                company_npwp = company_npwp.replace('.', '')
                company_npwp = company_npwp.replace('-', '')
                efaktur_values.update({
                    'fk_value':
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        % (
                            'FK', delimiter,
                            eTax.fields.kd_jenis_transaksi.value, delimiter,
                            eTax.fields.fg_pengganti.value, delimiter,
                            eTax.fields.nomor_faktur.value, delimiter,
                            eTax.fields.masa_pajak.value, delimiter,
                            eTax.fields.tahun_pajak.value, delimiter,
                            eTax.fields.tgl_faktur.value, delimiter,
                            eTax.fields.npwp.value, delimiter,
                            eTax.fields.nama.value, delimiter,
                            eTax.fields.alamat_lengkap.value, delimiter,
                            eTax.fields.jumlah_dpp.value, delimiter,
                            eTax.fields.jumlah_ppn.value, delimiter,
                            eTax.fields.jumlah_ppnbm.value, delimiter,
                            eTax.fields.id_keterangan_tambahan.value, delimiter,
                            eTax.fields.fg_uang_muka.value, delimiter,
                            eTax.fields.uang_muka_dpp.value, delimiter,
                            eTax.fields.uang_muka_ppn.value, delimiter,
                            eTax.fields.uang_muka_ppnbm.value, delimiter,
                            eTax.fields.referensi.value, delimiter,
                        ),
                    'lt_value':
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        '"%s"%s'
                        % (
                            'FAPR', delimiter,
                            company_npwp, delimiter,
                            company_id.partner_id.tax_holder_address or '', delimiter,
                            company_id.partner_id.tax_holder_name or '', delimiter,
                            company_id.partner_id.city or '', delimiter,
                            eTax.fields.nomor.value or '', delimiter,
                            eTax.fields.rt.value or '', delimiter,
                            eTax.fields.rw.value or '', delimiter,
                            eTax.fields.kecamatan.value or '', delimiter,
                            eTax.fields.kelurahan.value or '', delimiter,
                            eTax.fields.kabupaten.value or '', delimiter,
                            eTax.fields.propinsi.value or '', delimiter,
                            eTax.fields.kode_pos.value or '', delimiter,
                            eTax.fields.nomor_telp.value or '', delimiter,
                        )
                })
                output_head = '%s\n%s\n%s\n' % (
                    output_head,
                    efaktur_values.get('fk_value'),
                    efaktur_values.get('lt_value'),
                )

                # HOW TO ADD 2 line to 1 line for free product
                invoice_object = obj_inv.invoice_line_ids.filtered(
                    lambda inv: inv.tax_ids and inv.product_id)

                line_sorted = sorted(
                    invoice_object, key=lambda a: a.product_id)

                free, sales, tax_status = [], [], {
                    'included': False, 'excluded': False}

                for obj_inv_line in line_sorted:
                    '''
                        *invoice_line_unit_price is price unit use for harga_satuan's column
                        *invoice_line_quantity is quantity use for jumlah_barang's column
                        *invoice_line_total_price is bruto price use for harga_total's column
                        *invoice_line_discount_m2m is discount price use for diskon's column
                        *obj_inv_line.price_subtotal is subtotal price use for dpp's column
                        *tax_line or free_tax_line is tax price use for ppn's column
                    '''

                    invoice_line_unit_price = free_tax_line = tax_line = bruto_total = \
                        diff_bruto = diff_disc = total_discount = 0.0
                    invoice_line_default_code = obj_inv_line.product_id.default_code or ''
                    invoice_line_name = obj_inv_line.product_id.name or ''
                    invoice_line_quantity = obj_inv_line.quantity
                    disc_price = 0
                    currency = obj_inv_line.move_id and obj_inv_line.move_id.currency_id or None
                    if obj_inv_line.discount:
                        disc_price = obj_inv_line.price_unit * obj_inv_line.discount / 100
                    if not obj_inv_line.tax_ids:
                        invoice_line_unit_price = obj_inv_line.price_unit
                    if obj_inv_line.tax_ids:
                        taxes = obj_inv_line.tax_ids.compute_all(
                            disc_price, currency, 1, product=obj_inv_line.product_id, partner=obj_inv_line.move_id.partner_id)
                        disc_price = taxes['total_excluded']
                    if obj_inv_line.move_id.team_id.name != 'CAT':
                        invoice_line_unit_price = invoice_line_unit_price - disc_price
                        disc_price = 0
                    for tax in obj_inv_line.filtered(lambda x: x.price_unit > 0.0).tax_ids:
                        if tax.amount > 0:
                            if tax.price_include:
                                tax_status.update({'included': True})
                                invoice_line_unit_price = (
                                    obj_inv_line.price_subtotal / obj_inv_line.quantity if obj_inv_line.quantity else 0.0) + disc_price
                            else:
                                tax_status.update({'excluded': True})
                                invoice_line_unit_price = (
                                    obj_inv_line.price_subtotal / obj_inv_line.quantity if obj_inv_line.quantity else 0.0) + disc_price
                            tax_line += obj_inv_line.price_subtotal * \
                                (tax.amount/100.0)
                    invoice_line_total_price = invoice_line_unit_price * invoice_line_quantity
                    if tax_status.get('included'):
                        invoice_line_discount_m2m = invoice_line_total_price - \
                            (obj_inv_line.price_subtotal + round(tax_line, 2))
                        if invoice_line_discount_m2m < 0:
                            invoice_line_discount_m2m = 0.0
                    else:
                        invoice_line_discount_m2m = invoice_line_total_price\
                            - obj_inv_line.price_subtotal

                    if obj_inv_line.price_subtotal < 0:
                        for tax in obj_inv_line.tax_ids:
                            free_tax_line += (obj_inv_line.price_subtotal *
                                              (tax.amount / 100.0)) * -1.0
                        free.append({
                            'default_code': invoice_line_default_code,
                            'name': invoice_line_name,
                            'unit_price': round(invoice_line_unit_price, 2),
                            'quantity': invoice_line_quantity,
                            'bruto': invoice_line_total_price,
                            'subtotal': round(obj_inv_line.price_subtotal, 0),
                            'discount': disc_price * invoice_line_quantity,
                            'sale_line_ids': obj_inv_line.sale_line_ids.ids,
                            'order_id': obj_inv_line.sale_line_ids[0].order_id if
                            obj_inv_line.sale_line_ids else False,
                            'ppn': round(free_tax_line, 0),
                            'product_id': obj_inv_line.product_id.id,
                        })
                    elif obj_inv_line.price_subtotal != 0.0:
                        sales.append({
                            'default_code': invoice_line_default_code,
                            'name': invoice_line_name,
                            'unit_price': round(invoice_line_unit_price, 2),
                            'quantity': invoice_line_quantity,
                            'bruto': invoice_line_total_price,
                            'subtotal': round(obj_inv_line.price_subtotal, 0),
                            'discount': disc_price * invoice_line_quantity,
                            'sale_line_ids': obj_inv_line.sale_line_ids.ids,
                            'order_id': obj_inv_line.sale_line_ids[0].order_id if
                            obj_inv_line.sale_line_ids else False,
                            'ppn': round(tax_line, 0),
                            'product_id': obj_inv_line.product_id.id,
                        })

                sub_total_before_adjustment = sub_total_ppn_before_adjustment = 0.0

                '''
                    We are finding the product that has affected
                    by free product to adjustment the calculation
                of discount and subtotal.
                    - the price total of free product will be
                    included as a discount to related of product.
                '''
                if not sales:
                    raise ValidationError(
                        _("Invoice have not relation with sales order."))

                for sale in sales:
                    for f in free:
                        if f['product_id'] == sale['product_id'] and \
                                f['order_id'] == sale['order_id']:
                            sale['discount'] = sale['discount'] + \
                                (f['subtotal'] * -1.0) + f['ppn']
                            sale['subtotal'] = sale['subtotal'] - \
                                (f['subtotal'] * -1.0)

                            tax_line = 0

                            for tax in obj_inv_line.tax_ids:
                                if tax.amount > 0 and tax.export_on_etax == True:
                                    tax_line += sale['subtotal'] * \
                                        (tax.amount/100.0)

                            sale['ppn'] = tax_line

                            free.remove(f)

                    sub_total_before_adjustment += sale['subtotal']
                    sub_total_ppn_before_adjustment += sale['ppn']
                    bruto_total += sale['bruto']
                    total_discount += round(sale['discount'], 2)

                '''
                    We are collecting the list of DPP & PPN which has amount greather than 0.0
                and will be accessing by pass index directly as @params.
                '''
                sales_by_subtotal = [index for (index, sale) in
                                     enumerate(sales) if sale["subtotal"] > 0.0]
                sales_by_ppn = [index for (index, sale) in enumerate(
                    sales) if sale["ppn"] > 0.0]

                _logger.info('CHECK SBS ? : %s, CHECK INVOICE DPP : %s, CHECK INVOICE PPN : %s' % (
                    sales_by_subtotal, eTax.fields.jumlah_dpp.value, eTax.fields.jumlah_ppn.value
                ))

                if not sales_by_ppn:
                    first_ppn = 0.0
                else:
                    first_ppn = sales[sales_by_ppn[0]]['ppn']

                if not sales_by_subtotal:
                    first_dpp = 0.0
                else:
                    first_dpp = sales[sales_by_subtotal[0]]['subtotal']

                first_bruto = sales[0]['bruto']
                first_disc = round(sales[0]['discount'], 2)

                diff_dpp = eTax.fields.jumlah_dpp.value - sub_total_before_adjustment
                diff_ppn = eTax.fields.jumlah_ppn.value - sub_total_ppn_before_adjustment

                if tax_status.get('included') and tax_status.get('excluded'):
                    if total_discount > 0.0:
                        raise ValidationError(
                            _("There are Invoice Line have more tax type include and exclude : %s" % obj_inv.name))
                elif tax_status.get('excluded'):
                    if total_discount > 0.0:
                        diff_disc = (
                            bruto_total - (eTax.fields.jumlah_dpp.value)) - total_discount
                        diff_bruto = eTax.fields.jumlah_dpp.value - \
                            (bruto_total - total_discount)
                    else:
                        diff_bruto = eTax.fields.jumlah_dpp.value - bruto_total

                    diff_bruto = diff_bruto * \
                        (-1.0) if diff_bruto < 0.0 else diff_bruto
                elif tax_status.get('included'):
                    diff_disc = 0.0
                    diff_bruto = 0.0  # No Adjustment

                '''
                    We will adjust Bruto, DPP, PPN and Discount column if there is differential
                due to Rounding.
                '''

                # Adjustment Bruto
                if diff_bruto != 0.0:
                    first_bruto += diff_bruto

                # Adjustment DPP
                if diff_dpp != 0.0:
                    first_dpp += diff_dpp

                # Adjustment PPN
                if diff_ppn != 0:
                    first_ppn += diff_ppn

                # Adjustment Disount Total End
                if diff_disc != 0:
                    first_disc += diff_disc

                sales[0]['bruto'] = first_bruto
                sales[0]['discount'] = first_disc
                sales[sales_by_subtotal[0]
                      if sales_by_subtotal else 0]['subtotal'] = first_dpp
                sales[sales_by_ppn[0] if sales_by_ppn else 0]['ppn'] = first_ppn

                check_count = len(sales)
                n = 0
                for sale in sales:
                    n += 1
                    if n < check_count:
                        output_head += '"OF"' + delimiter + '\"' + sale['default_code'] + \
                            '\"' + delimiter + '\"' + sale['name'] + '\"' + delimiter + '\"' + \
                            str(sale['unit_price']) + '\"' + delimiter + '\"' + \
                            str(sale['quantity']) + \
                            '\"' + delimiter + '\"' + \
                            str(sale['bruto']) + '\"' + delimiter
                        output_head += '\"' + str(round(sale['discount'], 2)) + '\"' + delimiter + \
                            '\"' + str(sale['subtotal']) + '\"' + delimiter + '\"' + \
                            str(sale['ppn']) + \
                            '\"' + delimiter + '0' + delimiter + '0' + delimiter
                        output_head += delimiter + '' + delimiter + '' + delimiter + '' + delimiter + \
                            '' + delimiter + '' + delimiter + '' + delimiter + '' + '\n'
                    if n == check_count:
                        output_head += '"OF"' + delimiter + '\"' + sale['default_code'] + \
                            '\"' + delimiter + '\"' + sale['name'] + '\"' + delimiter + '\"' + \
                            str(sale['unit_price']) + '\"' + delimiter + '\"' + \
                            str(sale['quantity']) + \
                            '\"' + delimiter + '\"' + \
                            str(sale['bruto']) + '\"' + delimiter
                        output_head += '\"' + str(round(sale['discount'], 2)) + '\"' + delimiter + \
                            '\"' + str(sale['subtotal']) + '\"' + delimiter + '\"' + \
                            str(sale['ppn']) + \
                            '\"' + delimiter + '0' + delimiter + '0' + delimiter
                        output_head += delimiter + '' + delimiter + '' + delimiter + '' + delimiter + \
                            '' + delimiter + '' + delimiter + '' + delimiter

        download_ids = self.env['etax.invoice'].browse(self.get_active_ids())
        download_ids.write({'downloaded': True})

        return output_head
