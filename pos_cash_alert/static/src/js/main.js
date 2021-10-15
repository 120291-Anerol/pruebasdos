/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_cash_alert.pos_cash_alert', function (require) {
"use strict";
	var pos_model = require('point_of_sale.models');
	var rpc = require('web.rpc')
	var core = require('web.core');
	var _t = core._t;
	const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');

	pos_model.load_fields('pos.session','cash_register_difference');

    var PosResReceiptScreen = ReceiptScreen =>
        class extends ReceiptScreen {
            mounted() {
				var self = this;
				super.mounted();
				if(self.env.pos.config.cash_threshold != 0){
					setTimeout(function(){
						rpc.query({
							model:'pos.session',
							method:'get_cash_register_difference',
							args:[self.env.pos.pos_session.id]
						})
						.then(function(cash_register_difference){
							self.env.pos.cash_register_difference = cash_register_difference;
							if(self.env.pos.config.cash_threshold - Math.abs(cash_register_difference)<=0)
								self.showPopup('CashPopupWidget',{});
						})
					}, 100);
				}
			}	
	}

	Registries.Component.extend(ReceiptScreen, PosResReceiptScreen);

	Registries.Component.freeze();
	return ReceiptScreen;
});
