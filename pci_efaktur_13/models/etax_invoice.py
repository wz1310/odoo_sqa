# -*- coding: utf-8 -*-
"""E-Faktur object, inherit account.move and res.partner"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class ETaxSeries(models.Model):
    """Generate Tax Number"""

    _name = 'etax.series'
    _description = 'E-Tax Series'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Filename', readonly=True, track_visibility='onchange')
    register_date = fields.Date(string='Register Date', track_visibility='onchange')
    end_date = fields.Date(string='valid Until',compute='_compute_end_date',store=True, track_visibility='onchange')
    start_number = fields.Char('First Number', track_visibility='onchange')
    end_number = fields.Char('Last Number', track_visibility='onchange')
    next_avail_no = fields.Many2one('etax.invoice',string='Next Number',compute='_compute_next_avail_no', track_visibility='onchange')
    state_number = fields.Boolean(string='State Number', track_visibility='onchange')
    line_ids = fields.One2many('etax.invoice', 'e_tax_series_id', string='Lines', track_visibility='onchange')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id, track_visibility='onchange')

    def generate_number(self):
        """Function to generate tax number"""

        start_int = ('').join(('').join(self.start_number.split('.')).split('-'))
        end_int = ('').join(('').join(self.end_number.split('.')).split('-'))

        start_num = int(start_int)
        end_num = int(end_int)

        term = end_num - start_num

        if len(start_int) == 16 and len(end_int) == 16:
#             raise Warning("must 13")
            if start_int[:8] == end_int[:8]:
                if int(start_int[-8:]) < int(end_int[-8:]) and term <= 20000:
                    while start_num <= end_num:
                        zero_first_len = len(start_int) - len(str(start_num))
                        i = 1
                        zero_first = ''
                        while i <= zero_first_len:
                            zero_first += '0'
                            i += 1

                        res_value = zero_first + str(start_num)
                        values = {'name': res_value,'e_tax_series_id':self.id}
                        self.env['etax.invoice'].create(values)
                        start_num += 1
                else:
                    raise UserError(_(" last 8 digit of End Number should be greater than \
                        last 8 digit of Start Number && 8 digit of End Number MINUS 8 digit \
                        of Start Number no greater than 10.000"))
            else:
                raise UserError(_(" 1st of 5 digit should be same of Start Number and End Number."))
        else:
            raise UserError(_("total digit should be 16."))

    @api.constrains('state_number')
    def constrains_state_number(self):
        etax_series = self.env['etax.series'].search([('state_number','=',True)])
        if self.state_number == True and len(etax_series) > 1 :
            raise UserError(_("De-Activated other Tax Series before Activated this series!"))
    
    # @api.depends('line_ids')
    def _compute_next_avail_no(self):
        for rec in self:
            if len(rec.line_ids) > 0:
                query = """ 
                    SELECT ei.id FROM etax_invoice ei
                    LEFT JOIN etax_series es ON ei.e_tax_series_id = es.id
                    WHERE ei.e_tax_series_id = %s AND ei.invoice_id IS NULL AND NOW() <= es.end_date AND es.state_number = True
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

    @api.depends('register_date')
    def _compute_end_date(self):
        for rec in self:
            if rec.register_date:
                rec.end_date = fields.Date.to_date('%s-12-31' % (rec.register_date.year))

    @api.model
    def get_avail_number(self):
        # avail = ''
        # for rec in self:
        #     print(rec)
        #     if rec.state_number == True:
        #         avail = rec.next_avail_no
        #         print(rec.next_avail_no)
        # print(avail)
        return self.next_avail_no

