# 🚀 Day Trading Bot

An advanced day trading bot with multiple technical analysis strategies for real-time stock trading.

## Features

### 📊 Day Trading Strategies
- **Momentum Trading**: Uses RSI, MACD, and Volume analysis
- **Mean Reversion**: Leverages Bollinger Bands and VWAP
- **Breakout Trading**: Monitors pre-market highs/lows
- **VWAP Pullback**: Enters after price pulls back to VWAP
- **Scalping**: Quick trades using short-term EMA crossovers

### 🔧 Technical Indicators
- **RSI (Relative Strength Index)**: Momentum oscillator
- **MACD**: Moving Average Convergence Divergence
- **Bollinger Bands**: Volatility and trend indicators
- **VWAP**: Volume Weighted Average Price
- **EMA**: Exponential Moving Averages
- **Volume Analysis**: Volume-based confirmation signals

### ⚡ Real-time Features
- Live price monitoring with 5-minute intervals
- Automatic signal generation every minute
- Bot status monitoring with VIX integration
- Real-time portfolio tracking
- Trade history with detailed reasoning

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd got-trading-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5050`

## Usage

### Dashboard
- View real-time stock prices for NVDA, AMZN, and AAPL
- Monitor price changes and percentage movements
- Track portfolio value and holdings

### Day Trading Signals
- Real-time trading signals based on multiple strategies
- Detailed breakdown of each strategy's analysis
- Color-coded signals (✅ Buy, ❌ Sell, ⚠️ Wait)

### Strategies Overview
- Learn about each trading strategy
- Understand the indicators used
- View strategy descriptions and purposes

### Manual Trading
- Execute manual trades
- Set buy/sell orders
- Monitor trade execution

### Portfolio Management
- Track cash and holdings
- View trade history
- Monitor total portfolio value

## Trading Strategies Explained

### 1. Momentum Strategy
- **What it does**: Buys fast-moving stocks
- **Indicators**: RSI, MACD, Volume
- **Signal**: Buy when RSI < 30, MACD bullish, high volume

### 2. Mean Reversion Strategy
- **What it does**: Buys dips, sells rips
- **Indicators**: Bollinger Bands, VWAP
- **Signal**: Buy at lower band, sell at upper band

### 3. Breakout Strategy
- **What it does**: Buys after price breaks key levels
- **Indicators**: Pre-market highs/lows
- **Signal**: Buy above pre-market high, sell below pre-market low

### 4. VWAP Pullback Strategy
- **What it does**: Enters after price pulls back to VWAP
- **Indicators**: VWAP + EMA
- **Signal**: Buy when price pulls back to VWAP with trend confirmation

### 5. Scalping Strategy
- **What it does**: Small quick trades
- **Indicators**: 1-min/5-min chart crossover
- **Signal**: Buy on 5-min EMA crossing above 10-min EMA

## Bot Configuration

### Settings
- **Check Interval**: 60 seconds (configurable)
- **Day Trade Quantity**: 1 share per signal
- **Auto-trading**: Enabled by default
- **VIX Monitoring**: Real-time volatility index tracking

### API Endpoints
- `/api/prices` - Get current stock prices
- `/api/signals` - Get day trading signals
- `/api/strategies` - Get available strategies
- `/api/portfolio` - Get portfolio status
- `/api/bot-status` - Get bot status
- `/api/toggle-bot` - Toggle bot on/off
- `/api/trade` - Execute manual trades

## Risk Disclaimer

⚠️ **This is for educational purposes only. Day trading involves significant risk and may not be suitable for all investors. Past performance does not guarantee future results.**

## Technical Requirements

- Python 3.8+
- Flask 2.3.3
- yfinance 0.2.18
- pandas 2.1.4
- numpy 1.26.2

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License. 