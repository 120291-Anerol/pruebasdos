# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################
{
    'name': 'POS Receipt from Backend',
    'category': 'Point of Sale',
    'version': '14.0.1.0',
    'author': "Equick ERP",
    'summary': """This Module allows you to generate POS receipt(PDF report) from backend. pos receipt | pos receipt from backend | PDF pos receipt | pos pdf receipt | pos report pdf report pos receipt backend pos receipt""",
    'description': """
        This Module allows you to generate POS receipt(PDF report) from backend.
        * Allows user to print PDF POS receipt.
    """,
    'depends': ['base', 'point_of_sale'],
    'price': 15,
    'currency': 'EUR',
    'license': 'OPL-1',
    'website': "",
    'data': [
        'views/report.xml',
        'views/pos_order_receipt_pdf_template.xml',
    ],
    'demo': [],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: