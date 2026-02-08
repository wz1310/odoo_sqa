from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)

from odoo.osv.expression import OR,AND

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    user_allowed_warehouse_ids = fields.Many2many(comodel_name="stock.warehouse", compute="_compute_user_allowed_warehouse_ids")
    other_warehouse_ids = fields.Many2many(comodel_name="stock.warehouse", string="Other Allowed WHs")

    other_wh_can_read = fields.Boolean(string="Other Plant can Read?", default=False)

    count_picking_refused = fields.Integer(compute='_compute_picking_interco')
    count_picking_need_plan_confirm = fields.Integer(compute="_compute_picking_interco")

    show_dash = fields.Boolean(string="Show on Dashboard", compute="_compute_show_dash", store=False, search="_search_show_dash")
    diff_company_show_dash = fields.Boolean(default=False)
    diff_company = fields.Boolean(string="DIfferent Company", compute="_compute_diff_company")
    

    def _compute_diff_company(self):
        company = self.env.user.company_id
        for rec in self:
            res = False
            if rec.company_id.id not in company.ids:
                res = True
            rec.diff_company = res
            
    
    def read(self, fields=None, load='_classic_read'):
        res = super(StockPickingType, self.sudo()).read(fields=fields, load=load)
        
        return res


    def _search_show_dash(self, operator, value):
        domain = [('company_id','not in', self.env.user.company_id.ids),('other_wh_can_read','=',False)]
        
        if operator=='=':
            if value == True:
                domain = ['|', ('company_id','in', self.env.user.company_ids.ids),('other_wh_can_read','=',True)]
        # recs = self.search(domain)
        return domain
    
    
    def _compute_show_dash(self):
        allowed = self.filtered(lambda r:r.company_id.id in self.env.user.company_ids.ids or r.other_wh_can_read==True)
        not_allowed = self-allowed
        allowed.update({'show_dash':True})
        not_allowed.update({'show_dash':False})


    @api.constrains('other_wh_can_read')
    def constrains_other_wh_can_read(self):
        self.warehouse_id.other_wh_can_read = self.other_wh_can_read

        if self.default_location_src_id.id:
            self.default_location_src_id.other_wh_can_read = self.other_wh_can_read
            if self.default_location_src_id.location_id.id:
                self.default_location_src_id.location_id.other_wh_can_read = self.other_wh_can_read
            
        
        if self.default_location_dest_id.id:
            self.default_location_dest_id.other_wh_can_read = self.other_wh_can_read
            if self.default_location_dest_id.location_id.id:
                self.default_location_dest_id.location_id.other_wh_can_read = self.other_wh_can_read



    def _compute_picking_interco(self):
        for rec in self:
            query = """SELECT COUNT(id) as counter FROM stock_picking where company_id=%s 
                AND warehouse_plant_id IS NULL AND picking_type_id=%s AND state in ('confirmed')
            """
            self.env.cr.execute(query, (rec.company_id.id, rec.id,))
            query_res = self.env.cr.fetchall()
            total_refused = sum([x[0] for x in query_res])


            query = """SELECT COUNT(id) as counter FROM stock_picking where company_id=%s 
                AND plant_id = %s AND picking_type_id=%s AND state in ('confirmed')
            """
            self.env.cr.execute(query, (rec.company_id.id, self.env.user.company_id.id, rec.id,))
            query_res = self.env.cr.fetchall()
            total_need_confirmation = sum([x[0] for x in query_res])


            rec.update({
                'count_picking_refused': total_refused,
                'count_picking_need_plan_confirm': total_need_confirmation,
            })


    def _compute_picking_count(self):
        self = self.sudo()
        non_global_type = self.filtered(lambda r:r.other_wh_can_read==False)
        super(StockPickingType, non_global_type)._compute_picking_count()

        global_type = self.filtered(lambda r:r.other_wh_can_read==True)

        if len(global_type):
            for rec in global_type:
                super(StockPickingType, rec.with_user(SUPERUSER_ID).with_context(force_company=rec.company_id.id, allowed_company_ids=rec.company_id.ids))._compute_picking_count()

    def _compute_user_allowed_warehouse_ids(self):
        alloweds = self.env.user.sudo().warehouse_ids
        for rec in self:
            rec.user_allowed_warehouse_ids = alloweds

    def _get_action(self, action_xmlid):
        from ast import literal_eval
        
        if self.other_wh_can_read:
            action = self.env.ref(action_xmlid).read()[0]
            
            if self:
                action['display_name'] = self.sudo().display_name
            
            default_immediate_tranfer = True
            
            
            if self.env['ir.config_parameter'].sudo().get_param('stock.no_default_immediate_tranfer'):
                default_immediate_tranfer = False
            
            context = self._context.copy()
            
            context.update({
                'search_default_picking_type_id': [self.id],
                'default_picking_type_id': self.sudo().id,
                'default_immediate_transfer': default_immediate_tranfer,
                'default_company_id': self.sudo().company_id.id,
                'allowed_company_ids':self._context.get('allowed_company_ids'),
                'force_company':self.sudo().company_id.id
            })
            
            action_context = literal_eval(action['context'])
            context = {**action_context, **context}
            action['context'] = context
            
        else:
            action = super()._get_action(action_xmlid)
        return action


    def get_action_picking_tree_waiting(self):
        Env = self
        if self.other_wh_can_read:
            Env = self.with_context(force_company=self.company_id.id,allowed_company_ids=self.company_id.ids)
        return super(StockPickingType, Env).get_action_picking_tree_waiting()

    def get_action_picking_tree_need_plan_confirm(self):
        Env = self
        if self.other_wh_can_read:
            allowed_company_ids = self.company_id.ids+self.env.company.ids
            context = self._context.copy()
            context.update(dict(force_company=self.company_id.id,allowed_company_ids=allowed_company_ids,cids=2,uid=1))
            Env = self.with_context(context)
        return Env._get_action('sanqua_sale_flow.action_picking_tree_need_plan_confirm')
    

    def get_action_picking_tree_refused(self):
        Env = self
        if self.other_wh_can_read:
            Env = self.with_context(force_company=self.company_id.id,allowed_company_ids=self.company_id.ids)
        return Env._get_action('sanqua_sale_flow.action_picking_tree_refused')


    def get_stock_picking_action_picking_type(self):
        self.ensure_one()
        if self.other_wh_can_read:
            
            allowed_company_ids = self._context.get('allowed_company_ids')
            allowed_company_ids.append(self.company_id.id)
            
            self = self.with_user(1).with_context(all_companies=True,allowed_company_ids=allowed_company_ids, force_company=self.company_id.id, cids=self.company_id.id)
        return self._get_action('stock.stock_picking_action_picking_type')


    @api.model
    def adjust_global_rule(self):
        operation_rule = self.env.ref('stock.stock_picking_type_rule')
        operation_rule.write({'domain_force':"['|',('company_id','in', company_ids),('other_wh_can_read','=',True)]"})

        warehouse_rule = self.env.ref('stock.stock_warehouse_comp_rule')
        warehouse_rule.write({'domain_force':"['|',('company_id','in', company_ids),('other_wh_can_read','=',True)]"})

        picking_rule = self.env.ref('stock.stock_picking_rule')
        # picking_rule.write({'domain_force':"['|',('company_id','in', company_ids),('allowed_company_ids','in',company_ids)]"})
        picking_rule.write({'domain_force':"['|','|',('company_id','in', company_ids),('allowed_company_ids','in',company_ids),'&',('picking_type_code','=','outgoing'),('is_locked','=',False)]"})


        # write move rules
        move_rule = self.env.ref('stock.stock_move_rule')
        # move_rule.write({'domain_force':"['|',('company_id','in', company_ids),('allowed_company_ids','in',company_ids)]"})
        # origin = ['|', ('company_id', 'in', "{company_ids}"), ('location_dest_id.company_id', '=', "{False}")]
        # new_move_domain = OR(origin, [('allowed_company_ids','in',"{company_ids}")])


        new_move_domain = " ['|', '|', ('company_id', 'in', company_ids), ('location_dest_id.company_id', '=', False), ('allowed_company_ids','in',company_ids)]"
        move_rule.write({'domain_force':new_move_domain})

        move_line_rule = self.env.ref('stock.stock_move_line_rule')
        new_move_line_domain = "['|', '|', ('company_id','=',False),('company_id', 'in', company_ids), ('allowed_company_ids','in',company_ids)]"
        move_line_rule.write({'domain_force':new_move_line_domain})


        location_rule = self.env.ref('stock.stock_location_comp_rule')
        # location_rule.write({'domain_force':"['|','|',('company_id','=',False),('company_id', 'in', company_ids),('other_wh_can_read','=',True)]"})
        location_rule.write({'active':False})


        sale_rule = self.env.ref('sale.sale_order_comp_rule')
        sale_rule.write({'domain_force':"['|',('company_id','in', company_ids),('allowed_company_ids','in',company_ids)]"})

        sale_line_rule = self.env.ref('sale.sale_order_line_comp_rule')
        sale_line_rule.write({'domain_force':"['|','|', ('company_id','in', company_ids),('allowed_company_ids','in',company_ids),('company_id','=',False)]"})
        
        # operation type not show_operations
        picking_type = self.env['stock.picking.type'].sudo().search([])
        picking_type.write({'show_operations':False})


        operating_unit_picking_type = self.env.ref('operatingunit_warehouse.stock_picking_type_branch_rule')
        operating_unit_picking_type.write({'active':False})

        # SET SALE SEQUENCE TO NO GAP
        sale_sequence = self.env.ref('sale.seq_sale_order')
        sale_sequence.write({'implementation':'no_gap'})

        emp_intercompany_rule = self.env.ref('base.res_company_rule_employee')
        emp_intercompany_rule.write({'active':False})

        # hr.hr_employee_comp_rule
        # hr.hr_employee_public_comp_rule
        emp_intercompany_rule = self.env.ref('hr.hr_employee_comp_rule')
        emp_intercompany_rule.write({'active':False})
        hr_employee_public_comp_rule = self.env.ref('hr.hr_employee_public_comp_rule')
        hr_employee_public_comp_rule.write({'active':False})



        # blacklist rules
        # blacklist_rules = [
        #     'operatingunit_warehouse.stock_picking_branch_rule',
        #     'operatingunit_sale.sale_order_per_warehouse',
        # ]
        # for rule in blacklist_rules:
        #     rec_rule = self.env.ref(rule)
        #     rec_rule.write({'active':False})
        
