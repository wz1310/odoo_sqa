from . import models
from odoo import api, SUPERUSER_ID

def _auto_config_intercompany(cr, registry):
	env = api.Environment(cr, SUPERUSER_ID, {})

	companies = env['res.company'].search([('id', '!=', False)])
	# set all companies.partner_id.company_id = False
	companies.mapped('partner_id').write({'company_id':False})

	# config = env['res.config.settings'].browse(1)
	# config.module_inter_company_rules = True
	# config.rule_type = 'so_and_po'
	for comp in companies:
		env['res.config.settings'].create({
			'rule_type':'so_and_po',
			'company_id':comp.id,
			'auto_validation':True,
		})

	