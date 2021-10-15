odoo.define('wv_pos_create_so.wv_pos_create_so', function (require) {
"use strict";

	const models = require('point_of_sale.models');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const { useState, useRef } = owl.hooks;


    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this,arguments);
            this.wv_note = "";
            this.order_ref = "";
            this.save_to_db();
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.wv_note = this.wv_note;
            return json;
        },
        export_for_printing:function() {
            var json = _super_order.export_for_printing.apply(this,arguments);
            json.wv_note = this.wv_note;
            json.order_ref = this.order_ref;
            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            this.wv_note = json.wv_note;
            this.order_ref = json.order_ref;
        },
    });

    class CreateSaleOrderButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            var self = this;
            await this.showPopup('CreateSaleOrderPopupWidget');
            
        }
        
    }
    CreateSaleOrderButton.template = 'CreateSaleOrderButton';

    ProductScreen.addControlButton({
        component: CreateSaleOrderButton,
        condition: function() {
            return this.env.pos.config.allow_create_sale_order;
        },
    });

    Registries.Component.add(CreateSaleOrderButton);


    class CreateSaleOrderPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ inputValue: this.props.startingValue });
            this.inputRef = useRef('input');
            this.changes = {};
        }

        getPayload() {
            return this.state.inputValue;
        }

        async captureChange(event) {
            var order =this.env.pos.get('selectedOrder');
            if(order.get_client() != null){
                 order.wv_note = $(".wv_note").val();
                 // await this.save_order();

                  await this.save_order();
                 await this.trigger('close-popup');

            }
            else{
             alert("Customer is required for sale order. Please select customer first !!!!");
            }
            // this.cancel();
        }

        async print_quotation_bill(event) {
            var order =this.env.pos.get('selectedOrder');
            if(order.get_client() != null){
                 order.wv_note = $(".wv_note").val();
                 // await this.save_order();
                await this.save_order2();
                await this.trigger('close-popup');
                await this.showTempScreen('SaleOrderBillScreenWidget');


            }
            else{
             alert("Customer is required for sale order. Please select customer first !!!!");
            }
            // this.cancel();
        }
        save_order(){
         var self = this;
         var order = self.env.pos.get_order();
         var data = order.export_as_JSON();

        return  self.rpc({
                  model: 'sale.order',
                  method: 'create_new_quotation',
                  args: [data],
              }).then(function (quotation_data) {
                  order.finalize();
                  alert("Order Created "+quotation_data['result']);
                  // resolve();
              });
        }
        save_order2(){
         var self = this;
         var order = self.env.pos.get_order();
         var data = order.export_as_JSON();

        return  self.rpc({
                  model: 'sale.order',
                  method: 'create_new_quotation',
                  args: [data],
              }).then(function (quotation_data) {

                    order.order_ref = quotation_data['result'];
                  // order.finalize();
                  // alert("Order Created "+quotation_data['result']);
                  // resolve();
              });
        }

    }
    CreateSaleOrderPopupWidget.template = 'CreateSaleOrderPopupWidget';
    Registries.Component.add(CreateSaleOrderPopupWidget);
    CreateSaleOrderPopupWidget.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'Create SaleOrder',
        body: '',
    };

    const SaleOrderBillScreenWidget = (ReceiptScreen) => {
        class SaleOrderBillScreenWidget extends ReceiptScreen {
            confirm() {
                var order = this.env.pos.get_order();
                order.finalize();
                this.props.resolve({ confirmed: true, payload: null });
                this.trigger('close-temp-screen');
            }
        }
        SaleOrderBillScreenWidget.template = 'SaleOrderBillScreenWidget';
        return SaleOrderBillScreenWidget;
    };

    Registries.Component.addByExtending(SaleOrderBillScreenWidget, ReceiptScreen);
});
