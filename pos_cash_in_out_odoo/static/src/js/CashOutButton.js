odoo.define('pos_cash_in_out_odoo.CashOutButton', function(require) {
	"use strict";

	const PosComponent = require('point_of_sale.PosComponent');
	const ProductScreen = require('point_of_sale.ProductScreen');
	const { useListener } = require('web.custom_hooks');
	const Registries = require('point_of_sale.Registries');

	class CashOutButton extends PosComponent {
		constructor() {
			super(...arguments);
			useListener('click', this.onClick);
		}
		async onClick() {
			this.showPopup('CashOutPopup', {});
		}
	}
	CashOutButton.template = 'CashOutButton';

	ProductScreen.addControlButton({
		component: CashOutButton,
		condition: function() {
			return this.env.pos.config.is_cash_in_out;
		},
	});

	Registries.Component.add(CashOutButton);
	return CashOutButton;

});
