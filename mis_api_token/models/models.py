import hashlib
import logging
import os
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

expires_in = "mis_api_token.expires_token_in"


def nonce(length=40, prefix=""):
    rbytes = os.urandom(length)
    return "{}{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))


class MisToken(models.Model):
    _name = "mis.access.token"
    _description = "API Access Token"

    token = fields.Char("Access Token", required=True)
    user_id = fields.Many2one("res.users", string="User", required=True)
    expires = fields.Datetime(string="Expires", required=True)
    scope = fields.Char(string="Scope")

    # @api.multi
    def find_one_or_create_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = self.env["mis.access.token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None
        if not access_token and create:
            expires = datetime.now() + timedelta(days=1)
            vals = {
                "user_id": user_id,
                "scope": "userinfo",
                "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": nonce(),
            }
            access_token = self.env["mis.access.token"].sudo().create(vals)
        if not access_token:
            return None
        return access_token.token

    # @api.multi
    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None
        """
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)

    # @api.multi
    def has_expired(self):
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.expires)

    # @api.multi
    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)


class Users(models.Model):
    _inherit = "res.users"
    token_ids = fields.One2many("mis.access.token", "user_id", string="Access Tokens")


class IrModel(models.Model):
    _inherit = "ir.model"
    rest_api = fields.Boolean("REST API", default=True, help="Allow this model to be fetched through REST API")