odoo.define('bi_pos_stock.pos', function(require) {
	"use strict";

	const models = require('point_of_sale.models');

	models.load_fields('res.company', ['point_of_sale_update_stock_quantities'])

	models.load_fields('product.product', ['type','virtual_available',
		'available_quantity','qty_available','incoming_qty','outgoing_qty']);

	models.load_models({
		model: 'stock.location',
		fields: [],
		loaded: function(self, locations){
			self.locations = locations[0];
			if (self.config.show_stock_location == 'specific')
			{
				for(let i = 0; i < locations.length; i++){
					if(locations[i].id === self.config.stock_location_id[0]){
						self.locations =  locations[i];
					}
				}
			}
		},
	});	

});
