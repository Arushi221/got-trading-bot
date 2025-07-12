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
        if (tab.dataset.tab === 'dashboard') loadPrices();
    });
});

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}

// Prices
async function loadPrices() {
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
    const res = await fetch('/api/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, action, quantity })
    });
    const data = await res.json();
    if (data.success) {
        showToast('Trade successful!');
        loadPortfolio();
        loadPrices();
        tradeForm.reset();
    } else {
        msgDiv.textContent = data.error || 'Trade failed.';
        showToast(data.error || 'Trade failed.');
    }
});

// Portfolio
async function loadPortfolio() {
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
        history.innerHTML = data.history.slice(-10).reverse().map(tr =>
            `<div>${tr.time.slice(0,19).replace('T',' ')} - <b>${tr.action}</b> ${tr.qty} ${tr.symbol} @ $${tr.price.toFixed(2)}</div>`
        ).join('');
    }
}

// Signals
async function loadSignals() {
    const res = await fetch('/api/signals');
    const data = await res.json();
    const signalsDiv = document.getElementById('signals-list');
    signalsDiv.innerHTML = '';
    Object.entries(data).forEach(([symbol, info]) => {
        const card = document.createElement('div');
        card.className = `card signal-card ${info.signal.toLowerCase()}`;
        card.innerHTML = `<b>${symbol}</b>: <span>${info.signal}</span><br><span style="font-size:0.95em;">${info.reason}</span>`;
        signalsDiv.appendChild(card);
    });
}

// Initial load
loadPrices();
loadPortfolio(); 