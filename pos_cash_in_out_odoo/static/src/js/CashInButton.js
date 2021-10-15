odoo.define('pos_cash_in_out_odoo.CashInButton', function(require) {
	"use strict";

	const PosComponent = require('point_of_sale.PosComponent');
	const ProductScreen = require('point_of_sale.ProductScreen');
	const { useListener } = require('web.custom_hooks');
	const Registries = require('point_of_sale.Registries');

	class CashInButton extends PosComponent {
		constructor() {
			super(...arguments);
			useListener('click', this.onClick);
		}
		async onClick() {
			this.showPopup('CashInPopup', {});
		}
	}
	CashInButton.template = 'CashInButton';

	ProductScreen.addControlButton({
		component: CashInButton,
		condition: function() {
			return this.env.pos.config.is_cash_in_out;
		},
	});

	Registries.Component.add(CashInButton);
	return CashInButton;

});
