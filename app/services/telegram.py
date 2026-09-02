import requests
import os
from loguru import logger
from datetime import datetime

class TelegramService:
    """Service to send messages to Telegram."""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials missing")
    
    def send_message(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram credentials missing")
            return False
        
        # Telegram limit is 4096 characters
        if len(message) > 4000:
            message = message[:3997] + "..."
        
        # Remove problematic characters
        message = message.replace('\u200b', '')
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram message failed: {response.status_code}")
                # Try without HTML formatting
                if response.status_code == 400 and "parse_mode" in response.text:
                    payload["parse_mode"] = None
                    response2 = requests.post(url, json=payload, timeout=10)
                    if response2.status_code == 200:
                        logger.info("Telegram message sent without HTML")
                        return True
                return False
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    def format_signal_message(self, decision, market_data, tech_indicators, sentiment_score, sentiment_summary) -> str:
        signal_emoji = {
            "BUY": "🟢",
            "SELL": "🔴",
            "HOLD": "⏸️"
        }.get(decision.signal.value, "⚪")
        
        price = market_data.price if market_data else 0
        change = market_data.change_24h if market_data else 0
        
        rsi = tech_indicators.rsi if tech_indicators and tech_indicators.rsi else 0
        if rsi < 30:
            rsi_status = "Oversold"
        elif rsi > 70:
            rsi_status = "Overbought"
        else:
            rsi_status = "Neutral"
        
        if sentiment_score > 0.3:
            sentiment_label = "Bullish"
        elif sentiment_score < -0.3:
            sentiment_label = "Bearish"
        else:
            sentiment_label = "Neutral"
        
        # Shortened message to avoid 400 error
        message_lines = []
        message_lines.append(f"{signal_emoji} <b>TRADING SIGNAL</b> {signal_emoji}")
        message_lines.append("")
        message_lines.append(f"📊 <b>{market_data.symbol if market_data else 'N/A'}</b>")
        message_lines.append(f"💰 ${price:,.2f} | {change:.2f}%")
        message_lines.append("")
        message_lines.append(f"📐 RSI: {rsi:.1f} ({rsi_status})")
        message_lines.append(f"💭 Sentiment: {sentiment_score:.2f} ({sentiment_label})")
        message_lines.append("")
        message_lines.append(f"🎯 <b>{decision.signal.value}</b> ({decision.confidence:.0%})")
        if decision.reason:
            message_lines.append(f"📝 {decision.reason[:100]}...")
        
        if decision.entry_price:
            message_lines.append(f"💰 Entry: ${decision.entry_price:.2f}")
        if decision.stop_loss:
            message_lines.append(f"🛑 SL: ${decision.stop_loss:.2f}")
        if decision.take_profit:
            message_lines.append(f"🎯 TP: ${decision.take_profit:.2f}")
        
        message_lines.append("")
        message_lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(message_lines)