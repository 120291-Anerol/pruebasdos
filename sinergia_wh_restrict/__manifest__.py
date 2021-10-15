# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright © 2021 sinergia.
#
##############################################################################
{
    'name': "Restriccion de almacen",

    'summary': """
    Restriccion en uso de almacenes.""",

    'description': """
        Se limita las ubicaciones y alamcenes por usuario.
    """,

    'author': "Sinergia",
    'website': "http://www.sinergia-e.com",
    'license':'OPL-1',	
    'category': 'Warehouse',
    'version': '14.0',
    'images': [''],
    'depends': ['base', 'stock','sale_stock','sale'],

    'data': [

        'users_view.xml',
        'security/security.xml',
    ],
    
    
}
