/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_create_product.CashPopupWidget', function(require){
	"use strict";    
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
	const Registries = require('point_of_sale.Registries');
	class CashPopupWidget extends AbstractAwaitablePopup {
		mounted(){
			var self = this;
			var difference_amount = self.env.pos.format_currency(Math.abs(self.env.pos.cash_register_difference));
			var threshold_amount = self.env.pos.format_currency(self.env.pos.config.cash_threshold);
			var withdraw_amount = self.env.pos.format_currency(self.env.pos.config.cash_withdraw);
			var amount_to_withdraw = self.env.pos.format_currency(Math.abs(self.env.pos.cash_register_difference) - self.env.pos.config.cash_threshold)
			$("#cash_message").text('Realiza tareas pendientes por favor');		
		}
		open_cash_out_popup(){
			this.showPopup('CashOutPopupWidget',{});
		}
	}
	CashPopupWidget.template = 'CashPopupWidget';
	Registries.Component.add(CashPopupWidget);
	return CashPopupWidget;
});
