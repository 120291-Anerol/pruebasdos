/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_create_product.SuccessNotifyPopupWidget', function(require){
	"use strict";    
		const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
		const Registries = require('point_of_sale.Registries');
		class SuccessNotifyPopupWidget extends AbstractAwaitablePopup {
	
			mounted(){
				var self = this;
				$('.cash_out_status').show();
				$('.cash_out_status').removeClass('withdraw_done');
				$('.show_tick').hide();
				setTimeout(function(){
					$('.cash_out_status').addClass('withdraw_done');
					  $('.show_tick').show();
					$('.cash_out_status').css({'border-color':'#5cb85c'})
				},500)
				setTimeout(function(){
					self.cancel();
				},1500)
			}
		
		}
		SuccessNotifyPopupWidget.template = 'SuccessNotifyPopupWidget';
		SuccessNotifyPopupWidget.defaultProps = {
			body:''
		};
	
		Registries.Component.add(SuccessNotifyPopupWidget);
	
	
		return SuccessNotifyPopupWidget;
	
	
	
	
	
	
	
	
	
	
	
	
	
	
		
	});