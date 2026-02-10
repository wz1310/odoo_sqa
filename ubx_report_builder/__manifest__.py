{
    'name': 'Report Builder',
    'version': '18.0.1.0.3',
    # 'price': 25.00,
    # 'currency': 'USD',
    'category': 'Reporting',
    'summary': 'Dynamic Report Builder by Urbex',
    'description': """
Report Builder Module
=====================

This module provides a comprehensive report building interface that allows users to:

* Select models and related fields dynamically
* Build custom reports with drag & drop interface
* Export reports to Excel format
* Manage and view created reports
* Real-time field selection based on model relationships

Features:
---------
* Modern OWL-based user interface
* Drag and drop column builder
* Model and field selection wizard
* Excel export functionality
* Security groups and access controls
* Report management dashboard

Technical Features:
------------------
* Built with Odoo 18 best practices
* OWL JavaScript framework integration
* Responsive design
* Multi-company support
* Advanced filtering capabilities
    """,
    'author': 'Urbex Systems',
    'website': 'https://urbexlabs.com',
    'email': 'athumanishabani18@gmail.com',
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],
    'depends': [
        'base',
        'web',
        'base_setup',
    ],
    'external_dependencies': {
        'python': ['reportlab'],
    },
    'data': [
        'security/report_builder_security.xml',
        'security/ir.model.access.csv',
        'data/report_builder_data.xml',
        'views/report_builder_views.xml',
        'views/report_builder_field_views.xml',
        'views/report_builder_menus.xml',
        'views/report_builder_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ubx_report_builder/static/src/css/report_builder.css',
            'ubx_report_builder/static/src/js/report_builder_widget.js',
            'ubx_report_builder/static/src/js/report_display_widget.js',
            'ubx_report_builder/static/src/js/field_selector.js',
            'ubx_report_builder/static/src/js/drag_drop_builder.js',
            'ubx_report_builder/static/src/js/report_preview.js',
            'ubx_report_builder/static/src/xml/report_builder_widget.xml',
            'ubx_report_builder/static/src/xml/report_preview.xml',
            'ubx_report_builder/static/src/xml/report_display_widget.xml',
        ],
    },
    'demo': [
        'demo/report_builder_demo.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'auto_install': False,
    'application': True,
    'sequence': 10,
}
