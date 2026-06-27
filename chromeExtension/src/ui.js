// src/ui.js — 面板创建、事件绑定、拖动/折叠、导出/清空

(function () {
    const { Storage, STORAGE_KEY } = window.__boss__;

    // --- 创建面板 DOM ---
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

    const statusEl = document.createElement('div');
    statusEl.id = 'boss-auto-status';
    statusEl.style.display = 'none';
    document.body.appendChild(statusEl);

    // --- 获取 DOM 引用 ---
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const exportBtn = document.getElementById('export-btn');
    const clearBtn = document.getElementById('clear-btn');
    const greetToggle = document.getElementById('greet-toggle');
    const filterInput = document.getElementById('filter-input');
    const statusInfo = document.getElementById('status-info');
    const headerEl = document.getElementById('panel-header');
    const togglePanelBtn = document.getElementById('toggle-panel-btn');

    // --- 暴露给 core.js 使用 ---
    window.__boss__.dom = {
        panel, startBtn, stopBtn, greetToggle, filterInput, statusEl
    };

    // --- updateStatus / updateBadge ---
    window.__boss__.updateStatus = function (msg) {
        statusInfo.textContent = `状态: ${msg} | 已处理: ${window.__boss__.processedCount || 0}`;
    };

    window.__boss__.updateBadge = async function () {
        const items = JSON.parse(await Storage.get(STORAGE_KEY, '[]'));
        document.getElementById('cache-count').textContent = `缓存: ${items.length} 条`;
    };
    window.__boss__.updateBadge();

    // --- 面板折叠 ---
    togglePanelBtn.addEventListener('click', () => {
        const isCollapsed = panel.classList.toggle('collapsed');
        togglePanelBtn.innerText = isCollapsed ? '□' : '_';
    });

    // --- 面板拖动 ---
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    headerEl.addEventListener('mousedown', (e) => {
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
    Storage.get('boss_greet_enabled', false).then(val => {
        greetToggle.checked = val;
    });
    greetToggle.addEventListener('change', () => {
        Storage.set('boss_greet_enabled', greetToggle.checked);
        console.log(`[Boss] 自动沟通: ${greetToggle.checked ? '开启' : '关闭'}`);
    });

    // --- 加载/保存 屏蔽关键词 ---
    Storage.get('boss_filter_keywords', '').then(val => {
        filterInput.value = val;
    });
    filterInput.addEventListener('change', () => {
        Storage.set('boss_filter_keywords', filterInput.value);
        console.log(`[Boss] 屏蔽关键词已更新: ${filterInput.value}`);
    });

    // --- 导出 ---
    exportBtn.addEventListener('click', async () => {
        const items = JSON.parse(await Storage.get(STORAGE_KEY, '[]'));
        if (items.length === 0) { alert('暂无缓存数据'); return; }
        const exportData = items.map(it => it.data);
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'detail.json';
        a.click();
        URL.revokeObjectURL(a.href);
        await Storage.set(STORAGE_KEY, []);
        window.__boss__.updateBadge();
        console.log(`[Boss导出] 已导出 ${items.length} 条并清空缓存`);
    });

    // --- 清空 ---
    clearBtn.addEventListener('click', async () => {
        const items = JSON.parse(await Storage.get(STORAGE_KEY, '[]'));
        if (items.length === 0) { alert('暂无缓存数据'); return; }
        if (!confirm(`确定要清空 ${items.length} 条缓存数据吗？`)) return;
        await Storage.set(STORAGE_KEY, []);
        window.__boss__.updateBadge();
        console.log(`[Boss清空] 已清空 ${items.length} 条缓存`);
    });
})();
