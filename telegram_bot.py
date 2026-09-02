import os
import requests
from flask import Flask, request
from loguru import logger
from dotenv import load_dotenv
from app.core.orchestrator import TradingOrchestrator

load_dotenv()
app = Flask(__name__)

# Paper trading state - $1000 realistic capital
paper_balance = 1000
paper_portfolio = {}

# Active pairs (matches run_247.py)
ACTIVE_PAIRS = [
    "BTC/USDT",
    "ETH/USDT", 
    "SOL/USDT",
    "ADA/USDT",
    "AVAX/USDT",
    "DOGE/USDT",
    "DOT/USDT",
    "LINK/USDT"
]

def send_telegram_message(chat_id, text, reply_markup=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")

def get_price(symbol):
    import ccxt
    try:
        exchange = ccxt.kraken()
        ticker = exchange.fetch_ticker(symbol)
        return ticker.get('last', ticker.get('close', 0))
    except:
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or 'message' not in data:
        return 'OK', 200
    
    message = data['message']
    chat_id = message['chat']['id']
    text = message.get('text', '').strip().lower()
    
    # Inline keyboard
    keyboard = {
        "inline_keyboard": [
            [{"text": "📊 Status", "callback_data": "status"}],
            [{"text": "🔍 Scan", "callback_data": "scan"}],
            [{"text": "💰 Buy 50", "callback_data": "buy_50"}, {"text": "💵 Sell 50", "callback_data": "sell_50"}],
            [{"text": "📈 Price BTC", "callback_data": "price_btc"}, {"text": "📈 Price ETH", "callback_data": "price_eth"}],
            [{"text": "📈 Price SOL", "callback_data": "price_sol"}],
            [{"text": "❓ Help", "callback_data": "help"}]
        ]
    }
    
    if text == '/start' or text == '/help':
        msg = """🤖 <b>Trading Bot Active</b>

💰 Starting Capital: $1,000 (paper)

Click buttons below or type commands.
"""
        send_telegram_message(chat_id, msg, keyboard)
        return 'OK', 200
    
    elif text == '/status':
        msg = f"💰 Balance: ${paper_balance:,.2f}\n\n<b>Holdings:</b>\n"
        has_holdings = False
        for pair, qty in paper_portfolio.items():
            price = get_price(pair)
            if price and qty > 0:
                has_holdings = True
                value = qty * price
                msg += f"{pair}: {qty:.4f} (${value:,.2f})\n"
        if not has_holdings:
            msg += "No holdings\n"
        send_telegram_message(chat_id, msg, keyboard)
        return 'OK', 200
    
    elif text == '/scan':
        send_telegram_message(chat_id, "🔍 Scanning all pairs...")
        orch = TradingOrchestrator(send_telegram=False)
        for pair in ACTIVE_PAIRS:
            result = orch.run(symbol=pair)
            dec = result.get("trade_decision")
            if dec:
                signal_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⏸️"}.get(dec.signal.value, "⚪")
                send_telegram_message(chat_id, f"{pair}: {signal_emoji} <b>{dec.signal.value}</b> ({dec.confidence:.0%})")
        send_telegram_message(chat_id, "✅ Scan complete!", keyboard)
        return 'OK', 200
    
    elif text.startswith('/price '):
        symbol = text.split(' ')[1].upper()
        if not symbol.endswith('/USDT'):
            symbol = f"{symbol}/USDT"
        price = get_price(symbol)
        if price:
            send_telegram_message(chat_id, f"{symbol}: <b>${price:,.2f}</b>", keyboard)
        else:
            send_telegram_message(chat_id, f"❌ Could not fetch {symbol}", keyboard)
        return 'OK', 200
    
    elif text == '/pairs':
        msg = "📊 <b>Active Pairs:</b>\n" + "\n".join(ACTIVE_PAIRS)
        send_telegram_message(chat_id, msg, keyboard)
        return 'OK', 200
    
    elif text.startswith('/buy '):
        parts = text.split(' ')
        if len(parts) != 3:
            send_telegram_message(chat_id, "❌ Format: /buy SYMBOL AMOUNT")
            return 'OK', 200
        
        symbol = parts[1].upper()
        if not symbol.endswith('/USDT'):
            symbol = f"{symbol}/USDT"
        
        try:
            amount = float(parts[2])
        except:
            send_telegram_message(chat_id, "❌ Invalid amount")
            return 'OK', 200
        
        if amount > paper_balance:
            send_telegram_message(chat_id, f"❌ Insufficient balance: ${paper_balance:,.2f}")
            return 'OK', 200
        
        price = get_price(symbol)
        if not price:
            send_telegram_message(chat_id, f"❌ Could not fetch {symbol}")
            return 'OK', 200
        
        qty = amount / price
        paper_portfolio[symbol] = paper_portfolio.get(symbol, 0) + qty
        paper_balance -= amount
        
        send_telegram_message(chat_id, f"✅ Bought {qty:.4f} {symbol} at ${price:,.2f}")
        return 'OK', 200
    
    elif text.startswith('/sell '):
        parts = text.split(' ')
        if len(parts) != 3:
            send_telegram_message(chat_id, "❌ Format: /sell SYMBOL AMOUNT")
            return 'OK', 200
        
        symbol = parts[1].upper()
        if not symbol.endswith('/USDT'):
            symbol = f"{symbol}/USDT"
        
        try:
            amount = float(parts[2])
        except:
            send_telegram_message(chat_id, "❌ Invalid amount")
            return 'OK', 200
        
        price = get_price(symbol)
        if not price:
            send_telegram_message(chat_id, f"❌ Could not fetch {symbol}")
            return 'OK', 200
        
        qty = amount / price
        if paper_portfolio.get(symbol, 0) < qty:
            send_telegram_message(chat_id, f"❌ Insufficient {symbol} balance")
            return 'OK', 200
        
        paper_portfolio[symbol] = paper_portfolio.get(symbol, 0) - qty
        paper_balance += amount
        
        send_telegram_message(chat_id, f"✅ Sold {qty:.4f} {symbol} at ${price:,.2f}")
        return 'OK', 200
    
    else:
        send_telegram_message(chat_id, "Unknown command. Type /help for commands.", keyboard)
        return 'OK', 200

# Handle callback queries (button clicks)
@app.route('/callback', methods=['POST'])
def callback():
    data = request.get_json()
    if not data or 'callback_query' not in data:
        return 'OK', 200
    
    callback = data['callback_query']
    chat_id = callback['message']['chat']['id']
    data = callback['data']
    
    if data == 'status':
        msg = f"💰 Balance: ${paper_balance:,.2f}\n\n<b>Holdings:</b>\n"
        has_holdings = False
        for pair, qty in paper_portfolio.items():
            price = get_price(pair)
            if price and qty > 0:
                has_holdings = True
                value = qty * price
                msg += f"{pair}: {qty:.4f} (${value:,.2f})\n"
        if not has_holdings:
            msg += "No holdings\n"
        send_telegram_message(chat_id, msg)
    
    elif data == 'scan':
        send_telegram_message(chat_id, "🔍 Scanning all pairs...")
        orch = TradingOrchestrator(send_telegram=False)
        for pair in ACTIVE_PAIRS:
            result = orch.run(symbol=pair)
            dec = result.get("trade_decision")
            if dec:
                signal_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⏸️"}.get(dec.signal.value, "⚪")
                send_telegram_message(chat_id, f"{pair}: {signal_emoji} <b>{dec.signal.value}</b> ({dec.confidence:.0%})")
        send_telegram_message(chat_id, "✅ Scan complete!")
    
    elif data == 'buy_50':
        symbol = "BTC/USDT"
        amount = 50
        price = get_price(symbol)
        if not price:
            send_telegram_message(chat_id, f"❌ Could not fetch {symbol}")
            return 'OK', 200
        if amount > paper_balance:
            send_telegram_message(chat_id, f"❌ Insufficient balance: ${paper_balance:,.2f}")
            return 'OK', 200
        qty = amount / price
        paper_portfolio[symbol] = paper_portfolio.get(symbol, 0) + qty
        paper_balance -= amount
        send_telegram_message(chat_id, f"✅ Bought {qty:.4f} BTC at ${price:,.2f}")
    
    elif data == 'sell_50':
        symbol = "BTC/USDT"
        amount = 50
        price = get_price(symbol)
        if not price:
            send_telegram_message(chat_id, f"❌ Could not fetch {symbol}")
            return 'OK', 200
        qty = amount / price
        if paper_portfolio.get(symbol, 0) < qty:
            send_telegram_message(chat_id, f"❌ Insufficient BTC balance")
            return 'OK', 200
        paper_portfolio[symbol] = paper_portfolio.get(symbol, 0) - qty
        paper_balance += amount
        send_telegram_message(chat_id, f"✅ Sold {qty:.4f} BTC at ${price:,.2f}")
    
    elif data == 'price_btc':
        price = get_price("BTC/USDT")
        send_telegram_message(chat_id, f"BTC/USDT: <b>${price:,.2f}</b>" if price else "❌ Could not fetch")
    
    elif data == 'price_eth':
        price = get_price("ETH/USDT")
        send_telegram_message(chat_id, f"ETH/USDT: <b>${price:,.2f}</b>" if price else "❌ Could not fetch")
    
    elif data == 'price_sol':
        price = get_price("SOL/USDT")
        send_telegram_message(chat_id, f"SOL/USDT: <b>${price:,.2f}</b>" if price else "❌ Could not fetch")
    
    elif data == 'help':
        msg = """🤖 <b>Available Commands</b>

/status - Show portfolio
/scan - Run scan on all pairs
/price BTC - Get price
/buy BTC 100 - Paper buy
/sell BTC 100 - Paper sell
/pairs - Show active pairs
/help - Show this menu"""
        send_telegram_message(chat_id, msg)
    
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)