import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from app.models.trade import Signal, TradeDecision, AgentState

class PortfolioManager:
    """Makes the final trading decision based on all analyses."""
    
    def __init__(self):
        self.llm = ChatGroq(
            model="qwen/qwen3.6-27b",
            api_key=os.getenv("GROQ_API_KEY")
        )
    
    def make_decision(self, state: AgentState) -> TradeDecision:
        """Make a trading decision based on all available data."""
        system_prompt = """You are a senior portfolio manager. Based on the technical analysis and sentiment analysis provided, make a trading decision.
        
        Return your response in this exact format:
        
        SIGNAL: [BUY, SELL, or HOLD]
        CONFIDENCE: [number between 0 and 1]
        REASON: [2-3 sentences explaining your decision]
        ENTRY_PRICE: [price or N/A]
        STOP_LOSS: [price or N/A]
        TAKE_PROFIT: [price or N/A]
        POSITION_SIZE: [USDT amount or N/A]
        
        Rules:
        - Only trade when confidence is above 0.6
        - Consider risk-reward ratio (minimum 1:2)
        - Be conservative - capital preservation is priority"""
        
        user_prompt = f"""
        Symbol: {state.symbol}
        Current Price: ${state.market_data.price:,.2f}
        24h Change: {state.market_data.change_24h:.2f}%
        
        Technical Indicators:
        - RSI: {state.technical_indicators.rsi if state.technical_indicators.rsi else 'N/A'}
        - MACD Signal: {state.technical_indicators.macd_signal if state.technical_indicators.macd_signal else 'N/A'}
        
        Sentiment Score: {state.sentiment_score:.2f} (Range: -1 to 1)
        Sentiment Summary: {state.sentiment_summary}
        
        Make a trading decision.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        content = response.content
        
        # Parse the response
        signal = Signal.HOLD
        confidence = 0.0
        reason = "Unable to parse decision"
        entry_price = None
        stop_loss = None
        take_profit = None
        position_size = None
        
        lines = content.strip().split('\n')
        for line in lines:
            if 'SIGNAL:' in line:
                signal_str = line.split('SIGNAL:')[1].strip().upper()
                if signal_str in ['BUY', 'SELL', 'HOLD']:
                    signal = Signal(signal_str)
            elif 'CONFIDENCE:' in line:
                try:
                    confidence = float(line.split('CONFIDENCE:')[1].strip())
                    confidence = max(0, min(1, confidence))
                except:
                    pass
            elif 'REASON:' in line:
                reason = line.split('REASON:')[1].strip()
            elif 'ENTRY_PRICE:' in line:
                try:
                    entry_price = float(line.split('ENTRY_PRICE:')[1].strip().replace('$', ''))
                except:
                    pass
            elif 'STOP_LOSS:' in line:
                try:
                    stop_loss = float(line.split('STOP_LOSS:')[1].strip().replace('$', ''))
                except:
                    pass
            elif 'TAKE_PROFIT:' in line:
                try:
                    take_profit = float(line.split('TAKE_PROFIT:')[1].strip().replace('$', ''))
                except:
                    pass
            elif 'POSITION_SIZE:' in line:
                try:
                    position_size = float(line.split('POSITION_SIZE:')[1].strip().replace('$', ''))
                except:
                    pass
        
        return TradeDecision(
            signal=signal,
            confidence=confidence,
            reason=reason,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size
        )
    
    def run(self, state: AgentState) -> dict:
        """Execute the portfolio management step."""
        # Guard: ensure required data exists
        if not state.market_data or not state.technical_indicators or state.sentiment_score is None:
            logger.error("Missing required data for portfolio decision")
            return {"error": "Insufficient data for decision", "step": "failed"}
        
        try:
            logger.info(f"Making trading decision for {state.symbol}")
            
            decision = self.make_decision(state)
            
            logger.info(f"Decision: {decision.signal.value} with confidence {decision.confidence:.2f}")
            
            return {
                "trade_decision": decision,
                "step": "risk"
            }
        except Exception as e:
            logger.error(f"Portfolio management failed: {e}")
            return {"error": str(e), "step": "failed"}