// ==UserScript==
// @name         Boss直聘自动点击下一个职位
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  自动逐个点击职位卡片 + 拦截 job/detail.json 缓存并导出
// @match        *://www.zhipin.com/web/geek/jobs*
// @grant        GM_addStyle
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function () {
    'use strict';

    let isRunning = false;
    let processedCount = 0;
    const processedCardIds = new Set();

    const sleep = ms => new Promise(r => setTimeout(r, ms));

    // ============================================================
    // API 拦截 — 只拦截 job/detail.json，缓存到 GMStorage
    // ============================================================
    const STORAGE_KEY = 'boss_detail_cache';

    function saveToCache(data) {
        const items = JSON.parse(GM_getValue(STORAGE_KEY, '[]'));
        // 按 encryptId 去重
        const eid = data?.zpData?.jobInfo?.encryptId;
        if (eid && items.some(it => it.data?.zpData?.jobInfo?.encryptId === eid)) {
            return;
        }
        items.push({ timestamp: Date.now(), data });
        GM_setValue(STORAGE_KEY, JSON.stringify(items));
        updateBadge();
        console.log(`[Boss拦截] detail 已缓存，当前 ${items.length} 条`);
    }

    function isDetailUrl(url) {
        return url.includes('job/detail.json');
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

    // ============================================================
    // 样式
    // ============================================================
    GM_addStyle(`
        #boss-auto-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 99999;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: all 0.3s;
            color: #fff;
            background: #00d7c6;
        }
        #boss-auto-btn:hover { transform: scale(1.05); }
        #boss-auto-btn.running { background: #ff4d4f; }
        #boss-auto-status {
            position: fixed;
            bottom: 80px;
            right: 30px;
            z-index: 99999;
            background: rgba(0,0,0,0.75);
            color: #fff;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
            pointer-events: none;
        }
        #boss-export-btn {
            position: fixed;
            bottom: 30px;
            left: 30px;
            z-index: 99999;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            color: #fff;
            background: #1890ff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            transition: all 0.2s;
        }
        #boss-export-btn:hover { transform: scale(1.05); }
        #boss-cache-badge {
            position: fixed;
            bottom: 74px;
            left: 30px;
            z-index: 99999;
            background: rgba(0,0,0,0.75);
            color: #fff;
            padding: 4px 12px;
            border-radius: 10px;
            font-size: 12px;
            pointer-events: none;
        }
        #boss-clear-btn {
            position: fixed;
            bottom: 30px;
            left: 160px;
            z-index: 99999;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            color: #fff;
            background: #ff4d4f;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            transition: all 0.2s;
        }
        #boss-clear-btn:hover { transform: scale(1.05); }
    `);

    // ============================================================
    // UI
    // ============================================================

    // --- 自动点击按钮 ---
    const btn = document.createElement('button');
    btn.id = 'boss-auto-btn';
    btn.textContent = '▶ 开始自动点击';

    const status = document.createElement('div');
    status.id = 'boss-auto-status';
    status.style.display = 'none';

    document.body.appendChild(btn);
    document.body.appendChild(status);

    function updateStatus(msg) {
        status.textContent = msg;
    }

    // --- 导出按钮 + 清空按钮 + 缓存计数 ---
    const exportBtn = document.createElement('button');
    exportBtn.id = 'boss-export-btn';
    exportBtn.textContent = '📦 导出JSON';

    const clearBtn = document.createElement('button');
    clearBtn.id = 'boss-clear-btn';
    clearBtn.textContent = '🗑 清空缓存';

    const cacheBadge = document.createElement('div');
    cacheBadge.id = 'boss-cache-badge';

    document.body.appendChild(exportBtn);
    document.body.appendChild(clearBtn);
    document.body.appendChild(cacheBadge);

    function updateBadge() {
        const items = JSON.parse(GM_getValue(STORAGE_KEY, '[]'));
        cacheBadge.textContent = `缓存: ${items.length} 条`;
    }
    updateBadge();

    exportBtn.addEventListener('click', () => {
        const items = JSON.parse(GM_getValue(STORAGE_KEY, '[]'));
        if (items.length === 0) {
            alert('暂无缓存数据');
            return;
        }
        // 只导出 data 字段，合并为一个数组
        const exportData = items.map(it => it.data);
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'detail.json';
        a.click();
        URL.revokeObjectURL(a.href);
        // 导出后自动清空缓存
        GM_setValue(STORAGE_KEY, '[]');
        updateBadge();
        console.log(`[Boss导出] 已导出 ${items.length} 条并清空缓存`);
    });

    clearBtn.addEventListener('click', () => {
        const items = JSON.parse(GM_getValue(STORAGE_KEY, '[]'));
        if (items.length === 0) {
            alert('暂无缓存数据');
            return;
        }
        if (!confirm(`确定要清空 ${items.length} 条缓存数据吗？`)) return;
        GM_setValue(STORAGE_KEY, '[]');
        updateBadge();
        console.log(`[Boss清空] 已清空 ${items.length} 条缓存`);
    });

    // ============================================================
    // 核心：滚动加载 + 逐个点击职位（无限滚动模式）
    // ============================================================

    // 等待新卡片加载（检测列表数量变化或 loading 消失）
    async function waitForNewCards(prevCount, maxWait = 10000) {
        const list = document.querySelector('.rec-job-list');
        if (!list) return false;
        const step = 500;
        let waited = 0;
        while (waited < maxWait) {
            await sleep(step);
            waited += step;
            const curCount = document.querySelectorAll('.job-card-box').length;
            if (curCount > prevCount) return true;
            // loading 指示器消失且数量没变 → 到底了
            const loading = document.querySelector('.loading-wait');
            if (loading && loading.style.display === 'none' && waited > 2000) return false;
        }
        return false;
    }

    // 滚动到底部触发加载
    function scrollToBottom() {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }

    async function clickNextJob() {
        let noNewRound = 0;       // 连续未加载到新卡片的轮数
        const MAX_EMPTY_ROUNDS = 3; // 连续3次没新卡就结束

        while (isRunning) {
            const jobCards = document.querySelectorAll('.job-card-box');
            const prevCount = jobCards.length;

            // 处理当前所有未处理的卡片
            for (let i = 0; i < jobCards.length; i++) {
                if (!isRunning) return;

                const card = jobCards[i];
                const cardId = card.getAttribute('data-jobid') || card.innerText.substring(0, 50);

                if (processedCardIds.has(cardId)) continue;
                processedCardIds.add(cardId);

                const jobName = card.querySelector('.job-name')?.innerText || '未知职位';
                const companyName = card.querySelector('.boss-name')?.innerText || '未知公司';
                const exp = card.querySelector('.tag-list li')?.innerText || '';

                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await sleep(500);
                card.click();

                processedCount++;
                updateStatus(`已点击: ${companyName} - ${jobName} (${processedCount})`);
                console.log(`[Boss自动点击] ${processedCount}. ${companyName} | ${jobName} | ${exp}`);

                await sleep(2000);
            }

            if (!isRunning) return;

            // 检查是否所有卡片都已处理
            const allProcessed = [...document.querySelectorAll('.job-card-box')].every(card => {
                const id = card.getAttribute('data-jobid') || card.innerText.substring(0, 50);
                return processedCardIds.has(id);
            });

            if (allProcessed) {
                // 滚动到底部触发加载下一批
                updateStatus(`已处理 ${processedCount} 个，正在加载更多...`);
                scrollToBottom();
                await sleep(1500); // 等待网络请求

                const loaded = await waitForNewCards(prevCount);
                if (!loaded) {
                    noNewRound++;
                    if (noNewRound >= MAX_EMPTY_ROUNDS) {
                        updateStatus(`全部处理完毕，共 ${processedCount} 个`);
                        toggleRunning();
                        return;
                    }
                    // 再试一次滚动（可能没触发）
                    scrollToBottom();
                    await sleep(2000);
                } else {
                    noNewRound = 0;
                }
            }
        }
    }

    // ============================================================
    // 启动/停止
    // ============================================================
    function toggleRunning() {
        isRunning = !isRunning;
        if (isRunning) {
            btn.textContent = '■ 停止点击';
            btn.classList.add('running');
            status.style.display = 'block';
            updateStatus('运行中...');
            clickNextJob();
        } else {
            btn.textContent = '▶ 开始自动点击';
            btn.classList.remove('running');
            updateStatus(`已停止，共处理 ${processedCount} 个`);
            setTimeout(() => { status.style.display = 'none'; }, 3000);
        }
    }

    btn.addEventListener('click', toggleRunning);

})();
