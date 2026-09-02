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

# Handle START import gracefully
try:
    from langgraph.graph import START
except ImportError:
    # In older versions, START is not exported; use string
    START = "__start__"

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
        """Build the LangGraph workflow with conditional edges for error handling."""
        
        builder = StateGraph(AgentState)
        
        # Add nodes
        builder.add_node("collect_data", self._collect_data)
        builder.add_node("analyze_technical", self._analyze_technical)
        builder.add_node("analyze_sentiment", self._analyze_sentiment)
        builder.add_node("make_decision", self._make_decision)
        builder.add_node("check_risk", self._check_risk)
        
        # Start edge
        builder.add_edge(START, "collect_data")
        
        # Conditional edges: route to END on failure
        builder.add_conditional_edges(
            "collect_data",
            lambda state: "analyze_technical" if state.step != "failed" else END
        )
        builder.add_conditional_edges(
            "analyze_technical",
            lambda state: "analyze_sentiment" if state.step != "failed" else END
        )
        builder.add_conditional_edges(
            "analyze_sentiment",
            lambda state: "make_decision" if state.step != "failed" else END
        )
        builder.add_conditional_edges(
            "make_decision",
            lambda state: "check_risk" if state.step != "failed" else END
        )
        builder.add_conditional_edges(
            "check_risk",
            lambda state: END if state.step != "failed" else END
        )
        
        return builder.compile()
    
    def _collect_data(self, state: AgentState) -> dict:
        """Node: Collect market data."""
        return self.data_collector.run(state)
    
    def _analyze_technical(self, state: AgentState) -> dict:
        """Node: Analyze technical indicators."""
        if state.step == "failed":
            return {"step": "failed"}
        return self.technical_analyst.run(state)
    
    def _analyze_sentiment(self, state: AgentState) -> dict:
        """Node: Analyze market sentiment."""
        if state.step == "failed":
            return {"step": "failed"}
        return self.sentiment_analyst.run(state)
    
    def _make_decision(self, state: AgentState) -> dict:
        """Node: Make trading decision."""
        if state.step == "failed":
            return {"step": "failed"}
        return self.portfolio_manager.run(state)
    
    def _check_risk(self, state: AgentState) -> dict:
        """Node: Validate decision against risk rules."""
        if state.step == "failed":
            return {"step": "failed"}
        return self.risk_manager.run(state)
    
    def run(self, symbol: str = "BTC/USDT") -> dict:
        """Run the trading workflow for a symbol."""
        logger.info(f"Starting trading workflow for {symbol}")
        
        initial_state = AgentState(symbol=symbol)
        result = self.graph.invoke(initial_state)
        
        # Log final decision if successful
        if result.get("step") != "failed" and result.get("trade_decision"):
            logger.info(f"Workflow complete. Decision: {result['trade_decision'].signal.value}")
            
            # Send Telegram notification
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