# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    session_time_out = fields.Integer(
        string='La sesion caduca en :(Segundos)',
        help="Ingresa el valor en numeros enteros",
        default = 60
    )
