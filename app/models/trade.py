from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
from datetime import datetime

class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class TradeDecision(BaseModel):
    """Final trading decision."""
    signal: Signal = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    reason: str = Field(..., description="Reason for the decision")
    entry_price: Optional[float] = Field(None, description="Suggested entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    position_size: Optional[float] = Field(None, description="Position size in USDT")

class MarketData(BaseModel):
    """Market data for a symbol."""
    symbol: str
    price: float
    volume: float
    high_24h: float
    low_24h: float
    change_24h: float
    timestamp: datetime = Field(default_factory=datetime.now)

class TechnicalIndicators(BaseModel):
    """Technical analysis indicators."""
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None

class AgentState(BaseModel):
    """Shared state for all agents."""
    symbol: str = "BTC/USDT"
    market_data: Optional[MarketData] = None
    technical_indicators: Optional[TechnicalIndicators] = None
    sentiment_score: Optional[float] = None  # -1 to 1 (negative to positive)
    sentiment_summary: Optional[str] = None
    trade_decision: Optional[TradeDecision] = None
    error: Optional[str] = None
    step: Literal["data", "technical", "sentiment", "portfolio", "risk", "done", "failed"] = "data"