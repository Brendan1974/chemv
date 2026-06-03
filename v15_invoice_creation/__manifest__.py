# -*- coding: utf-8 -*-
{
    'name': "Sale Invoice Confirmation",

    'summary': "Allow a dedicated group to confirm customer invoices.",

    'description': """
        Grants invoice confirmation access to users in the Sale Invoice Confirmation group.
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_edi'],

    # always loaded test
    'data': [
        'security/group_access.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

