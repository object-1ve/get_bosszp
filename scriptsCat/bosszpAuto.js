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
        #boss-auto-panel {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 99999;
            background: #fff;
            border: 1px solid #00d7c6;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            width: 320px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: height 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        #boss-auto-panel.collapsed { height: 42px !important; }
        #boss-auto-panel.collapsed .panel-body { display: none; }
        #panel-header {
            background: #00d7c6;
            color: white;
            padding: 10px 15px;
            cursor: move;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
            flex-shrink: 0;
        }
        #panel-header h3 { margin: 0; font-size: 16px; color: white; border: none; }
        #toggle-panel-btn {
            background: rgba(255,255,255,0.2);
            border: none; color: white;
            width: 24px; height: 24px;
            border-radius: 4px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 18px;
        }
        #toggle-panel-btn:hover { background: rgba(255,255,255,0.3); }
        .panel-body {
            padding: 12px;
            overflow-y: auto;
            flex-grow: 1;
        }
        .panel-body::-webkit-scrollbar { width: 4px; }
        .panel-body::-webkit-scrollbar-thumb { background: #00d7c6; border-radius: 2px; }
        .boss-panel-btn {
            width: 100%;
            padding: 8px;
            margin-bottom: 8px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
            flex-shrink: 0;
        }
        #start-btn { background: #00d7c6; color: white; }
        #start-btn:hover { background: #00b3a5; }
        #stop-btn { background: #ff4d4f; color: white; }
        #stop-btn:hover { background: #d9363e; }
        #export-btn { background: #1890ff; color: white; }
        #export-btn:hover { background: #40a9ff; }
        #clear-btn { background: #8c8c8c; color: white; }
        #clear-btn:hover { background: #595959; }
        .filter-section { margin-bottom: 10px; }
        .filter-section .info-label {
            color: #999; font-size: 11px; margin-bottom: 4px;
        }
        .filter-section input[type="text"] {
            width: 100%;
            padding: 5px;
            font-size: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .filter-section input[type="text"]:focus {
            border-color: #00d7c6;
            outline: none;
        }
        .toggle-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
            padding: 6px 8px;
            background: #f9f9f9;
            border-radius: 4px;
        }
        .toggle-row label {
            font-size: 13px;
            color: #333;
            cursor: pointer;
            flex: 1;
        }
        .toggle-switch {
            position: relative;
            width: 36px;
            height: 20px;
            flex-shrink: 0;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background: #ccc;
            border-radius: 20px;
            transition: 0.3s;
        }
        .toggle-slider:before {
            content: "";
            position: absolute;
            height: 16px; width: 16px;
            left: 2px; bottom: 2px;
            background: white;
            border-radius: 50%;
            transition: 0.3s;
        }
        .toggle-switch input:checked + .toggle-slider { background: #00d7c6; }
        .toggle-switch input:checked + .toggle-slider:before { transform: translateX(16px); }
        #status-info {
            font-size: 12px; color: #666;
            margin-top: 8px;
            border-top: 1px solid #eee;
            padding-top: 8px;
        }
        #boss-auto-status {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 99999;
            background: rgba(0,0,0,0.75);
            color: #fff;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
            pointer-events: none;
            white-space: nowrap;
        }
    `);

    // ============================================================
    // UI
    // ============================================================

    // --- 控制面板 ---
    const panel = document.createElement('div');
    panel.id = 'boss-auto-panel';
    panel.innerHTML = `
        <div id="panel-header">
            <h3>Boss 自动点击</h3>
            <button id="toggle-panel-btn">_</button>
        </div>
        <div class="panel-body">
            <button id="start-btn" class="boss-panel-btn">▶ 开始自动点击</button>
            <button id="stop-btn" class="boss-panel-btn" style="display:none;">■ 停止点击</button>

            <div class="toggle-row">
                <label for="greet-toggle">自动点击立即沟通</label>
                <div class="toggle-switch">
                    <input type="checkbox" id="greet-toggle">
                    <span class="toggle-slider"></span>
                </div>
            </div>

            <div class="filter-section">
                <div class="info-label">屏蔽公司关键词 (逗号分隔):</div>
                <input type="text" id="filter-input" placeholder="例如: 外包,某某公司,派遣">
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <button id="export-btn" class="boss-panel-btn">📦 导出JSON</button>
                <button id="clear-btn" class="boss-panel-btn">🗑 清空缓存</button>
            </div>
            <div id="cache-count" style="text-align:center; font-size:12px; color:#999; margin-bottom:8px;">缓存: 0 条</div>
            <div id="status-info">状态: 未运行 | 已处理: 0</div>
        </div>
    `;
    document.body.appendChild(panel);

    const status = document.createElement('div');
    status.id = 'boss-auto-status';
    status.style.display = 'none';
    document.body.appendChild(status);

    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const exportBtn = document.getElementById('export-btn');
    const clearBtn = document.getElementById('clear-btn');
    const greetToggle = document.getElementById('greet-toggle');
    const filterInput = document.getElementById('filter-input');
    const statusInfo = document.getElementById('status-info');
    const header = document.getElementById('panel-header');
    const togglePanelBtn = document.getElementById('toggle-panel-btn');

    function updateStatus(msg) {
        statusInfo.textContent = `状态: ${msg} | 已处理: ${processedCount}`;
    }

    function updateBadge() {
        const items = JSON.parse(GM_getValue(STORAGE_KEY, '[]'));
        document.getElementById('cache-count').textContent = `缓存: ${items.length} 条`;
    }
    updateBadge();

    // --- 面板折叠 ---
    togglePanelBtn.addEventListener('click', () => {
        const isCollapsed = panel.classList.toggle('collapsed');
        togglePanelBtn.innerText = isCollapsed ? '□' : '_';
    });

    // --- 面板拖动 ---
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    header.addEventListener('mousedown', (e) => {
        isDragging = true;
        dragOffset = { x: e.clientX - panel.offsetLeft, y: e.clientY - panel.offsetTop };
        e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        let left = e.clientX - dragOffset.x;
        let top = e.clientY - dragOffset.y;
        const maxLeft = window.innerWidth - panel.offsetWidth;
        const maxTop = window.innerHeight - (panel.classList.contains('collapsed') ? 42 : panel.offsetHeight);
        left = Math.max(0, Math.min(left, maxLeft));
        top = Math.max(0, Math.min(top, maxTop));
        panel.style.left = left + 'px';
        panel.style.top = top + 'px';
        panel.style.right = 'auto';
    });
    document.addEventListener('mouseup', () => { isDragging = false; });

    // --- 加载/保存 打招呼开关 ---
    greetToggle.checked = GM_getValue('boss_greet_enabled', false);
    greetToggle.addEventListener('change', () => {
        GM_setValue('boss_greet_enabled', greetToggle.checked);
        console.log(`[Boss] 自动打招呼: ${greetToggle.checked ? '开启' : '关闭'}`);
    });

    // --- 加载/保存 屏蔽关键词 ---
    filterInput.value = GM_getValue('boss_filter_keywords', '');
    filterInput.addEventListener('change', () => {
        GM_setValue('boss_filter_keywords', filterInput.value);
        console.log(`[Boss] 屏蔽关键词已更新: ${filterInput.value}`);
    });

    exportBtn.addEventListener('click', () => {
        const items = JSON.parse(GM_getValue(STORAGE_KEY, '[]'));
        if (items.length === 0) {
            alert('暂无缓存数据');
            return;
        }
        const exportData = items.map(it => it.data);
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'detail.json';
        a.click();
        URL.revokeObjectURL(a.href);
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
        let noNewRound = 0;
        const MAX_EMPTY_ROUNDS = 3;

        while (isRunning) {
            const jobCards = document.querySelectorAll('.job-card-box');
            const prevCount = jobCards.length;

            for (let i = 0; i < jobCards.length; i++) {
                if (!isRunning) return;

                const card = jobCards[i];
                const cardId = card.getAttribute('data-jobid') || card.innerText.substring(0, 50);

                if (processedCardIds.has(cardId)) continue;
                processedCardIds.add(cardId);

                const jobName = card.querySelector('.job-name')?.innerText || '未知职位';
                const companyName = card.querySelector('.company-name')?.innerText ||
                                    card.querySelector('.company-info a span')?.innerText ||
                                    card.querySelector('div:nth-of-type(2) > a > span')?.innerText || '未知公司';
                const exp = card.querySelector('.tag-list li')?.innerText || '';

                // --- 屏蔽公司关键词过滤 ---
                const filterKeywords = filterInput.value.split(/[,，]/).map(k => k.trim()).filter(k => k);
                let isFiltered = false;
                for (const keyword of filterKeywords) {
                    if (companyName.includes(keyword)) {
                        isFiltered = true;
                        break;
                    }
                }
                if (isFiltered) {
                    processedCount++;
                    updateStatus(`[已屏蔽] ${companyName} - ${jobName}`);
                    console.log(`[Boss屏蔽] ${processedCount}. ${companyName} | ${jobName} (命中关键词)`);
                    continue;
                }

                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await sleep(500);
                card.click();

                processedCount++;
                updateStatus(`已点击: ${companyName} - ${jobName} (${processedCount})`);
                console.log(`[Boss自动点击] ${processedCount}. ${companyName} | ${jobName} | ${exp}`);

                await sleep(2000);

                // --- 自动点击立即沟通（触发详情拦截） ---
                if (greetToggle.checked) {
                    try {
                        const greetBtn = document.querySelector('.op-btn.op-btn-chat');
                        if (greetBtn) {
                            greetBtn.click();
                            await sleep(1500);
                            const cancelBtn = document.querySelector('.cancel-btn');
                            if (cancelBtn) {
                                cancelBtn.click();
                                await sleep(1000);
                            }
                            console.log(`[Boss沟通] ${companyName} | ${jobName} - 已触发`);
                        }
                    } catch (e) {
                        console.warn('[Boss沟通] 出错:', e);
                    }
                }
            }

            if (!isRunning) return;

            const allProcessed = [...document.querySelectorAll('.job-card-box')].every(card => {
                const id = card.getAttribute('data-jobid') || card.innerText.substring(0, 50);
                return processedCardIds.has(id);
            });

            if (allProcessed) {
                updateStatus(`已处理 ${processedCount} 个，正在加载更多...`);
                scrollToBottom();
                await sleep(1500);

                const loaded = await waitForNewCards(prevCount);
                if (!loaded) {
                    noNewRound++;
                    if (noNewRound >= MAX_EMPTY_ROUNDS) {
                        updateStatus(`全部处理完毕，共 ${processedCount} 个`);
                        toggleRunning();
                        return;
                    }
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
            startBtn.style.display = 'none';
            stopBtn.style.display = 'block';
            updateStatus('运行中...');
            clickNextJob();
        } else {
            startBtn.style.display = 'block';
            stopBtn.style.display = 'none';
            updateStatus(`已停止，共处理 ${processedCount} 个`);
        }
    }

    startBtn.addEventListener('click', toggleRunning);
    stopBtn.addEventListener('click', toggleRunning);

})();
