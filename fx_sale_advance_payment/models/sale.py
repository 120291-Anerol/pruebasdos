# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2021 German Ponce Dominguez
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError

from odoo.tools import float_is_zero, float_compare
from itertools import groupby


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        if self.sale_id:
            if self.sale_id.total_payment == False:
                if self.sale_id.payment_exception == False:
                    raise UserError(_("Solo puede entregarse la Mercancia si el Pedido esta Pagado."))
        res = super(StockPicking, self).button_validate()
        return res


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        if 'invoice_line_ids' in res:
            invoice_lines = res['invoice_line_ids']
            invoice_lines_updated = []
            for invline in invoice_lines:
                line_vals = invline[2]
                line_vals.update({'order_to_global_id': order.id})
                invoice_lines_updated.append((0,0,line_vals))
        return res


class ResCompany(models.Model):
    _name = 'res.company'
    _inherit ='res.company'

    account_sale_payments = fields.Many2one('account.account', 'Cuenta Puente Registro de Pagos')

class AccountInvoiceLine(models.Model):
    _name = 'account.move.line'
    _inherit ='account.move.line'

    order_to_global_id = fields.Many2one('sale.order','Pedido Origen', copy=False)
    re_invoiced = fields.Boolean('Refacturación', copy=False)



class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit ='sale.order.line'


    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'untaxed_amount_to_invoice')
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.move_type == 'out_invoice':
                        if not invoice_line.re_invoiced:
                            qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                    elif invoice_line.move_id.move_type == 'out_refund':
                        if not line.is_downpayment or line.untaxed_amount_to_invoice == 0 :
                            if not invoice_line.re_invoiced:
                                qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
            line.qty_invoiced = qty_invoiced


    # @api.model
    # def create(self, vals):
    #     if 'company_id' in vals:
    #         self = self.with_company(vals['company_id'])
    #     if 'name' not in vals or 'product_id' not in vals:
    #         return True
    #     if vals.get('name',False) == False and vals.get('product_id',False) == False:
    #         return True
    #     result = super(SaleOrderLine, self).create(vals)
    #     return result

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.depends('state', 'amount_payment', 'total_payment')
    def _get_payments(self):

        for order in self:
            payment_count = 0
            if order.payments_apply_ids:
                for pay in order.payments_apply_ids:
                    payment_count += 1
            order.update({
                'payment_count': payment_count,
            })

    @api.depends('state', 'amount_payment', 'total_payment')
    def _get_pending_amount(self):

        for order in self:
            order_total = order.amount_total
            amount_pending = order_total - order.amount_payment
            if amount_pending < 0.0:
                amount_pending = 0.0
            order.update({
                'amount_pending':  amount_pending,
                'amount_total_order':  order_total,
            })


    amount_payment = fields.Float('Importe Pagado', copy=False)
    total_payment = fields.Boolean('Pagado', copy=False)
    
    payment_exception = fields.Boolean('Excepcion Pago', copy=False)

    amount_pending = fields.Float('Importe Pendiente   ', compute='_get_pending_amount', store=True, digits=(14,4))

    amount_total_order = fields.Float('Importe Total   ', compute='_get_pending_amount', store=True, digits=(14,4))
    

    payment_count = fields.Integer(string='# of Pagos', compute='_get_payments', readonly=True)

    # product_on_id = fields.Many2one('product.product','Producto', required=False,)
    # product_qty =  fields.Integer('Cantidad', default=1)

    product_on_read = fields.Char('Lectura Codigo Barras', required=False, help="""Ingresa el Codigo del Producto Automaticamente se Agregara como linea tomando El precio del producto y su unidad de Medida
        Podemos Agregar los Siguientes Comodines:
            - Si queremos agregar el Producto y la Cantidad a la Vez ponemos el Codigo del Producto + Cantidad, es importante poner el simbolo + despues del Producto'""" )

    easy_refund = fields.Float('Cambio', copy=False)

    re_invoiced = fields.Boolean('Refacturado', copy=False)

    user_payment_register_id = fields.Many2one('res.users','Cajero')

    invoice_global_ids = fields.Many2many('account.move',
        'account_invoice_sale_rel', 'sale_id', 'invoice_id',
        string='Facturas', copy=False)

    ### Modulo Original ##
    payments_apply_ids = fields.One2many('account.payment', 'sale_order_id', 'Pagos aplicados')
    adv_payment_ids = fields.Many2many('account.payment', string="Pagos Relacionados", copy=False)

    def _create_invoices(self, grouped=False, final=False, date=None):
        res = super(sale_order, self)._create_invoices(grouped=grouped, final=final, date=date)
        if res:
            for inv in res:
                for line in inv.invoice_line_ids:
                    line.order_to_global_id = self.id
        return res

    def action_view_adv_payments(self):
        action = self.env.ref('account.action_account_payments').read()[0]
        action['domain'] = [('id', 'in', self.adv_payment_ids.ids)] if self.adv_payment_ids.ids else []
        action['context'] = {'create': 0}
        return action

    def btn_advance_payment(self):
        cus_ctx = {}
        if self.total_payment:
            raise UserError(_("El Pedido ya se encuentra en estado Pagado"))
        if self.state not in ('sale','done'):
            raise UserError(_("Solo se pueden realizar pagos en los estados:\n* Pedido Venta\n* Hecho"))
        amount_residual = self.amount_total-self.amount_payment
        cus_ctx.update({'default_amount': amount_residual})


        cus_ctx.update({'default_payment_type': 'inbound',
                   'default_partner_type': 'customer',
                   'search_default_inbound_filter': 1,
                   'res_partner_search_mode': 'customer',
                   'default_partner_id': self.partner_id.id,
                   'default_communication': self.name,
                   'default_sale_order_id': self.id,
                   'default_ref': self.name,
                   'active_ids':[],
                   'active_model':self._name,
                   'active_id':self.id,
                   'default_currency_id': self.currency_id.id})
        ctx = self._context.copy()
        ctx.update(cus_ctx)
        return {
            'name': _('Pago Avanzado'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'view_id': self.env.ref('fx_sale_advance_payment.view_sale_advance_account_payment_form').id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx
        }


    def action_cancel(self):
        for rec in self:
            payment_ids = self.env['account.payment'].sudo().search([('sale_order_id','=',rec.id)])
            if payment_ids:
                for payment in payment_ids:
                    if payment.state not in ( 'draft','cancel' ):
                        raise UserError(_("No puedes cancelar el Pedido, primero debes cancelar los Pagos Relacionados."))
        res = super(sale_order, self).action_cancel()
        for rec in self:
            rec.write({'total_payment':False,'amount_payment': 0.0})
        return res

    @api.onchange('partner_id', 'product_on_read', 'order_line','pricelist_id')
    def on_change_load_products(self):
        product_obj = self.env['product.product']
        salesman_obj = self.env['res.users']
        partner_obj = self.env['res.partner']
        partner = partner_obj.browse(self.partner_id)
        lines = [x.id for x in self.order_line]
        if not self.product_on_read:
            return {}

        qty_product = 1

        if self.product_on_read:
            if '+' in self.product_on_read:
                try:
                    product_on_read = self.product_on_read.split("+")
                    qty_product_str = product_on_read[1]
                    qty_product = float(qty_product_str)

                except:
                    raise UserError(_("Error!\nLa Informacion Introducida Contiene Errores. Verifique que el orden de la informacion sea como los siguientes ejemplos:\
                              \n -[Cantidad+CodigoProducto]"))

        product_on_read = self.product_on_read.split("+")
        default_code = product_on_read[0]
        if len(default_code) > 12:
            default_code = default_code[0:12]
        # product_search = product_obj.search([('default_code','=',default_code)])
        self.env.cr.execute("""
            select id from product_product where UPPER(default_code) = %s;
            """, (default_code.upper(),))
        cr_res = self.env.cr.fetchall()
        product_search = [x[0] for x in cr_res]
        if not product_search:
            self.env.cr.execute("""
                select id from product_product where UPPER(barcode) like %s;
                """, ('%'+default_code.upper()+'%',))
            cr_res = self.env.cr.fetchall()
            product_search = [x[0] for x in cr_res]
            if not product_search:
                raise UserError(_("Error!\nEl codigo [%s] no coincide con ninguna referencia de Producto." % default_code))

        product_id = product_search[0]
        product_br = product_obj.browse(product_search[0])
        if product_br.default_code:
            product_name = '['+product_br.default_code +']'+product_br.name
        else:
            product_name = product_br.name
        if product_br.property_account_income_id:
            account_id = product_br.property_account_income_id.id
        else:
            account_id = product_br.categ_id.property_account_income_categ_id.id
        # price = product_br.lst_price
        sale_order_line = self.env['sale.order.line']

        product_br_with_ctx = product_br.with_context(pricelist=self.pricelist_id.id)
        if self.pricelist_id and self.partner_id:
            # price = self.env['account.tax']._fix_tax_included_price(sale_order_line._get_display_price(product_br), product_br.taxes_id, [_w for _w in product_br.taxes_id] )
            price = product_br_with_ctx.price
        else:
            price = product_br.lst_price
        taxes_list = [_w.id for _w in product_br.taxes_id]

        if product_id:
            xline = (0,0,{
                    'product_id': product_id,
                    'name': product_name,
                    'tax_id': [(6, 0, taxes_list )],
                    'product_uom_qty': int(qty_product),
                    'price_unit': price,
                    'product_uom': product_br.uom_id.id,
                    # 'account_id': account_id,
                })
            lines.append(xline)
            self.simple_add_product(product_id, int(qty_product))
        # print ("######### lines >>>>>>>>>>>>>> ", lines)
        # self.update({'order_line': lines})
            
        self.product_on_read = False
        #self.recalculate_prices()

    def simple_add_product(self, product_id, qty=1.0):
        corresponding_line = self.order_line.filtered(
            lambda x: x.product_id.id == product_id)
        if corresponding_line:
            for cpline in corresponding_line:
                corresponding_line.product_uom_qty += qty
                break
        else:
            line = self.order_line.new({
                'product_id': product_id,
                'product_uom_qty': qty,
                'order_id': self.id,
            })
            line.product_id_change()
        return True

    def on_barcode_scanned(self, barcode):
        product = self.env[
            'product.product'].search([('barcode', '=', barcode)], limit=1)
        if product:
            self._add_product(product)
        else:
            product = self.env[
            'product.product'].search([('default_code', '=', barcode)], limi=1)
            if product:
                self._add_product(product)
            else:
                return {'warning': {
                    'title': _('Error'),
                    'message': _(
                        'El codigo de barras o referencia "%(barcode)s" no'
                        ' corresponde con ningun registro en la Base de Datos.') % {'barcode': barcode}
                }}

    def _add_product(self, product, qty=1.0):
        corresponding_line = self.order_line.filtered(
            lambda x: x.product_id == product)
        if corresponding_line:
            corresponding_line.product_uom_qty += qty
        else:
            line = self.order_line.new({
                'product_id': product.id,
                'product_uom_qty': qty,
                'order_id': self.id,
            })
            line.product_id_change()
        return True


    def recalculate_prices(self):
        for record in self:
            if record.order_line:
                for line in record.order_line:
                    res = line.product_id_change()
                    res2 = line._onchange_discount()
                    #print "######### RES >>> ",res
                    #self.update(res)
        return True

    def re_inviced_public(self):
        for rec in self:
            # invoice_obj = self.env['account.move']
            # invoice_line_obj = self.env['account.move.line']
            # rec.re_invoiced = True
            # invoice_vals = rec._prepare_invoice()
            # invoice_id = invoice_obj.create(invoice_vals)
            # for line in rec.order_line:
            #     invoice_line_vals = line._prepare_invoice_line()
            #     invoice_line_id = invoice_line_obj.sudo().with_context(default_move_type='out_invoice').create(invoice_line_vals)
            #     invoice_line_id.write({'invoice_id': invoice_id.id})

            # invoice_id.compute_taxes()
            invoice_ids = rec._create_invoice_single()
            for inv in invoice_ids:
                for line in inv.invoice_line_ids:
                    line.order_to_global_id = self.id
                    line.re_invoiced = True
            return {
                        'name': _('Refacturacion del Pedido %s' % rec.name),
                        'view_mode': 'form',
                        'view_id': self.env.ref('account.view_move_form').id,
                        'res_model': 'account.move',
                        'context': "{}", # self.env.context
                        'type': 'ir.actions.act_window',
                        'res_id': invoice_ids[0].id,
                    }
                    
    def _create_invoice_single(self, grouped=False, final=False, date=None):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
      
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            # Invoice values.
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            invoice_lines_vals = []
            for line in order.order_line:
                if line.display_type == 'line_section':
                    current_section_vals = line._prepare_invoice_line(sequence=invoice_item_sequence + 1)
                    continue

                if current_section_vals:
                    invoice_item_sequence += 1
                    invoice_lines_vals.append(current_section_vals)
                    current_section_vals = None
                invoice_item_sequence += 1
                prepared_line = line._prepare_invoice_line(quantity=line.product_uom_qty)
                invoice_lines_vals.append(prepared_line)

            # If down payments are present in SO, group them under common section
            if down_payments:
                invoice_item_sequence += 1
                down_payments_section = order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
                invoice_lines_vals.append(down_payments_section)
                for down_payment in down_payments:
                    invoice_item_sequence += 1
                    invoice_down_payment_vals = down_payment._prepare_invoice_line(sequence=invoice_item_sequence)
                    invoice_lines_vals.append(invoice_down_payment_vals)

            invoice_vals['invoice_line_ids'] = [(0, 0, invoice_line_id) for invoice_line_id in invoice_lines_vals]

            invoice_vals_list.append(invoice_vals)

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        return moves          



    ### Reemplazamos Imprimir por el Ticket ###
    def print_ticket(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        #return self.env['report'].get_action(self, 'easy_counter_sales_management.template_easy_ticket')
        return self.env.ref('fx_sale_advance_payment.report_eaty_order_ticket').report_action(self)

class account_payment(models.Model):
    _inherit = 'account.payment'

    sale_order_id = fields.Many2one('sale.order','Pedido de Venta', copy=False)
    easy_refund = fields.Float('Cambio')
    is_global_invoice_move = fields.Boolean('Apunte Agrupador')
    global_invoice_id = fields.Many2one('account.invoice','Factura Global')

    create_in_state_sale = fields.Selection([('draft', 'Borrador'),
                                             ('confirm', 'Confirmado')],
                                            default='confirm',
                                            string="Estado del Pago")

    def create_sale_adv_payment(self):
        amount_residual = self.sale_order_id.amount_total-self.sale_order_id.amount_payment
        if self.amount <= 0.0:
            raise ValidationError(_("El monto del pago no puede ser negativo o Cero."))
        if self.create_in_state_sale == 'confirm':
            self.action_post()
        if self.easy_refund:
            self.amount = self.amount - self.easy_refund
        if self.env.context.get('active_id'):
            sale_id = self.env['sale.order'].browse(self.env.context.get('active_id'))
            sale_id.write({'adv_payment_ids': [(4, self.id)]})
            if self.sale_order_id and self.create_in_state_sale == 'confirm':                
                # self.write({
                #     'sale_order_id': sale_id.id,
                #     })
                amount_payment = self.amount+sale_id.amount_payment
                sale_id.write({'amount_payment':amount_payment})
                amount_payment = amount_payment+0.01
                if amount_payment >= sale_id.amount_total:
                    sale_id.write({'total_payment':True, 'user_payment_register_id': self.env.user.id}) 
                if sale_id.amount_payment > sale_id.amount_total+0.01: 
                    raise ValidationError(_("El monto del pago no puede superar al monto adeudado."))

        return True

    @api.onchange('easy_refund','sale_order_id','amount')
    def on_change_easy_refund(self):
        if self.sale_order_id:
            amount_residual = self.sale_order_id.amount_total-self.sale_order_id.amount_payment
            amount_to_pay = self.sale_order_id.amount_payment + self.amount
            if amount_to_pay > self.sale_order_id.amount_total:
                #self.amount = self.sale_order_id.amount_total
                easy_refund = amount_to_pay - self.sale_order_id.amount_total
                self.easy_refund = easy_refund
                self.sale_order_id.write({'easy_refund':easy_refund})
            else:
                if not self.amount:
                    self.amount = self.sale_order_id.amount_total
                else:
                    self.amount = self.amount

    def action_post(self):
        context = self._context
        res = super(account_payment, self).action_post()
        active_model = context.get('active_model', '')
        if active_model == 'sale.order':
            return res
        for rec in self:
            if rec.sale_order_id:
                amount_payment = rec.amount+rec.sale_order_id.amount_payment
                rec.sale_order_id.write({'amount_payment':amount_payment})
                amount_payment = amount_payment+0.01
                if amount_payment >= rec.sale_order_id.amount_total:
                    rec.sale_order_id.write({'total_payment':True, 'user_payment_register_id': self.env.user.id}) 
                if rec.sale_order_id.amount_payment > rec.sale_order_id.amount_total+0.01: 
                    raise ValidationError(_("El monto del pago no puede superar al monto adeudado."))
        return res

    def action_draft(self):
        res = super(account_payment, self).action_draft()
        for rec in self:
            if rec.sale_order_id:
                # if rec.sale_order_id.invoice_status == 'invoiced':
                #     raise UserError("Error!\nEl pedido de venta relacionado se encuentra Facturado.\nRompa Conciliacion o consulte al Administrador.")
                amount_payment = rec.sale_order_id.amount_payment - rec.amount
                vals = {
                         'total_payment': False,
                         'amount_payment': amount_payment,
                        }
                rec.sale_order_id.write(vals)
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.depends('state', 'invoice_line_ids')
    def _get_orders_rel(self):
        for invoice in self:
            if type(invoice.id) == int:
                self.env.cr.execute("""
                    select sale_order_line.order_id from sale_order_line_invoice_rel 
                        join account_move_line on sale_order_line_invoice_rel.invoice_line_id =  account_move_line.id
                        join sale_order_line on sale_order_line.id = sale_order_line_invoice_rel.order_line_id
                        and account_move_line.move_id = %s
                        group by sale_order_line.order_id

                    """, (invoice.id,))
                cr_res = self.env.cr.fetchall()
                order_list = []
                if cr_res:
                    if cr_res and cr_res[0] and cr_res[0][0]:
                        order_list = [x[0] for x in cr_res if x]
                if not order_list:
                    order_list = []
                    self.env.cr.execute("""
                        select sale_id from account_invoice_sale_rel
                            where invoice_id = %s;
                        """, (invoice.id,))
                    cr_res = self.env.cr.fetchall()
                    if cr_res:
                        if cr_res[0] and cr_res[0][0]:
                            order_list = [x[0] for x in cr_res if x]
                # print "#### PEDIDOS RELACIONADOS >>> ",order_list
                if not order_list:
                    order_list = []
                    self.env.cr.execute("""
                        select order_to_global_id
                                from account_move_line where move_id = %s;
                        """, (invoice.id,))
                    cr_res = self.env.cr.fetchall()
                    if cr_res:
                        if cr_res and cr_res[0] and cr_res[0][0]:
                            order_list_2 = [x[0] for x in cr_res]
                            if order_list_2:
                                order_list = order_list+order_list_2
                if not order_list:
                    invoice_line_list = [x.id for x in invoice.invoice_line_ids]
                    if invoice_line_list:
                        self.env.cr.execute("""
                            select order_line_id from sale_order_line_invoice_rel
                                   where invoice_line_id in %s;
                            """, (tuple(invoice_line_list),))
                        cr_res = self.env.cr.fetchall()
                        if cr_res and cr_res[0] and cr_res[0][0]:
                            sale_order_res = [x[0] for x in cr_res]
                            self.env.cr.execute("""
                                select order_id from sale_order_line
                                       where id in %s;
                                """, (tuple(sale_order_res),))
                            cr_res = self.env.cr.fetchall()
                            if cr_res and cr_res[0] and cr_res[0][0]:
                                order_list = [x[0] for x in cr_res]

                invoice.update({
                    'sale_ids': order_list,
                })
            else:
                invoice.update({
                    'sale_ids': False,
                })


    @api.depends('sale_ids')
    def _get_orders(self):
        for rec in self:
            orders_count = 0
            orders_list = []
            if rec.sale_ids:
                for order in rec.sale_ids:
                    if order:
                        if order.id not in orders_list:
                            orders_list.append(order.id)
            rec.orders_count = len(orders_list)

    orders_count = fields.Integer(string='# of Pedidos', compute='_get_orders', readonly=True)

    sale_ids = fields.Many2many("sale.order", string='Pedidos', compute="_get_orders_rel", readonly=True, copy=False)
    is_global_invoice = fields.Boolean('Es una Factura Global', copy=False)


    def action_view_adv_sale_orders(self):
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('id', 'in', self.sale_ids.ids)] if self.sale_ids.ids else []
        action['context'] = {'create': 0}
        return action

    
    def action_post(self):
        res = super(AccountInvoice, self).action_post()
        mail_compose_message_pool = self.env['mail.compose.message']
        attachment_obj = self.env['ir.attachment']
        account_payment_obj = self.env['account.payment'].sudo()
        account_move_obj = self.env['account.move'].sudo()
        account_move_line_obj = self.env['account.move.line'].sudo()
        for rec in self.filtered(lambda w: w.move_type in ('out_invoice','out_refund') and \
                                     w.amount_total):        
            if rec.move_type == 'out_invoice':
                self.env.cr.execute("""
                    select sale_id from account_invoice_sale_rel
                        where invoice_id = %s;
                    """, (rec.id,))
                cr_res = self.env.cr.fetchall()
                order_list = []
                if cr_res:
                    order_list = [x[0] for x in cr_res if x]
                # print "####### order_list >>>> ",order_list
                if not order_list:
                    self.env.cr.execute("""
                    select sale_order_line.order_id from sale_order_line_invoice_rel 
                        join account_move_line on sale_order_line_invoice_rel.invoice_line_id =  account_move_line.id
                        join sale_order_line on sale_order_line.id = sale_order_line_invoice_rel.order_line_id
                        and account_move_line.move_id = %s
                        group by sale_order_line.order_id

                    """, (rec.id,))
                cr_res = self.env.cr.fetchall()
                order_list = []
                if cr_res:
                    order_list = [x[0] for x in cr_res if x]
                if not order_list:
                    return res
                ### Quitando las Excepciones de Pago ###
                self.env.cr.execute("""
                    select id from sale_order 
                        where id in %s and payment_exception=False;
                    """,(tuple(order_list),))
                cr_res = self.env.cr.fetchall()
                order_list = [x[0] for x in cr_res]
                ### FIN ###

                if not order_list:
                    invoice_line_list = [x.id for x in rec.invoice_line_ids]
                    if invoice_line_list:
                        self.env.cr.execute("""
                            select order_line_id from sale_order_line_invoice_rel
                                   where invoice_line_id in %s;
                            """, (tuple(invoice_line_list),))
                        cr_res = self.env.cr.fetchall()
                        if cr_res and cr_res[0] and cr_res[0][0]:
                            sale_order_res = [x[0] for x in cr_res]
                            self.env.cr.execute("""
                                select order_id from sale_order_line
                                       where id in %s;
                                """, (tuple(sale_order_res),))
                            cr_res = self.env.cr.fetchall()
                            if cr_res and cr_res[0] and cr_res[0][0]:
                                order_list = [x[0] for x in cr_res]
                if not order_list:
                    return res
                payment_list = account_payment_obj.search([('state','in',('posted','reconciled')),('sale_order_id','in',tuple(order_list))])
                # self.env.cr.execute("""
                #     select id from account_payment
                #         where sale_order_id in %s 
                #         and state in ('posted','reconciled') ;
                #     """,(tuple(order_list),))
                # cr_res = self.env.cr.fetchall()
                # payment_list = [x[0] for x in cr_res]

        return res

    def reconcile_payments_sale_order(self):
        payment_obj = self.env['account.payment']
        account_move_obj = self.env['account.move'].sudo()
        account_move_line_obj = self.env['account.move.line'].sudo()
        for invoice in self:
            ### Si no es Factura Global ###
            self.env.cr.execute("""
                select sale_order_line.order_id from sale_order_line_invoice_rel 
                    join account_move_line on sale_order_line_invoice_rel.invoice_line_id =  account_move_line.id
                    join sale_order_line on sale_order_line.id = sale_order_line_invoice_rel.order_line_id
                    and account_move_line.move_id = %s
                    group by sale_order_line.order_id

                """, (invoice.id,))
            cr_res = self.env.cr.fetchall()
            order_list = []
            if cr_res:
                order_list = [x[0] for x in cr_res if x]
            if not order_list:
                self.env.cr.execute("""
                    select sale_id from account_invoice_sale_rel
                        where invoice_id = %s;
                    """, (invoice.id,))
                cr_res = self.env.cr.fetchall()
                order_list = []
                if cr_res:
                    order_list = [x[0] for x in cr_res if x]
                if not order_list:
                    raise UserError(_("Error!\nNo existen registros de Pedidos a Conciliar."))
            if not order_list:
                invoice_line_list = [x.id for x in rec.invoice_line_ids]
                if invoice_line_list:
                    self.env.cr.execute("""
                        select order_line_id from sale_order_line_invoice_rel
                               where invoice_line_id in %s;
                        """, (tuple(invoice_line_list),))
                    cr_res = self.env.cr.fetchall()
                    if cr_res and cr_res[0] and cr_res[0][0]:
                        sale_order_res = [x[0] for x in cr_res]
                        self.env.cr.execute("""
                            select order_id from sale_order_line
                                   where id in %s;
                            """, (tuple(sale_order_res),))
                        cr_res = self.env.cr.fetchall()
                        if cr_res and cr_res[0] and cr_res[0][0]:
                            order_list = [x[0] for x in cr_res]

            for order in self.env['sale.order'].browse(order_list):
                if order.total_payment == False and order.payment_exception == False:
                    raise UserError(_("Error!\nEl Pedido %s no se encuentra pagado en su totalidad. \nPuede activar la Excepcion de Pago en el Pedido o Pedidos Origen." % order.name))

            ### Conciliando ####
            payment_list = payment_obj.search([('state','in',('posted','reconciled')),('sale_order_id','in',tuple(order_list))])
            if not payment_list:
                raise UserError(_("Error!\nNo existen Pagos para Conciliar."))

            ## Esto es para la version Normal con metodos de Odoo ###
            amls_to_reconcile = self.env['account.move.line']
            moves_to_reclasification = []
            for payment in payment_list.sudo():
                payment.write({'partner_id':invoice.partner_id.id})
                if payment.move_id and payment.move_id  not in moves_to_reclasification:
                        moves_to_reclasification.append(payment.move_id)
            amls_to_reconcile_payments = []
            if moves_to_reclasification:
                for mv in moves_to_reclasification:
                    # Cambiando el Partner ##
                    partner_list = [x.partner_id.id for x in mv.line_ids if x.partner_id]
                    partner_list = list(set(partner_list))
                    if partner_list:
                        if invoice.partner_id.id != partner_list[0]:
                            ## Cambiando el partner en las Partidas #
                            for mv_line in mv.line_ids:
                                mv_line.write({'partner_id':invoice.partner_id.id})
                                mv_line.move_id.write({'partner_id':invoice.partner_id.id})
                    for move_line in mv.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable')):
                        amls_to_reconcile += move_line
                        amls_to_reconcile_payments.append(move_line)
                amls_to_reconcile += invoice.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                amls_to_reconcile.reconcile()
            if invoice.currency_id.is_zero(invoice.amount_residual):    
                new_pmt_state = 'paid'
                invoice.payment_state = new_pmt_state

    def reconcile_customer_invoices(self, move_id, invoice_ids):
        move_line_obj = self.env['account.move.line']

        for invoice in invoice_ids:
            invoice_move_line = invoice.move_id.line_ids.filtered(lambda r: r.account_id.internal_type=='receivable')
            expense_move_line = move_id.line_ids.filtered(lambda r: r.account_id.internal_type=='receivable' and r.partner_id.id==invoice.partner_id.id \
                                                                and invoice.reference in r.name and r.debit==invoice.residual)
            (invoice_move_line + expense_move_line).reconcile()
        
        return
