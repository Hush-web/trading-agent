import pandas as pd
import numpy as np
from loguru import logger
from app.models.trade import TechnicalIndicators, AgentState
from app.agents.data_collector import DataCollector

class TechnicalAnalyst:
    """Calculates technical indicators and analyzes price patterns."""
    
    def __init__(self):
        self.data_collector = DataCollector()
    
    def calculate_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Calculate technical indicators from OHLCV data."""
        close = df['close']
        
        # RSI (Relative Strength Index)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        bb_upper = sma_20 + (std_20 * 2)
        bb_lower = sma_20 - (std_20 * 2)
        
        # Simple Moving Averages
        sma_50 = close.rolling(window=50).mean()
        
        return TechnicalIndicators(
            rsi=float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
            macd=float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
            macd_signal=float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else None,
            bb_upper=float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
            bb_middle=float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
            bb_lower=float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None,
            sma_20=float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
            sma_50=float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None
        )
    
    def generate_analysis(self, indicators: TechnicalIndicators, price: float) -> str:
        """Generate a textual analysis based on indicators."""
        signals = []
        
        if indicators.rsi:
            if indicators.rsi > 70:
                signals.append(f"RSI is overbought ({indicators.rsi:.1f}) - potential sell signal")
            elif indicators.rsi < 30:
                signals.append(f"RSI is oversold ({indicators.rsi:.1f}) - potential buy signal")
            else:
                signals.append(f"RSI is neutral ({indicators.rsi:.1f})")
        
        if indicators.macd and indicators.macd_signal:
            if indicators.macd > indicators.macd_signal:
                signals.append("MACD is bullish (above signal line)")
            else:
                signals.append("MACD is bearish (below signal line)")
        
        if indicators.bb_upper and indicators.bb_lower and price:
            if price > indicators.bb_upper:
                signals.append("Price is above upper Bollinger Band - overextended")
            elif price < indicators.bb_lower:
                signals.append("Price is below lower Bollinger Band - oversold")
            else:
                signals.append("Price is within Bollinger Bands")
        
        return "\n".join(signals) if signals else "No clear technical signals"
    
    def run(self, state: AgentState) -> dict:
        """Execute the technical analysis step."""
        # Guard: if market_data is missing, fail gracefully
        if not state.market_data:
            logger.error("No market data available for technical analysis")
            return {"error": "No market data", "step": "failed"}
        
        try:
            logger.info(f"Calculating technical indicators for {state.symbol}")
            
            # Get historical data
            df = self.data_collector.get_historical_ohlcv(state.symbol)
            
            # Calculate indicators
            indicators = self.calculate_indicators(df)
            
            # Generate analysis
            analysis = self.generate_analysis(indicators, state.market_data.price)
            
            logger.info(f"Technical analysis complete: {analysis[:100]}...")
            
            return {
                "technical_indicators": indicators,
                "step": "sentiment"
            }
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return {"error": str(e), "step": "failed"}