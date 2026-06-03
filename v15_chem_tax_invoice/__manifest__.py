# -*- coding: utf-8 -*-
{
    'name': "v15_chem_tax_invoice",

    'summary': "Show Tax Invoice title on customer invoice PDFs",

    'description': """
        Customizes the customer invoice report title and keeps inventory
        adjustments accessible with list and form views.
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Accounting/Accounting',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',

    'depends': ['account', 'stock'],

    'data': [
        'views/chem_tax_invoice.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
