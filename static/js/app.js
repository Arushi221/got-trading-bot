// Tab switching
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(tc => tc.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
        if (tab.dataset.tab === 'portfolio') loadPortfolio();
        if (tab.dataset.tab === 'signals') loadSignals();
        if (tab.dataset.tab === 'strategies') loadStrategies();
        if (tab.dataset.tab === 'dashboard') loadPrices();
    });
});

// Bot Status Management
let botStatus = { enabled: false };

async function loadBotStatus() {
    try {
        const res = await fetch('/api/bot-status');
        const data = await res.json();
        botStatus = data;
        
        const statusText = document.getElementById('bot-status-text');
        const vixDisplay = document.getElementById('vix-display');
        const checkInterval = document.getElementById('check-interval');
        const marketStatus = document.getElementById('market-status');
        const toggleBtn = document.getElementById('toggle-bot');
        const botStatusBar = document.getElementById('bot-status');
        
        // Show detailed status
        if (data.enabled && data.running) {
            statusText.textContent = '🟢 Bot Active & Running';
            botStatusBar.classList.remove('inactive');
        } else if (data.enabled && !data.running) {
            statusText.textContent = '🟡 Bot Enabled (Starting...)';
            botStatusBar.classList.remove('inactive');
        } else {
            statusText.textContent = '🔴 Bot Inactive';
            botStatusBar.classList.add('inactive');
        }
        
        // Show market status
        if (data.market_status) {
            const market = data.market_status;
            if (market.is_open) {
                marketStatus.textContent = `🟢 Market Open (${market.current_time})`;
            } else {
                marketStatus.textContent = `🔴 Market Closed - ${market.status}`;
            }
        }
        
        vixDisplay.textContent = `VIX: ${data.vix ? data.vix.toFixed(2) : '--'}`;
        checkInterval.textContent = `Check: ${Math.floor(data.check_interval / 60)}min`;
        toggleBtn.textContent = data.enabled ? 'Stop Bot' : 'Start Bot';
    } catch (error) {
        console.error('Error loading bot status:', error);
    }
}

async function toggleBot() {
    try {
        const newStatus = !botStatus.enabled;
        const res = await fetch('/api/toggle-bot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            loadBotStatus();
        } else {
            showToast('Failed to toggle bot');
        }
    } catch (error) {
        console.error('Error toggling bot:', error);
        showToast('Error toggling bot');
    }
}

// Add event listener for toggle button
document.getElementById('toggle-bot').addEventListener('click', toggleBot);

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}

// Prices
async function loadPrices() {
    try {
        const res = await fetch('/api/prices');
        const data = await res.json();
        const pricesDiv = document.getElementById('prices');
        pricesDiv.innerHTML = '';
        Object.entries(data).forEach(([symbol, info]) => {
            const card = document.createElement('div');
            card.className = 'card price-card';
            card.innerHTML = `
                <div style="font-size:1.3rem;font-weight:700;">${symbol}</div>
                <div class="price ${info.change > 0 ? 'price-up' : info.change < 0 ? 'price-down' : ''}">$${info.price ? info.price.toFixed(2) : '--'}</div>
                <div>${info.change > 0 ? '▲' : info.change < 0 ? '▼' : ''} ${info.change.toFixed(2)} (${info.change_percent.toFixed(2)}%)</div>
            `;
            pricesDiv.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading prices:', error);
    }
}

// Trade
const tradeForm = document.getElementById('trade-form');
tradeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const symbol = document.getElementById('symbol').value;
    const action = document.getElementById('action').value;
    const quantity = document.getElementById('quantity').value;
    const msgDiv = document.getElementById('trade-message');
    msgDiv.textContent = '';
    
    try {
        const res = await fetch('/api/trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, action, quantity })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            loadPortfolio();
            loadPrices();
            tradeForm.reset();
        } else {
            msgDiv.textContent = data.error || 'Trade failed.';
            showToast(data.error || 'Trade failed.');
        }
    } catch (error) {
        console.error('Error executing trade:', error);
        msgDiv.textContent = 'Network error. Please try again.';
        showToast('Network error. Please try again.');
    }
});

