import requests
import os
from loguru import logger

class TelegramService:
    """Service to send messages to Telegram."""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    def send_message(self, message: str) -> bool:
        """Send a message to Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram credentials missing")
            return False
        
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram message failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    def format_signal_message(self, decision, market_data, tech_indicators, sentiment_score, sentiment_summary) -> str:
        """Format a trading signal as a Telegram message."""
        
        # Determine emoji based on signal
        signal_emoji = {
            "BUY": "🟢",
            "SELL": "🔴",
            "HOLD": "⏸️"
        }.get(decision.signal.value, "⚪")
        
        message = f"""
{signal_emoji} <b>TRADING SIGNAL</b> {signal_emoji}

📊 <b>Symbol:</b> {market_data.symbol}
💵 <b>Price:</b> ${market_data.price:,.2f}
📉 <b>24h Change:</b> {market_data.change_24h:.2f}%
📈 <b>24h High/Low:</b> ${market_data.high_24h:,.2f} / ${market_data.low_24h:,.2f}

<b>📐 TECHNICAL ANALYSIS</b>
RSI: {tech_indicators.rsi:.1f} ({"Oversold" if tech_indicators.rsi < 30 else "Overbought" if tech_indicators.rsi > 70 else "Neutral"})
MACD: {"Bullish" if tech_indicators.macd and tech_indicators.macd_signal and tech_indicators.macd > tech_indicators.macd_signal else "Bearish"}
Price vs BB: {"Above Upper" if tech_indicators.bb_upper and market_data.price > tech_indicators.bb_upper else "Below Lower" if tech_indicators.bb_lower and market_data.price < tech_indicators.bb_lower else "Within Bands"}

<b>💭 SENTIMENT</b>
Score: {sentiment_score:.2f} ({"Bullish" if sentiment_score > 0.3 else "Bearish" if sentiment_score < -0.3 else "Neutral"})
Summary: {sentiment_summary[:200]}...

<b>🎯 DECISION</b>
Signal: {decision.signal.value} {signal_emoji}
Confidence: {decision.confidence:.1%}
Reason: {decision.reason[:300]}...
"""
        
        # Add TP/SL if available
        if decision.entry_price:
            message += f"\n\n<b>💰 ENTRY:</b> ${decision.entry_price:.2f}"
        if decision.stop_loss:
            message += f"\n<b>🛑 STOP LOSS:</b> ${decision.stop_loss:.2f}"
        if decision.take_profit:
            message += f"\n<b>🎯 TAKE PROFIT:</b> ${decision.take_profit:.2f}"
        if decision.position_size:
            message += f"\n<b>📊 POSITION SIZE:</b> ${decision.position_size:.2f}"
        
        # Add timestamp
        from datetime import datetime
        message += f"\n\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message