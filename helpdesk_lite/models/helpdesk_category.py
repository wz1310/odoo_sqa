# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models



class Category(models.Model):
    """ Model for case stages. This models the main stages of a document
        management flow. Tickets will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "helpdesk_lite.category"
    _description = "Category of case"
    _rec_name = 'name'
    _order = "sequence, name, id"

    description = fields.Char('Description of Category', translate=True)
    name = fields.Char('Name Of Category', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")