import os
from dotenv import load_dotenv
from loguru import logger
from app.core.orchestrator import TradingOrchestrator

load_dotenv()

def main():
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY not found in .env file")
        return
    
    orchestrator = TradingOrchestrator(send_telegram=True)
    result = orchestrator.run(symbol="BTC/USDT")
    
    print("\n" + "="*60)
    print("TRADING DECISION")
    print("="*60)
    
    if result.get("step") == "failed":
        print(f"Workflow failed: {result.get('error', 'Unknown error')}")
        print("="*60)
        return
    
    market_data = result.get("market_data")
    if market_data:
        print(f"Symbol: {market_data.symbol}")
        print(f"Price: ${market_data.price:,.2f}")
        print(f"24h Change: {market_data.change_24h:.2f}%")
    else:
        print("No market data available.")
    
    tech_indicators = result.get("technical_indicators")
    if tech_indicators and tech_indicators.rsi:
        print(f"\nRSI: {tech_indicators.rsi:.1f}")
    
    sentiment_score = result.get("sentiment_score")
    if sentiment_score is not None:
        print(f"Sentiment Score: {sentiment_score:.2f}")
    
    trade_decision = result.get("trade_decision")
    if trade_decision:
        print(f"\nDecision: {trade_decision.signal.value}")
        print(f"Confidence: {trade_decision.confidence:.2f}")
        print(f"Reason: {trade_decision.reason[:200]}...")
        if trade_decision.entry_price:
            print(f"Entry: ${trade_decision.entry_price:.2f}")
        if trade_decision.stop_loss:
            print(f"Stop Loss: ${trade_decision.stop_loss:.2f}")
        if trade_decision.take_profit:
            print(f"Take Profit: ${trade_decision.take_profit:.2f}")
    else:
        print("\nNo trading decision was made.")
    
    print("="*60)

if __name__ == "__main__":
    main()