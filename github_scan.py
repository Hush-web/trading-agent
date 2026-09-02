import os
from dotenv import load_dotenv
from loguru import logger
from app.core.orchestrator import TradingOrchestrator

load_dotenv()

def main():
    logger.info("🚀 Running GitHub Actions scan...")
    
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY not found")
        return
    
    orch = TradingOrchestrator(send_telegram=True)
    
    # All pairs to scan
    symbols = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "ADA/USDT",
        "AVAX/USDT",
        "DOGE/USDT"
    ]
    
    for symbol in symbols:
        logger.info(f"Scanning {symbol}...")
        orch.run(symbol=symbol)

if __name__ == "__main__":
    main()