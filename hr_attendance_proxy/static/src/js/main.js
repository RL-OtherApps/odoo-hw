odoo.define('hr_attendance_proxy.kiosk_mode', function (require) {
"use strict";


/*self.call('bus_service', 'addChannel', self._livechat.getUUID());
self.call('bus_service', 'startPolling');*/


require('bus.BusService');

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var Session = require('web.session');

var QWeb = core.qweb;

var OldKioskMode = require('hr_attendance.kiosk_mode');

// OldKioskMode.include({
/*    start: function () {
        var self = this;
        console.log('this:');
        console.log(this);
        console.log('_super:');
        console.log(this._super);
        
        
        return this._super.apply(this, arguments);

    },*/

    // _onBarcodeScanned: function(barcode) {
    //     var self = this;
    //     core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
    //     this._rpc({
    //             model: 'hr.employee',
    //             method: 'attendance_scan',
    //             args: [barcode, ],
    //         })
    //         .then(function (result) {
    //             if (result.action) {
    //                 self.do_action(result.action);
    //             } else if (result.warning) {
    //                 self.do_warn(result.warning);
    //                 core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
    //             }
    //         }, function () {
    //             core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
    //         });
    //},

    //~ start_clock: function() {
        //~ this.clock_start = setInterval(function() {this.$(".o_hr_attendance_clock").text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit', second:'2-digit'}));}, 500);
        //~ // First clock refresh before interval to avoid delay
        //~ this.$(".o_hr_attendance_clock").show().text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit', second:'2-digit'}));
    //~ },

    //~ destroy: function () {
        //~ core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        //~ clearInterval(this.clock_start);
        //~ clearInterval(this._interval);
        //~ this._super.apply(this, arguments);
    //~ },

    //~ _callServer: function () {
        //~ // Make a call to the database to avoid the auto close of the session
        //~ return ajax.rpc("/hr_attendance/kiosk_keepalive", {});
    //~ },

// });

//~ core.action_registry.add('hr_attendance_kiosk_mode', KioskMode);

return OldKioskMode;

});
