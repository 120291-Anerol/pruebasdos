# -*- coding: utf-8 -*-
# Sinergia


{
    "name" : "POS Control de stock Super Barato",
    "version" : "14.0.0.6",
    "category" : "Point of Sale",
    "depends" : ['base','sale_management','stock','point_of_sale'],
    "author": "Sinergia",
    'summary': 'Control de stock POS',
    'price': 600,
    'currency': "MXN",
    "description": """
    Se bloquea la venta en negativo
    """,
    "website" : "https://www.sinergia-e.com",
    "data": [
        'views/assets.xml',
        'views/custom_pos_config_view.xml',
    ],
    'qweb': [
        'static/src/xml/bi_pos_stock.xml',
    ],
    "auto_install": False,
    "installable": True,
}
