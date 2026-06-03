# -*- encoding: utf-8 -*-
{
    'name': 'AP Email Imports',
    'category': 'Email',
    'version': '18.0.1.0.0',
    'depends': ['base','mass_mailing','mass_mailing_extended'],
    'description': """AP Email Import""",
    'data': [
              'security/ir.model.access.csv',
              'wizard/email_import_view.xml',
            ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}



