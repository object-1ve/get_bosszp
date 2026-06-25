/**
 * boss-traceid v0.1.2
 * Copyright Â©2024 KanZhun. All rights reserved.
 * 2024-08-05 16:58:47
 */

!function (e) {
    "use strict"; var n = function () {
        var e = function () {
            for (var e = Date.now().toString(16), n = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", t = "", o = 0; o < 10; o++)t += n[Math.floor(62 * Math.random())]; return "".concat(e.slice(-6)).concat(t)
        }(); return "F-".concat(e)
    }, t = function (e) { var n = e.slice(2, 8), t = parseInt(n, 16), o = Date.now(), r = o.toString(16).slice(-6), a = o - parseInt(r, 16); return new Date(a + t) }; "undefined" != typeof window && "undefined" != typeof document && (window.generateBossTraceID = n, window.getTimeFromBossTraceID = t), e.generateBossTraceID = n, e.getTimeFromBossTraceID = t, Object.defineProperty(e, "__esModule", { value: !0 })
}({});
