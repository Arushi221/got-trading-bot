from flask import Flask, render_template, request, jsonify
import yfinance as yf
from datetime import datetime
import time
import threading
import pandas as pd

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

# AI Autocomplete settings
AUTO_TRADE_ENABLED = True
DROPOUT_THRESHOLD = -2.0  # 2% drop threshold
VIX_THRESHOLD = 20.0  # VIX threshold for buying
AUTO_BUY_QUANTITY = 1  # Number of shares to buy automatically

# If stock drops more than 2% today and VIX < 20, buy 1 share for any stock


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
    if portfolio['cash'] < price:
        print(f"Insufficient cash for auto-trade: {symbol}")
        return False
    
    portfolio['cash'] -= price
    portfolio['holdings'][symbol] += AUTO_BUY_QUANTITY
    
    portfolio['history'].append({
        'time': datetime.now().isoformat(),
        'symbol': symbol,
        'action': 'AUTO_BUY',
        'qty': AUTO_BUY_QUANTITY,
        'price': round(price, 2),
        'reason': reason
    })
    
    print(f"Auto-trade executed: BUY {AUTO_BUY_QUANTITY} {symbol} @ ${round(price, 2)} - {reason}")
    return True


def check_ai_signals():
    """Check for AI autocomplete signals and execute trades"""
    if not AUTO_TRADE_ENABLED:
        return
    
    try:
        # Get VIX data
        vix_value = get_vix_data()
        if vix_value is None:
            print("Could not get VIX data, skipping auto-trade check")
            return
        
        # Get current prices and check for signals
        prices = get_latest_prices()
        
        for key, stock in STOCKS.items():
            if prices[key]['price'] is None:
                continue
            
            change_percent = prices[key]['change_percent']
            price = prices[key]['price']
            
            # Check if stock dropped more than threshold and VIX is below threshold
            if change_percent <= DROPOUT_THRESHOLD and vix_value < VIX_THRESHOLD:
                reason = f"Stock dropped {change_percent:.2f}% and VIX ({vix_value:.2f}) < {VIX_THRESHOLD}"
                execute_auto_trade(key, price, reason)
                
    except Exception as e:
        print(f"Error in AI signal check: {e}")


def run_ai_autocomplete():
    """Background thread for running AI autocomplete"""
    while AUTO_TRADE_ENABLED:
        try:
            check_ai_signals()
            # Check every 5 minutes during market hours
            time.sleep(300)  # 5 minutes
        except Exception as e:
            print(f"Error in AI autocomplete thread: {e}")
            time.sleep(60)  # Wait 1 minute on error


# Start AI autocomplete thread
if AUTO_TRADE_ENABLED:
    ai_thread = threading.Thread(target=run_ai_autocomplete, daemon=True)
    ai_thread.start()


def get_stock_data(symbol, period='5d'):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        if hist.empty:
            print(f"[WARNING] No data found for {symbol} with period='{period}'")
        return hist
    except Exception as e:
        print(f"[ERROR] Failed to fetch data for {symbol}: {e}")
        return pd.DataFrame()


def get_latest_prices():
    prices = {}
    for key, stock in STOCKS.items():
        hist = get_stock_data(stock['symbol'], '5d')
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


def generate_signals():
    signals = {}
    for key, stock in STOCKS.items():
        hist = get_stock_data(stock['symbol'], '1y')
        if len(hist) < 200:
            signals[key] = {'signal': 'HOLD', 'reason': 'Not enough data'}
            continue
        sma50 = hist['Close'].rolling(50).mean()
        sma200 = hist['Close'].rolling(200).mean()
        if sma50.iloc[-1] > sma200.iloc[-1]:
            signals[key] = {'signal': 'BUY', 'reason': '50-day SMA above 200-day SMA'}
        elif sma50.iloc[-1] < sma200.iloc[-1]:
            signals[key] = {'signal': 'SELL', 'reason': '50-day SMA below 200-day SMA'}
        else:
            signals[key] = {'signal': 'HOLD', 'reason': 'No clear trend'}
    return signals


@app.route('/')
def index():
    return render_template('index.html', stocks=STOCKS)


@app.route('/api/prices')
def api_prices():
    return jsonify(get_latest_prices())


@app.route('/api/signals')
def api_signals():
    return jsonify(generate_signals())


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


@app.route('/api/ai-status')
def api_ai_status():
    """Get AI autocomplete status and current VIX"""
    vix_value = get_vix_data()
    return jsonify({
        'enabled': AUTO_TRADE_ENABLED,
        'vix': round(vix_value, 2) if vix_value else None,
        'vix_threshold': VIX_THRESHOLD,
        'dropout_threshold': DROPOUT_THRESHOLD,
        'auto_buy_quantity': AUTO_BUY_QUANTITY
    })


@app.route('/api/toggle-ai', methods=['POST'])
def api_toggle_ai():
    """Toggle AI autocomplete on/off"""
    global AUTO_TRADE_ENABLED
    data = request.json
    AUTO_TRADE_ENABLED = data.get('enabled', True)
    
    if AUTO_TRADE_ENABLED:
        # Restart AI thread if needed
        ai_thread = threading.Thread(target=run_ai_autocomplete, daemon=True)
        ai_thread.start()
    
    return jsonify({
        'success': True,
        'enabled': AUTO_TRADE_ENABLED,
        'message': f'AI autocomplete {"enabled" if AUTO_TRADE_ENABLED else "disabled"}'
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
