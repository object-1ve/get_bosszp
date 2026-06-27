// src/styles.js — 样式注入 + CSS

(function () {
    function addStyle(css) {
        const style = document.createElement('style');
        style.textContent = css;
        (document.head || document.documentElement).appendChild(style);
    }

    addStyle(`
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

    window.__boss__.addStyle = addStyle;
})();
