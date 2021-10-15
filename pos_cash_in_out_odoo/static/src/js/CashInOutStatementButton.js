odoo.define('pos_cash_in_out_odoo.CashInOutStatementButton', function(require) {
	"use strict";

	const PosComponent = require('point_of_sale.PosComponent');
	const ProductScreen = require('point_of_sale.ProductScreen');
	const { useListener } = require('web.custom_hooks');
	const Registries = require('point_of_sale.Registries');

	class CashInOutStatementButton extends PosComponent {
		constructor() {
			super(...arguments);
			useListener('click', this.onClick);
		}
		async onClick() {
			this.showPopup('CashInOutStatementPopup', {});
		}
	}
	CashInOutStatementButton.template = 'CashInOutStatementButton';

	ProductScreen.addControlButton({
		component: CashInOutStatementButton,
		condition: function() {
			return this.env.pos.config.is_print_statement;
		},
	});

	Registries.Component.add(CashInOutStatementButton);
	return CashInOutStatementButton;

});
