from typing import Literal
from langgraph.graph import StateGraph, END
from loguru import logger

from app.models.trade import AgentState
from app.agents.data_collector import DataCollector
from app.agents.technical_analyst import TechnicalAnalyst
from app.agents.sentiment_analyst import SentimentAnalyst
from app.agents.portfolio_manager import PortfolioManager
from app.agents.risk_manager import RiskManager
from app.services.telegram import TelegramService

class TradingOrchestrator:
    """Orchestrates the multi-agent trading workflow."""
    
    def __init__(self, send_telegram: bool = True):
        self.data_collector = DataCollector()
        self.technical_analyst = TechnicalAnalyst()
        self.sentiment_analyst = SentimentAnalyst()
        self.portfolio_manager = PortfolioManager()
        self.risk_manager = RiskManager()
        self.telegram = TelegramService() if send_telegram else None
        
        self.graph = self._build_graph()
    
    def _build_graph(self):
        builder = StateGraph(AgentState)
        
        builder.add_node("collect_data", self._collect_data)
        builder.add_node("analyze_technical", self._analyze_technical)
        builder.add_node("analyze_sentiment", self._analyze_sentiment)
        builder.add_node("make_decision", self._make_decision)
        builder.add_node("check_risk", self._check_risk)
        
        builder.set_entry_point("collect_data")
        
        builder.add_conditional_edges(
            "collect_data",
            lambda state: "analyze_technical" if state.get("step") != "failed" else END
        )
        builder.add_conditional_edges(
            "analyze_technical",
            lambda state: "analyze_sentiment" if state.get("step") != "failed" else END
        )
        builder.add_conditional_edges(
            "analyze_sentiment",
            lambda state: "make_decision" if state.get("step") != "failed" else END
        )
        builder.add_conditional_edges(
            "make_decision",
            lambda state: "check_risk" if state.get("step") != "failed" else END
        )
        builder.add_conditional_edges(
            "check_risk",
            lambda state: END if state.get("step") != "failed" else END
        )
        
        return builder.compile()
    
    def _collect_data(self, state: AgentState) -> dict:
        return self.data_collector.run(state)
    
    def _analyze_technical(self, state: AgentState) -> dict:
        if state.get("step") == "failed":
            return {"step": "failed"}
        return self.technical_analyst.run(state)
    
    def _analyze_sentiment(self, state: AgentState) -> dict:
        if state.get("step") == "failed":
            return {"step": "failed"}
        return self.sentiment_analyst.run(state)
    
    def _make_decision(self, state: AgentState) -> dict:
        if state.get("step") == "failed":
            return {"step": "failed"}
        return self.portfolio_manager.run(state)
    
    def _check_risk(self, state: AgentState) -> dict:
        if state.get("step") == "failed":
            return {"step": "failed"}
        return self.risk_manager.run(state)
    
    def run(self, symbol: str = "BTC/USDT") -> dict:
        logger.info(f"Starting trading workflow for {symbol}")
        
        # Pass a proper dictionary with all required fields
        initial_state = {
            "symbol": symbol,
            "market_data": None,
            "technical_indicators": None,
            "sentiment_score": None,
            "sentiment_summary": None,
            "trade_decision": None,
            "error": None,
            "step": "data"
        }
        
        result = self.graph.invoke(initial_state)
        
        if result.get("step") != "failed" and result.get("trade_decision"):
            logger.info(f"Workflow complete. Decision: {result['trade_decision'].signal.value}")
            
            if self.telegram:
                try:
                    message = self.telegram.format_signal_message(
                        result['trade_decision'],
                        result['market_data'],
                        result['technical_indicators'],
                        result['sentiment_score'],
                        result['sentiment_summary']
                    )
                    self.telegram.send_message(message)
                except Exception as e:
                    logger.error(f"Telegram notification failed: {e}")
        else:
            logger.warning("Workflow completed with errors or no decision")
        
        return result
