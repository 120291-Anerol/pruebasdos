# -*- coding: utf-8 -*-
#################################################################################
#
#   Sinergia Systems
#
#################################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class PosConfig(models.Model):
	_inherit = 'pos.config'

	cash_threshold = fields.Float('Limite de efectivo', default = 0, help = 'Limite de efectivo permitido')
	cash_withdraw = fields.Float('Monto de retiro recomendado', default = 0, help = "Recomendacion de retiro")

	# 
	@api.constrains('cash_threshold','cash_withdraw')
	def validate_cash_withdraw(self):
		if(self.cash_withdraw > self.cash_threshold):
			raise ValidationError("El monto recomendado no puede ser superior al limite.")


class PosSession(models.Model):
	_inherit = 'pos.session'

	# 
	def get_cash_register_difference(self):
		_logger.info("------------------cash_register_id------:%r-------:%r",self.cash_register_id,self.cash_register_id.difference)
		return self.cash_register_difference

	# 
	def set_cash_box_out_value(self,kwargs):
		bank_statements = [record.cash_register_id for record in self if record.cash_register_id]
		values = {}
		for record in bank_statements:
			if not record.journal_id:
				return {
					'msg':"Por favor configura un diario",
					'status':False
					}
			if not record.journal_id.company_id.transfer_account_id:
				return {
					'msg':"Please check that the field 'Transfer Account' is set on the company.",
					'status':False
					}
			amount = kwargs['amount']
			values =  {
				'date': record.date,
				'statement_id': record.id,
				'journal_id': record.journal_id.id,
				'amount': -amount if amount > 0.0 else amount,
				# 'account_id': record.journal_id.company_id.transfer_account_id.id,
				'ref': kwargs['ref'],
				'payment_ref': kwargs['ref'],
				'name': kwargs['reason'],
			}
			record.write({'line_ids': [(0, False, values)]})
			return {
					'msg':"Cash withdraw",
					'status':True
					}
