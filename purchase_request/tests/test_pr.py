import logging
import datetime

from odoo.tests import common,tagged


_logger = logging.getLogger(__name__)


@tagged('post_install', 'at_install')
class TestPR(common.TransactionCase):
    def setUp(self):
        return super().setUp()

    
    def test_pr(self):
        