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


class PosPaymentMethod(models.Model):
    _name = 'pos.payment.method'
    _inherit ='pos.payment.method'

    payment_tpv_id = fields.Many2one('l10n_mx_edi.payment.method', 'Forma de Pago SAT')

############# Herencia Facturas ####################


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit ='account.move'

    pos_order_ids = fields.Many2many('pos.order',
        'account_invoice_pos_rel_fx', 'invoice_id',  'sale_id',
        string='Pedidos POS', copy=False)

    def unlink(self):    
        for rec in self:
            if rec.move_type == 'out_invoice':
                pos_order_obj = self.env['pos.order'].sudo()
                pos_rel_ids = pos_order_obj.search([('account_move','=',rec.id)])
                if pos_rel_ids:
                    pos_rel_ids.write({'account_move' : False})
                    pos_rel_ids.write({'state' : 'paid'})
                    pos_rel_ids.write({'invoice_global_ids' : False})
        return super(AccountMove, self).unlink()

    def reconcile_payments_sale_order(self):
        for rec in self:
            pos_order_obj = self.env['pos.order'].sudo()
            #pos_rel_ids = pos_order_obj.search([('account_move','=',rec.id)])
            pos_rel_ids = rec.pos_order_ids
            context = dict(self._context)
            context.update({'active_id': rec.id, 'active_ids': [rec.id], 'active_model': 'account.move'})
            if pos_rel_ids:
                raise UserError("La Factura Global del POS no requiere una Conciliación Manual, en su lugar cierre el POS.")
                return {
                            'type': 'ir.actions.act_window',
                            # 'res_id': self.id,
                            'res_model': 'account.invoice.pos_reconcile_with_payments',
                            'view_mode': 'form',
                            'target': 'new',
                            'context': context
                        }
        res = super(AccountMove, self).reconcile_payments_sale_order()
        return res

######### Inicio Factura Global - VENTAS ###########

