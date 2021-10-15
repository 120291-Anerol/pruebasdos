odoo.define('pos_cash_in_out_odoo.StatementSummaryReceipt', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

	class StatementSummaryReceipt extends PosComponent {
		constructor() {
			super(...arguments);
		}
	}

	StatementSummaryReceipt.template = 'StatementSummaryReceipt';
	Registries.Component.add(StatementSummaryReceipt);
	return StatementSummaryReceipt;
});