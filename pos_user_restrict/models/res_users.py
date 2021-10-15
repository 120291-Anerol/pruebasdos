# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_config_ids = fields.Many2many(
        comodel_name='pos.config',
        string='Cajas Super Barato Permitidas ',
        help="Indica que cajas y operaciones relacionadas puede ver el usuario.",
    )

    def write(self, values):
        res = super(ResUsers, self).write(values)
        if 'pos_config_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            self.has_group.clear_cache(self)
        return res
