from . import models
from . import wizard
from odoo import api, SUPERUSER_ID

def _set_odoobot_intercompany(cr, registry, companies):
	env = api.Environment(cr, SUPERUSER_ID, {})
	odooBot = env['res.users'].browse(SUPERUSER_ID)
	warehouses = env['stock.warehouse'].search([('id','!=',False)])
	journals = env['account.journal'].search([('id','!=',False)])
	odooBot.write({
		'company_ids':[(6,0,companies.ids)],
		'warehouse_ids':[(6,0,warehouses.ids)],
		'journal_ids':[(6,0,journals.ids)],
		'tz':'Asia/Jakarta',
		})

	

def _set_picking_type_default(cr, registry):
	env = api.Environment(cr, SUPERUSER_ID, {})
	whs = env['stock.picking.type'].search([('active','=',True)])
	
	whs.write({
		'use_existing_lots':True,
		'use_create_lots':False,
		'show_operations':False,
		})


def _auto_config_intercompany(cr, registry):
	env = api.Environment(cr, SUPERUSER_ID, {})

	companies = env['res.company'].search([('id', '!=', False)])
	for comp in companies:
		env['res.config.settings'].create({
			'using_interco_master_on_sale':True,
			'company_id':comp.id,
		})
	picking_type_rule = env.ref('stock.stock_picking_type_rule')
	if len(picking_type_rule):
		picking_type_rule.write(dict(domain_force="['|', ('company_id','in', company_ids), ('other_wh_can_read','=',True)]"))
    
	_set_odoobot_intercompany(cr, registry, companies)
	_set_picking_type_default(cr, registry)