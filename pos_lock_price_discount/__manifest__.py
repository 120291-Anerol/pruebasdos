# -*- coding: utf-8 -*-

{
    'name': "POS LOCK PRICE DISCOUNT",
    'summary': """
        Lock change price or discount in Point Of Sale""",
    'description': """
        This module add features to lock change price or discount in Point Of Sale using password
    """,
    'author': "German Ponce Dominguez",
    'website': "",
    'category': 'Point Of Sale',
    'license': "LGPL-3",
    'version': '14.0.0',
    'images': ['static/description/banner.jpg'],
    'depends': [
                    'base', 
                    'point_of_sale', 
                    # 'pos_discount'
                ],
    'data': [
        'views/assets.xml',
        'views/pos_config_view.xml',
    ],
    "qweb": [
        # "static/src/xml/*.xml",
        ],
    'price': '500',
    'currency': 'EUR',
}
