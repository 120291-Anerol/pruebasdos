odoo.define('pos_cash_in_out_odoo.CashOutPopup', function(require){
	'use strict';

	const Popup = require('point_of_sale.ConfirmPopup');
	const Registries = require('point_of_sale.Registries');
	const PosComponent = require('point_of_sale.PosComponent');
	let redeem;
	let point_value = 0;
	let remove_line;
	let remove_true = false;
	let entered_code;

	class CashOutPopup extends Popup {

		constructor() {
			super(...arguments);
		}

		cancel() {
			this.trigger('close-popup');
		}

		mounted(){
			$('#error1').hide();
		}

		save_summary_details(operation, entered_reason, entered_amount){
			let self = this;
			this.trigger('close-popup');
			self.showTempScreen('CashInOutReceiptScreen',{ 
				operation:operation,
				purpose:entered_reason,
				amount:entered_amount
			});
		}

		cash_out() {
			let self = this;
			let order = this.env.pos.get_order();
			let user = self.env.pos.user;
			let entered_reason = $("#reason").val();
			let entered_amount = $("#amount").val();
			let session_id = self.env.pos.pos_session.id;

			if(entered_amount == '')
			{
				$("#error1").text("Please enter amount.");
				$('#error1').show();
				setTimeout(function() {$('#error1').hide()},2000);
				return;
			}
			else if(entered_reason == '')
			{
				$("#error1").text("Please enter reason.");
				$('#error1').show();
				setTimeout(function() {$('#error1').hide()},2000);
				return;
			}
			else{
				this.rpc({
					model: 'cash.box.out',
					method: 'create_cash_out',
					args: [0,user.id, entered_reason, entered_amount, session_id],

				}).then(function(output) {
					if (output == true){
						self.save_summary_details('Take Money Out', entered_reason,entered_amount)
					} else {
						self.showPopup('ErrorPopup', {
							'title': this.env._t('No Cash Register'),
							'body': this.env._t('There is no cash register for this PoS Session'),
						});
					}					
				});		
			}
		}
	};
	
	CashOutPopup.template = 'CashOutPopup';

	Registries.Component.add(CashOutPopup);

	return CashOutPopup;

});