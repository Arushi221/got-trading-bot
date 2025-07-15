from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

MEMECOINS = {
    'DOGE': {'symbol': 'DOGE-USD', 'name': 'Dogecoin'},
    'SHIB': {'symbol': 'SHIB-USD', 'name': 'Shiba Inu'},
    'PEPE': {'symbol': 'PEPE-USD', 'name': 'Pepe'}
}

# In-memory user portfolio
portfolio = {
    'cash': 10000.0,
    'holdings': {s: 0 for s in MEMECOINS},
    'history': []
}

# Fetch latest price from Coinbase API
COINBASE_API_URL = 'https://api.coinbase.com/v2/prices/{}/spot'

def get_latest_prices():
    prices = {}
    for k, v in MEMECOINS.items():
        try:
            url = COINBASE_API_URL.format(v['symbol'])
            resp = requests.get(url)
            data = resp.json()
            price = float(data['data']['amount'])
            prices[k] = {'price': price}
        except Exception as e:
            print(f"[ERROR] Failed to fetch price for {k}: {e}")
            prices[k] = {'price': None}
    return prices

@app.route('/')
def index():
    return render_template('crypto_index.html', coins=MEMECOINS)

@app.route('/api/prices')
def api_prices():
    return jsonify(get_latest_prices())

@app.route('/api/portfolio')
def api_portfolio():
    prices = get_latest_prices()
    holdings_value = sum(portfolio['holdings'][k] * prices[k]['price'] for k in MEMECOINS if prices[k]['price'] is not None)
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
    qty = float(data.get('quantity', 1))
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
            return jsonify({'error': 'Not enough coins'}), 400
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
    app.run(debug=True, port=5051) 