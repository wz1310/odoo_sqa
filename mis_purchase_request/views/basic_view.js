odoo.define('mis_purchase_request.BasicView', function (require) {
"use strict";
var session = require('web.session');
var BasicView = require('web.BasicView');
BasicView.include({
	init: function(viewInfo, params) {
		var self = this;
		this._super.apply(this, arguments);
		var model = self.controllerParams.modelName in ['purchase.request'] ? 'True' : 'False';
	if(model) {
		session.user_has_group('base.group_erp_manager').then(function(has_group) {
			if(!has_group) {
				self.controllerParams.hasSidebar = 'False' in viewInfo.fields;
					}
				});
			}
		},
	});
});