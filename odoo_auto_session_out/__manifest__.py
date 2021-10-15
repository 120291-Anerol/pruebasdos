# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C)Sinergia
###################################################################################

{
    'name': 'Cierra sesiones en automatico',
    'version': '1.0',
    'category': 'All',
    'sequence': 1,
    "license": "OPL-1",
    'author': 'Sinergia',
    'summary': 'Cierra sesiones sin actividad',
    'depends': ['web'],
    'data': [
        'views/view.xml',
        'views/assets.xml',
    ],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
    'price': 15,
    'currency': 'MXN',
    'bootstrap': True,
}
