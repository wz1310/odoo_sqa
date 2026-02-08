import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class PurchaseOrder(models.Model):
    _inherit = 'purchase.request'


    akses_admin					= fields.Boolean()
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    manager_apv = fields.Boolean('Manager')
    dekan_apv = fields.Boolean('Dekan')
    warek_apv = fields.Boolean('Warek')
    rektor_apv = fields.Boolean('Rektor')
    m_budget_apv = fields.Boolean('Manager Budget')
    corporate_apv = fields.Boolean('Corporate')
    ypk_apv = fields.Boolean('Ypk')
    man_id = fields.Many2one('res.users',related='assigned_to')
    dekan_id = fields.Many2one('res.users',related='department_id.dekan')
    warek_id = fields.Many2one('res.users',related='department_id.warek')
    rektor_id = fields.Many2one('res.users',related='department_id.rektor')
    m_budget_id = fields.Many2one('res.users',related='department_id.m_budget')
    corporate_id = fields.Many2one('res.users',related='department_id.corporate')
    ypk_id = fields.Many2one('res.users',related='department_id.ypk')
    tot_amount_pr = fields.Float(compute='_compute_total_amount_pr')
    login_id = fields.Many2one('res.users',compute='onchange_login')
    cek_id_man = fields.Boolean(compute='onchange_cek_id_man')
    cek_id_dekan = fields.Boolean(compute='onchange_cek_id_dekan')
    cek_id_warek = fields.Boolean(compute='onchange_cek_id_warek')
    cek_id_rektor = fields.Boolean(compute='onchange_cek_id_rektor')
    cek_id_m_budget = fields.Boolean(compute='onchange_cek_id_m_budget')
    cek_id_corporate = fields.Boolean(compute='onchange_cek_id_corporate')
    cek_id_ypk = fields.Boolean(compute='onchange_cek_id_ypk')
    man_state = fields.Selection(selection=[
            ('ap_man', 'Approved by manager')],string="Status",tracking=True)
    dekan_state = fields.Selection(selection=[
            ('ap_dekan', 'Approved by dekan')],string="Status",tracking=True)
    warek_state = fields.Selection(selection=[
            ('ap_war', 'Approved by warek')],string="Status",tracking=True)
    rektor_state = fields.Selection(selection=[
            ('ap_rektor', 'Approved by rektor')],string="Status",tracking=True)
    

    purchase_state = fields.Selection(
        comodel_name="purchase.request.line",
        related="line_ids.purchase_state",
        readonly=True,
    )

    @api.onchange('line_ids')
    def onchange_purchase_lines(self):
        for x in self.line_ids:
            x.department_id = self.department_id


    def onchange_login(self):
        if self.login_id != False:
            context = self._context
            current_uid = context.get('uid')
            log= self.env['res.users'].browse(current_uid).id
            self.login_id = log
        # elif self.login_id == False:
            # print("yyyyyyyyyyyyy")

    def onchange_cek_id_man(self):
        if self.login_id == self.man_id or self.login_id.id == 2:
            self.cek_id_man = True
        elif self.login_id != self.man_id or self.login_id.id != 2:
            self.cek_id_man = False

    def onchange_cek_id_dekan(self):
        if self.login_id == self.dekan_id or self.login_id.id == 2:
            self.cek_id_dekan = True
        elif self.login_id != self.dekan_id or self.login_id.id != 2:
            self.cek_id_dekan = False

    def onchange_cek_id_warek(self):
        if self.login_id == self.warek_id or self.login_id.id == 2:
            self.cek_id_warek = True
        elif self.login_id != self.warek_id or self.login_id.id != 2:
            self.cek_id_warek = False

    def onchange_cek_id_rektor(self):
        if self.login_id == self.rektor_id or self.login_id.id == 2:
            self.cek_id_rektor = True
        elif self.login_id != self.rektor_id or self.login_id.id != 2:
            self.cek_id_rektor = False

    def onchange_cek_id_m_budget(self):
        if self.login_id == self.m_budget_id or self.login_id.id == 2:
            self.cek_id_m_budget = True
        elif self.login_id != self.m_budget_id or self.login_id.id != 2:
            self.cek_id_m_budget = False

    def onchange_cek_id_corporate(self):
        if self.login_id == self.corporate_id or self.login_id.id == 2:
            self.cek_id_corporate = True
        elif self.login_id != self.corporate_id or self.login_id.id != 2:
            self.cek_id_corporate = False

    def onchange_cek_id_ypk(self):
        if self.login_id == self.ypk_id or self.login_id.id == 2:
            self.cek_id_ypk = True
        elif self.login_id != self.ypk_id or self.login_id.id != 2:
            self.cek_id_ypk = False

    def button_draft(self):
        self.mapped("line_ids").do_uncancel()
        self.man_state = ''
        self.dekan_state = ''
        self.warek_state = ''
        self.rektor_state = ''
        self.manager_apv = False
        self.dekan_apv = False
        self.warek_apv = False
        self.rektor_apv = False
        self.m_budget_apv = False
        self.corporate_apv = False
        self.ypk_apv = False
        return self.write({"state": "draft"})

    def _compute_total_amount_pr(self):
        if self.requested_by != False:
            self.tot_amount_pr = sum(self.line_ids.mapped('estimated_cost'))

    def cek_amount_level(self):
        nominal = self.tot_amount_pr
        if nominal <1000000:
            find_ap = self.env['approvals.department'].search([
                ('hr_id','=',self.department_id.id),('amount_ap','=','min_1jt')])
            self.manager_apv = find_ap['manager_ap']
            self.dekan_apv = find_ap['dekan_ap']
            self.warek_apv = find_ap['warek_ap']
            self.rektor_apv = find_ap['rektor_ap']
            self.m_budget_apv = find_ap['m_budget_ap']
            self.corporate_apv = find_ap['corporate_ap']
            self.ypk_apv = find_ap['ypk_ap']
        elif (nominal >= 1000000 and nominal < 10000000):
            find_ap = self.env['approvals.department'].search([
                ('hr_id','=',self.department_id.id),('amount_ap','=','min_10jt')])
            self.manager_apv = find_ap['manager_ap']
            self.dekan_apv = find_ap['dekan_ap']
            self.warek_apv = find_ap['warek_ap']
            self.rektor_apv = find_ap['rektor_ap']
            self.m_budget_apv = find_ap['m_budget_ap']
            self.corporate_apv = find_ap['corporate_ap']
            self.ypk_apv = find_ap['ypk_ap']
        elif (nominal >= 10000000) and (nominal < 50000000):
            find_ap = self.env['approvals.department'].search([
                ('hr_id','=',self.department_id.id),('amount_ap','=','min_50jt')])
            self.manager_apv = find_ap['manager_ap']
            self.dekan_apv = find_ap['dekan_ap']
            self.warek_apv = find_ap['warek_ap']
            self.rektor_apv = find_ap['rektor_ap']
            self.m_budget_apv = find_ap['m_budget_ap']
            self.corporate_apv = find_ap['corporate_ap']
            self.ypk_apv = find_ap['ypk_ap']
        elif (nominal >= 50000000):
            find_ap = self.env['approvals.department'].search([
                ('hr_id','=',self.department_id.id),('amount_ap','=','max_50jt')])
            self.manager_apv = find_ap['manager_ap']
            self.dekan_apv = find_ap['dekan_ap']
            self.warek_apv = find_ap['warek_ap']
            self.rektor_apv = find_ap['rektor_ap']
            self.m_budget_apv = find_ap['m_budget_ap']
            self.corporate_apv = find_ap['corporate_ap']
            self.ypk_apv = find_ap['ypk_ap']

    def button_to_approve(self):
        self.cari_estimated_cost()
        self.to_approve_allowed_check()
        self.cek_amount_level()
        return self.write({"state": "to_approve"})

    def cari_estimated_cost(self):
        for rec in self.line_ids:
            if rec.analytic_account_id:
                sql = """ SELECT sum(dt.jml) as total
                FROM (
                SELECT sum(total_amount) AS jml
                FROM hr_expense WHERE state != 'refused' AND state!= 'done' AND state!= 'approved'
                AND analytic_account_id=%s
                UNION ALL
                SELECT coalesce(sum(prl.estimated_cost),0) AS jml FROM purchase_request_line prl
                LEFT JOIN purchase_request pr on prl.request_id = pr.id
                WHERE pr.state not in ('rejected','done')
                AND analytic_account_id=%s) dt """
                cr= self.env.cr
                cr.execute(sql,(rec.analytic_account_id.id,rec.analytic_account_id.id,))
                results  = cr.dictfetchall()
                for res in results:
                    tot_remain = res['total']
                    if self.line_ids.analytic_account_id:
                        amount = []
                        amounts = []
                        for x in self.line_ids.analytic_account_id.crossovered_budget_line:
                            amounts.append(x.practical_amount)
                            amount.append(x.planned_amount)
                            pl_am = sum(amount)
                            pr_am = sum(amounts)
                            # pros = (pl_am * -1 + pr_am) - tot_remain
                            pros = (pl_am * -1)- (self.tot_amount_pr+tot_remain)
                            # print("Pros :",pros)
                            # print("Plane amount :",pl_am)
                            # print("Practical amount :",pr_am)
                            # print("Total amount :",self.tot_amount_pr)
                            # print("Total remaining :",tot_remain)
                            # print("Estimated cost :",self.line_ids.estimated_cost)
                            # if self.line_ids.estimated_cost > pros or self.tot_amount_pr > pros:
                            if pros < 0:
                                raise UserError(_("Budget not enough! Choose other Budget"))

    def button_manager(self):
        self.manager_apv = False
        self.man_state = 'ap_man'
        m_ap = self.manager_apv == False
        d_ap = self.dekan_apv == False
        w_ap = self.warek_apv == False
        r_ap = self.rektor_apv == False
        m_b_ap = self.m_budget_apv == False
        c_ap = self.corporate_apv == False
        y_ap = self.ypk_apv == False
        if (d_ap and w_ap and r_ap and m_b_ap and c_ap and y_ap):
            self.button_approved()
        else :
            self.manager_apv = False

    def button_dekan(self):
        self.dekan_apv = False
        self.dekan_state = 'ap_dekan'
        m_ap = self.manager_apv == False
        d_ap = self.dekan_apv == False
        w_ap = self.warek_apv == False
        r_ap = self.rektor_apv == False
        m_b_ap = self.m_budget_apv == False
        c_ap = self.corporate_apv == False
        y_ap = self.ypk_apv == False
        if (d_ap and w_ap and r_ap and m_b_ap and c_ap and y_ap):
            self.button_approved()
        else :
            self.dekan_apv = False

    def button_warek(self):
        self.warek_apv = False
        self.warek_state = 'ap_war'
        m_ap = self.manager_apv == False
        d_ap = self.dekan_apv == False
        w_ap = self.warek_apv == False
        r_ap = self.rektor_apv == False
        m_b_ap = self.m_budget_apv == False
        c_ap = self.corporate_apv == False
        y_ap = self.ypk_apv == False
        if (d_ap and w_ap and r_ap and m_b_ap and c_ap and y_ap):
            self.button_approved()
        else :
            self.warek_apv = False

    def button_rektor(self):
        self.rektor_apv = False
        self.rektor_state = 'ap_rektor'
        m_ap = self.manager_apv == False
        d_ap = self.dekan_apv == False
        w_ap = self.warek_apv == False
        r_ap = self.rektor_apv == False
        m_b_ap = self.m_budget_apv == False
        c_ap = self.corporate_apv == False
        y_ap = self.ypk_apv == False
        if (d_ap and w_ap and r_ap and m_b_ap and c_ap and y_ap):
            self.button_approved()
        else :
            self.rektor_apv = False

    def button_m_budget(self):
        self.m_budget_apv = False
        m_ap = self.manager_apv == False
        d_ap = self.dekan_apv == False
        w_ap = self.warek_apv == False
        r_ap = self.rektor_apv == False
        m_b_ap = self.m_budget_apv == False
        c_ap = self.corporate_apv == False
        y_ap = self.ypk_apv == False
        if (d_ap and w_ap and r_ap and m_b_ap and c_ap and y_ap):
            self.button_approved()
        else :
            self.m_budget_apv = False

    def button_corporate(self):
        self.corporate_apv = False
        m_ap = self.manager_apv == False
        d_ap = self.dekan_apv == False
        w_ap = self.warek_apv == False
        r_ap = self.rektor_apv == False
        m_b_ap = self.m_budget_apv == False
        c_ap = self.corporate_apv == False
        y_ap = self.ypk_apv == False
        if (d_ap and w_ap and r_ap and m_b_ap and c_ap and y_ap):
            self.button_approved()
        else :
            self.corporate_apv = False

    def button_ypk(self):
        self.ypk_apv = False
        m_ap = self.manager_apv == False
        d_ap = self.dekan_apv == False
        w_ap = self.warek_apv == False
        r_ap = self.rektor_apv == False
        m_b_ap = self.m_budget_apv == False
        c_ap = self.corporate_apv == False
        y_ap = self.ypk_apv == False
        if (d_ap and w_ap and r_ap and m_b_ap and c_ap and y_ap):
            self.button_approved()
        else :
            self.ypk_apv = False

    @api.onchange('requested_by')
    def onchange_app(self):
        for order in self:
            if order.user_has_groups("base.group_erp_manager"):
                self.akses_admin = True

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'purchase.request'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for data in self:
            data.attachment_number = attachment.get(data.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'purchase.request'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'purchase.request', 'default_res_id': self.id}
        return res