class sale_order_invoice_wizard(models.TransientModel):
    _name = "sale.order.invoice_wizard"
    _description = "Wizard Factura Global Ventas"


    @api.model  
    def default_get(self, fields):
        res = super(sale_order_invoice_wizard, self).default_get(fields)
        record_ids = self._context.get('active_ids', [])
        sale_order_obj = self.env['sale.order']
        if not record_ids:
            return {}
        tickets = []
        
        partner_id = sale_order_obj.get_customer_for_general_public().id
        
        for ticket in sale_order_obj.browse(record_ids):
            ### Restriccion de Tickets Pagados ###
            if ticket.total_payment == False:
                if ticket.payment_exception == False:
                    raise UserError(_("Solo puede facturar Pedidos Pagados o con Excepción de Pago."))

            if ticket.state in ('cancel') or ticket.invoice_status != 'to invoice':
                continue
            # flag = not bool(ticket.partner_id) or bool(ticket.partner_id.invoice_2_general_public or ticket.partner_id.id == partner_id) or False
            flag = False
            if self.env.user.company_id.invoice_public_default:
                flag = True
            else:
                flag = not bool(ticket.partner_id) or bool(ticket.partner_id.invoice_2_general_public or ticket.partner_id.id == partner_id) or False
            
            tickets.append((0,0,{
                    'ticket_id'     : ticket.id,
                    'date_order'    : ticket.date_order,
                    'sale_reference' : ticket.name,
                    'user_id'       : ticket.user_id.id,
                    'partner_id'    : ticket.partner_id and ticket.partner_id.id or False,
                    'amount_total'  : ticket.amount_total,
                    'invoice_2_general_public' : flag,
                    }))
        res.update(ticket_ids=tickets)
        return res


    date       = fields.Datetime(string='Fecha', default=fields.Datetime.now(), required=True,
                              help='This date will be used as the invoice date and period will be chosen accordingly!')
    journal_id = fields.Many2one('account.journal', string='Diario Facturacion', required=True,
                                  default=lambda self: self.env['account.journal'].search([('type', '=', 'sale'), ('company_id','=',self.env.user.company_id.id)], limit=1),
                                  help='You can select here the journal to use for the Invoice that will be created.')
    ticket_ids = fields.One2many('sale.order.invoice_wizard.line','wiz_id',string='Ventas a Facturar', required=True)

    def check_all_public_invoice(self):
        for line in self.ticket_ids:
            line.invoice_2_general_public = True
            line.amount_total = line.ticket_id.amount_total
        return{
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'res_model': 'sale.order.invoice_wizard',
                'view_mode': 'form',
                'target': 'new',
            }
                
    

    def create_invoice_from_sales(self):
        invoice_obj = self.env['account.move']
        invoice_ids = []
        ### Busqueda del Cliente Publico en General ###
        general_public_partner = self.env['sale.order'].get_customer_for_general_public()
        tickets_to_set_as_general_public = []

        tickets_simple_invoice =  []
        res = {}
        for line in self.ticket_ids:
            if line.invoice_2_general_public:
                tickets_to_set_as_general_public += line.ticket_id
            else:
                tickets_simple_invoice.append(line.ticket_id)
            
        # Ponemos todos los tickets a facturar como si no fueran Publico en General, esto por si se cancelo/elimino una Factura previa
        
        if tickets_to_set_as_general_public:
            lines_to_invoice = []
            global_origin_name = ""
            ### Busqueda del Producto para Facturacion ###
            global_product_id = tickets_to_set_as_general_public[0].search_product_global()
            ### Rertorno de la cuenta para Facturación ###
            account = global_product_id.property_account_income_id or global_product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(_('Por favor crea una cuenta para el producto: "%s" (id:%d) - or for its category: "%s".') %
                    (global_product_id.name, global_product_id.id, global_product_id.categ_id.name))

            # fpos = tickets_to_set_as_general_public[0].fiscal_position_id or tickets_to_set_as_general_public[0].partner_id.property_account_position_id
            # if fpos:
            #     account = fpos.map_account(account)

            ticket_id_list = []
            for ticket in tickets_to_set_as_general_public:
                global_origin_name += ticket.name+","
                order_line_ids = [x.id for x in ticket.order_line]
                if not ticket.global_line_ids:
                    ticket.update_concepts_to_global_invoice()

                for line in ticket.order_line:
                    lines_to_invoice_vals = line._prepare_invoice_line()
                    lines_to_invoice_vals.update({
                            'noidentificacion': ticket.name,
                            'name': 'VENTA: %s' % ticket.name,
                        })
                    lines_to_invoice.append((0,0,lines_to_invoice_vals))

                # for concept in ticket.global_line_ids:
                #     lines_to_invoice.append((0,0,{
                #             'noidentificacion': ticket.name,
                #             'product_id': concept.product_id.id,
                #             'name': 'VENTA: %s' % ticket.name,
                #             'quantity': 1,
                #             'account_id': account.id,
                #             'product_uom_id': concept.uom_id.id,
                #             'tax_ids': [(6,0,[x.id for x in concept.invoice_line_tax_ids])] if concept.invoice_line_tax_ids else False,
                #             'price_unit':concept.price_unit,
                #             'discount': 0.0,
                #             #'sale_line_ids': [(6,0,order_line_ids)]
                #         }))
                ticket.write({'invoice_2_general_public': True, 'type_invoice_global': 'general_public'})

                ### Escribiendo como Facturados los Pedidos ####
                ticket.order_line.write({'invoice_status' : 'invoiced'})
                ticket_id_list.append(ticket.id)
            # metodo_pago_id = self.env['sat.metodo.pago'].search([('code','=','PUE')])
            # if not metodo_pago_id:
            #     raise UserError("Error!\nNo se encuentra el metodo de Pago PUE.")
            # metodo_pago_id = metodo_pago_id[0]
            # uso_cfdi_id = self.env['sat.uso.cfdi'].search([('code','=','P01')])
            # if not uso_cfdi_id:
            #     raise UserError("Error!\nNo se encuentra el uso de cfdi P01.")
            uso_cfdi_id = 'P01'
            metodo_pago = 'PUE'
            pay_method_id = self.env['l10n_mx_edi.payment.method'].search([('code','=','01')], limit=1)
            if not pay_method_id:
                raise UserError("Error!\nNo se encuentra el metodo de Pago 01.")

            invoice_vals = {
                'partner_id': general_public_partner.id,
                'l10n_mx_edi_payment_policy': metodo_pago,
                'l10n_mx_edi_usage': uso_cfdi_id,
                'l10n_mx_edi_payment_method_id': pay_method_id.id,
                'journal_id': self.journal_id.id,
                'invoice_date': self.date,
                'invoice_line_ids': lines_to_invoice,
                'narration': 'Factura Global [ '+global_origin_name+' ]',
                'move_type': 'out_invoice',

            }

            invoice_id = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals)
            invoice_ids.append(invoice_id.id)
            ### Grabar Facturas #####
            self.env['sale.order'].browse(ticket_id_list).write({'invoice_global_ids': [(6,0,[invoice_id.id])], 'invoice_status': 'invoiced', 'invoice_count': 1 })
            # self.env['sale.order'].browse(ticket_id_list)._get_invoiced()

            # self.env.cr.execute("""
            #     update sale_order_line set invoice_id = %s where order_id in %s;
            #     """, (invoice_id.id, tuple(ticket_id_list),))
        if tickets_simple_invoice:
            for ticket in tickets_simple_invoice:
                invoice_create_ids = ticket._create_invoice_single()
                for inv in invoice_create_ids:
                    invoice_ids.append(inv.id)

        ### Rertorno de la información ###
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_move_out_invoice_type')
        form_view_id = imd.xmlid_to_res_id('account.view_move_form')
        list_view_id = imd.xmlid_to_res_id('account.view_invoice_tree')
        if len(invoice_ids) > 1:
            return {
                        'name': _('Facturacion Global Ventas'),
                        'view_mode': 'form',
                        'view_id': self.env.ref('account.view_invoice_tree').id,
                        'res_model': 'account.move',
                        'context': "{}", # self.env.context
                        'type': 'ir.actions.act_window',
                        'domain': [('id', 'in', invoice_ids)],
                    }
        else:
            return {
                        'name': _('Factura Global'),
                        'view_mode': 'form',
                        'view_id': self.env.ref('account.view_move_form').id,
                        'res_model': 'account.move',
                        'context': "{}", # self.env.context
                        'type': 'ir.actions.act_window',
                        'res_id': invoice_ids[0],
                    }
                    
        

        
class sale_order_invoice_wizard_line(models.TransientModel):
    _name = "sale.order.invoice_wizard.line"
    _description = "Wizard Factura Global Detalle Ventas"

    wiz_id        = fields.Many2one('sale.order.invoice_wizard',string='ID Return', ondelete="cascade")
    ticket_id     = fields.Many2one('sale.order', string='Venta')
    date_order    = fields.Datetime(related='ticket_id.date_order', string="Fecha", readonly=True)
    sale_reference = fields.Char(related='ticket_id.name', string="Referencia", readonly=True)
    user_id       = fields.Many2one("res.users", related='ticket_id.user_id', string="Vendedor", readonly=True)
    amount_total  = fields.Float("Total", readonly=True)
    partner_id    = fields.Many2one("res.partner", related='ticket_id.partner_id', string="Cliente", readonly=True)
    invoice_2_general_public = fields.Boolean('Publico en General')
        

