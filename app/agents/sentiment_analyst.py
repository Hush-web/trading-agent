import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from app.models.trade import AgentState

class SentimentAnalyst:
    """Analyzes market sentiment using LLM."""
    
    def __init__(self):
        self.llm = ChatGroq(
            model="qwen/qwen3.6-27b",
            api_key=os.getenv("GROQ_API_KEY")
        )
    
    def analyze_sentiment(self, market_data, technical_indicators) -> tuple:
        """Analyze market sentiment based on available data."""
        system_prompt = """You are a market sentiment analyst. Analyze the provided market data and technical indicators to determine market sentiment.
        
        Return your response in this exact format:
        
        SENTIMENT_SCORE: [number between -1 and 1, where -1 is extremely bearish, 0 is neutral, 1 is extremely bullish]
        SENTIMENT_SUMMARY: [2-3 sentences explaining your sentiment analysis]
        
        Consider:
        1. Price action and momentum
        2. Technical indicators (RSI, MACD, Bollinger Bands)
        3. Overall market context"""
        
        user_prompt = f"""
        Market Data:
        - Symbol: {market_data.symbol}
        - Price: ${market_data.price:,.2f}
        - 24h Change: {market_data.change_24h:.2f}%
        - 24h Volume: ${market_data.volume:,.0f}
        - 24h High: ${market_data.high_24h:,.2f}
        - 24h Low: ${market_data.low_24h:,.2f}
        
        Technical Indicators:
        - RSI: {technical_indicators.rsi if technical_indicators.rsi else 'N/A'}
        - MACD: {technical_indicators.macd if technical_indicators.macd else 'N/A'}
        - MACD Signal: {technical_indicators.macd_signal if technical_indicators.macd_signal else 'N/A'}
        - Bollinger Upper: {technical_indicators.bb_upper if technical_indicators.bb_upper else 'N/A'}
        - Bollinger Middle: {technical_indicators.bb_middle if technical_indicators.bb_middle else 'N/A'}
        - Bollinger Lower: {technical_indicators.bb_lower if technical_indicators.bb_lower else 'N/A'}
        - SMA 20: {technical_indicators.sma_20 if technical_indicators.sma_20 else 'N/A'}
        - SMA 50: {technical_indicators.sma_50 if technical_indicators.sma_50 else 'N/A'}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        content = response.content
        
        # Parse the response
        score = 0.0
        summary = "Unable to parse sentiment"
        
        lines = content.strip().split('\n')
        for line in lines:
            if 'SENTIMENT_SCORE:' in line:
                try:
                    score = float(line.split('SENTIMENT_SCORE:')[1].strip())
                    score = max(-1, min(1, score))  # Clamp to [-1, 1]
                except:
                    pass
            elif 'SENTIMENT_SUMMARY:' in line:
                summary = line.split('SENTIMENT_SUMMARY:')[1].strip()
        
        return score, summary
    
    def run(self, state: AgentState) -> dict:
        """Execute the sentiment analysis step."""
        # Guard: ensure required data exists
        if not state.market_data or not state.technical_indicators:
            logger.error("Missing market data or technical indicators for sentiment analysis")
            return {"error": "Insufficient data for sentiment", "step": "failed"}
        
        try:
            logger.info(f"Analyzing sentiment for {state.symbol}")
            
            score, summary = self.analyze_sentiment(
                state.market_data,
                state.technical_indicators
            )
            
            logger.info(f"Sentiment score: {score:.2f} - {summary[:50]}...")
            
            return {
                "sentiment_score": score,
                "sentiment_summary": summary,
                "step": "portfolio"
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"error": str(e), "step": "failed"}