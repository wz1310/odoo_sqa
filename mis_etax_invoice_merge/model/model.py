from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class ETaxInvoiceMerge(models.Model):
    _inherit = 'etax.invoice.merge'

    commercial_note = fields.Text(string='Note', store=True)
    custom_customer = fields.Char()

    def btn_posted(self):
        res = super(ETaxInvoiceMerge, self).btn_posted()
        if any(x.state == 'draft' for x in self.invoice_ids):
            raise UserError("You are cannot post if any state draft in Invoices SO")
        return res

    # penambahan popup custom customer
    def open_change_post_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('mis_etax_invoice_merge.change_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'active_id':self.id,'active_ids':self.ids,'default_change_customer':self.custom_customer,'active_model':'etax.invoice.merge'})
        print("context",context)
        res = {
            'name': "%s - %s" % (_('Change custom customer'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'change.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    @api.onchange('partner_id')
    def _onchange_custom_cust(self):
        context = dict(self.env.context or {})
        context.update({'custom_customer':self.custom_customer})
        if not self.ids:
            self.custom_customer = self.partner_id.name


class ChangePostWizard(models.TransientModel):
    _name = 'change.post.wizard'

    reason = fields.Text(required=True)
    suffix_action = fields.Char()
    change_customer = fields.Char(string="Custom customer")
    change_customer_string = fields.Char(related="change_customer", readonly=True)
    user_post = fields.Many2one('res.users')


    def confirm(self):
        res_id = self._context.get('active_id')
        model = self._context.get('active_model')
        if not res_id or not model:
            raise UserError("Require to get context active id and active model!")
        
        Env = self.env[model]
        Record = Env.sudo().browse(res_id)

        if len(Record):
            msgs = []

            if self.change_customer:
                self.user_post = self.env.user.id
                msgs.append("<span class=\"text-danger\">%s --> %s</span>" % (self.env.context.get('default_change_customer'),self.change_customer_string,))
                msgs.append("<span class=\"text-danger\">Changed by: %s</span>" % (self.user_post.name))
            
            if self.reason:
                msgs.append("<span>Reason: %s</span>" % (self.reason))

            msgs = "<br/>".join(msgs)
            
            Record.custom_customer = self.change_customer
            Record.message_post(body=msgs)
            if self.suffix_action:
                getattr(Record, self.suffix_action)()

class MyAccountMovePopup(models.Model):
    _inherit = 'account.move'

#     pick_method = fields.Selection([('Take in Plant','Take in Plant'),
#         ('Deliver','Deliver')],store=True)
    call_pick_method = fields.Boolean('Pick',compute='_domain_pick_method')
    pick_method = fields.Many2one('order.pickup.method',store=True)
    div_method = fields.Many2one('crm.team',store=True)
#     invoice_origin = fields.Char(string='Origin', readonly=True, tracking=True,
#         help="The document(s) that generated the invoice.", related='picking_ids.doc_name')
#     pick_methods = fields.Char(compute='_pick_method',store=True)

#     @api.depends('invoice_origin')
#     def _pick_method(self):
#         for rec in self:
#             if rec.invoice_origin:
#                 find_pick = self.env['stock.picking'].search([('doc_name','=',rec.invoice_origin)])
#                 if find_pick.order_pickup_method_id.name == 'Take in Plant':
#                     rec.pick_method.id = 2
# #                     rec.pick_methods = rec.pick_method
#                 elif find_pick.order_pickup_method_id.name == 'Deliver':
#                     rec.pick_method.id = 1
# #                     rec.pick_methods = rec.pick_method
#                 else:
#                     rec.pick_method = False
# #                     rec.pick_methods = rec.pick_method
#             else:
#                 rec.pick_method = False
# #                 rec.pick_methods = rec.pick_method

    @api.onchange('picking_ids')
    def _onchange_pick(self):
        idz = []
        if self.picking_ids:
            n_id = [x.doc_name for x in self.picking_ids]
            self.invoice_origin = n_id[0]
        else:
            self.invoice_origin = ''

    @api.depends('call_pick_method')
    def _domain_pick_method(self):
        for rec in self:
            if rec.invoice_origin:
#                 self.env.cr.execute("""UPDATE account_move SET invoice_origin=%s
#                 WHERE id=%s""",(rec.invoice_origin,rec.id))
                if not rec.pick_method or not rec.div_method:
                    rec.call_pick_method = True
                    if rec.call_pick_method :
                        sql = """SELECT order_pickup_method_id,sales_team_id FROM stock_picking where doc_name=%s"""
                        cr= self.env.cr
                        cr.execute(sql,(rec.invoice_origin,))
                        result= cr.fetchall()
                        find_pick = [x[0] for x in result]
                        find_div = [x[1] for x in result]
                        # print("FIND PICK",find_pick)
                        # print("FIND DIV",find_pick)
                        rec.pick_method = find_pick[0] if len(find_pick)>0 else rec.pick_method
                        rec.div_method = find_div[0] if len(find_div)>0 else rec.div_method
                    else:
                        rec.call_pick_method = False
                        rec.pick_method = rec.pick_method
                        rec.div_method = rec.div_method
                else:
                    rec.call_pick_method = False
                    rec.pick_method = rec.pick_method
                    rec.div_method = rec.div_method
            else:
                rec.call_pick_method = False
                rec.pick_method = rec.pick_method
                rec.div_method = rec.div_method

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    e_tax_vendor_bill = fields.Many2one('account.move', string="E Tax No.")
