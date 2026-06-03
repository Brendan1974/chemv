# -*- coding: utf-8 -*-
{
    'name': "otr_job",

    'summary': """
    AP Accounting made studio change to code and added new functionality
        """,

    'description': """
        V1.studio to backend code to avoide studio export import issue
        v2.added button to create job card from tyre details
        v3. add sequnence in new job card menu
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account','portal','mail'],

    # always loaded
    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/tyre.xml',
        'views/job_card.xml',
        'views/risk_assessments.xml',
        'views/configuration.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
