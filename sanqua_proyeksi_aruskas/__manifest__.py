# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Proyeksi Arus Kas Report",
    "summary": "Proyeksi Arus Kas Report.",
    "version": "13.0.1.0.0",
    "category": "Warehouse",
    "website": "",
    "author": "Portcities",
    "license": "AGPL-3",
    "depends": ["date_range", "report_xlsx_helper"],
    "data": [
        "data/paper_format.xml",
        "data/report_data.xml",
        "reports/aruskas_report.xml",
        "wizard/aruskas_report_wizard_view.xml",
    ],
    "installable": True,
}
