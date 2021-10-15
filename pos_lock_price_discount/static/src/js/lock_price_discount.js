// pos_global_discounts_pricelist js
//console.log("HOLA MUNDO >>>>> ")
odoo.define('pos_lock_price_discount.lock_price_discount', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    //var screens = require('point_of_sale.screens');
    var core = require('web.core');
    const { Gui } = require('point_of_sale.Gui');
    //var popups = require('point_of_sale.popups');
    var QWeb = core.qweb;
    //var posdiscount = require('pos_discount.pos_discount');

   /* const NumpadWidget = require('point_of_sale.NumpadWidget');*/
    const ProductScreen = require('point_of_sale.ProductScreen');
    var _super_product = models.Product.prototype;

    var _t = core._t;

    console.log("HOLA MUNDO >>>>> ")

    const { Component } = owl;


    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    /**
     * @prop {'quantiy' | 'price' | 'discount'} activeMode
     * @event set-numpad-mode - triggered when mode button is clicked
     * @event numpad-click-input - triggered when numpad button is clicked
     *
     * IMPROVEMENT: Whenever new-orderline-selected is triggered,
     * numpad mode should be set to 'quantity'. Now that the mode state
     * is lifted to the parent component, this improvement can be done in
     * the parent component.
     */
    class NumpadWidget extends PosComponent {
        mounted() {
            // IMPROVEMENT: This listener shouldn't be here because in core point_of_sale
            // there is no way of changing the cashier. Only when pos_hr is installed
            // that this listener makes sense.
            console.log("### this.props >>>> ", this.props);
            this.trigger('set-numpad-mode', { mode: null });
            this.env.pos.on('change:cashier', () => {
                if (!this.hasPriceControlRights && this.props.activeMode === 'price') {
                    this.trigger('set-numpad-mode', { mode: 'quantity' });
                }
            });
        }
        willUnmount() {
            this.env.pos.on('change:cashier', null, this);
        }
        get hasPriceControlRights() {
            const cashier = this.env.pos.get('cashier') || this.env.pos.get_cashier();
            return !this.env.pos.config.restrict_price_control || cashier.role == 'manager';
        }
        get hasManualDiscount() {
            return this.env.pos.config.manual_discount;
        }

        async changeMode(mode) {
            console.log("#### CHANGE MODE >>>>>>>>>> ");
            console.log("#### mode >>>>>>>>>> ", mode);
            console.log("### event >>>> ",event);
            console.log("### this.props.activeMode >>>> ",this.props.activeMode);
            var self = this;
            console.log("::::::: self >>> ", self);
            console.log("### this.env.pos.config.lock_discount >>>>> ", this.env.pos.config.lock_discount);
            if (mode === 'price') {
                if (this.env.pos.config.lock_price == true) {
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
                                if (inputPin !== this.env.pos.config.price_password) {
                                        await this.showPopup('ErrorPopup', {
                                            title: this.env._t('Contraseña incorrecta'),
                                        });
                                        return false;
                                    } else {
                                        this.trigger('set-numpad-mode', { mode });
                                    }

                            } else {
                                this.trigger('set-numpad-mode', { mode });
                            }
                        }
                        if (inputPin !== this.env.pos.config.price_password) {
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Contraseña incorrecta'),
                            });
                            return false;
                        } else {
                            this.trigger('set-numpad-mode', { mode });
                        }

                } else {
                    this.trigger('set-numpad-mode', { mode });
                }
            }

            if (mode === 'quantity') {
                if (this.env.pos.config.lock_quantity == true) {
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
                                if (inputPin !== this.env.pos.config.quantity_password) {
                                        await this.showPopup('ErrorPopup', {
                                            title: this.env._t('Contraseña incorrecta'),
                                        });
                                        return false;
                                    } else {
                                        this.trigger('set-numpad-mode', { mode });
                                    }

                            } else {
                                this.trigger('set-numpad-mode', { mode });
                            }
                        }
                        if (inputPin !== this.env.pos.config.quantity_password) {
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Contraseña incorrecta'),
                            });
                            return false;
                        } else {
                            this.trigger('set-numpad-mode', { mode });
                        }

                } else {
                    this.trigger('set-numpad-mode', { mode });
                }
            }

            if (mode === 'discount') {
                if (this.env.pos.config.lock_discount == true) {
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
                                if (inputPin !== this.env.pos.config.discount_password) {
                                        await this.showPopup('ErrorPopup', {
                                            title: this.env._t('Contraseña incorrecta'),
                                        });
                                        return false;
                                    } else {
                                        this.trigger('set-numpad-mode', { mode });
                                    }

                            } else {
                                this.trigger('set-numpad-mode', { mode });
                            }
                        }
                        if (inputPin !== this.env.pos.config.discount_password) {
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Contraseña incorrecta'),
                            });
                            return false;
                        } else {
                            this.trigger('set-numpad-mode', { mode });
                        }

                } else {
                    this.trigger('set-numpad-mode', { mode });
                }
            }

            if (!this.hasManualDiscount && mode === 'discount') {
                if (this.env.pos.config.lock_discount == true) {
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
                                if (inputPin !== this.env.pos.config.discount_password) {
                                        await this.showPopup('ErrorPopup', {
                                            title: this.env._t('Contraseña incorrecta'),
                                        });
                                        return false;
                                    } else {
                                        this.trigger('set-numpad-mode', { mode });
                                    }

                            } else {
                                this.trigger('set-numpad-mode', { mode });
                            }
                        }
                        if (inputPin !== this.env.pos.config.discount_password) {
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Contraseña incorrecta'),
                            });
                            return false;
                        } else {
                            this.trigger('set-numpad-mode', { mode });
                        }

                } else {
                    this.trigger('set-numpad-mode', { mode });
                }
            }
            this.trigger('set-numpad-mode', { mode });
        }
        sendInput(key) {
            this.trigger('numpad-click-input', { key });
        }
        get decimalSeparator() {
            return this.env._t.database.parameters.decimal_point;
        }
    }
    NumpadWidget.template = 'NumpadWidget';

    Registries.Component.add(NumpadWidget);

    return NumpadWidget;


});
