odoo.define('pos_lock_price_discount.lock_price_backspace', function(require) {
    'use strict';

    const { Component } = owl;
    const { EventBus } = owl.core;
    const { Gui } = require('point_of_sale.Gui');

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');


    const ExtendProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                            super(...arguments);
                        }
            async _updateSelectedOrderline(event) {
                            console.log("#### _updateSelectedOrderline >>>>> ");
                            console.log("#### event >>>>> ",event);
                            console.log("#### event.detail >>>>> ",event.detail);
                            console.log("#### this.state.numpadMode >>>>> ",this.state.numpadMode);
                            var event_detail_key = event.detail.key;
                            console.log("#### event_detail_key >>>>> ", event_detail_key);

                            if (event_detail_key === 'Backspace' && this.state.numpadMode === 'quantity') {
                                var lock_delete = this.env.pos.config.lock_delete;
                                var supervisor_pin =  this.env.pos.config.supervisor_pin;
                                console.log("### Lanzar Contraseña >>>>> ");
                                console.log("### lock_delete >>>>> ", lock_delete);
                                /*console.log("### supervisor_pin >>>>> ", supervisor_pin);*/
                                if (this.env.pos.config.lock_delete == true) {
                                    let currentQuantity = this.env.pos.get_order().get_selected_orderline().get_quantity();
                                    console.log("##### currentQuantity >>>>>>>> ", currentQuantity);
                                    if (currentQuantity <= 0.0){
                                        super._updateSelectedOrderline(event);
                                        return;
                                    } else {
                                        /*self.gui.show_popup('insert_pin_password', {*/
                                        const { confirmed, payload: inputPin } = await this.showPopup('NumberPopup', {
                                            isPassword: true,
                                            title: this.env._t('Password ?'),
                                            startingValue: null,
                                        });
                                        /*console.log("#### inputPin >>>>>>>>> ", inputPin);*/
                                        if (this.env.pos.config.enable_supervisor){
                                                if (inputPin !== this.env.pos.config.supervisor_pin) {
                                                    console.log("## Contraseña de Supervisor Incorrecta.");
                                                    if (inputPin !== this.env.pos.config.delete_password) {
                                                            await this.showPopup('ErrorPopup', {
                                                                title: this.env._t('Contraseña incorrecta'),
                                                            });
                                                            return false;
                                                        } else {
                                                            console.log("#### access granted 00 >>>>>>>>> ");
                                                            super._updateSelectedOrderline(event);
                                                            return ;
                                                        }

                                                } else {
                                                    console.log("#### access granted 01 >>>>>>>>> ");
                                                    super._updateSelectedOrderline(event);
                                                    return ;
                                                }
                                            }
                                            if (inputPin !== this.env.pos.config.delete_password) {
                                                await this.showPopup('ErrorPopup', {
                                                    title: this.env._t('Contraseña incorrecta'),
                                                });
                                                return false;
                                            } else {
                                                console.log("#### access granted 02 >>>>>>>>>");
                                                super._updateSelectedOrderline(event);
                                                return ;
                                            }
                                    }
                                    
                                } else {
                                    console.log("#### no tiene habilitado el bloqueo de eliminacion >>>>>>>>> ");
                                    super._updateSelectedOrderline(event);
                                    return ;
                                }

                            }
                            console.log("#### no es accion de eliminar cantidad >>>>>>>>> ");
                            super._updateSelectedOrderline(event);
                            return ;
                        }

        }

    Registries.Component.extend(ProductScreen, ExtendProductScreen);

    return ExtendProductScreen;

});
