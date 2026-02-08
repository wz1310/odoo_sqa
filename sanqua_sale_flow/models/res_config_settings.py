# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)


class SanquaSetting(models.TransientModel):
	_inherit = 'res.config.settings'
	

	using_interco_master_on_sale = fields.Boolean('Default Order as Intercompany Procurement', related="company_id.using_interco_master_on_sale", readonly=False)

	