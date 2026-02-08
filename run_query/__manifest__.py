# """
#  This module is developed by Portcities Indonesia
#  Copyright (C) 2017 Portcities Indonesia (<http://portcities.net>).
#  All Rights Reserved
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# """

{
    "name": "Interface Run Query",
    "summary": "interface make to run query",
    "version": "11.0.1.0.0",
    "author": "Portcities Ltd",
    "website" : "https://www.portcities.net",
    "license": "AGPL-3",
    "complexity": "normal",
    "description": """

v1.1
----
* Interface Run Query

*Author : Nur Imam Agung R.

                      """,
    "category": "Reporting",
    "depends": [ 'base'],
    "data": [
        'views/view_run_query.xml',
        'security/ir.model.access.csv',
    ],
    "test": [
    ],
    "auto_install": False,
    'installable': True,
    "application": False,
}
