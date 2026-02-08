# -*- coding: utf-8 -*-

import logging
import pytz

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.addons.sanqua_print.helpers import amount_to_text,\
    format_local_currency,\
    format_local_datetime
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    total_discount_amount = fields.Float(string='Total Discount', readonly=True,
        digits=dp.get_precision('Discount'), compute='_compute_discount', store=True)
    
    return_picking_id = fields.Many2one('stock.picking', string="Return Doc", copy=False)
    available_reverse_picking_ids = fields.Many2many('stock.picking', string="Available Reverse Pickings", compute="_compute_available_reverse_picking_ids")

    def terbilang(self, satuan):
        huruf = ["","Satu","Dua","Tiga","Empat","Lima","Enam","Tujuh","Delapan","Sembilan","Sepuluh","Sebelas"]
        # huruf = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve"]
        hasil = ""; 
        if satuan < 12: 
            hasil = hasil + huruf[int(satuan)]; 
        elif satuan < 20: 
            hasil = hasil + self.terbilang(satuan-10)+" Belas"; 
        elif satuan < 100:
            hasil = hasil + self.terbilang(satuan/10)+" Puluh "+self.terbilang(satuan%10); 
        elif satuan < 200: 
            hasil=hasil+"Seratus "+self.terbilang(satuan-100); 
        elif satuan < 1000: 
            hasil=hasil+self.terbilang(satuan/100)+" Ratus "+self.terbilang(satuan%100); 
        elif satuan < 2000: 
            hasil=hasil+"Seribu "+self.terbilang(satuan-1000); 
        elif satuan < 1000000: 
            hasil=hasil+self.terbilang(satuan/1000)+" Ribu "+self.terbilang(satuan%1000); 
        elif satuan < 1000000000:
            hasil=hasil+self.terbilang(satuan/1000000)+" Juta "+self.terbilang(satuan%1000000);
        elif satuan < 1000000000000:
            hasil=hasil+self.terbilang(satuan/1000000000)+" Milyar "+self.terbilang(satuan%1000000000)
        elif satuan >= 1000000000000:
            hasil="Angka terlalu besar, harus kurang dari 1 Trilyun!"; 
        return hasil;

    def _compute_available_reverse_picking_ids(self):
        for rec in self:
            pickings = self.env['stock.picking']
            purchase_lines = rec.line_ids.mapped('purchase_line_id')
            pickings = purchase_lines.order_id.picking_ids.filtered(lambda r:r.picking_type_code!='incoming' and r.state=='done')
            rec.available_reverse_picking_ids = pickings.ids

    @api.depends('invoice_line_ids')
    def _compute_discount(self):
        for rec in self:
            rec.total_discount_amount = sum([x.amount_discount for x in rec.invoice_line_ids])

    @staticmethod
    def get_format_currency(value,total=False):
        """ Get format currency with rule: thousand -> (.) and no decimal place.
        :param value: Float. Value that need to be formatting.
        :return: String. Format currency result.
        """
        return format_local_currency(value,total)

    def get_format_datetime(self, datetime_value, only_date=False):
        """ Get format datetime as string.
        :param datetime_value: Datetime. Datetime that need to be formatting.
        :param only_date: Boolean. If 'True' then value will be return as Date.
        :return: String. Format datetime result.
        """
        user_tz = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        return format_local_datetime(user_tz, datetime_value, only_date=True)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    return_move_id = fields.Many2one('stock.move', compute="_compute_return_move_id")

    def _compute_return_move_id(self):
        for rec in self:
            move = self.env['stock.move']
            if rec.move_id.return_picking_id.id:
                move = rec.move_id.return_picking_id.move_lines.filtered(lambda r:r.product_id.id == rec.product_id.id)
                exact_qty = move.filtered(lambda r:r.product_uom_qty==rec.quantity)
                if len(exact_qty):
                    move = exact_qty
                
                if len(move)>1:
                    move = move[0]

                
            rec.return_move_id = move.id

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.move_id

        # Create default values.
        default_values_list = []
        for move in moves:
            default_values_list.append(self._prepare_vals_reversal(move))

        # Handle reverse method.
        if self.refund_method == 'cancel':
            if any([vals.get('auto_post', False) for vals in default_values_list]):
                new_moves = moves._reverse_moves(default_values_list)
            else:
                new_moves = moves._reverse_moves(default_values_list, cancel=True)
        elif self.refund_method == 'modify':
            moves._reverse_moves(default_values_list, cancel=True)
            moves_vals_list = []
            for move in moves.with_context(include_business_fields=True):
                moves_vals_list.append(move.copy_data({
                    'invoice_payment_ref': move.name,
                    'date': self.date or move.date,
                })[0])
            new_moves = self.env['account.move'].create(moves_vals_list)
        elif self.refund_method == 'refund':
            new_moves = moves._reverse_moves(default_values_list)
        else:
            return

        # Create action.
        action = {
            'name': _('Reverse Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
        }
        if len(new_moves) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': new_moves.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', new_moves.ids)],
            })
        return action

    def _prepare_vals_reversal(self, move):
        return {
                'ref': _('%s') % (move.name),
                'date': self.date or move.date,
                'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
                'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
                'invoice_payment_term_id': None,
                'auto_post': True if self.date > fields.Date.context_today(self) else False,
            }