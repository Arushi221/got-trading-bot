from flask import Flask, render_template, request, jsonify
import yfinance as yf
from datetime import datetime
import time
import threading
import pandas as pd
import numpy as np

app = Flask(__name__)

STOCKS = {
    'NVDA': {'symbol': 'NVDA', 'name': 'Nvidia'},
    'AMZN': {'symbol': 'AMZN', 'name': 'Amazon'},
    'AAPL': {'symbol': 'AAPL', 'name': 'Apple'}
}

# User's portfolio
portfolio = {
    'cash': 10000.0,
    'holdings': {s: 0 for s in STOCKS},
    'history': []
}

# Day Trading Settings
AUTO_TRADE_ENABLED = True
DAY_TRADE_QUANTITY = 1  # Number of shares for day trading
CHECK_INTERVAL = 60  # Check signals every 1 minute for day trading

# Day Trading Strategies
STRATEGIES = {
    'momentum': {
        'name': 'Momentum',
        'description': 'Buys fast-moving stocks',
        'indicators': ['RSI', 'MACD', 'Volume']
    },
    'mean_reversion': {
        'name': 'Mean Reversion', 
        'description': 'Buys dips, sells rips',
        'indicators': ['Bollinger_Bands', 'VWAP']
    },
    'breakout': {
        'name': 'Breakout',
        'description': 'Buys after price breaks key levels',
        'indicators': ['Pre_market_highs', 'Support_Resistance']
    },
    'vwap_pullback': {
        'name': 'VWAP Pullback',
        'description': 'Enters after price pulls back to VWAP',
        'indicators': ['VWAP', 'EMA']
    },
    'scalping': {
        'name': 'Scalping',
        'description': 'Small quick trades',
        'indicators': ['1min_crossover', '5min_crossover']
    }
}


def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band


def calculate_vwap(high, low, close, volume):
    """Calculate Volume Weighted Average Price"""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap


def calculate_ema(prices, period=20):
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period).mean()


def get_pre_market_data(symbol):
    """Get pre-market data for breakout strategy"""
    try:
        stock = yf.Ticker(symbol)
        # Get extended hours data
        hist = stock.history(period='5d', interval='1h')
        if not hist.empty:
            # Filter for pre-market hours (4:00 AM - 9:30 AM EST)
            hist.index = pd.to_datetime(hist.index)
            pre_market = hist[hist.index.time < pd.Timestamp('09:30').time()]
            if not pre_market.empty:
                return {
                    'high': pre_market['High'].max(),
                    'low': pre_market['Low'].min(),
                    'volume': pre_market['Volume'].sum()
                }
    except Exception as e:
        print(f"Error getting pre-market data for {symbol}: {e}")
    return None


def analyze_momentum_strategy(hist):
    """Analyze momentum strategy using RSI, MACD, and Volume"""
    if len(hist) < 26:
        return {'signal': 'WAIT', 'reason': 'Insufficient data for momentum analysis'}
    
    # Calculate indicators
    rsi = calculate_rsi(hist['Close'])
    macd_line, signal_line, histogram = calculate_macd(hist['Close'])
    
    current_rsi = rsi.iloc[-1]
    current_macd = macd_line.iloc[-1]
    current_signal = signal_line.iloc[-1]
    current_volume = hist['Volume'].iloc[-1]
    avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
    
    # Momentum signals
    if current_rsi < 30 and current_macd > current_signal and current_volume > avg_volume * 1.5:
        return {'signal': 'BUY', 'reason': f'RSI oversold ({current_rsi:.1f}), MACD bullish, high volume'}
    elif current_rsi > 70 and current_macd < current_signal:
        return {'signal': 'SELL', 'reason': f'RSI overbought ({current_rsi:.1f}), MACD bearish'}
    else:
        return {'signal': 'WAIT', 'reason': f'RSI neutral ({current_rsi:.1f}), no clear momentum'}


