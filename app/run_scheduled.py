import os
import time
import schedule
from dotenv import load_dotenv
from loguru import logger
from app.core.orchestrator import TradingOrchestrator

load_dotenv()

def run_signal():
    """Run the trading signal and send to Telegram."""
    try:
        logger.info("Running scheduled signal...")
        orchestrator = TradingOrchestrator(send_telegram=True)
        orchestrator.run(symbol="BTC/USDT")
    except Exception as e:
        logger.error(f"Signal generation failed: {e}")

if __name__ == "__main__":
    # Run immediately on start
    run_signal()
    
    # Schedule to run every hour
    schedule.every(1).hours.do(run_signal)
    
    logger.info("Scheduled signal bot started. Running every hour.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)