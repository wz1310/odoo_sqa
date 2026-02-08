# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models



class Subject(models.Model):
    """ Model for case stages. This models the main stages of a document
        management flow. Tickets will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "helpdesk_lite.subject"
    _description = "Subject of helpdesk"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Subject', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")