######### Fin Factura Global ###########

######### Inicio Factura Global - PUNTO DE VENTA ###########

class pos_order_invoice_wizard(models.TransientModel):
    _name = "pos.order.invoice_wizard"
    _description = "Wizard Factura Global POS"


    @api.model  
    def default_get(self, fields):
        res = super(pos_order_invoice_wizard, self).default_get(fields)
        record_ids = self._context.get('active_ids', [])
        pos_order_obj = self.env['pos.order']
        if not record_ids:
            return {}
        tickets = []
        
        partner_id = pos_order_obj.get_customer_for_general_public().id
        journal_id = False
        for ticket in pos_order_obj.browse(record_ids):
            ### Restriccion de Tickets Pagados ###
            # if ticket.total_payment == False:
            #     if ticket.payment_exception == False:
            #         raise UserError(_("Solo puede facturar Pedidos Pagados o con Excepción de Pago."))
            if not journal_id:
                if ticket.session_id.config_id and ticket.session_id.config_id.invoice_journal_id:
                    journal_id = ticket.session_id.config_id.invoice_journal_id.id
            if ticket.state in ('cancel','draft', 'invoiced') or (ticket.account_move and ticket.account_move.state != 'cancel'):
                continue
            # flag = not bool(ticket.partner_id) or bool(ticket.partner_id.invoice_2_general_public or ticket.partner_id.id == partner_id) or False
            flag = False
            if self.env.user.company_id.invoice_public_default:
                flag = True
            else:
                flag = not bool(ticket.partner_id) or bool(ticket.partner_id.invoice_2_general_public or ticket.partner_id.id == partner_id) or False
            
            tickets.append((0,0,{
                    'ticket_id'     : ticket.id,
                    'date_order'    : ticket.date_order,
                    'pos_reference' : ticket.pos_reference if ticket.pos_reference else ticket.name,
                    'user_id'       : ticket.user_id.id,
                    'partner_id'    : ticket.partner_id and ticket.partner_id.id or False,
                    'amount_total'  : ticket.amount_total,
                    'invoice_2_general_public' : flag,
                    }))
        res.update(ticket_ids=tickets,journal_id=journal_id)
        return res


    date       = fields.Datetime(string='Fecha', default=fields.Datetime.now(), required=True,
                              help='This date will be used as the invoice date and period will be chosen accordingly!')
    journal_id = fields.Many2one('account.journal', string='Diario Facturacion', required=True,
                                  help='You can select here the journal to use for the Invoice that will be created.')
    ticket_ids = fields.One2many('pos.order.invoice_wizard.line','wiz_id',string='Ventas a Facturar', required=True)
    
    pay_method_grouped = fields.Boolean('Agrupar por Forma de Pago', help="Agrupara los pedidos por Forma de Pago y creara una Factura por cada uno de ellos.")

    invoice_detail_products = fields.Boolean('Detalle Ventas', help="Crea la factura global con el detalle de cada venta.", default=True)

    def check_all_public_invoice(self):
        for line in self.ticket_ids:
            line.invoice_2_general_public = True
            line.amount_total = line.ticket_id.amount_total
        return{
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'res_model': 'pos.order.invoice_wizard',
                'view_mode': 'form',
                'target': 'new',
            }
                
    

    def create_invoice_from_sales(self):
        invoice_obj = self.env['account.move']
        invoice_ids = []
        ### Busqueda del Cliente Publico en General ###
        general_public_partner = self.env['pos.order'].get_customer_for_general_public()
        tickets_to_set_as_general_public = []
        tickets_simple_invoice =  []
        tickets_to_set_as_general_public_ids = []

        ### Agrupando por Forma de Pago ####
        cr = self.env.cr
        pos_order_obj = self.env['pos.order']
        record_ids = self._context.get('active_ids', [])
        ticket_without_payment_type = pos_order_obj.search([('payment_tpv_id','=',False),('id','in',tuple(record_ids))])

        if ticket_without_payment_type and self.pay_method_grouped:
            ticket_without_payment_type.update_concepts_to_global_invoice()

        res = {}
        for line in self.ticket_ids:
            if line.invoice_2_general_public:
                tickets_to_set_as_general_public += line.ticket_id
                tickets_to_set_as_general_public_ids.append(line.ticket_id.id)
            else:
                tickets_simple_invoice.append(line.ticket_id)
            
        # Ponemos todos los tickets a facturar como si no fueran Publico en General, esto por si se cancelo/elimino una Factura previa
        
        if tickets_to_set_as_general_public:
            ### Busqueda del Producto para Facturacion ###
            global_product_id = tickets_to_set_as_general_public[0].search_product_global()
            ### Rertorno de la cuenta para Facturación ###
            account = global_product_id.property_account_income_id or global_product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(_('Por favor crea una cuenta para el producto: "%s" (id:%d) - or for its category: "%s".') %
                    (global_product_id.name, global_product_id.id, global_product_id.categ_id.name))

            fpos = tickets_to_set_as_general_public[0].fiscal_position_id or tickets_to_set_as_general_public[0].partner_id.property_account_position_id
            if fpos:
                account = fpos.map_account(account)
            if self.pay_method_grouped:
                if len(tickets_to_set_as_general_public_ids) == 1:
                    cr.execute("""
                        select payment_tpv_id from pos_order where id = %s group by payment_tpv_id;
                        """, (tickets_to_set_as_general_public_ids, ))
                else:
                    cr.execute("""
                        select payment_tpv_id from pos_order where id in %s group by payment_tpv_id;
                        """, (tuple(tickets_to_set_as_general_public_ids),))
                cr_res = cr.fetchall()
                payment_tpv_ids = [x[0] for x in cr_res]
                for payment_type in payment_tpv_ids:
                    lines_to_invoice = []
                    global_origin_name = ""
                    tickets_by_payment = pos_order_obj.search([('payment_tpv_id','=',payment_type),('id','in',tuple(tickets_to_set_as_general_public_ids))])
                    if tickets_by_payment:
                        ticket_id_list = []
                        for ticket in tickets_by_payment:
                            global_origin_name += ticket.name+","
                            order_line_ids = [x.id for x in ticket.lines]
                            if self.invoice_detail_products:
                                for line in ticket.lines:
                                    lines_to_invoice_vals = ticket._prepare_invoice_line(line)
                                    lines_to_invoice_vals.update({
                                            'noidentificacion': ticket.pos_reference,
                                            'name': ticket.pos_reference,
                                        })
                                    lines_to_invoice.append((0,0,lines_to_invoice_vals))
                            else:
                                if not ticket.global_line_ids:
                                    ticket.update_concepts_to_global_invoice()
                                for concept in ticket.global_line_ids:
                                    lines_to_invoice.append((0,0,{
                                            'noidentificacion': concept.noidentificacion,
                                            'product_id': concept.product_id.id,
                                            'name': concept.noidentificacion,
                                            'quantity': 1,
                                            'account_id': account.id,
                                            'product_uom_id': concept.uom_id.id,
                                            'tax_ids': [(6,0,[x.id for x in concept.invoice_line_tax_ids])] if concept.invoice_line_tax_ids else False,
                                            'price_unit':concept.price_unit,
                                            'discount': 0.0,
                                            #'sale_line_ids': [(6,0,order_line_ids)]
                                        }))
                            ticket.write({'invoice_2_general_public': True, 'type_invoice_global': 'general_public'})

                            ticket_id_list.append(ticket.id)

                        uso_cfdi_id = 'P01'
                        metodo_pago = 'PUE'

                        invoice_vals = {
                            'partner_id': general_public_partner.id,
                            'l10n_mx_edi_payment_policy': metodo_pago,
                            'l10n_mx_edi_usage': uso_cfdi_id,
                            'l10n_mx_edi_payment_method_id': payment_type,
                            'journal_id': self.journal_id.id,
                            'invoice_date': self.date,
                            'invoice_line_ids': lines_to_invoice,
                            'narration': 'Factura Global [ '+global_origin_name+' ]',
                            'move_type': 'out_invoice',

                        }

                        invoice_id = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals)
                        invoice_ids.append(invoice_id.id)
                        ### Grabar Facturas #####
                        self.env['pos.order'].browse(ticket_id_list).write({'invoice_global_ids': [(6,0,[invoice_id.id])], 
                                                                            'state': 'invoiced', 
                                                                            'account_move':  invoice_id.id,
                                                                            'partner_id': general_public_partner.id,
                                                                            })

            else:
                lines_to_invoice = []
                global_origin_name = ""
                ticket_id_list = []
                for ticket in tickets_to_set_as_general_public:
                    global_origin_name += ticket.name+","
                    order_line_ids = [x.id for x in ticket.lines]
                    if self.invoice_detail_products:
                        for line in ticket.lines:
                            lines_to_invoice_vals = ticket._prepare_invoice_line(line)
                            lines_to_invoice_vals.update({
                                    'noidentificacion': ticket.pos_reference,
                                    'name': ticket.pos_reference,
                                })
                            lines_to_invoice.append((0,0,lines_to_invoice_vals))
                    else:
                        if not ticket.global_line_ids:
                            ticket.update_concepts_to_global_invoice()
                        for concept in ticket.global_line_ids:
                            lines_to_invoice.append((0,0,{
                                    'noidentificacion': concept.noidentificacion,
                                    'product_id': concept.product_id.id,
                                    'name': concept.noidentificacion,
                                    'quantity': 1,
                                    'account_id': account.id,
                                    'product_uom_id': concept.uom_id.id,
                                    'tax_ids': [(6,0,[x.id for x in concept.invoice_line_tax_ids])] if concept.invoice_line_tax_ids else False,
                                    'price_unit':concept.price_unit,
                                    'discount': 0.0,
                                    #'sale_line_ids': [(6,0,order_line_ids)]
                                }))
                    ticket.write({'invoice_2_general_public': True, 'type_invoice_global': 'general_public'})

                    ### Escribiendo como Facturados los Pedidos ####
                    # ticket.order_line.write({'invoice_status' : 'invoiced'})
                    ticket_id_list.append(ticket.id)
                # metodo_pago_id = self.env['sat.metodo.pago'].search([('code','=','PUE')])
                # if not metodo_pago_id:
                #     raise UserError("Error!\nNo se encuentra el metodo de Pago PUE.")
                # metodo_pago_id = metodo_pago_id[0]
                # uso_cfdi_id = self.env['sat.uso.cfdi'].search([('code','=','P01')])
                # if not uso_cfdi_id:
                #     raise UserError("Error!\nNo se encuentra el uso de cfdi P01.")
                uso_cfdi_id = 'P01'
                metodo_pago = 'PUE'
                pay_method_id = self.env['l10n_mx_edi.payment.method'].search([('code','=','01')], limit=1)
                if not pay_method_id:
                    raise UserError("Error!\nNo se encuentra el metodo de Pago 01.")

                invoice_vals = {
                    'partner_id': general_public_partner.id,
                    'l10n_mx_edi_payment_policy': metodo_pago,
                    'l10n_mx_edi_usage': uso_cfdi_id,
                    'l10n_mx_edi_payment_method_id': pay_method_id.id,
                    'journal_id': self.journal_id.id,
                    'invoice_date': self.date,
                    'invoice_line_ids': lines_to_invoice,
                    'narration': 'Factura Global [ '+global_origin_name+' ]',
                    'move_type': 'out_invoice',

                }

                invoice_id = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals)
                invoice_ids.append(invoice_id.id)
                ### Grabar Facturas #####
                self.env['pos.order'].browse(ticket_id_list).write({'invoice_global_ids': [(6,0,[invoice_id.id])], 
                                                                    'state': 'invoiced', 
                                                                    'account_move':  invoice_id.id,
                                                                    'partner_id': general_public_partner.id,
                                                                    })

                # self.env.cr.execute("""
                #     update sale_order_line set invoice_id = %s where order_id in %s;
                #     """, (invoice_id.id, tuple(ticket_id_list),))
        
        if tickets_simple_invoice:
            for ticket in tickets_simple_invoice:
                invoice_create_ids = ticket._create_invoice_single()
                for inv in invoice_create_ids:
                    invoice_ids.append(inv.id)

        ### Rertorno de la información ###
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_move_out_invoice_type')
        form_view_id = imd.xmlid_to_res_id('account.view_move_form')
        list_view_id = imd.xmlid_to_res_id('account.view_out_invoice_tree')
        if len(invoice_ids) > 1:
            action_invoices = self.env.ref('account.action_move_out_invoice_type')
            action = action_invoices.read()[0]
            action['context'] = {}
            action['domain'] = [('id', 'in',invoice_ids)]
            return action
        else:
            return {
                        'name': _('Factura Global'),
                        'view_mode': 'form',
                        'view_id': self.env.ref('account.view_move_form').id,
                        'res_model': 'account.move',
                        'context': "{}", # self.env.context
                        'type': 'ir.actions.act_window',
                        'res_id': invoice_ids[0],
                    }
                    
        

        
