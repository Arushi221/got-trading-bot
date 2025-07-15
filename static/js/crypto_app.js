document.addEventListener('DOMContentLoaded', () => {
    const pricesDiv = document.getElementById('prices');
    const portfolioDiv = document.getElementById('portfolio');
    const tradeForm = document.getElementById('tradeForm');
    const tradeMessage = document.getElementById('tradeMessage');
    const coinSelect = document.getElementById('coinSelect');
    const priceChartCanvas = document.getElementById('priceChart');

    let priceChart;
    let currentCoin = coinSelect.value;

    // Fetch and display prices
    async function loadPrices() {
        const res = await fetch('/api/prices');
        const data = await res.json();
        pricesDiv.innerHTML = '';
        Object.entries(data).forEach(([symbol, info]) => {
            const card = document.createElement('div');
            card.className = 'price-card';
            card.innerHTML = `
                <div class="coin-name">${symbol}</div>
                <div class="coin-price">$${info.price ? info.price.toFixed(6) : 'N/A'}</div>
            `;
            pricesDiv.appendChild(card);
        });
    }

    // Fetch and display portfolio
    async function loadPortfolio() {
        const res = await fetch('/api/portfolio');
        const data = await res.json();
        portfolioDiv.innerHTML = `
            <div><b>Cash:</b> $${data.cash.toFixed(2)}</div>
            <div><b>Holdings Value:</b> $${data.holdings_value.toFixed(2)}</div>
            <div><b>Total Value:</b> $${data.total.toFixed(2)}</div>
            <div><b>Holdings:</b>
                <ul>
                    ${Object.entries(data.holdings).map(([k, v]) => `<li>${k}: ${v}</li>`).join('')}
                </ul>
            </div>
            <div><b>Trade History:</b>
                <ul>
                    ${data.history.slice(-5).reverse().map(h => `<li>${h.time.split('T')[0]}: ${h.action} ${h.qty} ${h.symbol} @ $${h.price.toFixed(6)}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Fetch and render price chart for selected coin
    async function loadPriceChart(symbol) {
        // For demo, just show last 20 price points (simulate with repeated current price)
        const res = await fetch('/api/prices');
        const data = await res.json();
        const price = data[symbol]?.price || 0;
        const now = new Date();
        const labels = Array.from({length: 20}, (_, i) => {
            const d = new Date(now.getTime() - (19 - i) * 60000);
            return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
        });
        const prices = Array(20).fill(price);
        if (priceChart) priceChart.destroy();
        priceChart = new Chart(priceChartCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: symbol + ' Price',
                    data: prices,
                    borderColor: '#d291bc',
                    backgroundColor: 'rgba(160, 132, 202, 0.15)',
                    tension: 0.3,
                    pointRadius: 0,
                    fill: true
                }]
            },
            options: {
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { display: false },
                    y: { beginAtZero: false }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // Handle trading
    tradeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        tradeMessage.textContent = '';
        const symbol = coinSelect.value;
        const action = document.getElementById('actionSelect').value;
        const quantity = document.getElementById('quantityInput').value;
        const res = await fetch('/api/trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, action, quantity })
        });
        const data = await res.json();
        if (data.error) {
            tradeMessage.textContent = data.error;
        } else {
            tradeMessage.textContent = 'Trade successful!';
            loadPortfolio();
        }
    });

    // Update chart when coin changes
    coinSelect.addEventListener('change', (e) => {
        currentCoin = e.target.value;
        loadPriceChart(currentCoin);
    });

    // Initial load
    loadPrices();
    loadPortfolio();
    loadPriceChart(currentCoin);
    setInterval(loadPrices, 10000);
    setInterval(loadPortfolio, 15000);
    setInterval(() => loadPriceChart(currentCoin), 20000);
}); 