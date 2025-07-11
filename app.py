from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.utils
import json
import threading
import time
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'winter_is_coming_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Game of Thrones themed trading data
houses = {
    'STARK': {'symbol': 'AAPL', 'name': 'House Stark', 'motto': 'Winter is Coming'},
    'LANNISTER': {'symbol': 'MSFT', 'name': 'House Lannister', 'motto': 'Hear Me Roar'},
    'TARGARYEN': {'symbol': 'GOOGL', 'name': 'House Targaryen', 'motto': 'Fire and Blood'},
    'BARATHEON': {'symbol': 'AMZN', 'name': 'House Baratheon', 'motto': 'Ours is the Fury'},
    'TYRELL': {'symbol': 'TSLA', 'name': 'House Tyrell', 'motto': 'Growing Strong'},
    'GREYJOY': {'symbol': 'NVDA', 'name': 'House Greyjoy', 'motto': 'We Do Not Sow'}
}

# User portfolios (in-memory storage for demo)
portfolios = {}

class WesterosTrader:
    def __init__(self):
        self.current_prices = {}
        self.price_history = {}
        
    def get_stock_data(self, symbol, period='1d'):
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='5d')
            if not hist.empty:
                return {
                    'current_price': hist['Close'].iloc[-1],
                    'change': hist['Close'].iloc[-1] - hist['Open'].iloc[0],
                    'change_percent': ((hist['Close'].iloc[-1] - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100,
                    'volume': hist['Volume'].iloc[-1],
                    'high': hist['High'].max(),
                    'low': hist['Low'].min()
                }
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_all_houses_data(self):
        data = {}
        for house, info in houses.items():
            stock_data = self.get_stock_data(info['symbol'])
            if stock_data:
                data[house] = {
                    **info,
                    **stock_data,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        return data
    
    def generate_trading_signals(self, house_data):
        signals = []
        for house, data in house_data.items():
            # Simple signal generation based on price movement
            if data['change_percent'] > 2:
                signals.append({
                    'house': house,
                    'signal': 'BUY',
                    'strength': 'STRONG',
                    'reason': f"{data['name']} shows strong upward momentum"
                })
            elif data['change_percent'] < -2:
                signals.append({
                    'house': house,
                    'signal': 'SELL',
                    'strength': 'STRONG',
                    'reason': f"{data['name']} is losing ground"
                })
        return signals

trader = WesterosTrader()

@app.route('/')
def index():
    return render_template('index.html', houses=houses)

@app.route('/api/houses')
def get_houses_data():
    data = trader.get_all_houses_data()
    return jsonify(data)

@app.route('/api/signals')
def get_signals():
    data = trader.get_all_houses_data()
    signals = trader.generate_trading_signals(data)
    return jsonify(signals)

@app.route('/api/portfolio/<user_id>')
def get_portfolio(user_id):
    if user_id not in portfolios:
        portfolios[user_id] = {
            'gold': 10000,  # Starting gold
            'holdings': {},
            'transactions': []
        }
    return jsonify(portfolios[user_id])

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    data = request.json
    user_id = data.get('user_id', 'default_user')
    house = data.get('house')
    action = data.get('action')  # 'buy' or 'sell'
    quantity = int(data.get('quantity', 1))
    
    if user_id not in portfolios:
        portfolios[user_id] = {
            'gold': 10000,
            'holdings': {},
            'transactions': []
        }
    
    # Get current price
    house_data = trader.get_stock_data(houses[house]['symbol'])
    if not house_data:
        return jsonify({'error': 'Unable to fetch current price'}), 400
    
    current_price = house_data['current_price']
    total_cost = current_price * quantity
    
    if action == 'buy':
        if portfolios[user_id]['gold'] < total_cost:
            return jsonify({'error': 'Insufficient gold'}), 400
        
        portfolios[user_id]['gold'] -= total_cost
        if house not in portfolios[user_id]['holdings']:
            portfolios[user_id]['holdings'][house] = 0
        portfolios[user_id]['holdings'][house] += quantity
        
    elif action == 'sell':
        if house not in portfolios[user_id]['holdings'] or portfolios[user_id]['holdings'][house] < quantity:
            return jsonify({'error': 'Insufficient holdings'}), 400
        
        portfolios[user_id]['gold'] += total_cost
        portfolios[user_id]['holdings'][house] -= quantity
        if portfolios[user_id]['holdings'][house] == 0:
            del portfolios[user_id]['holdings'][house]
    
    # Record transaction
    transaction = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'house': house,
        'action': action,
        'quantity': quantity,
        'price': current_price,
        'total': total_cost
    }
    portfolios[user_id]['transactions'].append(transaction)
    
    return jsonify({
        'success': True,
        'portfolio': portfolios[user_id],
        'transaction': transaction
    })

def background_price_updates():
    """Background task to update prices and emit to connected clients"""
    while True:
        try:
            data = trader.get_all_houses_data()
            socketio.emit('price_update', data)
            time.sleep(30)  # Update every 30 seconds
        except Exception as e:
            print(f"Error in background updates: {e}")
            time.sleep(60)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'data': 'Connected to Westeros Trading Bot'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    import sys, os
    # Use Heroku's PORT if available
    port = int(os.environ.get('PORT', 5000))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default {port}.")
    update_thread = threading.Thread(target=background_price_updates, daemon=True)
    update_thread.start()
    print("🏰 Westeros Trading Bot is starting...")
    print("🌙 Winter is coming, but profits are already here!")
    print(f"🚀 Access the bot at: http://localhost:{port}")
    # Use eventlet for production
    import eventlet
    import eventlet.wsgi
    socketio.run(app, host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'False') == 'True') 