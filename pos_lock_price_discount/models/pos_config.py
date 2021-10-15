# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _name = 'res.users'
    _inherit ='res.users'

    pos_security_pin = fields.Char('Contraseña Punto Venta')
    

class PosConfig(models.Model):
    _inherit = 'pos.config'

    ### Bloqueos ####
    
    lock_price = fields.Boolean(string="Bloquear Precio", default=False)

    price_password = fields.Char(string=u"Contraseña")

    lock_discount = fields.Boolean(string="Bloquear Descuentos", default=False)

    discount_password = fields.Char(string=u"Contraseña")

    enable_supervisor = fields.Boolean(string="Habilitar Supervisor Tienda", default=False)

    supervisor_id = fields.Many2one('res.users', string="Supervisor")

    supervisor_pin = fields.Char('Contraseña Supervisor')

    lock_quantity = fields.Boolean(string="Bloquear Cantidad", default=False)

    quantity_password = fields.Char(string=u"Contraseña")

    lock_delete = fields.Boolean(string="Bloquear Eliminar", default=False)

    delete_password = fields.Char(string=u"Contraseña")

    @api.onchange('supervisor_id')
    def onchange_supervisor_id(self):
        if self.supervisor_id:
            self.supervisor_pin = self.supervisor_id.pos_security_pin
            if not self.lock_price:
                self.lock_price = True
                self.price_password = self.supervisor_id.pos_security_pin
            if not self.lock_discount:
                self.lock_discount = True
                self.discount_password = self.supervisor_id.pos_security_pin
            if self.lock_discount and not self.discount_password:
                self.discount_password = self.supervisor_id.pos_security_pin
            if self.lock_price and not self.price_password:
                self.price_password = self.supervisor_id.pos_security_pin

            if not self.lock_quantity:
                self.lock_quantity = True
                self.quantity_password = self.supervisor_id.pos_security_pin
            if not self.lock_delete:
                self.lock_delete = True
                self.delete_password = self.supervisor_id.pos_security_pin
            if self.lock_delete and not self.delete_password:
                self.delete_password = self.supervisor_id.pos_security_pin
            if self.lock_quantity and not self.quantity_password:
                self.quantity_password = self.supervisor_id.pos_security_pin
                

    

    # @api.constrains('price_password')
    # def check_price_password(self):
    #     if self.lock_price is True:
    #         for item in str(self.price_password):
    #             try:
    #                 int(item)
    #             except Exception as e:
    #                 raise ValidationError(_("The unlock price password should be a number"))

    # @api.constrains('discount_password')
    # def check_discount_password(self):
    #     if self.lock_discount is True:
    #         for item in str(self.discount_password):
    #             try:
    #                 int(item)
    #             except Exception as e:
    #                 raise ValidationError(_("The unlock discount password should be a number"))
