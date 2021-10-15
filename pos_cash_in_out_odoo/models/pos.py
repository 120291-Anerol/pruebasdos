# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, time, datetime


class ABSLInherit(models.Model):
	_inherit = 'account.bank.statement.line'

	is_cash_in_out_entry = fields.Boolean('Movimientos de Efectivo')


class POSConfigSummery(models.Model):
	_inherit = 'pos.config'
	
	is_cash_in_out = fields.Boolean('Realiza retiros en el POS')
	is_print_statement = fields.Boolean('Imprime Historicos de retiro')


class pos_cash_in_out(models.Model):
	_name = 'pos.cash.in.out'
	_rec_name = 'user_id'
	_description = "Retiros de Efectivo Super Barato"

	name = fields.Char(string = "Consecutivo" , required=True, copy=False)
	user_id  = fields.Many2one('res.users','Responsible')
	session_id  = fields.Many2one('pos.session','Session')
	amount  =  fields.Float('Amount')
	create_date  =  fields.Datetime('Create Date', default = datetime.now(), )
	cash_type = fields.Selection([
		('credit', 'Credit'),
		('debit', 'Debit')
		], string='Type', default='credit')

	@api.model
	def create(self, values):
		values['name'] = self.env['ir.sequence'].next_by_code('pos.cash.in.out')
		res = super(pos_cash_in_out,self).create(values)
		return res

	def get_statement_data(self,stmt_st_date, stmt_end_date,selected_cashier):
		cash_in_data = []
		cash_out_data = []
		credit_total = 0.0
		debit_total = 0.0
		final_data = []
		if selected_cashier == 'Selecciona al Cajero':
			statements = self.env['account.bank.statement.line'].search([
				('date', '>=', stmt_st_date ),
				('date', '<=', stmt_end_date),
				('is_cash_in_out_entry', '=', True),
			])
		else:
			statements = self.env['account.bank.statement.line'].search([
				('date', '>=', stmt_st_date ),
				('date', '<=', stmt_end_date),
				('is_cash_in_out_entry', '=', True),
				('statement_id.pos_session_id.user_id', '=', int(selected_cashier)),
			])
		for line in statements:
			data = {}
			if line.amount > 0 :
				credit_total += line.amount
				data.update({'credit': line.amount, 'debit': '-', 'date':line.date})
				cash_in_data.append(data)
			else:
				debit_total += -(line.amount)
				data.update({'credit': '-', 'debit': -(line.amount), 'date':line.date})
				cash_out_data.append(data)
			final_data.append(data)

		return[cash_in_data,cash_out_data,final_data,credit_total,debit_total]


class PosBoxIn(models.TransientModel):
	_name = 'cash.box.in'
	_description = "POS Entrada de efectivo"

	def create_cash_in(self, user, reason, amount, session_id):

		cash_in_obj = self.env['pos.cash.in.out'].sudo()
		account_in_obj = self.env['account.bank.statement.line'].sudo()

		vals = {
			'cash_type': 'credit',
			'user_id': user,
			'session_id' : session_id,
			'amount' : float(amount),
			'create_date': datetime.now().date(),
		}
		cash_create = cash_in_obj.create(vals)
		
		stmt_id = self.env['pos.session'].browse(session_id).cash_register_id
		
		if not stmt_id:
			return False

		if stmt_id.difference < 0.0:
			account = stmt_id.journal_id.loss_account_id
			name = _('Loss')
		else:
			account = stmt_id.journal_id.profit_account_id
			name = _('Profit')

		values = {
			'statement_id': stmt_id.id,
			'name': stmt_id.name+'/'+cash_create.name+'/'+reason,
			'counterpart_account_id': account.id,
			'payment_ref' : stmt_id.name,
			'amount' : float(amount),
			'is_cash_in_out_entry':True,
			'date': datetime.now().date(),
		}
		account_create = account_in_obj.create(values)
		return True
		

class PosBoxOut(models.TransientModel):
	_inherit = 'cash.box.out'

	def create_cash_out(self, user, reason, amount, session_id):

		cash_out_obj = self.env['pos.cash.in.out'].sudo()
		account_in_obj = self.env['account.bank.statement.line'].sudo()

		vals = {
			'cash_type': 'debit',
			'user_id': user,
			'session_id' : session_id,
			'amount' : float(amount),
			'create_date': datetime.now().date(),
		}
		cash_create = cash_out_obj.create(vals)

		stmt_id = self.env['pos.session'].browse(session_id).cash_register_id
		
		if not stmt_id:
			return False
		if stmt_id.difference < 0.0:
			account = stmt_id.journal_id.loss_account_id
			name = _('Loss')
		else:
			account = stmt_id.journal_id.profit_account_id
			name = _('Profit')

		values = {
			'statement_id': stmt_id.id,
			'name': stmt_id.name+'/'+cash_create.name+'/'+reason,
			'payment_ref' : stmt_id.name,
			'amount' : -float(amount),
			'counterpart_account_id': account.id,
			'is_cash_in_out_entry':True,
			'date': datetime.now().date(),
		}
		account_create = account_in_obj.create(values)
		return True
				
			   
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
