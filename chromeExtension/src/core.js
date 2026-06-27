// src/core.js — 自动点击逻辑 + 启动入口

(function () {
    const { sleep, dom, updateStatus, updateBadge } = window.__boss__;

    let isRunning = false;
    const processedCardIds = new Set();
    let processedCount = 0;

    // 暴露给 ui.js 的 updateStatus 回调使用
    window.__boss__.processedCount = 0;

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
            const loading = document.querySelector('.loading-wait');
            if (loading && loading.style.display === 'none' && waited > 2000) return false;
        }
        return false;
    }

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
                const filterKeywords = dom.filterInput.value.split(/[,，]/).map(k => k.trim()).filter(k => k);
                let isFiltered = false;
                for (const keyword of filterKeywords) {
                    if (companyName.includes(keyword)) {
                        isFiltered = true;
                        break;
                    }
                }
                if (isFiltered) {
                    processedCount++;
                    window.__boss__.processedCount = processedCount;
                    updateStatus(`[已屏蔽] ${companyName} - ${jobName}`);
                    console.log(`[Boss屏蔽] ${processedCount}. ${companyName} | ${jobName} (命中关键词)`);
                    continue;
                }

                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await sleep(500);
                card.click();

                processedCount++;
                window.__boss__.processedCount = processedCount;
                updateStatus(`已点击: ${companyName} - ${jobName} (${processedCount})`);
                console.log(`[Boss自动点击] ${processedCount}. ${companyName} | ${jobName} | ${exp}`);

                await sleep(2000);

                // --- 自动点击立即沟通（触发详情拦截） ---
                if (dom.greetToggle.checked) {
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

    function toggleRunning() {
        isRunning = !isRunning;
        if (isRunning) {
            dom.startBtn.style.display = 'none';
            dom.stopBtn.style.display = 'block';
            updateStatus('运行中...');
            clickNextJob();
        } else {
            dom.startBtn.style.display = 'block';
            dom.stopBtn.style.display = 'none';
            updateStatus(`已停止，共处理 ${processedCount} 个`);
        }
    }

    dom.startBtn.addEventListener('click', toggleRunning);
    dom.stopBtn.addEventListener('click', toggleRunning);
})();
