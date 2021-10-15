# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, fields


class pos_order(models.Model):
    _inherit = "pos.order"

    def get_order_tax_value_in_receipt(self):
        fiscal_position_id = self.fiscal_position_id
        taxes_dict = {}
        for line in self.lines:
            taxes = line.tax_ids.filtered(lambda t: t.company_id.id == self.company_id.id)
            if fiscal_position_id:
                taxes = fiscal_position_id.map_tax(taxes, line.product_id, self.partner_id)
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = taxes.compute_all(price, self.pricelist_id.currency_id, line.qty, product=line.product_id, partner=self.partner_id or False)['taxes']
            for each_line_tax in taxes:
                taxes_dict.setdefault(each_line_tax['name'], 0.0)
                taxes_dict[each_line_tax['name']] += each_line_tax['amount']
        return taxes_dict

    def get_total_discount_in_receipt(self):
        total_discount = 0.0
        for line in self.lines:
            if line.discount:
                total_discount += (line.qty * line.price_unit - line.price_subtotal)
        return total_discount

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: