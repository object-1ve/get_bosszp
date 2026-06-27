// background.js — Service Worker
chrome.runtime.onInstalled.addListener(() => {
  console.log('[Boss自动点击] 扩展已安装');
});

// 监听来自 content script 的通知请求
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'notify') {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon128.png',
      title: msg.title || 'Boss自动点击',
      message: msg.text || ''
    });
  }
});
