/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_create_product.CashOutPopupWidget', function(require){
	"use strict";    
		const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
		const Registries = require('point_of_sale.Registries');
		var core = require('web.core');
		var _t = core._t;
		var rpc = require('web.rpc');
		class CashOutPopupWidget extends AbstractAwaitablePopup {
	
			mounted(){
				var self = this;
				$('#amount_out').focus();
				$('#amount_out').on('focus',function(){
					$('#wk-warning').hide()
				})
				var max_withdraw_amount = Math.abs(self.env.pos.cash_register_difference) - self.env.pos.config.cash_threshold;
				$('#amount_out').val(max_withdraw_amount);
				$('.button.cash_apply').on('click',function(){
					var amount_out = parseFloat($('#amount_out').val());
					if(amount_out > max_withdraw_amount){
						$("#wk-warning").show();
					}
					if (!amount_out || amount_out <= 0 || amount_out > max_withdraw_amount){
						$("#amount_out").css("background-color","burlywood");
						setTimeout(function(){
							$("#amount_out").css("background-color","");
						},100);
						setTimeout(function(){
							$("#amount_out").css("background-color","burlywood");
						},200);
						setTimeout(function(){
							$("#amount_out").css("background-color","");
						},300);
						setTimeout(function(){
							$("#amount_out").css("background-color","burlywood");
						},400);
						setTimeout(function(){
							$("#amount_out").css("background-color","");
						},500);
						return;
					}
					else if ($("#reason_out").val() == ''){
						$("#reason_out").css("background-color","burlywood");
						setTimeout(function(){
							$("#reason_out").css("background-color","");
						},100);
						setTimeout(function(){
							$("#reason_out").css("background-color","burlywood");
						},200);
						setTimeout(function(){
							$("#reason_out").css("background-color","");
						},300);
						setTimeout(function(){
							$("#reason_out").css("background-color","burlywood");
						},400);
						setTimeout(function(){
							$("#reason_out").css("background-color","");
						},500);
						return;
					}
					else{
						var amount = parseFloat($('#amount_out').val());
						var reason = "Reason:" + ($("#reason_out").val());
						rpc.query({
							model:'pos.session',
							method:'set_cash_box_out_value',
							args:[self.env.pos.pos_session.id,{
								'amount': amount,
								'reason': reason,
								'ref' : self.env.pos.pos_session.name
							}]
						})
						.catch(function(error){
							self.showPopup('ErrorPopup', {
								title: _t('Failed To Take Money Out.'),
								body: _t('Please make sure you are connected to the network.'),
							});
						})
						.then(function(result){
							if(result && result['status']){
								self.showPopup('SuccessNotifyPopupWidget',{
									message:self.env.pos.format_currency(amount)+'   is successfully taken out'
								})
							}
							else if(result && result['msg']){
								self.showPopup('ErrorPopup',{
									'title': _t('Failed To Take Money Out'),
									'body': _t(result['msg']),
								});
							}
						})
						self.cancel();	
					}
				});
			}
		
		}
		CashOutPopupWidget.template = 'CashOutPopupWidget';
		CashOutPopupWidget.defaultProps = {
			body:''
		};
	
		Registries.Component.add(CashOutPopupWidget);
	
	
		return CashOutPopupWidget;
	
	
	
	
	
	
	
	
	
	
	
	
	
	
		
	});