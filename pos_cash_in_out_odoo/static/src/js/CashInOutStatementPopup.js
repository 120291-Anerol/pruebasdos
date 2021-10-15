odoo.define('pos_cash_in_out_odoo.CashInOutStatementPopup', function(require){
	'use strict';

	const Popup = require('point_of_sale.ConfirmPopup');
	const Registries = require('point_of_sale.Registries');
	const PosComponent = require('point_of_sale.PosComponent');


	class CashInOutStatementPopup extends Popup {

		constructor() {
            super(...arguments);            
        }

		cancel() {
			this.trigger('close-popup');
		}

		mounted(){
			$('#statement_error').hide();
		}

		print_cash_in_out_statement(){
			let self = this;
			let stmt_st_date = $('#stmt_st_date').val();
			let stmt_end_date = $('#stmt_end_date').val();
			let selected_cashier = $('#cashier').val();
			if(stmt_st_date == false){
				$('#statement_error').text('Please Enter Start Date')
				$('#statement_error').show()
				setTimeout(function() {$('#statement_error').hide()},3000);
				return;
			}
			else if(stmt_end_date == false){
				$('#statement_error').text('Please Enter End Date')
				$('#statement_error').show()
				setTimeout(function() {$('#statement_error').hide()},3000);
				return;
			}
			else{
				this.rpc({
					model: 'pos.cash.in.out',
					method: 'get_statement_data',
					args: [1, stmt_st_date, stmt_end_date,selected_cashier],
				}).then(function(output){
					self.showTempScreen('StatementReportScreen',{
						statement_data:output,
						stmt_st_date:stmt_st_date,
						stmt_end_date:stmt_end_date,
					});
					self.trigger('close-popup')
				});
			}

		}
	};
	
	CashInOutStatementPopup.template = 'CashInOutStatementPopup';

	Registries.Component.add(CashInOutStatementPopup);

	return CashInOutStatementPopup;

});