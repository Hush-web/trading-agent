import ccxt
import pandas as pd
from datetime import datetime
from loguru import logger
from app.models.trade import MarketData, AgentState

class DataCollector:
    """Fetches real-time market data from exchanges."""
    
    def __init__(self, exchange_id="binance"):
        self.exchange = getattr(ccxt, exchange_id)({
            'enableRateLimit': True,
        })
    
    def fetch_market_data(self, symbol: str) -> MarketData:
        """Fetch current market data for a symbol."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            # CCXT may use different keys for volume; handle all common ones
            volume = ticker.get('quoteVolume') or ticker.get('baseVolume') or ticker.get('volume', 0)
            
            return MarketData(
                symbol=symbol,
                price=ticker.get('last', ticker.get('close', 0)),
                volume=volume,
                high_24h=ticker.get('high', 0),
                low_24h=ticker.get('low', 0),
                change_24h=ticker.get('percentage', 0) or 0,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            raise
    
    def get_historical_ohlcv(self, symbol: str, timeframe='1h', limit=100):
        """Fetch historical OHLCV data for technical analysis."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            raise
    
    def run(self, state: AgentState) -> dict:
        """Execute the data collection step."""
        try:
            logger.info(f"Fetching market data for {state.symbol}")
            market_data = self.fetch_market_data(state.symbol)
            return {"market_data": market_data, "step": "technical"}
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            return {"error": str(e), "step": "failed"}