class pos_order_invoice_wizard_line(models.TransientModel):
    _name = "pos.order.invoice_wizard.line"
    _description = "Wizard Factura Global Tickets POS"

    wiz_id        = fields.Many2one('pos.order.invoice_wizard',string='ID Return', ondelete="cascade")
    ticket_id     = fields.Many2one('pos.order', string='Venta')
    date_order    = fields.Datetime(related='ticket_id.date_order', string="Fecha", readonly=True)
    pos_reference = fields.Char(related='ticket_id.name', string="Referencia", readonly=True)
    user_id       = fields.Many2one("res.users", related='ticket_id.user_id', string="Vendedor", readonly=True)
    amount_total  = fields.Float("Total", readonly=True)
    partner_id    = fields.Many2one("res.partner", related='ticket_id.partner_id', string="Cliente", readonly=True)
    invoice_2_general_public = fields.Boolean('Publico en General')
        

######### Fin Factura Global - PUNTO DE VENTA ###########


######### Conciliación de Pagos Factura Global - PUNTO DE VENTA ###########

class account_invoice_pos_reconcile_with_payments(models.TransientModel):
    _name = "account.invoice.pos_reconcile_with_payments"
    _description = "Wizard to Reconcile POS Payments with Invoices from POS Orders"

    date = fields.Date(string='Payment Date', help='This date will be used as the payment date !', 
                       default=fields.Date.context_today, required=True)
    
    
    def get_aml_to_reconcile(self, am_ids):
        am_obj = self.pool.get('account.move')
        amls = []
        for move in am_obj.browse(am_ids):
            for line in move.line_id:
                if line.account_id.type=='receivable':
                    #print "line: %s - %s - %s" % (move.name, line.account_id.code, line.account_id.name)
                    amls.append(line.id)
        return amls
    
    def reconcile_invoice_with_pos_payments(self):
        rec_ids = self._context.get('active_ids', [])
        
        am_obj = self.env['account.move']
        pos_order_obj = self.env['pos.order']
        for invoice in self.env['account.move'].browse(rec_ids):
            amls_to_reconcile = self.env['account.move.line']
            #print "----------------------------------------"
            #print "Procesando Factura: ", invoice.number
            if invoice.state != 'posted':
                continue                
            #order_ids = pos_order_obj.search([('account_move','=',invoice.id)])

            data_statement_line_ids, data_aml_ids = [], []

            Statement = self.env['account.bank.statement']

            for order in invoice.pos_order_ids:
                #print "order: %s - %s " % (order.name, order.amount_total)
                if order.session_id.state != 'closed':
                    raise UserError('Advertencia!\nLa Sesion %s del TPV %s asociado al Ticket %s el cual esta asociado a la Factura %s no ha sido cerrada, no se pudo realizar la Conciliacion de los Pagos. Primero cierre la sesion para poder correr este proceso.' % (order.session_id.name, order.session_id.config_id.name, order.name, invoice.name))
                if order.state != 'invoiced':
                    continue
                

                statement_ids = Statement.search([
                    ('pos_session_id', '=', order.session_id.id),
                ])
                for payment in order.payment_ids:
                    for statement in order.statement_ids:
                        if statement.journal_id.pos_payments_remove_entries or not statement.journal_entry_ids: 
                                continue
                        for account_move in statement.journal_entry_ids:
                            for move_line in account_move.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable')):
                                amls_to_reconcile += move_line
            amls_to_reconcile += invoice.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
            amls_to_reconcile.reconcile(writeoff_acc_id=False, writeoff_journal_id=False)

        #raise osv.except_osv('Pausa!', 'Pausa')
        return True   