// Portfolio
async function loadPortfolio() {
    try {
        const res = await fetch('/api/portfolio');
        const data = await res.json();
        const summary = document.getElementById('portfolio-summary');
        summary.innerHTML = `
            <div><strong>Cash:</strong> $${data.cash.toFixed(2)}</div>
            <div><strong>Holdings Value:</strong> $${data.holdings_value.toFixed(2)}</div>
            <div><strong>Total Value:</strong> $${data.total.toFixed(2)}</div>
            <div style="margin-top:10px;"><strong>Stocks:</strong> ${Object.entries(data.holdings).map(([k,v]) => `${k}: ${v}`).join(', ')}</div>
        `;
        const history = document.getElementById('history');
        if (data.history.length === 0) {
            history.textContent = 'No trades yet.';
        } else {
            history.innerHTML = data.history.slice(-10).reverse().map(tr => {
                const time = new Date(tr.time).toLocaleString();
                let actionClass = 'buy';
                if (tr.action === 'SELL' || tr.action === 'AUTO_SELL') {
                    actionClass = 'sell';
                } else if (tr.action === 'AUTO_BUY') {
                    actionClass = 'auto';
                }
                return `<div class="history-item ${actionClass}">
                    <span class="time">${time}</span> - 
                    <span class="action"><b>${tr.action}</b></span> 
                    <span class="details">${tr.qty} ${tr.symbol} @ $${tr.price.toFixed(2)}</span>
                    ${tr.reason ? `<span class="reason">(${tr.reason})</span>` : ''}
                </div>`;
            }).join('');
        }
    } catch (error) {
        console.error('Error loading portfolio:', error);
    }
}

// Day Trading Signals
async function loadSignals() {
    try {
        const res = await fetch('/api/signals');
        const data = await res.json();
        const signalsDiv = document.getElementById('signals-list');
        signalsDiv.innerHTML = '';
        
        Object.entries(data).forEach(([symbol, info]) => {
            const card = document.createElement('div');
            card.className = 'signal-card';
            
            const signalIcon = info.signal === 'BUY' ? '✅' : info.signal === 'SELL' ? '❌' : '⚠️';
            
            let strategiesHtml = '';
            if (info.strategies) {
                strategiesHtml = `
                    <div class="strategies-breakdown">
                        ${Object.entries(info.strategies).map(([strategyName, strategy]) => {
                            const strategyIcon = strategy.signal === 'BUY' ? '✅' : strategy.signal === 'SELL' ? '❌' : '⚠️';
                            return `
                                <div class="strategy-item">
                                    <span class="strategy-name">${strategyName.replace('_', ' ').toUpperCase()}</span>
                                    <span class="strategy-signal ${strategy.signal.toLowerCase()}">
                                        ${strategyIcon} ${strategy.signal}
                                    </span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }
            
            card.innerHTML = `
                <div class="signal-header">
                    <span class="signal-symbol">${symbol}</span>
                    <span class="signal-status ${info.signal.toLowerCase()}">
                        ${signalIcon} ${info.signal}
                    </span>
                </div>
                <div class="signal-reason">${info.reason}</div>
                ${strategiesHtml}
            `;
            signalsDiv.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading signals:', error);
    }
}

// Strategies
async function loadStrategies() {
    try {
        const res = await fetch('/api/strategies');
        const data = await res.json();
        const strategiesDiv = document.getElementById('strategies-list');
        strategiesDiv.innerHTML = '';
        
        Object.entries(data).forEach(([key, strategy]) => {
            const card = document.createElement('div');
            card.className = 'strategy-card';
            
            const indicatorsHtml = strategy.indicators.map(indicator => 
                `<span class="indicator-tag">${indicator.replace('_', ' ')}</span>`
            ).join('');
            
            card.innerHTML = `
                <div class="strategy-title">${strategy.name}</div>
                <div class="strategy-description">${strategy.description}</div>
                <div class="strategy-indicators">
                    ${indicatorsHtml}
                </div>
            `;
            strategiesDiv.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading strategies:', error);
    }
}

// Auto-refresh functionality
function startAutoRefresh() {
    // Refresh prices every 30 seconds
    setInterval(loadPrices, 30000);
    
    // Refresh signals every 60 seconds
    setInterval(() => {
        if (document.querySelector('#signals.active')) {
            loadSignals();
        }
    }, 60000);
    
    // Refresh bot status every 30 seconds
    setInterval(loadBotStatus, 30000);
    
    // Refresh portfolio every 30 seconds to show bot trades
    setInterval(() => {
        if (document.querySelector('#portfolio.active')) {
            loadPortfolio();
        }
    }, 30000);
}

// Initial load
loadPrices();
loadPortfolio();
loadBotStatus();
loadStrategies();
startAutoRefresh(); 