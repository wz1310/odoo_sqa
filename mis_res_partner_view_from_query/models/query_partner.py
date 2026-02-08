from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)

class QueryResPartner(models.Model):
    _name = 'query.view.res.partner'
    _description = "Query Partner"
    _auto = False

    id_rp = fields.Integer(string='Id')
    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    parent = fields.Integer(string='Parent Id')

    def get_main_request(self):
        request = """
        CREATE or REPLACE VIEW %s AS
        SELECT ROW_NUMBER() OVER (ORDER BY rp.id) AS "id",rps.id AS "id_rp",
        rp.parent_id AS "parent",rp.code AS "code",rp.name AS "name" FROM res_partner rp
        LEFT JOIN res_partner rps on rps.id = rp.id
        WHERE rp.state ='approved'
        ORDER BY rp.name ASC
        """ % (self._table)
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())

    def cek_id(self):
        for rec in self:
            print("ID NYAAA", self.env.context)