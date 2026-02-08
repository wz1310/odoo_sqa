# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ["purchase.order", "approval.matrix.mixin"]

    request_id = fields.Many2many('purchase.request', string='Purchase Request',compute='_compute_purchase_request')
    asset = fields.Boolean(string='Asset', oldname="asset")
    non_asset_type = fields.Selection([("saleable", "Saleable Product"), ("operational", "Operational"), ("material", "Material")], string="Non Asset Type", compute="_compute_non_asset_type")
    inword_amount = fields.Char('Inword',compute="inword")
    purchase_order_type = fields.Selection([('bahan_baku','PO BAHAN BAKU PRODUKSI'),
                                    ('bahan_pendukung','PO BAHAN PENDUKUNG PRODUKSI'),
                                    ('asset','PO ASSET'),
                                    ('barang_khusus','PO BARANG KHUSUS'),
                                    ('operasional','PO OPERATIONAL'),
                                    ('amdk','PO AMDK & BVG '),
                                    ('lain','PO LAIN LAIN')
                                    ], string="PO Kategori")
    status_po = fields.Selection([("open","In Progress"),("done","Done"),("close","Close")])
    sisa_picking = fields.Float(string="Sisa Picking")
    def inword(self):
        result = {}
        for row in self:
            temp = row.terbilang(int(row.amount_total))
            result.update({row.id:temp})
            row.inword_amount = temp + " Rupiah"

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


    @api.depends('order_line')
    def _compute_non_asset_type(self):
        for rec in self:
            mapped_non_asset_type = rec.order_line.mapped('product_id.non_asset_type')
            if len(mapped_non_asset_type) == 1:
                rec.non_asset_type = mapped_non_asset_type[0]
            else:
                rec.non_asset_type = False

    @api.depends('order_line')
    def _compute_purchase_request(self):
        self.request_id = self.order_line.mapped('purchase_request_line_id').purchase_request_id

    @api.model_create_multi
    def create(self,vals):
        if not self._context.get('active_model')=='purchase.request' and not self._context.get('force_request'):
            if not self._context.get('active_model')=='purchase.requisition':
                raise UserError(_('Only can create PO from Purchase Request!'))
        return super(PurchaseOrder,self).create(vals)

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order.checking_approval_matrix()
            order._add_supplier_to_product()
            order.write({'state': 'to approve'})
    
    def btn_approve(self, force=False):
        
        if not self._context.get('force_request'):    
            self.approving_matrix()
        
        if self.approved:
            self.status_po = 'open'
            
            self.with_context(allowed_company_ids=self.company_id.ids,cids=self.company_id.id).button_approve()

    def button_reject(self):
        self.rejecting_matrix()
        self.button_cancel()

    @api.depends('order_line.move_ids.returned_move_ids',
                'order_line.move_ids.state',
                'order_line.move_ids.picking_id')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)
            id_order = False
            try:
                id_order = self.id
            except:
                id_order = self._origin.id
            idsk = self.env['stock.picking'].search([('purchase_id','=', id_order),('state','not in',['done','cancel'])])
            order.sisa_picking = len(idsk)
            if len(idsk) == 0 and order.status_po == 'open':
                order.status_po = 'done'
            elif len(idsk) > 0:
                order.status_po = 'open'
        
    def btn_close(self):
        self.status_po = 'close'
        picking_ids = self.env['stock.picking'].search([('purchase_id','=',self.id),('state','not in',['cancel','done'])])
        print("PICKING_IDS",picking_ids.id)
        for picking in picking_ids:
            picking.action_cancel()
        self.state = 'done'
            


    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Purchase Order</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'purchase.order'})
        res = {
            'name': "%s - %s" % (_('Rejecting Purchase'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def __authorized_form(self, root):
          
        def append_readonly_non_draft(elm):
            # _logger.info(('---- loop', elm.tag))
            if elm.tag!='field':
                return elm
            
            # _logger.info(('-------------->', elm.get('name')))
            attrs = elm.get('attrs')
            
            if attrs:
                # IF HAS EXISTING "attrs" ATTRIBUTE
                attrs_dict = literal_eval(attrs)
                attrs_readonly = attrs_dict.get('readonly')
                # if had existing readonly rules on attrs will append it with or operator
                
                if attrs_readonly:
                    if type(attrs_readonly) == list:
                        # readonly if limit_approval_state not in draft,approved
                        # incase:
                        # when so.state locked (if limit automatically approved the limit_approval_state will still in draft) so will use original functions
                        # when so.state == draft and limit approval strate in (need_approval_request,  need_approval, reject) will lock the field form to readonly
                        
                        # print(attrs_readonly)
                        # forced domain
                        attrs_readonly = [('state', 'not in',['draft'])]
                    attrs_dict.update({'readonly':attrs_readonly})
                else:
                    # if not exsit append new readonly key on attrs
                    attrs_dict.update({'readonly':[('state','not in',['draft'])]})
            else:
                
                attrs_dict = {'readonly':[('state','not in',['draft'])]}
            try:
                new_attrs_str = str(attrs_dict)
                elm.set('attrs',new_attrs_str)
            except Exception as e:
                pass

            return elm


        def set_readonly_on_fields(elms):
            for elm in elms:

                if elm.tag=='field':
                    elm = append_readonly_non_draft(elm)
                else:
                    if len(elm)>0:
                        _logger.info((len(elm)))
                        if elm.tag in ['tree','kanban','form','calendar']:
                            continue # skip if *2many field child element
                        elm = set_readonly_on_fields(elm)
                    else:
                        if elm.tag=='field':
                            elm = append_readonly_non_draft(elm)
            return elms
        paths = []
        for child in root:
            if child.tag=='sheet':
                # child = append_readonly_non_draft(child)
                child = set_readonly_on_fields(child)
        return root

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):

        sup = super()._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        # get generated xml view
        
        # if form
        if view_type=='form':
            root_elm = ET.fromstring("%s" % (sup['arch']))
            # AUTHORIZED ALL "<field>" element
            new_view = self.__authorized_form(root_elm)
            sup.update({'arch':ET.tostring(new_view)})

        return sup

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    purchase_request_line_id = fields.Many2one('purchase.request.line', string='Purchase Request Line')

    def _check_request_qty(self):
        for rec in self:
            if not rec._context.get('force_request'):
                if self._context.get('active_model') not in ['purchase.requisition']:
                    if round(rec.product_qty, 2) > round(rec.purchase_request_line_id.qty, 2):
                        raise UserError(_('Cannot Create Product Qty of PO greather than Qty of Purchase Request : %s --> Qty PR = %s, Qty PO = %s')%(rec.product_id.name, round(rec.purchase_request_line_id.qty, 2),round(rec.product_qty, 2)))
                
    def _check_request_product(self):
        for rec in self:
            if not rec._context.get('force_request'):
                if self._context.get('active_model') not in ['purchase.requisition']:
                    if rec.product_id != rec.purchase_request_line_id.product_id:
                        raise UserError(_('Cannot change Product different of Purchase Request Product '))
                
    @api.constrains('product_id','product_qty','purchase_request_line_id')
    def _constraints_qty_request(self):
        self._check_request_qty()
        self._check_request_product()

    @api.onchange('product_id','product_qty','purchase_request_line_id')
    def _onchange_qty(self):
        self._check_request_qty()
        self._check_request_product()

    def write(self,vals):
        self._check_request_qty()
        self._check_request_product()
        return super(PurchaseOrderLine,self).write(vals)