def analyze_mean_reversion_strategy(hist):
    """Analyze mean reversion strategy using Bollinger Bands and VWAP"""
    if len(hist) < 20:
        return {'signal': 'WAIT', 'reason': 'Insufficient data for mean reversion analysis'}
    
    # Calculate indicators
    upper_band, middle_band, lower_band = calculate_bollinger_bands(hist['Close'])
    vwap = calculate_vwap(hist['High'], hist['Low'], hist['Close'], hist['Volume'])
    
    current_price = hist['Close'].iloc[-1]
    current_upper = upper_band.iloc[-1]
    current_lower = lower_band.iloc[-1]
    current_vwap = vwap.iloc[-1]
    
    # Mean reversion signals
    if current_price <= current_lower and current_price <= current_vwap:
        return {'signal': 'BUY', 'reason': f'Price at lower Bollinger Band and below VWAP'}
    elif current_price >= current_upper and current_price >= current_vwap:
        return {'signal': 'SELL', 'reason': f'Price at upper Bollinger Band and above VWAP'}
    else:
        return {'signal': 'WAIT', 'reason': f'Price between bands, no clear reversal signal'}


def analyze_breakout_strategy(symbol, hist):
    """Analyze breakout strategy using pre-market levels"""
    pre_market_data = get_pre_market_data(symbol)
    if not pre_market_data:
        return {'signal': 'WAIT', 'reason': 'No pre-market data available'}
    
    current_price = hist['Close'].iloc[-1]
    pre_market_high = pre_market_data['high']
    pre_market_low = pre_market_data['low']
    
    # Breakout signals
    if current_price > pre_market_high:
        return {'signal': 'BUY', 'reason': f'Breakout above pre-market high ${pre_market_high:.2f}'}
    elif current_price < pre_market_low:
        return {'signal': 'SELL', 'reason': f'Breakdown below pre-market low ${pre_market_low:.2f}'}
    else:
        return {'signal': 'WAIT', 'reason': f'Price within pre-market range ${pre_market_low:.2f}-${pre_market_high:.2f}'}


def analyze_vwap_pullback_strategy(hist):
    """Analyze VWAP pullback strategy"""
    if len(hist) < 20:
        return {'signal': 'WAIT', 'reason': 'Insufficient data for VWAP analysis'}
    
    # Calculate indicators
    vwap = calculate_vwap(hist['High'], hist['Low'], hist['Close'], hist['Volume'])
    ema20 = calculate_ema(hist['Close'], 20)
    
    current_price = hist['Close'].iloc[-1]
    current_vwap = vwap.iloc[-1]
    current_ema = ema20.iloc[-1]
    
    # VWAP pullback signals
    vwap_distance = abs(current_price - current_vwap) / current_vwap * 100
    
    if current_price > current_vwap and current_price > current_ema and vwap_distance < 1:
        return {'signal': 'BUY', 'reason': f'Price pulled back to VWAP (${current_vwap:.2f})'}
    elif current_price < current_vwap and current_price < current_ema and vwap_distance < 1:
        return {'signal': 'SELL', 'reason': f'Price pulled back to VWAP (${current_vwap:.2f})'}
    else:
        return {'signal': 'WAIT', 'reason': f'Price ${current_price:.2f} away from VWAP ${current_vwap:.2f}'}


def analyze_scalping_strategy(hist):
    """Analyze scalping strategy using short-term crossovers"""
    if len(hist) < 10:
        return {'signal': 'WAIT', 'reason': 'Insufficient data for scalping analysis'}
    
    # Calculate short-term EMAs
    ema5 = calculate_ema(hist['Close'], 5)
    ema10 = calculate_ema(hist['Close'], 10)
    
    current_ema5 = ema5.iloc[-1]
    current_ema10 = ema10.iloc[-1]
    prev_ema5 = ema5.iloc[-2]
    prev_ema10 = ema10.iloc[-2]
    
    # Scalping signals
    if current_ema5 > current_ema10 and prev_ema5 <= prev_ema10:
        return {'signal': 'BUY', 'reason': '5-min EMA crossed above 10-min EMA'}
    elif current_ema5 < current_ema10 and prev_ema5 >= prev_ema10:
        return {'signal': 'SELL', 'reason': '5-min EMA crossed below 10-min EMA'}
    else:
        return {'signal': 'WAIT', 'reason': 'No short-term crossover signal'}


def get_vix_data():
    """Get current VIX (volatility index) value"""
    try:
        vix = yf.Ticker('^VIX')
        hist = vix.history(period='1d')
        if not hist.empty:
            return hist['Close'].iloc[-1]
        return None
    except Exception as e:
        print(f"Error getting VIX data: {e}")
        return None


