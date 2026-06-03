# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Ap Inventory Lot Serial",
    "version" : "18.0.1.0.0",
    "summary": "Ap Inventory Lot Serial",
    "sequence": 1,
    "description": """ Ap Inventory Lot Serial """,
    "category": "Product",
    "website": "http://ap-accounting.co.za",
    "depends" : ["base",
                 "stock",
                 "purchase",
                 ],
    "data": [
            # "views/stock_picking_view.xml",
            ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

