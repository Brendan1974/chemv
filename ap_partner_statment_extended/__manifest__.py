# -*- coding: utf-8 -*-
{
    'name': "ap_partner_statment_extended",
    'summary': "Extended Partner Statement with scheduled email delivery",
    'description': """
Extension of partner_statement adding:
- Activity Statement Record model to queue statements
- Cron to send queued statements by email
- Email templates for activity and outstanding statements
- 'Send by Email' button on wizards
    """,
    'author': "Ap Systems",
    'website': "https://ap-systems.co.za",
    'category': 'Accounting',
    'version': '18.0.1.0.0',
    'license': 'AGPL-3',
    'depends': ['partner_statement'],
    'data': [
        'data/mail_template.xml',
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
}