def execute_auto_trade(symbol, price, reason):
    """Execute an automatic trade and record it"""
    if portfolio['cash'] < price * DAY_TRADE_QUANTITY:
        print(f"Insufficient cash for auto-trade: {symbol}")
        return False
    
    portfolio['cash'] -= price * DAY_TRADE_QUANTITY
    portfolio['holdings'][symbol] += DAY_TRADE_QUANTITY
    
    portfolio['history'].append({
        'time': datetime.now().isoformat(),
        'symbol': symbol,
        'action': 'AUTO_BUY',
        'qty': DAY_TRADE_QUANTITY,
        'price': round(price, 2),
        'reason': reason
    })
    
    print(f"Auto-trade executed: BUY {DAY_TRADE_QUANTITY} {symbol} @ ${round(price, 2)} - {reason}")
    return True


def check_day_trading_signals():
    """Check for day trading signals and execute trades"""
    if not AUTO_TRADE_ENABLED:
        return
    
    try:
        for key, stock in STOCKS.items():
            hist = get_stock_data(stock['symbol'], '1d')
            if hist.empty:
                continue
            
            # Analyze all strategies
            momentum_signal = analyze_momentum_strategy(hist)
            mean_reversion_signal = analyze_mean_reversion_strategy(hist)
            breakout_signal = analyze_breakout_strategy(key, hist)
            vwap_signal = analyze_vwap_pullback_strategy(hist)
            scalping_signal = analyze_scalping_strategy(hist)
            
            # Execute trades based on strong signals
            price = hist['Close'].iloc[-1]
            
            # Priority: Breakout > Momentum > VWAP > Mean Reversion > Scalping
            if breakout_signal['signal'] == 'BUY':
                execute_auto_trade(key, price, f"Breakout: {breakout_signal['reason']}")
            elif momentum_signal['signal'] == 'BUY':
                execute_auto_trade(key, price, f"Momentum: {momentum_signal['reason']}")
            elif vwap_signal['signal'] == 'BUY':
                execute_auto_trade(key, price, f"VWAP: {vwap_signal['reason']}")
                
    except Exception as e:
        print(f"Error in day trading signal check: {e}")


def run_day_trading_bot():
    """Background thread for running day trading bot"""
    while AUTO_TRADE_ENABLED:
        try:
            check_day_trading_signals()
            # Check every minute for day trading
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Error in day trading bot thread: {e}")
            time.sleep(30)  # Wait 30 seconds on error


# Start day trading bot thread
if AUTO_TRADE_ENABLED:
    day_trading_thread = threading.Thread(target=run_day_trading_bot, daemon=True)
    day_trading_thread.start()


def get_stock_data(symbol, period='1d'):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval='5m')
        if hist.empty:
            print(f"[WARNING] No data found for {symbol} with period='{period}'")
        return hist
    except Exception as e:
        print(f"[ERROR] Failed to fetch data for {symbol}: {e}")
        return pd.DataFrame()


def get_latest_prices():
    prices = {}
    for key, stock in STOCKS.items():
        hist = get_stock_data(stock['symbol'], '1d')
        if not hist.empty:
            try:
                close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else close
                change = close - prev_close
                change_percent = (change / prev_close) * 100 if prev_close != 0 else 0.0
                prices[key] = {
                    'price': round(close, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2)
                }
            except Exception as e:
                print(f"[ERROR] Problem processing price data for {key}: {e}")
                prices[key] = {'price': None, 'change': 0.0, 'change_percent': 0.0}
        else:
            prices[key] = {'price': None, 'change': 0.0, 'change_percent': 0.0}
    return prices


def generate_day_trading_signals():
    """Generate day trading signals using multiple strategies"""
    signals = {}
    
    for key, stock in STOCKS.items():
        hist = get_stock_data(stock['symbol'], '1d')
        if hist.empty or len(hist) < 20:
            signals[key] = {
                'signal': 'WAIT',
                'reason': 'Insufficient data for analysis',
                'strategies': {}
            }
            continue
        
        # Analyze all strategies
        momentum = analyze_momentum_strategy(hist)
        mean_reversion = analyze_mean_reversion_strategy(hist)
        breakout = analyze_breakout_strategy(key, hist)
        vwap_pullback = analyze_vwap_pullback_strategy(hist)
        scalping = analyze_scalping_strategy(hist)
        
        # Determine overall signal (priority order)
        overall_signal = 'WAIT'
        overall_reason = 'No clear signal'
        
        if breakout['signal'] == 'BUY':
            overall_signal = 'BUY'
            overall_reason = f"Breakout: {breakout['reason']}"
        elif momentum['signal'] == 'BUY':
            overall_signal = 'BUY'
            overall_reason = f"Momentum: {momentum['reason']}"
        elif vwap_pullback['signal'] == 'BUY':
            overall_signal = 'BUY'
            overall_reason = f"VWAP: {vwap_pullback['reason']}"
        elif mean_reversion['signal'] == 'SELL':
            overall_signal = 'SELL'
            overall_reason = f"Mean Reversion: {mean_reversion['reason']}"
        elif scalping['signal'] == 'BUY':
            overall_signal = 'BUY'
            overall_reason = f"Scalping: {scalping['reason']}"
        
        signals[key] = {
            'signal': overall_signal,
            'reason': overall_reason,
            'strategies': {
                'momentum': momentum,
                'mean_reversion': mean_reversion,
                'breakout': breakout,
                'vwap_pullback': vwap_pullback,
                'scalping': scalping
            }
        }
    
    return signals


