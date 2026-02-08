# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields
from odoo.tools.misc import format_date
from dateutil.relativedelta import relativedelta


class report_mis_budget_vs_real(models.AbstractModel):
    _name = "mis.budget.vs.real"
    _description = "Consolidated Journals Report"
    _inherit = 'account.report'

    filter_multi_company = True
    filter_date = {'mode': 'range', 'filter': 'today'}
    filter_warehouse = True
    # filter_all_entries = False
    # filter_journals = True
    # filter_unfold_all = False

    # Override: disable multicompany
    def _get_filter_journals(self):
        return self.env['account.journal'].search([('company_id', 'in', [self.env.company.id, False])], order="company_id, name")

    @api.model
    def _get_options(self, previous_options=None):
        options = super(report_mis_budget_vs_real, self)._get_options(previous_options=previous_options)
        # We do not want multi company for this report
        options.setdefault('date', {})
        options['date'].setdefault('date_to', fields.Date.context_today(self))
        return options

    def _get_report_name(self):
        return _("Mis Budget Vs Realisasi")

    def get_header(self, options):
        start_date = options['date']['date_from']
        end_date = options['date']['date_to']
        jum_mth = (fields.Date.to_date(end_date).year - fields.Date.to_date(start_date).year)*12 + (fields.Date.to_date(end_date).month - fields.Date.to_date(start_date).month)
        bln = []
        x=0
        for x in range(jum_mth):
            bln.append((fields.Date.to_date(start_date) + relativedelta(months=x+1)).strftime('%b %Y'))

        cols_head = [
            [
                {'name': ""},
                {'name': fields.Date.to_date(start_date).strftime('%b %Y'), 'colspan': 4}],
            [
                {'name': ''},
                {'name': _('Forecast/Budget'), 'colspan': 2},
                {'name': _('Realisasi'), 'colspan': 2}
            ],
            [
                {'name': _('KETERANGAN')},
                {'name': _('Qty/Nilai'), 'class': 'number'},
                {'name': _('% / Cost Per Box'), 'class': 'number'},
                {'name': _('Qty/Nilai'), 'class': 'number'},
                {'name': _('% Pencapaian'), 'class': 'number'},
                {}
                ]
        ]
        if jum_mth>0:
            for x in bln:
                cols_head[0]+=[{},{'name': x, 'colspan':4}]
                cols_head[1]+=[
                                {'name': ''},
                                {'name': _('Forecast/Budget'), 'colspan': 2},
                                {'name': _('Realisasi'), 'colspan': 2}]
                cols_head[2]+=[
                                {'name': _('Qty/Nilai'), 'class': 'number'},
                                {'name': _('% / Cost Per Box'), 'class': 'number'},
                                {'name': _('Qty/Nilai'), 'class': 'number'},
                                {'name': _('% / Cost Per Box'), 'class': 'number'},
                                {'name': _('Selisih'), 'class': 'number'}]
        return cols_head

    def _get_sum_pract(self, results_msb, lambda_filter):
        sum_prac_qty = sum([r['prac_qty'] for r in results_msb if lambda_filter(r) and r['prac_qty']])
        return [sum_prac_qty]

    def _get_sum_bgt(self, results_msb, lambda_filter):
        smbgt = [r['msb_amt'] for r in results_msb if lambda_filter(r)]
        if smbgt:
            sum_plm_qty = int(float(
                [r['msb_amt'] for r in results_msb if lambda_filter(r)][0]))
        else:
            sum_plm_qty = 0
        return [sum_plm_qty]

    def _get_sum_sf(self, results, lambda_filter):
        m_comp = None
        if len(tuple(self.env.context['allowed_company_ids']))>1:
            m_comp = "sf.company_id in %s" % str(tuple(self.env.context['allowed_company_ids']))
        else:
            m_comp = "sf.company_id = %s" % str(self.env.company.id)
        sfor = """SELECT pt.amdk_groups am_gr,sf.forecast_qty sfr_qty,
        sf.month as month,sf.year as year
        FROM sale_forecast sf
        LEFT JOIN product_template pt ON pt.ID = sf.product_id
        WHERE """+m_comp+""""""
        self.env.cr.execute(sfor,)
        result_sf = self.env.cr.dictfetchall()
        sum_sf_qty = int(float(sum([r['sfr_qty'] for r in result_sf if lambda_filter(r)])))
        return [sum_sf_qty]

    def _get_sum(self, results, lambda_filter):
        sum_mp_qty = int(float(sum([r['qty'] for r in results if lambda_filter(r)])))
        return [sum_mp_qty]

    def _get_sum_tot_bp(self, results_msb, lambda_filter):
        sum_bp_qty = int(float(sum([r['bgt_plant'] for r in results_msb if lambda_filter(r)])))
        print("HASIL_get_sum_tot_bp>>>>>>>>>>>>>>>>",f"{sum_bp_qty:,}")
        # sum_credit = self.format_value(sum([r['qty'] for r in results if lambda_filter(r)]))
        # sum_balance = self.format_value(sum([r['qty'] for r in results if lambda_filter(r)]))
        return [sum_bp_qty]

    def _get_total_line_bp(self, options,cek, current_group_bp,current_group_bgt,current_div, results_msb, values, results):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        tot_qty = 0
        tot_pcp = 0
        sum_sfaa = sum([n for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (1,2,3) and x['month']==str(mm) and x['year']==str(yy))])
        sum_sfpa = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in (1,2,3) and x['month']==str(mm) and x['year']==str(yy))])
        sum_sfp = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in (4,5,6) and x['month']==str(mm) and x['year']==str(yy))])
        if current_div == 1:
            tot_qty = sum([x/sum_sfpa for x in self._get_sum_tot_bp(results_msb, lambda x: x['bp_group']==current_group_bp and x['bp_group'] == current_group_bp and x['month']==str(mm) and x['year']==str(yy))])
            tot_pcp = sum([x/sum_sfaa for x in self._get_sum_pract(results_msb, lambda x: x['bp_group'] == current_group_bp and x['month']==str(mm) and x['year']==str(yy))])
        elif current_div == 2:
            tot_qty = sum([x/sum_sfp for x in self._get_sum_tot_bp(results_msb, lambda x: x['bp_group']==current_group_bp and x['month']==str(mm) and x['year']==str(yy))])
            tot_pcp = sum([x/sum_sfaa for x in self._get_sum_pract(results_msb, lambda x: x['bp_group'] == current_group_bp and x['month']==str(mm) and x['year']==str(yy))])
        tot_gl_bp = {
                'id': 'totbpgroup',
                'name': 'Total %s' % values['bg_name'],
                'level': 2,
                'columns': [
                {'name': f"{x:,}" for x in self._get_sum_tot_bp(results_msb, lambda x: x['bp_group']==current_group_bp and x['bp_group'] == current_group_bp and x['month']==str(mm) and x['year']==str(yy))},
                {'name': f"{round(tot_qty,3):,}"},
                {'name': f"{x:,}" for x in self._get_sum_pract(results_msb, lambda x: x['bp_group']==current_group_bp and x['month']==str(mm) and x['year']==str(yy))},
                {'name': f"{round(tot_pcp,3):,}"},
                {'name': f"{round(tot_pcp-tot_qty,3):,}"}
                ],
                'unfoldable': False,
                # 'parent_id': 'budgetgroup_%s_%s' % (current_group_bp,current_group_bgt),
            }
        start_date = options['date']['date_from']
        end_date = options['date']['date_to']
        jum_mth = (fields.Date.to_date(end_date).year - fields.Date.to_date(start_date).year)*12 + (fields.Date.to_date(end_date).month - fields.Date.to_date(start_date).month)
        bln = []
        x=0
        for x in range(jum_mth):
            bln.append((fields.Date.to_date(start_date) + relativedelta(months=x+1)))
        for y in bln:
            tot_qty_loop = 0
            tot_pcp_loop = 0
            sum_sfaa_loop = sum([n for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year))])
            sum_sfpa_loop = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year))])
            sum_sfp_loop = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in (4,5,6) and x['month']==str(y.month) and x['year']==str(y.year))])
            sum_sfa_loop = sum([n for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (4,5,6) and x['month']==str(y.month) and x['year']==str(y.year))])
            if sum_sfp_loop == 0:
                sum_sfp_loop += 1
            if sum_sfa_loop == 0:
                sum_sfa_loop += 1
            if sum_sfpa_loop == 0:
                sum_sfpa_loop += 1
            if sum_sfaa_loop == 0:
                sum_sfaa_loop += 1
            if current_div == 1:
                tot_qty_loop = sum([x/sum_sfpa_loop for x in self._get_sum_tot_bp(results_msb, lambda x: x['bp_group'] == current_group_bp and x['month']==str(y.month) and x['year']==str(y.year))])
                tot_pcp_loop = sum([x/sum_sfaa_loop for x in self._get_sum_pract(results_msb, lambda x: x['bp_group'] == current_group_bp and x['month']==str(y.month) and x['year']==str(y.year))])
            elif current_div == 2:
                tot_qty_loop = sum([x/sum_sfp_loop for x in self._get_sum_tot_bp(results_msb, lambda x: x['bp_group'] == current_group_bp and x['month']==str(y.month) and x['year']==str(y.year))])
                tot_pcp_loop = sum([x/sum_sfa_loop for x in self._get_sum_pract(results_msb, lambda x: x['bp_group'] == current_group_bp and x['month']==str(y.month) and x['year']==str(y.year))])
            tot_gl_bp['columns'] += [
            {'name': f"{x:,}" for x in self._get_sum_tot_bp(results_msb, lambda x: x['bp_group'] == current_group_bp and x['month']==str(y.month) and x['year']==str(y.year))},
            {'name': f"{round(tot_qty_loop,3):,}"},
            {'name': f"{x:,}" for x in self._get_sum_pract(results_msb, lambda x: x['bp_group'] == current_group_bp and x['month']==str(y.month) and x['year']==str(y.year))},
            {'name': f"{round(tot_pcp_loop,3):,}"},
            {'name': f"{round(tot_pcp_loop-tot_qty_loop,3):,}"}
            ]
        return tot_gl_bp

    def _get_group_line_bp(self,options, current_group_bp, results,results_msb, values):
        gl_bp = {
                'id': 'bpgroup_%s' % (current_group_bp),
                'name': '%s' % (values['bg_name']),
                'level': 2,
                'columns': [{'name':""}],
                'unfoldable': True,
                'unfolded': self._need_to_unfold('bpgroup_%s' % (current_group_bp,), options),
            }
        return gl_bp

    def _get_group_line_bgt(self,options,current_group_bgt,current_div,current_group_bp,results_msb, values,results):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        cbb_sum = 0
        cbr_sum = 0
        sum_sfaa = sum([n for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (1,2,3) and x['month']==str(mm) and x['year']==str(yy))])
        sum_sfpa = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in (1,2,3) and x['month']==str(mm) and x['year']==str(yy))])
        sum_sfp = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in (4,5,6) and x['month']==str(mm) and x['year']==str(yy))])
        sum_sfa = sum([n for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (4,5,6) and x['month']==str(mm) and x['year']==str(yy))])
        if sum_sfp == 0:
            sum_sfp += 1
        if sum_sfa == 0:
            sum_sfa += 1
        if sum_sfpa == 0:
            sum_sfpa += 1
        if sum_sfaa == 0:
            sum_sfaa += 1
        if current_div == 1:
            cbb_sum = sum([x/sum_sfpa for x in self._get_sum_bgt(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(mm) and x['year']==str(yy))])
            cbr_sum = sum([x/sum_sfaa for x in self._get_sum_pract(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(mm) and x['year']==str(yy))])
        elif current_div == 2:
            cbb_sum = sum([x/sum_sfp for x in self._get_sum_bgt(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(mm) and x['year']==str(yy))])
            cbr_sum = sum([x/sum_sfa for x in self._get_sum_pract(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(mm) and x['year']==str(yy))])
        gl_bgt = {
                'id': 'budgetgroup_%s_%s' % (current_group_bp,current_group_bgt),
                'name': '%s' % (values['bpos_name']),
                'level': 3,
                'columns': [
                {'name': f"{x:,}" for x in self._get_sum_bgt(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(mm) and x['year']==str(yy))},
                {'name': f"{round(cbb_sum,3):,}"},
                {'name': f"{x:,}" for x in self._get_sum_pract(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(mm) and x['year']==str(yy))},
                {'name': f"{round(cbr_sum,3):,}"},
                {'name': f"{round(cbr_sum-cbb_sum,3):,}"}
                ],
                'unfoldable': False,
                'unfolded': self._need_to_unfold('budgetgroup_%s_%s' % (current_group_bp,current_group_bgt), options),
                'parent_id': 'bpgroup_%s' % (current_group_bp),
            }
        start_date = options['date']['date_from']
        end_date = options['date']['date_to']
        jum_mth = (fields.Date.to_date(end_date).year - fields.Date.to_date(start_date).year)*12 + (fields.Date.to_date(end_date).month - fields.Date.to_date(start_date).month)
        bln = []
        x=0
        for x in range(jum_mth):
            bln.append((fields.Date.to_date(start_date) + relativedelta(months=x+1)))
        for y in bln:
            cbb_sum_loop = 0
            cbr_sum_loop = 0
            sum_sfaa_loop = sum([n for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year))])
            sum_sfpa_loop = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year))])
            sum_sfp_loop = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in (4,5,6) and x['month']==str(y.month) and x['year']==str(y.year))])
            sum_sfa_loop = sum([n for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (4,5,6) and x['month']==str(y.month) and x['year']==str(y.year))])
            if sum_sfp_loop == 0:
                sum_sfp_loop += 1
            if sum_sfa_loop == 0:
                sum_sfa_loop += 1
            if sum_sfpa_loop == 0:
                sum_sfpa_loop += 1
            if sum_sfaa_loop == 0:
                sum_sfaa_loop += 1
            if current_div == 1:
                cbb_sum_loop = sum([x/sum_sfpa_loop for x in self._get_sum_bgt(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(y.month) and x['year']==str(y.year))])
                cbr_sum_loop = sum([x/sum_sfaa_loop for x in self._get_sum_pract(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(y.month) and x['year']==str(y.year))])
            elif current_div == 2:
                cbb_sum_loop = sum([x/sum_sfp_loop for x in self._get_sum_bgt(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(y.month) and x['year']==str(y.year))])
                cbr_sum_loop = sum([x/sum_sfa_loop for x in self._get_sum_pract(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(y.month) and x['year']==str(y.year))])
            gl_bgt['columns'] += [
            {'name': f"{x:,}" for x in self._get_sum_bgt(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(y.month) and x['year']==str(y.year))},
            {'name': f"{round(cbb_sum_loop,3):,}"},
            {'name': f"{x:,}" for x in self._get_sum_pract(results_msb, lambda x: x['bpos'] == current_group_bgt and x['month']==str(y.month) and x['year']==str(y.year))},
            {'name': f"{round(cbr_sum_loop,3):,}"},
            {'name': f"{round(cbr_sum_loop-cbb_sum_loop,3):,}"}
            ]
        return gl_bgt

    def _get_bgt_line(self, options,current_group_bp, current_group_bgt,current_div, current_anl, results_msb, values):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        return {
                'id': 'bgtfold_%s_%s' % (current_anl,current_group_bgt),
                'name': '(%s-%s)'" "'%s'" "'%s' % (values['month'],values['year'],values['anl_acc_code'],values['anl_acc_id']),
                'level': 4,
                'columns': [
                {},
                {},
                {'name': f"{n:,}" for n in self._get_sum_pract(results_msb, lambda x: x['bpos'] == current_group_bgt and x['aac_id'] == current_anl and x['month']==str(mm) and x['year']==str(yy))}
                ],
                'unfoldable': False,
                'unfolded': self._need_to_unfold('bgtfold_%s_%s' % (current_anl,current_group_bgt), options),
                'parent_id': 'budgetgroup_%s_%s' % (current_group_bp,current_group_bgt),
            }

    def _get_group_line_plastik(self, options, current_group, results, record):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        n_budget_p = sum([x for x in self._get_sum_sf(results, lambda x: x['am_gr'] == current_group and x['month']==str(mm) and x['year']==str(yy))])
        cost_real_pls = sum([n/n_budget_p for n in self._get_sum(results, lambda x: x['ms_id'] == current_group and x['month']==str(mm) and x['year']==str(yy))]) if n_budget_p >0 else 0
        gl_plast = {
                'id': 'plastikgroup_%s' % current_group,
                'name': '%s' % (record['group']),
                'level': 2,
                'columns': [
                {'name': f"{x:,}" for x in self._get_sum_sf(results, lambda x: x['am_gr'] == current_group and x['month']==str(mm) and x['year']==str(yy))},
                {},
                {'name': f"{n:,}" for n in self._get_sum(results, lambda x: x['ms_id'] == current_group and x['month']==str(mm) and x['year']==str(yy))},
                {'name': f"{round(cost_real_pls * 100):,}"'%'},
                ],
                'unfoldable': True,
                'unfolded': self._need_to_unfold('plastikgroup_%s' % (current_group,), options),
            }
        start_date = options['date']['date_from']
        end_date = options['date']['date_to']
        jum_mth = (fields.Date.to_date(end_date).year - fields.Date.to_date(start_date).year)*12 + (fields.Date.to_date(end_date).month - fields.Date.to_date(start_date).month)
        bln = []
        x=0
        for x in range(jum_mth):
            bln.append((fields.Date.to_date(start_date) + relativedelta(months=x+1)))
        for y in bln:
            n_budget_p_loop = sum([x for x in self._get_sum_sf(results, lambda x: x['am_gr'] == current_group and x['month']==str(y.month) and x['year']==str(y.year))])
            cost_real_pls_loop = sum([n/n_budget_p_loop for n in self._get_sum(results, lambda x: x['ms_id'] == current_group and x['month']==str(y.month) and x['year']==str(y.year))]) if n_budget_p_loop>0 else 0
            gl_plast['columns'] += [
            {},
            {'name': f"{x:,}" for x in self._get_sum_sf(results, lambda x: x['am_gr'] == current_group and x['month']==str(y.month) and x['year']==str(y.year))},
            {},
            {'name': f"{n:,}" for n in self._get_sum(results, lambda x: x['ms_id'] == current_group and x['month']==str(y.month) and x['year']==str(y.year))},
            {'name': f"{round(cost_real_pls_loop * 100):,}"'%'}
            ]
        return gl_plast

    def _get_mp_line_plastik(self, options, current_group, current_mp, results, record):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        return {
                'id': 'plastikmp_%s_%s' % (current_mp,current_group),
                'name': '%s (%s)' % (record['mp_name'],record['pt_name']),
                'level': 3,
                'columns': [{},{},{'name': f"{n:,}" for n in self._get_sum(results, lambda x: x['mp_id'] == current_mp and x['month']==str(mm) and x['year']==str(yy))}],
                'unfoldable': False,
                'unfolded': self._need_to_unfold('plastikmp_%s_%s' % (current_mp, current_group), options),
                'parent_id': 'plastikgroup_%s' % (current_group),
            }

    def _get_tot_plastik(self, options, current_group, current_mp, results, record):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        n_tot_p = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in
            [*set([x['ms_id'] for x in results])] and x['am_gr'] not in (1,2,3) and x['month']==str(mm) and x['year']==str(yy) if results else x['am_gr'])])
        cost_tot_p = sum([z/n_tot_p for z in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] not in (1,2,3) and x['month']==str(mm) and x['year']==str(yy))]) if n_tot_p >0 else 0
        gt_pls = {
                'id': 'tot_plastik',
                'name': 'Total Plastik',
                'level': 2,
                'columns': [
                {'name': f"{n:,}" for n in self._get_sum_sf(results, lambda x: x['am_gr'] in
                    [*set([x['ms_id'] for x in results])] and x['am_gr'] not in (1,2,3) and x['month']==str(mm) and x['year']==str(yy) if results else x['am_gr'])},
                {},
                {'name': f"{z:,}" for z in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] not in (1,2,3) and x['month']==str(mm) and x['year']==str(yy))},
                {'name': f"{round(cost_tot_p * 100):,}"'%'}
                ],
                'unfoldable': False
            }
        start_date = options['date']['date_from']
        end_date = options['date']['date_to']
        jum_mth = (fields.Date.to_date(end_date).year - fields.Date.to_date(start_date).year)*12 + (fields.Date.to_date(end_date).month - fields.Date.to_date(start_date).month)
        bln = []
        x=0
        for x in range(jum_mth):
            bln.append((fields.Date.to_date(start_date) + relativedelta(months=x+1)))
        for y in bln:
            n_tot_p_loop = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in
                [*set([x['ms_id'] for x in results])] and x['am_gr'] not in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year) if results else x['am_gr'])])
            cost_tot_p_loop = sum([z/n_tot_p_loop for z in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] not in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year))]) if n_tot_p_loop >0 else 0
            gt_pls['columns'] += [
            {},
            {'name': f"{n:,}" for n in self._get_sum_sf(results, lambda x: x['am_gr'] in
                [*set([x['ms_id'] for x in results])] and x['am_gr'] not in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year) if results else x['am_gr'])},
            {},
            {'name': f"{n:,}" for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] not in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year))},
            {'name': f"{round(cost_tot_p_loop * 100):,}"'%'}
            ]
        return gt_pls

    def _get_group_line_amdk(self, options, current_group, results, record):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        n_budget = sum([x for x in self._get_sum_sf(results, lambda x: x['am_gr'] == current_group and x['month']==str(mm) and x['year']==str(yy))])
        cost_real = sum(n/n_budget for n in self._get_sum(results, lambda x: x['ms_id'] == current_group and x['month']==str(mm) and x['year']==str(yy))) if n_budget >0 else 0
        gl_amdk = {
                'id': 'amdkgroup_%s' % current_group,
                'name': '%s' % (record['group']),
                'level': 2,
                'columns': [
                {'name': f"{x:,}" for x in self._get_sum_sf(results, lambda x: x['am_gr'] == current_group and x['month']==str(mm) and x['year']==str(yy))},
                {},
                {'name': f"{n:,}" for n in self._get_sum(results, lambda x: x['ms_id'] == current_group and x['month']==str(mm) and x['year']==str(yy))},
                {'name': f"{round(cost_real * 100):,}"'%'}
                ],
                'unfoldable': True,
                'unfolded': self._need_to_unfold('amdkgroup_%s' % (current_group,), options),
            }
        start_date = options['date']['date_from']
        end_date = options['date']['date_to']
        jum_mth = (fields.Date.to_date(end_date).year - fields.Date.to_date(start_date).year)*12 + (fields.Date.to_date(end_date).month - fields.Date.to_date(start_date).month)
        bln = []
        x=0
        for x in range(jum_mth):
            bln.append((fields.Date.to_date(start_date) + relativedelta(months=x+1)))
        for y in bln:
            n_budget_loop = sum([x for x in self._get_sum_sf(results, lambda x: x['am_gr'] == current_group and x['month']==str(y.month) and x['year']==str(y.year))])
            cost_real_loop = sum(n/n_budget_loop for n in self._get_sum(results, lambda x: x['ms_id'] == current_group and x['month']==str(y.month) and x['year']==str(y.year))) if n_budget_loop>0 else 0
            gl_amdk['columns'] += [
            {},
            {'name': f"{x:,}" for x in self._get_sum_sf(results, lambda x: x['am_gr'] == current_group and x['month']==str(y.month) and x['year']==str(y.year))},{},{'name': f"{n:,}" for n in self._get_sum(results, lambda x: x['ms_id'] == current_group and x['month']==str(y.month) and x['year']==str(y.year))},
            {'name': f"{round(cost_real_loop * 100):,}"'%'}
            ]
        return gl_amdk

    def _get_mp_line_amdk(self, options, current_group, current_mp, results, record):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        return {
                'id': 'mp_%s_%s' % (current_mp,current_group),
                'name': '%s (%s)' % (record['mp_name'],record['pt_name']),
                'level': 3,
                'columns': [{},{},{'name': f"{n:,}" for n in self._get_sum(results, lambda x: x['mp_id'] == current_mp and x['month']==str(mm) and x['year']==str(yy))}],
                'unfoldable': False,
                'unfolded': self._need_to_unfold('mp_%s_%s' % (current_mp, current_group), options),
                'parent_id': 'amdkgroup_%s' % (current_group),
            }

    def _get_tot_amdk(self, options, current_group, current_mp, results, record):
        start_date = options['date']['date_from']
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        tots_amdk = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in
            [*set([x['ms_id'] for x in results])] and x['am_gr'] in (1,2,3)
            and x['month']==str(mm) and x['year']==str(yy) if results else x['am_gr'])])
        cost_tot_real_amdk = sum(y/tots_amdk for y in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (1,2,3) and x['month']==str(mm) and x['year']==str(yy))) if tots_amdk>0 else 0
        gtot_amdk = {
                'id': 'tot_amdk',
                'name': 'Total AMDK',
                'level': 2,
                'columns': [
                {'name': f"{n:,}" for n in self._get_sum_sf(results, lambda x: x['am_gr'] in
                    [*set([x['ms_id'] for x in results])] and x['am_gr'] in (1,2,3) and x['month']==str(mm) and x['year']==str(yy) if results else x['am_gr'])},
                {},
                {'name': f"{y:,}" for y in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (1,2,3) and x['month']==str(mm) and x['year']==str(yy))},
                {'name': f"{round(cost_tot_real_amdk * 100):,}"'%'},
                ],
                'unfoldable': False
            }
        start_date = options['date']['date_from']
        end_date = options['date']['date_to']
        jum_mth = (fields.Date.to_date(end_date).year - fields.Date.to_date(start_date).year)*12 + (fields.Date.to_date(end_date).month - fields.Date.to_date(start_date).month)
        bln = []
        x=0
        for x in range(jum_mth):
            bln.append((fields.Date.to_date(start_date) + relativedelta(months=x+1)))
        for y in bln:
            n_tot_amdk_loop = sum([n for n in self._get_sum_sf(results, lambda x: x['am_gr'] in
                [*set([x['ms_id'] for x in results])] and x['am_gr'] in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year) if results else x['am_gr'])])
            cost_tot_real_amdk_loop = sum(z/n_tot_amdk_loop for z in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year))) if n_tot_amdk_loop>0 else 0
            gtot_amdk['columns'] += [
            {},
            {'name': f"{n:,}" for n in self._get_sum_sf(results, lambda x: x['am_gr'] in
                [*set([x['ms_id'] for x in results])] and x['am_gr'] in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year) if results else x['am_gr'])},
            {},
            {'name': f"{n:,}" for n in self._get_sum(results, lambda x: x['mp_id'] == x['mp_id'] and x['ms_id'] in (1,2,3) and x['month']==str(y.month) and x['year']==str(y.year))},
            {'name': f"{round(cost_tot_real_amdk_loop * 100):,}"'%'}
            ]

        return gtot_amdk

    def _get_tot_forecast_no_res(self, options,results=None):
        forecast_qty = self._get_sum_sf(results, lambda x: x['am_gr'] == x['am_gr'])
        return {
                'id': 'tot_forecast',
                'name': '',
                'level': 2,
                'columns': [{'name': f"{n:,}" for n in self._get_sum_sf(results, lambda x: x['am_gr'] == x['am_gr'])}],
            }

    @api.model
    def _need_to_unfold(self, line_id, options):
        return line_id in options.get('unfolded_lines') or options.get('unfold_all')

    @api.model
    def _get_lines(self, options, line_id=None):
        act_warehouse = None
        selected_warehouse = self._get_options_warehouse(options)
        act_warehouse = list(x['id'] for x in selected_warehouse)
        print("OPTIONNN", list(x['id'] for x in selected_warehouse))
        start_date = options['date']['date_from']
        end_date = options['date']['date_to']
        print("END DATE", end_date)
        mm = fields.Date.to_date(start_date).month
        yy = fields.Date.to_date(start_date).year
        mme = fields.Date.to_date(end_date).month
        yye = fields.Date.to_date(end_date).year
        # 1.Build SQL query
        lines = []
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        sku_dm = self.env['mis.sku'].search([]).mapped('id')
        domain =[('product_id.product_tmpl_id.amdk_groups','in',sku_dm),('company_id','in',self.env.context['allowed_company_ids'])]
        if act_warehouse:
            domain += [('picking_type_id.warehouse_id','in',act_warehouse)]
        mp = self.env['mrp.production']
        where_query = mp._where_calc(domain)
        tables, where_clause, where_params = where_query.get_sql()
        select = """SELECT 
        to_char("mrp_production".date_planned_finished, 'FMMM') as month,
        to_char("mrp_production".date_planned_finished, 'YYYY') as year,
        ms.id as ms_id,pt.name as pt_name,ms.name as group,pp.default_code as code,"mrp_production".name as mp_name, "mrp_production".product_qty as qty,"mrp_production".id AS mp_id,sf.forecast_qty as sf_qty FROM %s
        LEFT JOIN product_product pp on pp.id = "mrp_production".product_id
        LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
        LEFT JOIN mis_sku ms on ms.id = pt.amdk_groups
        LEFT JOIN sale_forecast sf on sf.product_id = pp.product_tmpl_id
        AND sf.year = to_char("mrp_production".date_planned_finished, 'YYYY')
        AND sf.month = to_char("mrp_production".date_planned_finished, 'FMMM')
        WHERE %s AND ms.name IS NOT NULL
        AND "mrp_production".state = 'qc_done'
        GROUP BY month,year,sf.forecast_qty,ms.id,ms.name,pp.default_code,"mrp_production".name,"mrp_production".product_qty,"mrp_production".id,pt.name
        ORDER BY ms_id,month,year"""
        line_model = None
        if line_id:
            split_line_id = line_id.split('_')
            line_model = split_line_id[0]
            model_id = split_line_id[1]
            print("LINE_ID",line_id)
            print("LINE_MODEL",model_id)
            if line_model == 'amdkgroup' or line_model == 'plastikgroup':
                where_clause += line_model == 'mp' and ' AND "mrp_production".id = %s AND ms.id = %s' or  ' AND ms.id = %s'
                where_params += [str(model_id)]
            if line_model == 'mp':
                where_params +=[str(split_line_id[2])]

        # 2.Fetch data from DB
        select = select % (tables, where_clause)
        self.env.cr.execute(select, where_params)
        results = self.env.cr.dictfetchall()

        domains =[('company_id','in',self.env.context['allowed_company_ids'])]
        if act_warehouse:
            domains += [('acc_group.warehouse_id','in',act_warehouse)]
        msb = self.env['mis.summary.budget']
        where_queris = msb._where_calc(domains)
        tables2, where_clauses, where_params2 = where_queris.get_sql()
        select2 = """SELECT
        cb."month" as month,cb."year" as year,
        "mis_summary_budget".date_start as d_start,"mis_summary_budget".date_end as d_end,
        "mis_summary_budget".plan_amt as bgt_plant,
        "mis_summary_budget".budget_pos as bpos,aac.id as aac_id,
        abp.bp_group as bp_group,
        mgb.name as bg_name,
        abp.divider as div_id,
        aac.code AS anl_acc_code,
        abp.name AS bpos_name,aac.name AS anl_acc_id,
        (CASE WHEN aac.id is not null THEN
        (SELECT sum(amount) FROM account_analytic_line
        WHERE account_id = aac.id and general_account_id in (
        SELECT COALESCE(a_a.id, 0) FROM account_account a_a
        LEFT JOIN account_budget_rel abr on abr.account_id = a_a.id
        WHERE abr.budget_id = "mis_summary_budget".budget_pos)
        AND company_id = "mis_summary_budget".company_id
        AND date <= "mis_summary_budget".date_end
        AND date >= "mis_summary_budget".date_start
        )End) AS prac_qty,
        (CASE WHEN "mis_summary_budget".id is not null
        THEN (SELECT sum(plan_amt) FROM mis_summary_budget mbb
        WHERE mbb.budget_cros_id = "mis_summary_budget".budget_cros_id
        AND mbb.budget_pos = "mis_summary_budget".budget_pos)
        END) AS msb_amt
        FROM %s
        LEFT JOIN crossovered_budget cb ON cb.id = "mis_summary_budget".budget_cros_id
        LEFT JOIN crossovered_budget_lines cbl ON cbl.crossovered_budget_id = "mis_summary_budget".budget_cros_id
        LEFT JOIN account_analytic_account aac ON aac.group_id = "mis_summary_budget".acc_group
        LEFT JOIN account_budget_post abp ON abp.id = "mis_summary_budget".budget_pos
        LEFT JOIN mis_grouping_bp mgb ON mgb.id = abp.bp_group
        WHERE %s
        GROUP BY "mis_summary_budget".plan_amt,"mis_summary_budget".date_start,
        "mis_summary_budget".date_end,aac.name,abp.name,aac.id,"mis_summary_budget".budget_pos,
        "mis_summary_budget".company_id,
        "mis_summary_budget".id,
        mgb.name,
        abp.bp_group,
        aac.code,
        cb."month",cb."year",
        abp.divider
        ORDER BY abp.bp_group"""
        where_clauses += ' AND "mis_summary_budget".date_start BETWEEN %s AND %s' % ("""'"""+start_date+"""'""","""'"""+end_date+"""'""")
        # where_clause += line_model == 'bpgroup' and ' AND abp.bp_group = %s  ' or ' AND abp.bp_group = %s'
        # where_clauses += line_model == 'budgetgroup' and ' AND abp.bp_group = %s AND "mis_summary_budget".budget_pos = %s' or  ' AND "mis_summary_budget".budget_pos = %s'

        if line_model == 'bpgroup':
            where_clauses += line_model == 'bpgroup' and ' AND abp.bp_group = %s' or  ' AND abp.bp_group = %s'
            where_params2 +=[str(split_line_id[1])]

        if line_model == 'budgetgroup':
            where_clauses += line_model == 'budgetgroup' and ' AND abp.bp_group = %s AND "mis_summary_budget".budget_pos = %s' or  ' AND "mis_summary_budget".budget_pos = %s'
            where_params2 +=[str(split_line_id[1]),str(split_line_id[2])]

        print("LINEE MODEL", line_model)
        select2 = select2 % (tables2, where_clauses)
        self.env.cr.execute(select2, where_params2)
        results_msb = self.env.cr.dictfetchall()

        forecast_qty = self._get_sum_sf(results, lambda x: x['am_gr'] == x['am_gr'])
        if not results and line_model != 'budgetgroup':
            values = None
            lines.append(self._get_tot_forecast_no_res(options,values))

        if not results and not forecast_qty:
            return lines

        current_mp = None
        current_div = None
        plas_exs = False
        current_anl = None
        # 3.Build report lines
        amdk_exs = False
        current_group = line_model == 'mp' and results[0]['mp_name'] or None # If line_id points toward an account line, we don't want to regenerate the parent journal line
        for values in results:
            if values['ms_id'] != current_group and values['ms_id'] in (1,2,3) and line_model != 'budgetgroup' and line_model != 'bpgroup':
                amdk_exs = True
                current_group = values['ms_id']
                lines.append(self._get_group_line_amdk(options, current_group, results, values))

            if self._need_to_unfold('amdkgroup_%s' % (current_group,), options) and values['group'] != current_mp:
                current_mp = values['mp_id']
                if values['year'] == str(yy) and values['month'] == str(mm):
                    lines.append(self._get_mp_line_amdk(options, current_group, current_mp, results, values))

        if not line_id and amdk_exs and line_model != 'budgetgroup':
            lines.append(self._get_tot_amdk(options, current_group, current_mp, results, values))
        if not line_id == 'tot_amdk' and line_model != 'budgetgroup':
            for values in results:
                if values['ms_id'] != current_group and values['ms_id'] not in (1,2,3) and line_model != 'budgetgroup' and line_model != 'bpgroup':
                    plas_exs = True
                    current_group = values['ms_id']
                    lines.append(self._get_group_line_plastik(options, current_group, results, values))
                if self._need_to_unfold('plastikgroup_%s' % (current_group,), options) and values['group'] != current_mp and line_model != 'budgetgroup':
                    current_mp = values['mp_id']
                    if values['year'] == str(yy) and values['month'] == str(mm):
                        lines.append(self._get_mp_line_plastik(options, current_group, current_mp, results, values))
        if not line_id in ['plastikgroup_4','plastikgroup_5','plastikgroup_6'] and plas_exs and line_model != 'budgetgroup' and line_model != 'plastikgroup':
            lines.append(self._get_tot_plastik(options, current_group, current_mp, results, values))
        if not line_model in ['amdkgroup','plastikgroup','budgetgroup'] and not line_id in ['tot_plastik','bgtfold']:
            self.get_header(options)
        if not line_model in ['amdkgroup','plastikgroup'] and not line_id == 'tot_plastik':
            current_group_bp = line_model == 'budgetgroup' and results_msb[0]['bp_group'] if results_msb else line_model == 'budgetgroup'
            current_group_bgt = line_model == 'bgtfold' and results_msb[0]['bpos'] if results_msb else line_model == 'bgtfold'
            current_div = None
            current_bp = None
            current_group_bgt = None
            t_bp = None
            t_bps = None
            i = 0
            cek = None
            ceks = None
            new_list = None
            for values in results_msb:
                if values['bp_group'] != current_group_bp:
                    current_group_bp = values['bp_group']
                    lines.append(self._get_group_line_bp(options, current_group_bp, results,results_msb, values))

                if self._need_to_unfold('bpgroup_%s' % (current_group_bp,), options) and values['bpos'] != current_group_bgt:
                    current_div = values['div_id']
                    current_group_bgt = values['bpos']
                    if values['year'] >= str(yy) and values['month'] >= str(mm) and values['year'] <= str(yye) and values['month'] <= str(mme):
                        lines.append(self._get_group_line_bgt(options,current_group_bgt,current_div,current_group_bp,results_msb, values,results))
                    # if values['year'] == str(yy) and values['month'] == str(mm):
                    #     lines.append(self._get_group_line_bgt(options,current_group_bgt,current_div,current_group_bp,results_msb, values,results))

                cek = len([x['bpos'] for x in results_msb])
                ceks = len([x['bp_group'] for x in results_msb])
                if line_id and i == cek-1 and ceks>=1 and line_model not in['bp_group','bgtfold','budgetgroup']:
                    lines.append(self._get_total_line_bp(options,cek,current_group_bp,current_group_bgt,current_div, results_msb, values,results))

                # if self._need_to_unfold('budgetgroup_%s_%s' % (current_group_bp,current_group_bgt,), options) and values['aac_id'] != current_bp:
                #     current_bp = values['bp_group']
                #     current_group_bgt = values['bpos']
                #     current_anl = values['aac_id']
                #     if values['year'] >= str(yy) and values['month'] >= str(mm) and values['year'] <= str(yye) and values['month'] <= str(mme):
                #         lines.append(self._get_bgt_line(options,current_group_bp,current_group_bgt,current_div, current_anl, results_msb, values))
                i += 1
        return lines