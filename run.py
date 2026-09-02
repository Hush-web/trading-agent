import os
from dotenv import load_dotenv
from loguru import logger
from app.core.orchestrator import TradingOrchestrator

# Load environment variables
load_dotenv()

def main():
    """Run the trading agent."""
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY not found in .env file")
        return
    
    # Create orchestrator with Telegram enabled
    orchestrator = TradingOrchestrator(send_telegram=True)
    
    # Run for Bitcoin
    result = orchestrator.run(symbol="BTC/USDT")
    
    # Display results
    print("\n" + "="*60)
    print("TRADING DECISION")
    print("="*60)
    
    if result.get("step") == "failed":
        print(f"Workflow failed: {result.get('error', 'Unknown error')}")
        print("="*60)
        return
    
    # Safely access attributes from dict
    market_data = result.get("market_data")
    if market_data:
        print(f"Symbol: {market_data.symbol}")
        print(f"Price: ${market_data.price:,.2f}")
        print(f"24h Change: {market_data.change_24h:.2f}%")
    
    tech_indicators = result.get("technical_indicators")
    if tech_indicators:
        print(f"\nTechnical Indicators:")
        if tech_indicators.rsi:
            print(f"  RSI: {tech_indicators.rsi:.1f}")
        else:
            print("  RSI: N/A")
    
    print(f"\nSentiment Score: {result.get('sentiment_score', 'N/A')}")
    if result.get('sentiment_summary'):
        print(f"Sentiment Summary: {result['sentiment_summary'][:100]}...")
    
    trade_decision = result.get("trade_decision")
    if trade_decision:
        print(f"\nDecision: {trade_decision.signal.value}")
        print(f"Confidence: {trade_decision.confidence:.2f}")
        print(f"Reason: {trade_decision.reason[:150]}...")
        if trade_decision.entry_price:
            print(f"Entry: ${trade_decision.entry_price:.2f}")
        if trade_decision.stop_loss:
            print(f"Stop Loss: ${trade_decision.stop_loss:.2f}")
        if trade_decision.take_profit:
            print(f"Take Profit: ${trade_decision.take_profit:.2f}")
    else:
        print("\nNo trading decision was made.")
    
    print("="*60)
    
    # Send a test message if Telegram is configured
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        print("\n📨 Telegram notification sent to your bot!")
    else:
        print("\n⚠️ Telegram not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env")

if __name__ == "__main__":
    main()