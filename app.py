from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

app = Flask(__name__)

STOCKS = {
    'NVDA': {'symbol': 'NVDA', 'name': 'Nvidia'},
    'AMZN': {'symbol': 'AMZN', 'name': 'Amazon'},
    'AAPL': {'symbol': 'AAPL', 'name': 'Apple'}
}

# In-memory user portfolio
portfolio = {
    'cash': 10000.0,
    'holdings': {s: 0 for s in STOCKS},
    'history': []
}

def get_stock_data(symbol, period='1y'):
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
    for k, v in STOCKS.items():
        hist = get_stock_data(v['symbol'], '5d')
        if not hist.empty:
            try:
                close = hist['Close']
                prices[k] = {
                    'price': float(close.iloc[-1]),
                    'change': float(close.iloc[-1] - close.iloc[-2]) if len(close) > 1 else 0.0,
                    'change_percent': float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100) if len(close) > 1 else 0.0
                }
            except Exception as e:
                print(f"[ERROR] Problem processing price data for {k}: {e}")
                prices[k] = {'price': None, 'change': 0.0, 'change_percent': 0.0}
        else:
            prices[k] = {'price': None, 'change': 0.0, 'change_percent': 0.0}
    return prices

def generate_signals():
    signals = {}
    for k, v in STOCKS.items():
        hist = get_stock_data(v['symbol'], '1y')
        if len(hist) < 200:
            signals[k] = {'signal': 'HOLD', 'reason': 'Not enough data'}
            continue
        sma50 = hist['Close'].rolling(50).mean()
        sma200 = hist['Close'].rolling(200).mean()
        if sma50.iloc[-1] > sma200.iloc[-1]:
            signals[k] = {'signal': 'BUY', 'reason': '50-day SMA above 200-day SMA'}
        elif sma50.iloc[-1] < sma200.iloc[-1]:
            signals[k] = {'signal': 'SELL', 'reason': '50-day SMA below 200-day SMA'}
        else:
            signals[k] = {'signal': 'HOLD', 'reason': 'No clear trend'}
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
    holdings_value = sum(portfolio['holdings'][k] * prices[k]['price'] for k in STOCKS if prices[k]['price'] is not None)
    total = portfolio['cash'] + holdings_value
    return jsonify({
        'cash': portfolio['cash'],
        'holdings': portfolio['holdings'],
        'history': portfolio['history'],
        'holdings_value': holdings_value,
        'total': total
    })

@app.route('/api/trade', methods=['POST'])
def api_trade():
    data = request.json
    symbol = data.get('symbol')
    action = data.get('action')
    qty = int(data.get('quantity', 1))
    prices = get_latest_prices()
    price = prices.get(symbol, {}).get('price')

    if price is None:
        return jsonify({'error': 'Price unavailable'}), 400

    if action == 'buy':
        cost = price * qty
        if portfolio['cash'] < cost:
            return jsonify({'error': 'Not enough cash'}), 400
        portfolio['cash'] -= cost
        portfolio['holdings'][symbol] += qty
        portfolio['history'].append({
            'time': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'BUY',
            'qty': qty,
            'price': price
        })
    elif action == 'sell':
        if portfolio['holdings'][symbol] < qty:
            return jsonify({'error': 'Not enough shares'}), 400
        proceeds = price * qty
        portfolio['cash'] += proceeds
        portfolio['holdings'][symbol] -= qty
        portfolio['history'].append({
            'time': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'SELL',
            'qty': qty,
            'price': price
        })
    else:
        return jsonify({'error': 'Invalid action'}), 400

    return jsonify({'success': True, 'portfolio': portfolio})

if __name__ == '__main__':
    app.run(debug=True, port=5050)
