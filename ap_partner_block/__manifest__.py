# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Ap Partner Block",
    "version" : "18.0.1.0.0",
    "summary": "Ap Partner Block",
    "sequence": 1,
    "description": """ Ap Partner Block """,
    "category": "Product",
    "website": "http://ap-accounting.co.za",
    "depends" : ["base",
                 "stock",
                 "purchase",
                 "sale"
                 ],
    "data": [
            "views/res_partner.xml",
            ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

