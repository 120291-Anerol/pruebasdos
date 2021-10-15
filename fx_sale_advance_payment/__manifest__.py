# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2021 German Ponce Dominguez
#
##############################################################################

{
    'name' : 'Pagos Avanzados en Ventas',
    'category': 'Sales',
    'version': '1.0',
    'author': 'Fixdoo, German Ponce Dominguez',
    'website': 'https://fixdoo.mx',
    'description': """
        This Module allows to create Customers Advance payment from Sales order.
        * Allow user to manage the Customers Advance payment for the Sales order.
        * Manage with Multi Company & Multi Currency.
    """,
    'summary': 'Este modulo permite realizar Pagos desde las Ventas.',
    'depends' : ['base', 'sale_management', 'stock', 'sale_stock', 'point_of_sale'],
    'price': 1000,
    'currency': 'USD',
    'license': 'OPL-1',
    'data': [
        'views/sale_view.xml',
        'views/global_invoice.xml',
        'report/report.xml',
        "security/ir.model.access.csv",
    ],
    'demo': [],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: