from datetime import datetime
from typing import Dict, Any, Tuple
from app.core.config import settings
from app.core.database import get_db_connection
from app.agents.learning_agent import learning_agent

class CRORiskManagerAgent:
    def __init__(self):
        self.name = "Chief Risk Officer (CRO)"
        self.role = "Indian Markets Capital & F&O Lot Size Risk Gatekeeper"
        self.max_risk_pct = settings.MAX_RISK_PER_TRADE_PCT # 1.5% max risk
        self.min_rr = 1.9 # Institutional minimum 1:1.9 R:R
        self.max_open_pos = 3 # Max 3 concurrent positions
        self.max_daily_dd = settings.MAX_DAILY_DRAWDOWN_PCT # 3.0% daily circuit breaker
        self.max_single_trade_margin_pct = 0.25 # Max 25% portfolio margin per trade (₹2.5L)

    def _get_instrument_specs(self, symbol: str) -> dict:
        match = next((item for item in settings.WATCHLIST if item["symbol"] == symbol or symbol in item["symbol"]), None)
        return {
            "lot_size": match.get("lot_size", 25) if match else 25,
            "margin_pct": match.get("margin_pct", 0.15) if match else 0.15
        }

    def evaluate_and_size_order(self, signal: Dict[str, Any], sentiment: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Validates signal against strict CRO risk rules, sizes order in F&O lots, and scales sizing by strategy reinforcement weight.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Check open positions count
        cursor.execute("SELECT COUNT(*) FROM positions")
        open_count = cursor.fetchone()[0]
        if open_count >= self.max_open_pos:
            conn.close()
            return False, f"Risk Gate: Maximum concurrent positions ({self.max_open_pos}) reached.", 0

        # 2. Check if already positioned in this symbol
        cursor.execute("SELECT COUNT(*) FROM positions WHERE symbol = ?", (signal['symbol'],))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, f"Risk Gate: Existing position already active for {signal['symbol']}.", 0

        # 3. Check Current Portfolio Equity, Available Free Cash & Drawdown
        cursor.execute("SELECT equity, cash, margin_blocked, max_drawdown FROM portfolio ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        equity = row['equity'] if row else settings.INITIAL_BALANCE
        cash = row['cash'] if row else settings.INITIAL_BALANCE
        margin_blocked = row['margin_blocked'] if row else 0.0
        max_dd = row['max_drawdown'] if row else 0.0
        conn.close()

        # Real Drawdown Circuit Breaker
        if max_dd >= (self.max_daily_dd * 100):
            return False, f"Circuit Breaker: Current drawdown ({max_dd:.2f}%) exceeds daily limit ({self.max_daily_dd*100:.1f}%). Trading halted.", 0

        # 4. Check Strategy Reinforcement Learning Weight
        strategy_weight = learning_agent.get_strategy_weight(signal['strategy'])
        if strategy_weight < 0.50:
            return False, f"Risk Gate: Strategy '{signal['strategy']}' is currently COOLING_DOWN (Weight: {strategy_weight:.2f}x). Setup skipped.", 0

        # 5. Check Risk-Reward Ratio
        if signal.get("risk_reward_ratio", 0) < self.min_rr:
            return False, f"Risk Gate: R:R {signal.get('risk_reward_ratio')}:1 below institutional floor of {self.min_rr}:1.", 0

        # 6. Check High Volatility Macro Block
        if sentiment.get("high_volatility_event", False):
            return False, f"Risk Gate: Macro Event Risk ({sentiment.get('top_catalyst', 'Event')}) active. Capital protected in cash.", 0

        # 7. Calculate Lot-Based Position Sizing (Scaled by Learning Weight)
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        price_risk_per_unit = abs(entry_price - stop_loss)
        
        if price_risk_per_unit <= 0:
            return False, "Risk Gate: Invalid stop loss distance.", 0

        # Scale risk budget dynamically (e.g., 1.5% * 1.2x weight = 1.8% on hot streak; 1.5% * 0.7x = 1.05% on drawdowns)
        effective_risk_pct = self.max_risk_pct * min(1.3, max(0.6, strategy_weight))
        capital_at_risk = equity * effective_risk_pct
        raw_units = capital_at_risk / price_risk_per_unit
        
        specs = self._get_instrument_specs(signal['symbol'])
        lot_size = specs["lot_size"]
        margin_pct = specs["margin_pct"]

        lots = max(1, int(raw_units // lot_size))
        final_quantity = int(lots * lot_size)

        # 8. Single-Trade Margin Concentration Cap (Max 25% of Equity = ₹2,50,000)
        max_allowed_margin = equity * self.max_single_trade_margin_pct
        margin_required = (final_quantity * entry_price) * margin_pct

        if margin_required > max_allowed_margin:
            lots = max(1, int(max_allowed_margin / ((lot_size * entry_price) * margin_pct)))
            final_quantity = int(lots * lot_size)
            margin_required = (final_quantity * entry_price) * margin_pct

        # 9. Available Free Cash Verification
        if margin_required > (cash * 0.90): # Leave 10% cash buffer
            lots = max(1, int((cash * 0.90) / ((lot_size * entry_price) * margin_pct)))
            final_quantity = int(lots * lot_size)
            margin_required = (final_quantity * entry_price) * margin_pct

        if margin_required > cash or final_quantity == 0:
            return False, f"Risk Gate: Insufficient free cash (₹{cash:,.2f}) for margin required (₹{margin_required:,.2f}).", 0

        approval_note = (
            f"Approved by CRO (Weight: {strategy_weight:.2f}x): Risked ₹{capital_at_risk:,.2f} ({effective_risk_pct*100:.2f}%), "
            f"Allocated {lots} Lots ({final_quantity} units) @ ₹{entry_price:.2f}, "
            f"Margin: ₹{margin_required:,.2f}, Target R:R {signal['risk_reward_ratio']}:1"
        )
        return True, approval_note, final_quantity

cro_risk_manager_agent = CRORiskManagerAgent()