@app.route('/')
def index():
    return render_template('index.html', stocks=STOCKS)


@app.route('/api/prices')
def api_prices():
    return jsonify(get_latest_prices())


@app.route('/api/signals')
def api_signals():
    return jsonify(generate_day_trading_signals())


@app.route('/api/strategies')
def api_strategies():
    """Get available day trading strategies"""
    return jsonify(STRATEGIES)


@app.route('/api/portfolio')
def api_portfolio():
    prices = get_latest_prices()
    holdings_value = sum(
        portfolio['holdings'][s] * prices[s]['price']
        for s in STOCKS if prices[s]['price'] is not None
    )
    return jsonify({
        'cash': round(portfolio['cash'], 2),
        'holdings_value': round(holdings_value, 2),
        'total': round(portfolio['cash'] + holdings_value, 2),
        'holdings': portfolio['holdings'],
        'history': portfolio['history']
    })


@app.route('/api/bot-status')
def api_bot_status():
    """Get day trading bot status"""
    vix_value = get_vix_data()
    return jsonify({
        'enabled': AUTO_TRADE_ENABLED,
        'vix': round(vix_value, 2) if vix_value else None,
        'check_interval': CHECK_INTERVAL,
        'day_trade_quantity': DAY_TRADE_QUANTITY,
        'strategies': list(STRATEGIES.keys())
    })


@app.route('/api/toggle-bot', methods=['POST'])
def api_toggle_bot():
    """Toggle day trading bot on/off"""
    global AUTO_TRADE_ENABLED
    data = request.json
    AUTO_TRADE_ENABLED = data.get('enabled', True)
    
    if AUTO_TRADE_ENABLED:
        # Restart bot thread if needed
        day_trading_thread = threading.Thread(target=run_day_trading_bot, daemon=True)
        day_trading_thread.start()
    
    return jsonify({
        'success': True,
        'enabled': AUTO_TRADE_ENABLED,
        'message': f'Day trading bot {"enabled" if AUTO_TRADE_ENABLED else "disabled"}'
    })


@app.route('/api/trade', methods=['POST'])
def api_trade():
    data = request.json
    symbol = data.get('symbol')
    action = data.get('action', '').lower()
    quantity = int(data.get('quantity', 1))

    if symbol not in STOCKS:
        return jsonify({'error': 'Invalid stock symbol'}), 400

    prices = get_latest_prices()
    price = prices.get(symbol, {}).get('price')

    if price is None:
        return jsonify({'error': 'Price unavailable'}), 400

    if action == 'buy':
        total_cost = price * quantity
        if portfolio['cash'] < total_cost:
            return jsonify({'error': 'Not enough cash'}), 400
        portfolio['cash'] -= total_cost
        portfolio['holdings'][symbol] += quantity
        trade_action = 'BUY'
    elif action == 'sell':
        if portfolio['holdings'][symbol] < quantity:
            return jsonify({'error': 'Not enough shares'}), 400
        proceeds = price * quantity
        portfolio['cash'] += proceeds
        portfolio['holdings'][symbol] -= quantity
        trade_action = 'SELL'
    else:
        return jsonify({'error': 'Invalid action'}), 400

    portfolio['history'].append({
        'time': datetime.now().isoformat(),
        'symbol': symbol,
        'action': trade_action,
        'qty': quantity,
        'price': round(price, 2)
    })

    return jsonify({
        'success': True,
        'message': f'{trade_action} {quantity} {symbol} @ ${round(price, 2)}',
        'portfolio': portfolio
    })


if __name__ == '__main__':
    app.run(debug=True, port=5050)
