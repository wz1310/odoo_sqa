# -*- coding: utf-8 -*-

##############################################################################
#
#    Author: Al Kidhma
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Confirm Button From Tree View Of Sale And Purchase',
    'version': '13.0.1.0.0',
    'category': 'Sales Management',
    'summary': 'This module will confirm sale order and Purchase order from tree view action.',
    'live_test_url': '',
    'author': 'Al Khidma Systems',
    'license': 'OPL-1',
    'price': '0.00',
    'currency': 'USD',
    'maintainer': 'Al Khidma Systems',
    'support': 'tech@alkhidmasystems.com',
    'website': '',
    'description': 'confirm sale order and Purchase order from tree view action',
    'depends': [
        'sale_management', 'purchase'
    ],
    'data': [
        'wizard/purchase_view.xml',
        'wizard/sale_view.xml',
    ],

    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [

    ],
    'live_test_url': 'http://65.21.254.98:8069/contactus',
}
