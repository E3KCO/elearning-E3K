odoo.define('e3k_psa.ExtendListController', function (require) {
"use strict";

var core = require('web.core');
var ListController = require('web.ListController');

var _t = core._t;

var ExtendListController = ListController.include({

    _toggleCreateButton: function () {

        if (this.$buttons) {
            var state = this.model.get(this.handle);
            var model = state.model;
            var createHidden = this.renderer.isEditable() && state.groupedBy.length && state.data.length;
            if (model === 'account.analytic.line' && !!createHidden){
                this.$buttons.find('.o_list_button_add').removeClass('o_hidden');
            } else {
                this.$buttons.find('.o_list_button_add').toggleClass('o_hidden', !!createHidden);
            }
        }
    },

});

return ExtendListController;

});
