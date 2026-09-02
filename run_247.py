import time
import os
from dotenv import load_dotenv
from loguru import logger
from app.core.orchestrator import TradingOrchestrator

load_dotenv()

def main():
    logger.info("🚀 Starting 24/7 Trading Bot...")
    
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY not found in .env file")
        return
    
    orch = TradingOrchestrator(send_telegram=True)
    # Added more volatile pairs
    symbols = [
        "BTC/USDT",
        "ETH/USDT", 
        "SOL/USDT",
        "ADA/USDT",
        "AVAX/USDT",
        "DOGE/USDT",
        "DOT/USDT",
        "LINK/USDT"
    ]
    
    while True:
        try:
            logger.info(f"Scanning {len(symbols)} pairs...")
            for symbol in symbols:
                logger.info(f"Processing {symbol}...")
                orch.run(symbol=symbol)
                time.sleep(5)  # Short delay between pairs
            
            logger.info("✅ Scan complete. Sleeping for 1 hour...")
            time.sleep(3600)  # 1 hour
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()