######### Inicio Herencia Objetos y Metodos  Punto de Venta ###########

class PosOrderLineGlobalConcept(models.Model):
    _name = 'pos.order.line.global.concept'
    _description = 'Concetps de Facturación Global'
    _rec_name = 'noidentificacion' 

    noidentificacion = fields.Char('NoIdentificacion', size=128)
    product_id = fields.Many2one('product.product', 'Producto')
    uom_id = fields.Many2one('uom.uom', 'Unidad de Medida')
    invoice_line_tax_ids = fields.Many2many('account.tax',
        'pos_order_account_invoice_line_global_tax', 'global_line_id', 'tax_id',
        string='Impuestos',)
    quantity = fields.Float('Cantidad', digits=(14,2), default=1.0)
    price_unit = fields.Float('Total')
    sale_id = fields.Many2one('pos.order', 'ID Ref')

class PosOrder(models.Model):
    _inherit = "pos.order"
        
    invoice_2_general_public = fields.Boolean(string='Facturado a Publico en General', 
                                              help="La factura se realizo a Publico en General.")

    global_line_ids = fields.One2many('pos.order.line.global.concept', 'sale_id', 'Conceptos de Facturacion Global')

    type_invoice_global = fields.Selection([('simple','Cliente'),
                                            ('general_public','Publico en General')], 'Facturado a', default="simple")

    partner_original_id =  fields.Many2one('res.partner', 'Partner Pedido Original')

    invoice_global_ids = fields.Many2many('account.move',
        'account_invoice_pos_rel_fx', 'sale_id', 'invoice_id',
        string='Facturas', copy=False)

    payment_tpv_id = fields.Many2one('l10n_mx_edi.payment.method', 'Forma de Pago SAT')


    def add_payment(self, data):
        res = super(PosOrder, self).add_payment(data)
        for rec in self:
            rec.update_concepts_to_global_invoice()
        return res


    def _create_invoice_single(self,):
        moves = self.env['account.move']
        for order in self:
            # Force company for all SUPERUSER_ID action
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_('Por favor ingresa un Cliente para la Venta.'))

            move_vals = order._prepare_invoice_vals()
            new_move = moves.sudo()\
                            .with_company(order.company_id)\
                            .with_context(default_move_type=move_vals['move_type'])\
                            .create(move_vals)
            message = _("Se ha creado una factura relacionada con la Sesión: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
            new_move.message_post(body=message)
            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            #new_move.sudo().with_company(order.company_id)._post()
            moves += new_move
        return moves          



    def search_product_global(self):
        for rec in self:
            product_uom = self.env['uom.uom']
            product_obj = self.env['product.product']
            company = rec.company_id
            if not company.product_for_global_invoice:
                uom_id = product_uom.search([('name','=','Actividad Facturacion')])
                uom_id = uom_id[0] if uom_id else False
                if not uom_id:
                    sat_udm  = self.env['product.unspsc.code']
                    sat_uom_id = sat_udm.search([('code','=','ACT')])
                    if not sat_uom_id:
                        raise UserError("Error!\nNo existe la Unidad de Medida [ACT] Actividades.")
                    category_id = self.env['uom.category'].search([('name','=','Facturacion')],limit=1)
                    if not category_id:
                        category_id = self.env['uom.category'].sudo().create({'name':'Facturacion'})
                    uom_id = product_uom.create({
                                                    'unspsc_code_id':sat_uom_id[0].id,
                                                    'name':'Actividad Facturacion',
                                                    'category_id': category_id.id,
                                                    'uom_type': 'reference',
                                                    'use_4_invoice_general_public':True,

                                                })

                sat_product_id = self.env['product.unspsc.code'].search([('code','=','01010101')])
                if not sat_product_id:
                    raise UserError("El Codigo 01010101 no existe en el Catalogo del SAT.")
                product_id = product_obj.search([('product_for_global_invoice','=',True)])
                if product_id:
                    product_id = product_id[0]
                else:
                    product_id = product_obj.create({
                            'name': 'Servicio Facturacion Global',
                            'uom_id': uom_id.id,
                            'uom_po_id': uom_id.id,
                            'type': 'service',
                            'unspsc_code_id': sat_product_id[0].id,
                            'product_for_global_invoice': True,
                        })
                company.write({'product_for_global_invoice': product_id.id})
            else:
                product_id = company.product_for_global_invoice

            return product_id

    def update_concepts_to_global_invoice(self):
        inv_ref = self.env['account.move']
        acc_tax_obj = self.env['account.tax']
        inv_line_ref = self.env['account.move.line']
        product_obj = self.env['product.product']
        picking_obj = self.env['stock.picking']
        payment_tpv_id = False
        for rec in self:
            if rec.partner_id:
                rec.partner_original_id = rec.partner_id.id
            if rec.global_line_ids:
                rec.global_line_ids.unlink()

            if rec.payment_ids:
                payment_amount = 0.0
                payment_id = False
                for pay in rec.payment_ids:
                    if pay.amount > payment_amount:
                        payment_amount = pay.amount
                        payment_id = pay.payment_method_id

                if payment_id and payment_id.payment_tpv_id:
                    payment_tpv_id = payment_id.payment_tpv_id.id

            inv_ids = []
            lines = {}
            for line in rec.lines:
                ## Agrupamos las líneas según el impuesto
                xval = 0.0
                taxes_list = [x.id for x in line.product_id.taxes_id]
                for tax in acc_tax_obj.browse(taxes_list):
                    xval += (tax.price_include and tax.amount or 0.0)

                tax_names = ", ".join([x.name for x in line.product_id.taxes_id])
                val={
                    'tax_names'           : ", ".join([x.name for x in line.product_id.taxes_id]),
                    'taxes_id'            : ",".join([str(x.id) for x in line.product_id.taxes_id]),
                    'price_subtotal'      : line.price_subtotal * (1.0 + xval),
                    'price_subtotal_incl' : line.price_subtotal,
                    }
                key = (val['tax_names'],val['taxes_id'])
                if not key in lines:
                    lines[key] = val
                    lines[key]['price_subtotal'] = val['price_subtotal']
                    lines[key]['price_subtotal_incl'] = val['price_subtotal_incl']

                else:
                    lines[key]['price_subtotal'] += val['price_subtotal']

            global_line_ids = []
            product_global = rec.search_product_global()
            for key, line in lines.items():
                tax_name = ''
                taxes_ids = line['taxes_id'].split(',') if line['taxes_id'] else False
                if taxes_ids:
                    taxes_ids = [int(x) for x in taxes_ids]
                global_vals = {
                    'product_id': product_global.id,
                    'noidentificacion': rec.pos_reference,
                    'uom_id': product_global.uom_id.id,
                    'invoice_line_tax_ids': [(6, 0, taxes_ids)] if line['taxes_id'] else False,
                    'quantity': 1,
                    'price_unit': line['price_subtotal'],
                }
                global_line_ids.append((0,0, global_vals))
            if global_line_ids:
                rec.write({'global_line_ids': global_line_ids})
            if payment_tpv_id:
                rec.write({'payment_tpv_id': payment_tpv_id})


    def get_customer_for_general_public(self):
        partner_obj = self.env['res.partner']
        partner_id = partner_obj.search([('use_as_general_public','=',1)], limit=1)
        if not partner_id:
            raise UserError(_('Por favor, configura un cliente como Publico en General.'))    
        return partner_id  



######### Inicio Herencia Objetos y Metodos  Ventas ###########


class SaleOrderLineGlobalConcept(models.Model):
    _name = 'sale.order.line.global.concept'
    _description = 'Concetps de Facturación Global'
    _rec_name = 'noidentificacion' 

    noidentificacion = fields.Char('NoIdentificacion', size=128)
    product_id = fields.Many2one('product.product', 'Producto')
    uom_id = fields.Many2one('uom.uom', 'Unidad de Medida')
    invoice_line_tax_ids = fields.Many2many('account.tax',
        'sale_order_account_invoice_line_global_tax', 'global_line_id', 'tax_id',
        string='Impuestos',)
    quantity = fields.Float('Cantidad', digits=(14,2), default=1.0)
    price_unit = fields.Float('Total')
    sale_id = fields.Many2one('sale.order', 'ID Ref')



class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit ='sale.order'

    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            if order.invoice_global_ids:
                invoice_ids = [x.id for x in order.invoice_global_ids]
                invoices = self.env['account.move'].browse(invoice_ids)
            else:
                invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    invoice_2_general_public = fields.Boolean(string='Facturado a Publico en General', 
                                              help="La factura se realizo a Publico en General.")

    type_invoice_global = fields.Selection([('simple','Cliente'),
                                            ('general_public','Publico en General')], 'Facturado a', default="simple")

    global_line_ids = fields.One2many('sale.order.line.global.concept', 'sale_id', 'Conceptos de Facturacion Global')
    invoice_global_ids = fields.Many2many('account.move',
        'account_invoice_sale_rel', 'sale_id', 'invoice_id',
        string='Facturas', copy=False)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            rec.update_concepts_to_global_invoice()
        return res

    def search_product_global(self):
        for rec in self:
            product_uom = self.env['uom.uom']
            product_obj = self.env['product.product']
            company = rec.company_id
            if not company.product_for_global_invoice:
                uom_id = product_uom.search([('name','=','Actividad Facturacion')])
                uom_id = uom_id[0] if uom_id else False
                if not uom_id:
                    sat_udm  = self.env['product.unspsc.code']
                    sat_uom_id = sat_udm.search([('code','=','ACT')])
                    if not sat_uom_id:
                        raise UserError("Error!\nNo existe la Unidad de Medida [ACT] Actividades.")
                    category_id = self.env['uom.category'].search([('name','=','Facturacion')],limit=1)
                    if not category_id:
                        category_id = self.env['uom.category'].sudo().create({'name':'Facturacion'})
                    uom_id = product_uom.create({
                                                    'unspsc_code_id':sat_uom_id[0].id,
                                                    'name':'Actividad Facturacion',
                                                    'category_id': category_id.id,
                                                    'uom_type': 'reference',
                                                    'use_4_invoice_general_public':True,

                                                })

                sat_product_id = self.env['product.unspsc.code'].search([('code','=','01010101')])
                if not sat_product_id:
                    raise UserError("El Codigo 01010101 no existe en el Catalogo del SAT.")
                product_id = product_obj.search([('product_for_global_invoice','=',True)])
                if product_id:
                    product_id = product_id[0]
                else:
                    product_id = product_obj.create({
                            'name': 'Servicio Facturacion Global',
                            'uom_id': uom_id.id,
                            'uom_po_id': uom_id.id,
                            'type': 'service',
                            'unspsc_code_id': sat_product_id[0].id,
                            'product_for_global_invoice': True,
                        })
                company.write({'product_for_global_invoice': product_id.id})
            else:
                product_id = company.product_for_global_invoice

            return product_id

    def update_concepts_to_global_invoice(self):
        inv_ref = self.env['account.move']
        acc_tax_obj = self.env['account.tax']
        inv_line_ref = self.env['account.move.line']
        product_obj = self.env['product.product']
        sales_order_obj = self.env['sale.order']
        order_line_obj = self.env['sale.order.line']
        picking_obj = self.env['stock.picking']

        for rec in self:
            if rec.global_line_ids:
                rec.global_line_ids.unlink()
            inv_ids = []
            lines = {}
            for line in rec.order_line:
                ## Agrupamos las líneas según el impuesto
                xval = 0.0
                taxes_list = [x.id for x in line.product_id.taxes_id]
                for tax in acc_tax_obj.browse(taxes_list):
                    xval += (tax.price_include and tax.amount or 0.0)

                tax_names = ", ".join([x.name for x in line.product_id.taxes_id])
                val={
                    'tax_names'           : ", ".join([x.name for x in line.product_id.taxes_id]),
                    'taxes_id'            : ",".join([str(x.id) for x in line.product_id.taxes_id]),
                    'price_subtotal'      : line.price_subtotal * (1.0 + xval),
                    'price_subtotal_incl' : line.price_subtotal,
                    }
                key = (val['tax_names'],val['taxes_id'])
                if not key in lines:
                    lines[key] = val
                    lines[key]['price_subtotal'] = val['price_subtotal']
                    lines[key]['price_subtotal_incl'] = val['price_subtotal_incl']

                else:
                    lines[key]['price_subtotal'] += val['price_subtotal']

            global_line_ids = []
            product_global = rec.search_product_global()
            for key, line in lines.items():
                tax_name = ''
                taxes_ids = line['taxes_id'].split(',') if line['taxes_id'] else False
                if taxes_ids:
                    taxes_ids = [int(x) for x in taxes_ids]
                global_vals = {
                    'product_id': product_global.id,
                    'noidentificacion': rec.name,
                    'uom_id': product_global.uom_id.id,
                    'invoice_line_tax_ids': [(6, 0, taxes_ids)] if line['taxes_id'] else False,
                    'quantity': 1,
                    'price_unit': line['price_subtotal'],
                }
                global_line_ids.append((0,0, global_vals))
            if global_line_ids:
                rec.write({'global_line_ids': global_line_ids})



    def get_customer_for_general_public(self):
        partner_obj = self.env['res.partner']
        partner_id = partner_obj.search([('use_as_general_public','=',1)], limit=1)
        if not partner_id:
            raise UserError(_('Por favor, configura un cliente como Publico en General.'))    
        return partner_id  


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit ='product.product'

    product_for_global_invoice = fields.Boolean('Facturacion Global')

class Company(models.Model):
    _inherit = 'res.company'

    product_for_global_invoice = fields.Many2one("product.product", "Producto Facturas Globales",
                                  help="Producto para Generar el Descuento Global")
    invoice_public_default = fields.Boolean('Marcar Publico General', 
        help='Indica si el Asistente de Factura Global marcara el campo de Factura a Publico en General por defecto.', )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_for_global_invoice = fields.Many2one("product.product", "Producto Facturacion Global",
                                  related='company_id.product_for_global_invoice',
                                  help="Producto para Generar el concepto del ticket Global", readonly=False)

    # @api.onchange('company_id')
    # def onchange_company_id(self):
    #     if self.company_id:
    #         company = self.company_id
    #         self.product_for_global_invoice = company.product_for_global_invoice.id
    #         res = super(ResConfigSettings, self).onchange_company_id()
    #         return res

class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit ='product.product'

    product_for_global_invoice = fields.Boolean('Facturacion Global')



class product_uom(models.Model):
    _inherit = 'uom.uom'
    """
    Adds check to indicate if this UoM will be used when creating Invoice from POS Tickets for Partner is General Public
    """

    use_4_invoice_general_public = fields.Boolean(string='Usar para Factura Global')
    
    
    @api.constrains('use_4_invoice_general_public')
    def _check_use_4_invoice_general_public(self):        
        for record in self:
            if record.use_4_invoice_general_public:
                res = self.search([('use_4_invoice_general_public', '=', 1)])                
                if res and res.id != record.id:
                    raise UserError(_("Solo puede marcar una Unidad para ser utilizada en la facturación global."))
        return True



class res_partner(models.Model):
    _inherit = 'res.partner'
    """
    Adds check to indicate Partner is General Public
    """

    invoice_2_general_public = fields.Boolean(string='Facturar a Publico en General', help="Facturar a este cliente como publico en general.", default=True)
    use_as_general_public    = fields.Boolean(string='Cliente Publico en General', help="Comodin cliente para facturas globales.")
    
    @api.constrains('use_as_general_public')
    def _check_use_as_general_public(self):        
        for record in self:
            if record.use_as_general_public:
                res = self.search([('use_as_general_public', '=', 1), ('id','!=', record.id)])
                if res:
                    raise UserError(_("Error ! You can have only one Partner checked to Use for General Public Invoice..."))
        return True

    @api.onchange('use_as_general_public')
    def on_change_use_as_general_public(self):
        res = {}
        if self.use_as_general_public:
            self.invoice_2_general_public = False    
            
    # @api.constrains('vat')
    # def _constraint_uniq_vat(self):
    #    if self.is_company and self.vat:
    #         other_partner = self.search([('vat','=',self.vat),('id','!=',self.id),('is_company','=',True)])
    #         if other_partner:
    #             raise UserError(_("Error!\nEl RFC ya existe en la Base de Datos"))


class AccountInvoiceLine(models.Model):
    _name = 'account.move.line'
    _inherit ='account.move.line'

    noidentificacion = fields.Char('NoIdentificacion', size=128)


