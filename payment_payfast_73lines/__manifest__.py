# Part of chemv (migrated from v16 by 73lines).
{
    'name': 'Payment Provider: PayFast (73lines)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "South African payment gateway: redirect-form integration with PayFast.",
    'description': " ",
    'author': '73Lines (chemv v18 port)',
    'depends': ['payment'],
    'data': [
        'data/payfast.xml',
        'views/payment_form_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'OPL-1',
    'images': ['static/description/icon.png'],
    'installable': True,
}