class PurchaseOrder(models.Model):
    _inherit = 'res.partner'

    signup_expiration = fields.Datetime(copy=False, 
        groups="base.group_erp_manager,account.group_account_user,purchase.group_purchase_user,purchase.group_purchase_manager, pundi_purchase.group_purchase_corporate")


class InherietPurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    analytic_account_group = fields.Many2one('account.analytic.group',
        domain="[('name', '=', department_name)]")
    department_name = fields.Char(related='department_id.name')
    planned_amount          = fields.Float()
    practicals_amount       = fields.Float()
    sisa_budget             = fields.Float()
    outstanding_amount      = fields.Float()

    @api.onchange('analytic_account_group')
    def onchange_analytic_account_group(self):
        if self.analytic_account_group:
            cari_state = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.state','=','validate'),
                ('grouping_id','=',self.analytic_account_group.id)])
            id_list = []
            for rec in cari_state:
                id_list.append(rec.analytic_account_id.id)
            res = {}
            res ['domain'] = {'analytic_account_id': [('id','in',id_list)]}
            return res

    def cari_sisa_budget(self):
        for rec in self.analytic_account_id.crossovered_budget_line:
            if rec.analytic_account_id:
                sql = """SELECT sum(dt.jml) as total
                        FROM (
                            SELECT sum(ex.total_amount) AS jml
                            FROM hr_expense ex
                            LEFT JOIN hr_expense_sheet exps on ex.sheet_id = exps.id
                            WHERE (exps.state ='draft' OR exps.state='submit' OR exps.state='approve' OR exps.state is Null)
                            AND ex.analytic_account_id="""+str(int(self.analytic_account_id.id))+"""
                            UNION ALL
                            SELECT sum(estimated_cost) AS jml
                            FROM purchase_request_line
                            WHERE request_state != 'rejected' AND request_state != 'done'
                            AND analytic_account_id="""+str(int(self.analytic_account_id.id))+"""
                        ) dt"""
                cr= self.env.cr
                cr.execute(sql)
                results  = cr.dictfetchall()
                for res in results:
                    tot_remain = res['total']
                    # print("iiiiiiiiiiiiiiiiiii",tot_remain)
                    self.outstanding_amount = tot_remain
                    # self.sisa_budget = (self.planned_amount * -1) + (self.practicals_amount - self.outstanding_amount)
                remain_amount = []
                stat_remain = self.env['crossovered.budget.lines'].search([('status', '!=', 'close'),('analytic_account_id', '=', self.analytic_account_id.id)])
                for data in self.analytic_account_id.crossovered_budget_line and stat_remain:
                    remain_amount.append(data.remainings_amount)
                    hasil_remain_amount = sum(remain_amount)
                    print("Remaining amount", hasil_remain_amount)
                    self.sisa_budget = hasil_remain_amount

    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_id(self):
        amount = []
        amounts = []
        if self.analytic_account_id:
            for x in self.analytic_account_id.crossovered_budget_line:
                amount.append(x.planned_amount)
                amounts.append(x.practical_amount)
                pls_am = sum(amount)
                prs_am = sum(amounts)
                # print("----------",pls_am)
                self.planned_amount = pls_am
                self.practicals_amount = prs_am
                self.cari_sisa_budget()


    # @api.onchange('estimated_cost')
    # def onchange_estimated_cost(self):
    #     if self.estimated_cost != False and self.analytic_account_id != False:
    #         sql = """SELECT sum(estimated_cost)
    #         FROM purchase_request_line
    #         WHERE state !='rejected,done'
    #         AND analytic_account_id=%s"""
    #         cr= self.env.cr
    #         cr.execute(sql,(self.analytic_account_id.id,))
    #         result= cr.fetchall()
    #         for res in result:
    #             tot_pr_remain = res[0]
    #         sql = """SELECT sum(total_amount)
    #         FROM hr_expense
    #         WHERE state !='refuse,done,paid'
    #         AND analytic_account_id=%s"""
    #         cr= self.env.cr
    #         cr.execute(sql,(self.analytic_account_id.id,))
    #         results= cr.fetchall()
    #         for res in results:
    #             tot_remain = res[0]
    #             if self.analytic_account_id:
    #                 amount = []
    #                 amounts = []
    #                 for x in self.analytic_account_id.crossovered_budget_line:
    #                     amounts.append(x.practical_amount)
    #                     amount.append(x.planned_amount)
    #                     pl_am = sum(amount)
    #                     pr_am = sum(amounts)
    #                     pros = (pl_am * -1 + pr_am) - tot_remain
    #                     print("wawwwwwwwwwwwwwwwwwwww",pros)
    #                     if self.estimated_cost > pros or self.request_id.tot_amount_pr > pros:
    #                         raise UserError(_("Budget not enough! Choose other Budget"))










