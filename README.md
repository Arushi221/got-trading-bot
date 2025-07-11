# 🏰 Westeros Trading Bot

A Game of Thrones themed trading bot that allows you to trade stocks representing the great houses of Westeros. Built with Flask, Socket.IO, and real-time stock data from Yahoo Finance.

## 🌟 Features

### 🏛️ Game of Thrones Theme
- **House Stark** (AAPL) - "Winter is Coming"
- **House Lannister** (MSFT) - "Hear Me Roar"
- **House Targaryen** (GOOGL) - "Fire and Blood"
- **House Baratheon** (AMZN) - "Ours is the Fury"
- **House Tyrell** (TSLA) - "Growing Strong"
- **House Greyjoy** (NVDA) - "We Do Not Sow"

### 📊 Trading Features
- **Real-time stock data** from Yahoo Finance
- **Live price updates** every 30 seconds
- **Portfolio management** with gold currency
- **Trading signals** based on price movements
- **Transaction history** tracking
- **Responsive design** for all devices

### 🎨 Beautiful UI
- Dark medieval theme with gold accents
- House-specific color coding
- Smooth animations and transitions
- Toast notifications for trade confirmations
- Real-time WebSocket updates

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd got-trading-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the trading bot:**
   Open your browser and go to `http://localhost:5000`

## 🎮 How to Use

### Dashboard
- View your current gold balance
- See total portfolio value
- Monitor today's profit/loss
- Browse all houses with real-time prices

### Trading
1. Select a house from the dropdown
2. Choose Buy or Sell action
3. Enter quantity
4. Review current price and total cost
5. Execute the trade

### Portfolio
- View your holdings and their current values
- Track transaction history
- Monitor portfolio performance

### Signals
- View trading signals based on price movements
- Get recommendations for buying or selling
- See signal strength and reasoning

## 🏗️ Architecture

### Backend (Flask)
- **Real-time data fetching** from Yahoo Finance
- **WebSocket support** for live updates
- **RESTful API** for trading operations
- **Portfolio management** with in-memory storage

### Frontend (JavaScript)
- **Real-time updates** via Socket.IO
- **Responsive design** with CSS Grid
- **Interactive trading interface**
- **Toast notifications** for user feedback

### Data Sources
- **Yahoo Finance API** for real stock data
- **Real-time price updates** every 30 seconds
- **Historical data** for trend analysis

## 🎨 Theme Details

### Color Scheme
- **Primary Gold**: #D4AF37 (House Lannister gold)
- **Dark Background**: #1a1a1a (Night's Watch black)
- **Card Background**: #2a2a2a (Castle stone)
- **Success Green**: #4CAF50 (Tyrell green)
- **Danger Red**: #f44336 (Targaryen red)

### House Colors
- **Stark**: Blue (#4a90e2) - Winterfell colors
- **Lannister**: Gold (#d4af37) - Casterly Rock gold
- **Targaryen**: Red (#dc143c) - Dragon fire
- **Baratheon**: Yellow (#ffd700) - Storm's End
- **Tyrell**: Green (#90ee90) - Highgarden
- **Greyjoy**: Dark (#2f4f4f) - Iron Islands

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```env
FLASK_SECRET_KEY=your_secret_key_here
DEBUG=True
```

### Customization
You can modify the houses and their corresponding stocks in `app.py`:
```python
houses = {
    'STARK': {'symbol': 'AAPL', 'name': 'House Stark', 'motto': 'Winter is Coming'},
    # Add more houses here
}
```

## 📱 Features in Detail

### Real-time Trading
- Live price updates every 30 seconds
- Instant trade execution
- Real-time portfolio updates
- WebSocket connection for live data

### Portfolio Management
- Starting gold: 10,000 dragons
- Track holdings by house
- Transaction history
- Portfolio value calculation

### Trading Signals
- Automatic signal generation
- Based on price movements
- Buy/Sell recommendations
- Signal strength indicators

### Responsive Design
- Works on desktop, tablet, and mobile
- Touch-friendly interface
- Adaptive layout
- Fast loading times

## 🛠️ Development

### Project Structure
```
got-trading-bot/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Game of Thrones themed CSS
    └── js/
        └── app.js        # Frontend JavaScript
```

### Adding New Features
1. **New Houses**: Add to the `houses` dictionary in `app.py`
2. **New Indicators**: Modify the `generate_trading_signals` method
3. **UI Changes**: Update CSS in `static/css/style.css`
4. **Frontend Logic**: Modify JavaScript in `static/js/app.js`

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Kill the process using port 5000
   lsof -ti:5000 | xargs kill -9
   ```

2. **Dependencies not found:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Stock data not loading:**
   - Check internet connection
   - Verify Yahoo Finance API availability
   - Check console for error messages

### Debug Mode
Run with debug enabled:
```bash
export FLASK_DEBUG=1
python app.py
```

## 📈 Future Enhancements

- [ ] User authentication and multiple portfolios
- [ ] Advanced trading strategies
- [ ] Historical charts and graphs
- [ ] News integration for house events
- [ ] Mobile app version
- [ ] Backtesting capabilities
- [ ] Social trading features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and entertainment purposes. The Game of Thrones theme is inspired by George R.R. Martin's work.

## 🙏 Acknowledgments

- **George R.R. Martin** for the Game of Thrones universe
- **Yahoo Finance** for stock data
- **Flask** and **Socket.IO** communities
- **Font Awesome** for icons

---

**"When you play the game of thrones, you win or you lose. But when you play the game of trading, you win or you win more."**

🏰 *May your trades be as sharp as Valyrian steel!* ⚔️ 