# -*- coding: utf-8 -*-

{
    'name': 'POS create sales order',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'WebVeer',
    'summary': "This module allows you to create sale order from point of sale." ,
    'description': """

=======================
This module allows you to create sale order from point of sale.

""",
    'depends': ['sale','point_of_sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        # 'views/sequence.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/create_so.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 30,
    'currency': 'EUR',
}
