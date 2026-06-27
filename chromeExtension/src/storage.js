// src/storage.js — Storage 包装层 (chrome.storage.local)
// 所有文件通过 window.__boss__.Storage 访问

window.__boss__ = window.__boss__ || {};

window.__boss__.Storage = {
    async set(key, value) {
        await chrome.storage.local.set({ [key]: JSON.stringify(value) });
    },
    async get(key, defaultValue) {
        const result = await chrome.storage.local.get(key);
        if (result[key] === undefined) return defaultValue;
        try { return JSON.parse(result[key]); } catch { return result[key]; }
    }
};

window.__boss__.notify = function (title, text) {
    try {
        chrome.runtime.sendMessage({ type: 'notify', title, text });
    } catch (e) {
        console.warn('[Boss] 通知失败:', e);
    }
};

window.__boss__.sleep = ms => new Promise(r => setTimeout(r, ms));

window.__boss__.STORAGE_KEY = 'boss_detail_cache';
