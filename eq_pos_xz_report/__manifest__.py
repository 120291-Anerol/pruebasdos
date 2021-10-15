# -*- coding: utf-8 -*-
##############################################################################
#
# Sinergia 
#
##############################################################################

{
    'name': "Reporte de Sesiones",
    'category': 'Sales/Point Of Sale',
    'version': '14.0.1.0',
    'author': 'Synergy Systems',
    'description': """
        Generamos reportes de sesion para grupo San Luis.
    """,
    'summary': """X report | Z report | pos XZ report | pos sales summary report | pos sale summary report | point of sale report | point of sales report | point of sale summary""",
    'depends': ['point_of_sale'],
    'price': 12,
    'currency': 'MXN',
    'license': 'OPL-1',
    'website': "",
    'data': ['security/ir.model.access.csv',
             'report/report_view.xml',
             'report/x_report_template.xml',
             'report/z_report_template.xml',
             'views/xz_report_view.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: