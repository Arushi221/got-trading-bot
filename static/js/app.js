// Westeros Trading Bot - Frontend JavaScript
class WesterosTradingBot {
    constructor() {
        this.socket = io();
        this.currentUser = 'default_user';
        this.housesData = {};
        this.portfolio = null;
        this.signals = [];
        
        this.initializeEventListeners();
        this.initializeSocketListeners();
        this.loadInitialData();
    }

    initializeEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Trading form
        const tradeForm = document.getElementById('trade-form');
        if (tradeForm) {
            tradeForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.executeTrade();
            });
        }

        // House selection for trading
        const houseSelect = document.getElementById('house-select');
        if (houseSelect) {
            houseSelect.addEventListener('change', (e) => {
                this.updateTradingInfo(e.target.value);
            });
        }

        // Quantity input for trading
        const quantityInput = document.getElementById('quantity-input');
        if (quantityInput) {
            quantityInput.addEventListener('input', () => {
                this.updateTotalCost();
            });
        }

        // Action selection for trading
        const actionSelect = document.getElementById('action-select');
        if (actionSelect) {
            actionSelect.addEventListener('change', () => {
                this.updateTotalCost();
            });
        }
    }

    initializeSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to Westeros Trading Bot');
            this.showToast('Connected to the realm', 'success');
        });

        this.socket.on('price_update', (data) => {
            this.housesData = data;
            this.updateDashboard();
            this.updateHousesGrid();
            this.updateTradingInfo(document.getElementById('house-select')?.value);
        });

        this.socket.on('disconnect', () => {
            this.showToast('Disconnected from the realm', 'warning');
        });
    }

    async loadInitialData() {
        try {
            // Load houses data
            const housesResponse = await fetch('/api/houses');
            this.housesData = await housesResponse.json();
            this.updateDashboard();
            this.updateHousesGrid();

            // Load portfolio
            const portfolioResponse = await fetch(`/api/portfolio/${this.currentUser}`);
            this.portfolio = await portfolioResponse.json();
            this.updatePortfolio();

            // Load signals
            const signalsResponse = await fetch('/api/signals');
            this.signals = await signalsResponse.json();
            this.updateSignals();

        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('Error loading data from the realm', 'error');
        }
    }

    switchTab(tabName) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Add active class to selected tab and content
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName).classList.add('active');

        // Load specific data for the tab
        if (tabName === 'portfolio') {
            this.loadPortfolio();
        } else if (tabName === 'signals') {
            this.loadSignals();
        }
    }

    updateDashboard() {
        // Update gold amount
        const userGold = document.getElementById('user-gold');
        if (userGold && this.portfolio) {
            userGold.textContent = this.formatCurrency(this.portfolio.gold);
        }

        // Update total value
        const totalValue = document.getElementById('total-value');
        if (totalValue && this.portfolio) {
            const holdingsValue = this.calculateHoldingsValue();
            const total = this.portfolio.gold + holdingsValue;
            totalValue.textContent = this.formatCurrency(total);
        }

        // Update P&L (simplified calculation)
        const todayPnl = document.getElementById('today-pnl');
        if (todayPnl) {
            // This would be calculated based on actual trading history
            todayPnl.textContent = this.formatCurrency(0);
        }
    }

    updateHousesGrid() {
        const housesGrid = document.getElementById('houses-grid');
        if (!housesGrid) return;

        housesGrid.innerHTML = '';

        Object.entries(this.housesData).forEach(([houseKey, houseData]) => {
            const houseCard = this.createHouseCard(houseKey, houseData);
            housesGrid.appendChild(houseCard);
        });
    }

    createHouseCard(houseKey, houseData) {
        const card = document.createElement('div');
        card.className = `house-card ${houseKey.toLowerCase()}`;
        
        const changeClass = houseData.change_percent >= 0 ? 'positive' : 'negative';
        const changeIcon = houseData.change_percent >= 0 ? '↗' : '↘';

        card.innerHTML = `
            <div class="house-header">
                <div>
                    <div class="house-name">${houseData.name}</div>
                    <div class="house-motto">"${houseData.motto}"</div>
                </div>
                <div class="house-symbol">${houseData.symbol}</div>
            </div>
            <div class="house-price">$${houseData.current_price.toFixed(2)}</div>
            <div class="house-change">
                <span class="change-amount ${changeClass}">
                    ${changeIcon} $${Math.abs(houseData.change).toFixed(2)} (${houseData.change_percent.toFixed(2)}%)
                </span>
                <span class="house-volume">Vol: ${this.formatNumber(houseData.volume)}</span>
            </div>
        `;

        card.addEventListener('click', () => {
            this.selectHouseForTrading(houseKey);
        });

        return card;
    }

    selectHouseForTrading(houseKey) {
        const houseSelect = document.getElementById('house-select');
        if (houseSelect) {
            houseSelect.value = houseKey;
            this.updateTradingInfo(houseKey);
        }
    }

    updateTradingInfo(houseKey) {
        const currentPriceDiv = document.getElementById('current-price');
        const tradingInfoContent = document.getElementById('trading-info-content');

        if (!houseKey || !this.housesData[houseKey]) {
            if (currentPriceDiv) currentPriceDiv.textContent = 'Select a house';
            if (tradingInfoContent) {
                tradingInfoContent.innerHTML = '<p>Select a house to see current trading information.</p>';
            }
            return;
        }

        const houseData = this.housesData[houseKey];
        const changeClass = houseData.change_percent >= 0 ? 'positive' : 'negative';

        if (currentPriceDiv) {
            currentPriceDiv.textContent = `$${houseData.current_price.toFixed(2)}`;
        }

        if (tradingInfoContent) {
            tradingInfoContent.innerHTML = `
                <div class="trading-info-item">
                    <strong>Current Price:</strong> $${houseData.current_price.toFixed(2)}
                </div>
                <div class="trading-info-item">
                    <strong>Today's Change:</strong> 
                    <span class="${changeClass}">${houseData.change_percent.toFixed(2)}%</span>
                </div>
                <div class="trading-info-item">
                    <strong>Volume:</strong> ${this.formatNumber(houseData.volume)}
                </div>
                <div class="trading-info-item">
                    <strong>High:</strong> $${houseData.high.toFixed(2)}
                </div>
                <div class="trading-info-item">
                    <strong>Low:</strong> $${houseData.low.toFixed(2)}
                </div>
                <div class="trading-info-item">
                    <strong>Last Updated:</strong> ${houseData.last_updated}
                </div>
            `;
        }

        this.updateTotalCost();
    }

    updateTotalCost() {
        const houseSelect = document.getElementById('house-select');
        const quantityInput = document.getElementById('quantity-input');
        const totalCostDiv = document.getElementById('total-cost');

        if (!houseSelect.value || !this.housesData[houseSelect.value]) {
            if (totalCostDiv) totalCostDiv.textContent = '0';
            return;
        }

        const houseData = this.housesData[houseSelect.value];
        const quantity = parseInt(quantityInput.value) || 0;
        const totalCost = houseData.current_price * quantity;

        if (totalCostDiv) {
            totalCostDiv.textContent = this.formatCurrency(totalCost);
        }
    }

    async executeTrade() {
        const houseSelect = document.getElementById('house-select');
        const actionSelect = document.getElementById('action-select');
        const quantityInput = document.getElementById('quantity-input');

        if (!houseSelect.value || !actionSelect.value || !quantityInput.value) {
            this.showToast('Please fill in all trading fields', 'warning');
            return;
        }

        const tradeData = {
            user_id: this.currentUser,
            house: houseSelect.value,
            action: actionSelect.value,
            quantity: parseInt(quantityInput.value)
        };

        try {
            const response = await fetch('/api/trade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(tradeData)
            });

            const result = await response.json();

            if (result.success) {
                this.portfolio = result.portfolio;
                this.updatePortfolio();
                this.updateDashboard();
                
                const actionText = tradeData.action === 'buy' ? 'purchased' : 'sold';
                this.showToast(`Successfully ${actionText} ${tradeData.quantity} shares of ${this.housesData[tradeData.house].name}`, 'success');
                
                // Reset form
                document.getElementById('trade-form').reset();
                this.updateTradingInfo('');
            } else {
                this.showToast(result.error || 'Trade failed', 'error');
            }
        } catch (error) {
            console.error('Error executing trade:', error);
            this.showToast('Error executing trade', 'error');
        }
    }

    async loadPortfolio() {
        try {
            const response = await fetch(`/api/portfolio/${this.currentUser}`);
            this.portfolio = await response.json();
            this.updatePortfolio();
        } catch (error) {
            console.error('Error loading portfolio:', error);
            this.showToast('Error loading portfolio', 'error');
        }
    }

    updatePortfolio() {
        if (!this.portfolio) return;

        // Update portfolio summary
        const portfolioGold = document.getElementById('portfolio-gold');
        const holdingsValue = document.getElementById('holdings-value');
        const portfolioTotal = document.getElementById('portfolio-total');

        if (portfolioGold) portfolioGold.textContent = this.formatCurrency(this.portfolio.gold);
        
        const holdingsValueAmount = this.calculateHoldingsValue();
        if (holdingsValue) holdingsValue.textContent = this.formatCurrency(holdingsValueAmount);
        
        const totalValue = this.portfolio.gold + holdingsValueAmount;
        if (portfolioTotal) portfolioTotal.textContent = this.formatCurrency(totalValue);

        // Update holdings list
        this.updateHoldingsList();

        // Update transaction history
        this.updateTransactionHistory();
    }

    calculateHoldingsValue() {
        if (!this.portfolio || !this.portfolio.holdings) return 0;

        let totalValue = 0;
        Object.entries(this.portfolio.holdings).forEach(([house, quantity]) => {
            if (this.housesData[house]) {
                totalValue += this.housesData[house].current_price * quantity;
            }
        });
        return totalValue;
    }

    updateHoldingsList() {
        const holdingsContainer = document.getElementById('holdings-container');
        if (!holdingsContainer) return;

        if (!this.portfolio.holdings || Object.keys(this.portfolio.holdings).length === 0) {
            holdingsContainer.innerHTML = '<p>No holdings yet. Start trading to build your portfolio!</p>';
            return;
        }

        holdingsContainer.innerHTML = '';
        Object.entries(this.portfolio.holdings).forEach(([house, quantity]) => {
            const houseData = this.housesData[house];
            if (!houseData) return;

            const value = houseData.current_price * quantity;
            const holdingItem = document.createElement('div');
            holdingItem.className = 'holding-item';
            holdingItem.innerHTML = `
                <div class="holding-info">
                    <div class="holding-name">${houseData.name}</div>
                    <div class="holding-details">${quantity} shares @ $${houseData.current_price.toFixed(2)}</div>
                </div>
                <div class="holding-value">${this.formatCurrency(value)}</div>
            `;
            holdingsContainer.appendChild(holdingItem);
        });
    }

    updateTransactionHistory() {
        const transactionsContainer = document.getElementById('transactions-container');
        if (!transactionsContainer) return;

        if (!this.portfolio.transactions || this.portfolio.transactions.length === 0) {
            transactionsContainer.innerHTML = '<p>No transactions yet.</p>';
            return;
        }

        transactionsContainer.innerHTML = '';
        this.portfolio.transactions.slice(-10).reverse().forEach(transaction => {
            const houseData = this.housesData[transaction.house];
            const transactionItem = document.createElement('div');
            transactionItem.className = 'transaction-item';
            transactionItem.innerHTML = `
                <div class="transaction-info">
                    <div class="transaction-type">${transaction.action.toUpperCase()} ${houseData ? houseData.name : transaction.house}</div>
                    <div class="transaction-details">${transaction.quantity} shares @ $${transaction.price.toFixed(2)} - ${transaction.timestamp}</div>
                </div>
                <div class="transaction-amount">${this.formatCurrency(transaction.total)}</div>
            `;
            transactionsContainer.appendChild(transactionItem);
        });
    }

    async loadSignals() {
        try {
            const response = await fetch('/api/signals');
            this.signals = await response.json();
            this.updateSignals();
        } catch (error) {
            console.error('Error loading signals:', error);
            this.showToast('Error loading signals', 'error');
        }
    }

    updateSignals() {
        const signalsList = document.getElementById('signals-list');
        if (!signalsList) return;

        if (this.signals.length === 0) {
            signalsList.innerHTML = '<p>No trading signals available at the moment.</p>';
            return;
        }

        signalsList.innerHTML = '';
        this.signals.forEach(signal => {
            const signalItem = document.createElement('div');
            signalItem.className = `signal-item ${signal.signal.toLowerCase()}`;
            signalItem.innerHTML = `
                <div class="signal-header">
                    <div class="signal-house">${signal.house}</div>
                    <div class="signal-type ${signal.signal.toLowerCase()}">${signal.signal}</div>
                </div>
                <div class="signal-strength">Strength: ${signal.strength}</div>
                <div class="signal-reason">${signal.reason}</div>
            `;
            signalsList.appendChild(signalItem);
        });
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        if (!toast) return;

        toast.textContent = message;
        toast.className = `toast ${type} show`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString();
    }
}

// Initialize the trading bot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new WesterosTradingBot();
    
    // Add some Game of Thrones themed console messages
    console.log('%c🏰 Welcome to Westeros Trading Bot!', 'color: #D4AF37; font-size: 20px; font-weight: bold;');
    console.log('%c🌙 Winter is coming, but profits are already here!', 'color: #4a90e2; font-size: 14px;');
    console.log('%c⚔️ May your trades be as sharp as Valyrian steel!', 'color: #dc143c; font-size: 12px;');
}); 