class ETaxInvoice(models.Model):
    """E-Faktur object with add some field that need in E-Faktur format"""

    _name = "etax.invoice"
    _description = 'E-Tax Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    is_replaced_e_tax = fields.Boolean(string='Replaced E-Tax', track_visibility='onchange')
    tax_number = fields.Char(compute='_compute_tax_number',string="Tax Number",store=True, track_visibility='onchange')
    tax_digit = fields.Char(related='invoice_id.partner_tax_digit', string='Tax Digit', track_visibility='onchange')

    e_tax_series_id = fields.Many2one('etax.series', string='E-Tax Series', track_visibility='onchange')
    name = fields.Char('e-Faktur code', track_visibility='onchange')
    validated = fields.Boolean('Upload Success',
                               help="if already updloaded to e-pajak check this", default=False, track_visibility='onchange')
    invoice_ids = fields.One2many('account.move','e_tax_invoice_id',string="Invoices", track_visibility='onchange')
    invoice_id = fields.Many2one('account.move', 'Invoice',
                                 help="If you can't find invoice mean already have serial number",
                                 copy=False, readonly=True,compute='_compute_invoice_id',store=True, track_visibility='onchange')
                                 
    date_validated = fields.Datetime('Upload Date', readonly=True, track_visibility='onchange')

    is_vendor = fields.Boolean('Vendor Bill', readonly=True, track_visibility='onchange')
    from_picking = fields.Boolean('From Picking', readonly=True, track_visibility='onchange')
    related_picking_id = fields.Many2one('stock.picking', 'Related Picking', readonly=True, track_visibility='onchange')
    upload_user = fields.Many2one('res.users', 'Upload User', track_visibility='onchange')
    downloaded = fields.Boolean('Downloaded', default=False, track_visibility='onchange')
    invoice_date = fields.Date(related='invoice_id.invoice_date', store=True, track_visibility='onchange')
    tax_payer = fields.Boolean('NPWP', compute="_compute_tax_payer",store=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company.id, track_visibility='onchange')

    def upload_etax(self):
        for rec in self:
            rec.update({
                'validated':True,
                'date_validated':fields.Datetime.today(),
                'upload_user':self.env.user.id
            })

    @api.depends('invoice_id','is_replaced_e_tax','name')
    def _compute_tax_number(self):
        for rec in self:
            digit = rec.tax_digit or ''
            name =  rec.name or ''
            rec.tax_number = digit + str(int(rec.is_replaced_e_tax))+'.' + name

    @api.depends('invoice_id.partner_id')
    def _compute_tax_payer(self):
        for self_id in self:
            if self_id.invoice_id.partner_id.vat not in ('00.000.000.0-000.000', '000000000000000') or self_id.invoice_id.partner_id.vat != False:
                self_id.tax_payer = True
            else:
                self_id.tax_payer = False

    @api.depends('invoice_ids')
    def _compute_invoice_id(self):
        for rec in self:
            if len(rec.invoice_ids) == 1:
                rec.invoice_id = rec.invoice_ids
            else:
                rec.invoice_id = False
    
    def name_get(self):
        result = []
        for efaktur in self:
            result.append((efaktur.id, efaktur.name))
            if not '.' in efaktur.name:
                format = ""
                name = str(efaktur.name)
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
                result.append((efaktur.id, format))
        return result

    
    def write(self, values):
        """Check e-faktur id"""
        if values.get('invoice_id') == False:
            inv_ids = self.env['account.move'].search([('e_tax_invoice_id', '=', self.id)])
            if inv_ids:
                inv_ids.write({'e_tax_invoice_id':False})
        result = super(ETaxInvoice, self).write(values)
        return result

    def apply_e_tax(self):
        if self._context.get('invoice_id'):
            move_id = self.env['account.move'].browse(self._context.get('invoice_id'))
            move_id.write({
                'e_tax_invoice_id':self.id
            })

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'E-Faktur code already exists !'),
    ]

