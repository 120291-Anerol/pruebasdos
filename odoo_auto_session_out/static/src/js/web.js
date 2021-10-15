odoo.define('odoo_auto_session_out.Logout', function (require) {
    "use strict";

    var rpc = require('web.rpc');
    var session = require('web.session');

    rpc.query({
        model: 'res.company',
        method: 'read',
        args: [[session.company_id], ['session_time_out']],
    }).then(function (result) {
        if (result) {
            var logout_timeout = result[0]['session_time_out'] * 1000
            var timeout = setTimeout(function () {
                window.location.href = "/web/session/logout?redirect=/";
            }, logout_timeout);

            $(document).off('mousemove').on('mousemove', function () {
                if (timeout !== null) {
                    clearTimeout(timeout);
                }
                timeout = setTimeout(function () {
                    window.location.href = "/web/session/logout?redirect=/";
                }, logout_timeout);
            });
        }
    });
});
