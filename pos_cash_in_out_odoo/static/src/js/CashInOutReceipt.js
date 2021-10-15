odoo.define('pos_cash_in_out_odoo.CashInOutReceipt', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

	class CashInOutReceipt extends PosComponent {
		constructor() {
			super(...arguments);
		}
	}
	
	CashInOutReceipt.template = 'CashInOutReceipt';
	Registries.Component.add(CashInOutReceipt);
	return CashInOutReceipt;
});