class AccountInvoice(models.Model):
    """Inherit account.move to add some e-faktur field and function"""

    _inherit = "account.move"

    partner_tax_digit = fields.Char(compute='_compute_partner_tax_digit',store=True, track_visibility='onchange')
    e_tax_invoice_id = fields.Many2one('etax.invoice', string="E-Tax",copy=False, track_visibility='onchange')
    e_tax_vendor_bill = fields.Char(string="E-Tax", copy=False, track_visibility='onchange')
    is_replaced_e_tax = fields.Boolean(related='e_tax_invoice_id.is_replaced_e_tax',string='Replaced E-Tax', track_visibility='onchange')
    tax_number = fields.Char(related='e_tax_invoice_id.tax_number',string="Tax Number", track_visibility='onchange')

    e_tax_invoice_validated = fields.Boolean(string="E-faktur Uploaded Success",
                                       readonly=True, related='e_tax_invoice_id.validated', store=True, track_visibility='onchange')
    move_commercial_id = fields.Many2one('etax.invoice.merge', string='Commercial', track_visibility='onchange')
    in_tax_no = fields.Char(related='purchase_id.tax_no',string='Tax Number', track_visibility='onchange')

    # _sql_constraints = [
    #     ('name_uniq', 'unique (tax_number)', 'Tax Number already exists !'),
    #     ]

    @api.depends('partner_id')
    def _compute_partner_tax_digit(self):
        for rec in self:
            rec.partner_tax_digit = rec.partner_id.digit2

    def action_cancel(self):
        """Canceling or unlink E-Faktur"""
        if self.e_tax_invoice_id:
            self.e_tax_invoice_id = False
            self.reset_efaktur()

    
    def name_get(self):
        """Get name"""
        TYPES = {
            'entry': _('Journal Entry'),
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Refund'),
            'in_refund': _('Vendor Refund'),
            'in_receipt': _('Vendor Bill Asset')
        }
        result = []
        for inv in self:
            if inv.state == 'cancel':
                result.append((inv.id, "Cancelled %s %s" % (TYPES[inv.type] or '',
                                                            inv.name or '')))
            else:
                result.append((inv.id, "%s %s" % (TYPES[inv.type] or '', inv.name or '')))
        return result

    
    def reset_efaktur(self):
        """To reset E-Faktur, so it can be use for other invoice"""
        for faktur in self:
            obj = faktur.e_tax_invoice_id
            no_fak = faktur.e_tax_invoice_id.name
            obj.write({
                'validated':False,
                'invoice_id':False,
                'downloaded':False
                })
            faktur.message_post(
                body='e-Faktur Reset: %s ' %(no_fak,),
                subject="Reset Efaktur")
            faktur.write({'e_tax_invoice_id':False})
        return True

    def open_reset_message_wizard(self):
        self.ensure_one()
              
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rev-Efaktur</h4>","default_suffix_action": "replacement_efaktur"}) #uncomment if need append context
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
        replaced = False
        if self.e_tax_invoice_validated == True:
            replaced = True
        self.e_tax_invoice_id.write({
            'is_replaced_e_tax':replaced
        })

    def btn_view_next_e_tax_no(self):
        next_e_tax_no = self.call_etax_series()
        view_id = self.env.ref('pci_efaktur_13.etax_invoice_form_view_readonly')
        return {
         'type': 'ir.actions.act_window',
         'name': _('Faktur Number'),
         'res_model': 'etax.invoice',
         'view_type': 'form',
         'view_mode': 'tree,form',
         'views': [(view_id.id, 'form'),(False,'tree')],
         'view_id': view_id.id,
         'res_id':next_e_tax_no.id,
         'target': 'new',
         'flags': {'mode': 'readonly'},
         'context':{
             'invoice_id':self.id
         }
        }

    def btn_register_next_e_tax_no(self):
        self.e_tax_invoice_id = self.call_etax_series()
    
    def call_etax_series(self):
        register_tax = self.env['etax.series'].search([('state_number','=',True)])
        if not register_tax:
            raise UserError(_('Not more Active Series.'))
        if not register_tax.get_avail_number():
            raise UserError(_('No more allocation faktur number.'))
        return register_tax.get_avail_number()

class ResPartner(models.Model):
    """Inherit res.partner object to add NPWP field and Kode Transaksi"""
    _inherit = "res.partner"

    taxable_enterprise = fields.Boolean(default=False, track_visibility='onchange')
    tax_reg_no = fields.Char(string='NPWP', track_visibility='onchange')
    citizen_id_no = fields.Char(string='NIK', track_visibility='onchange')
    digit2 = fields.Selection([
        ('01', '01 Non Tax Collector'),
        ('02', '02 To the Treasurer Collector (Government Service)'),
        ('03', '03 To Non Treasurer Collectors (BUMN)'),
        ('04', '04 Other Tax Collectors (PPN 1%)'),
        ('06', '06 Other Submissions (Foreigner Tourist)'),
        ('07', '07 Submissions for wich VAT is Not Charged (Special Economic Zone/ Batam)'),
        ('08', '08 Submissions of VAT Exempt (Import Of Certains Goods)'),
        ('09', '09 Transfer of Assets ( Articles 16D of the VAT Act )'),
        ], string='Kode Transaksi', help='The First two digits of the tax number',
                              track_visibility='onchange')
    tax_holder_address = fields.Char('Tax Address', track_visibility='onchange')
    tax_holder_name = fields.Char('Tax Name', track_visibility='onchange')