from loguru import logger
from app.models.trade import Signal, AgentState

class RiskManager:
    """Enforces risk limits and validates trading decisions."""
    
    def __init__(self, max_position_size=1000, max_risk_per_trade=0.02):
        self.max_position_size = max_position_size  # Maximum USDT per trade
        self.max_risk_per_trade = max_risk_per_trade  # 2% of portfolio
    
    def validate_decision(self, state: AgentState) -> tuple:
        """Validate a trading decision against risk rules."""
        decision = state.trade_decision
        current_price = state.market_data.price
        
        # Rule 1: No trade if confidence is too low
        if decision.confidence < 0.6:
            return False, f"Confidence too low: {decision.confidence:.2f} < 0.6"
        
        # Rule 2: HOLD is always valid
        if decision.signal == Signal.HOLD:
            return True, "HOLD decision is valid"
        
        # Rule 3: Validate position size
        if decision.position_size and decision.position_size > self.max_position_size:
            return False, f"Position size too large: ${decision.position_size:.2f} > ${self.max_position_size:.2f}"
        
        # Rule 4: Validate stop-loss exists for BUY/SELL
        if decision.signal in [Signal.BUY, Signal.SELL]:
            if not decision.stop_loss:
                return False, "Stop-loss is required for BUY/SELL orders"
            
            # Check stop-loss is reasonable
            if decision.signal == Signal.BUY and decision.stop_loss >= current_price:
                return False, f"Stop-loss (${decision.stop_loss:.2f}) must be below entry (${current_price:.2f})"
            
            if decision.signal == Signal.SELL and decision.stop_loss <= current_price:
                return False, f"Stop-loss (${decision.stop_loss:.2f}) must be above entry (${current_price:.2f})"
        
        return True, "Risk check passed"
    
    def run(self, state: AgentState) -> dict:
        """Execute the risk management step."""
        # Guard: ensure required data exists
        if not state.market_data or not state.trade_decision:
            logger.error("Missing market data or trade decision for risk check")
            return {"error": "Insufficient data for risk", "step": "failed"}
        
        try:
            logger.info(f"Validating trading decision for {state.symbol}")
            
            is_valid, message = self.validate_decision(state)
            
            if is_valid:
                logger.info(f"Risk check passed: {message}")
                return {"step": "done"}
            else:
                logger.warning(f"Risk check failed: {message}")
                # Override with HOLD if risk check fails
                state.trade_decision.signal = Signal.HOLD
                state.trade_decision.reason = f"Risk override: {message}"
                return {"step": "done"}
                
        except Exception as e:
            logger.error(f"Risk management failed: {e}")
            return {"error": str(e), "step": "failed"}