# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


{
    "name" : "POS Stock in Odoo",
    "version" : "14.0.0.6",
    "category" : "Point of Sale",
    "depends" : ['base','sale_management','stock','point_of_sale'],
    "author": "Sinergia",
    'summary': 'Control de stock',
    'price': 29,
    'currency': "EUR",
    "description": """
    Restringe venta en negativo
    """,
    "website" : "https://www.browseinfo.in",
    "data": [
        'views/assets.xml',
        'views/custom_pos_config_view.xml',
    ],
    'qweb': [
        'static/src/xml/bi_pos_stock.xml',
    ],
    "auto_install": False,
    "installable": True,
    "live_test_url":'https://youtu.be/X1GSrJl9iWY',
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
