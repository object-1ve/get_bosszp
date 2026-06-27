// src/interceptor.js — XHR / Fetch 拦截
// 拦截 job/detail.json 并缓存到 Storage

(function () {
    const { Storage, sleep, STORAGE_KEY } = window.__boss__;

    function isDetailUrl(url) {
        return url.includes('job/detail.json');
    }

    async function saveToCache(data) {
        const items = JSON.parse(await Storage.get(STORAGE_KEY, '[]'));
        const eid = data?.zpData?.jobInfo?.encryptId;
        if (eid && items.some(it => it.data?.zpData?.jobInfo?.encryptId === eid)) {
            return;
        }
        items.push({ timestamp: Date.now(), data });
        await Storage.set(STORAGE_KEY, items);
        // updateBadge 在 ui.js 中定义，这里安全调用
        if (window.__boss__.updateBadge) window.__boss__.updateBadge();
        console.log(`[Boss拦截] detail 已缓存，当前 ${items.length} 条`);
    }

    // --- XHR 拦截 ---
    const _xhrOpen = XMLHttpRequest.prototype.open;
    const _xhrSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
        this._bosszpUrl = url;
        return _xhrOpen.call(this, method, url, ...rest);
    };
    XMLHttpRequest.prototype.send = function (...args) {
        this.addEventListener('load', function () {
            try {
                const url = this._bosszpUrl || '';
                if (isDetailUrl(url)) {
                    saveToCache(JSON.parse(this.responseText));
                }
            } catch (e) { /* 非 JSON 忽略 */ }
        });
        return _xhrSend.call(this, ...args);
    };

    // --- Fetch 拦截 ---
    const _fetch = window.fetch;
    window.fetch = function (input, init) {
        const url = typeof input === 'string' ? input : input?.url || '';
        return _fetch.call(this, input, init).then(response => {
            if (isDetailUrl(url)) {
                response.clone().text().then(text => {
                    try {
                        saveToCache(JSON.parse(text));
                    } catch (e) { /* 忽略 */ }
                });
            }
            return response;
        });
    };

    window.__boss__.saveToCache = saveToCache;
})();
