# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Retiros de efectivo en POS",
    "version" : "14.0.1.3",
    "category" : "Point of Sale",
    "depends" : ['base','sale','account','point_of_sale'],
    "author": "BrowseInfo",
    'summary': 'Permite Realizar retiros a los cajeros',
    "description": """
    
    Retiros de efectivo para super barato
    
    """,
    "website" : "https://www.sinergia-e.com",

    "price": 15,

    "currency": "MXN",

    "data": [
        'security/ir.model.access.csv',
        'views/custom_pos_view.xml',
    ],

    'qweb': [
        'static/src/xml/pos.xml',
    ],
    "auto_install": False,
    "installable": True,
    "live_test_url":"",
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
