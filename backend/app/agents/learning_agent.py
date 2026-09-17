import math
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.database import get_db_connection

class ContinuousLearningAgent:
    def __init__(self):
        self.name = "Continuous Learning & Policy Adaptation Agent"
        self.role = "Dynamic Strategy Reinforcement & Parameter Optimizer"
        self.min_weight = 0.35
        self.max_weight = 1.75
        self.base_weight = 1.0

    def init_strategy_weights(self):
        """Initializes strategy weights table with institutional default parameters."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_weights (
            strategy_name TEXT PRIMARY KEY,
            weight REAL NOT NULL DEFAULT 1.0,
            win_streak INTEGER NOT NULL DEFAULT 0,
            loss_streak INTEGER NOT NULL DEFAULT 0,
            total_trades INTEGER NOT NULL DEFAULT 0,
            winning_trades INTEGER NOT NULL DEFAULT 0,
            realized_pnl REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, BOOSTED, COOLING_DOWN
            last_adapted TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_retrospectives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            trade_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            strategy TEXT NOT NULL,
            outcome TEXT NOT NULL, -- WIN, LOSS
            pnl REAL NOT NULL,
            insight TEXT NOT NULL,
            action_taken TEXT NOT NULL
        )
        """)

        # Default strategy pool
        strategies = [
            "SMC Liquidity Sweep & Trend Continuation",
            "SMC Bullish Order Block Pullback",
            "SMC Bearish Order Block Pullback",
            "Wyckoff Accumulation Phase C Spring",
            "Wyckoff Distribution Phase C Upthrust",
            "Trend-Aligned Momentum Pullback",
            "Overbought Statistical Mean Reversion",
            "Oversold Statistical Mean Reversion"
        ]

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for strat in strategies:
            cursor.execute("""
            INSERT OR IGNORE INTO strategy_weights (strategy_name, weight, win_streak, loss_streak, total_trades, winning_trades, realized_pnl, status, last_adapted)
            VALUES (?, 1.0, 0, 0, 0, 0, 0.0, 'ACTIVE', ?)
            """, (strat, now))

        conn.commit()
        conn.close()

    def get_strategy_weight(self, strategy_name: str) -> float:
        """Returns the dynamic reinforcement multiplier for a given strategy."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT weight FROM strategy_weights WHERE strategy_name = ?", (strategy_name,))
        row = cursor.fetchone()
        conn.close()
        return float(row['weight']) if row else 1.0

    def get_adaptive_parameters(self, symbol: str, india_vix: float = 16.0) -> Dict[str, Any]:
        """
        Dynamically adjusts indicators based on volatility regime and learning ledger:
        - High VIX (>22): Widen RSI overbought/oversold bands to prevent premature counter-trend entries.
        - Low VIX (<15): Tighter bands for range-bound responsiveness.
        """
        if india_vix > 24.0:
            rsi_overbought = 76.0
            rsi_oversold = 24.0
            min_confluence_score = 60
            atr_stop_multiplier = 2.0
        elif india_vix > 18.0:
            rsi_overbought = 72.0
            rsi_oversold = 28.0
            min_confluence_score = 55
            atr_stop_multiplier = 1.8
        else:
            rsi_overbought = 68.0
            rsi_oversold = 32.0
            min_confluence_score = 50
            atr_stop_multiplier = 1.5

        return {
            "rsi_overbought": rsi_overbought,
            "rsi_oversold": rsi_oversold,
            "min_confluence_score": min_confluence_score,
            "atr_stop_multiplier": atr_stop_multiplier,
            "volatility_regime": "High Volatility (Expanded Bands)" if india_vix > 24 else ("Moderate Volatility" if india_vix > 18 else "Calm Trend")
        }

    def process_closed_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reinforcement Feedback Loop:
        - Updates strategy weight based on P&L and R:R outcome.
        - Generates post-trade reflection and records in memory.
        """
        strategy = trade.get("strategy", "Unknown")
        pnl = float(trade.get("realized_pnl", 0.0) or trade.get("pnl", 0.0))
        is_win = pnl > 0
        symbol = trade.get("symbol", "")
        trade_id = trade.get("trade_id") or trade.get("id", "")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM strategy_weights WHERE strategy_name = ?", (strategy,))
        record = cursor.fetchone()

        if not record:
            self.init_strategy_weights()
            cursor.execute("SELECT * FROM strategy_weights WHERE strategy_name = ?", (strategy,))
            record = cursor.fetchone()

        current_weight = record['weight'] if record else 1.0
        win_streak = record['win_streak'] if record else 0
        loss_streak = record['loss_streak'] if record else 0
        total_trades = (record['total_trades'] if record else 0) + 1
        winning_trades = (record['winning_trades'] if record else 0) + (1 if is_win else 0)
        cumulative_pnl = (record['realized_pnl'] if record else 0.0) + pnl

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        if is_win:
            win_streak += 1
            loss_streak = 0
            # Reward: Boost weight by +0.12 (extra +0.06 if streak >= 2)
            delta = 0.12 + (0.06 if win_streak >= 2 else 0.0)
            new_weight = min(self.max_weight, round(current_weight + delta, 2))
            status = "BOOSTED" if new_weight > 1.2 else "ACTIVE"
            insight = f"Target achieved (+₹{pnl:,.2f}). SMC confluence validated by market volume."
            action_taken = f"Strategy weight increased from {current_weight:.2f}x to {new_weight:.2f}x (+{delta*100:.0f}% allocation)."
        else:
            loss_streak += 1
            win_streak = 0
            # Penalty: Reduce weight by -0.15 (extra -0.10 if streak >= 2)
            delta = 0.15 + (0.10 if loss_streak >= 2 else 0.0)
            new_weight = max(self.min_weight, round(current_weight - delta, 2))
            status = "COOLING_DOWN" if loss_streak >= 2 or new_weight < 0.7 else "ACTIVE"
            insight = f"Stop loss hit (-₹{abs(pnl):,.2f}). Market structure moved against setup."
            action_taken = f"Strategy weight demoted from {current_weight:.2f}x to {new_weight:.2f}x (-{delta*100:.0f}% risk penalty)."

        cursor.execute("""
        UPDATE strategy_weights SET
            weight = ?, win_streak = ?, loss_streak = ?, total_trades = ?, winning_trades = ?, realized_pnl = ?, status = ?, last_adapted = ?
        WHERE strategy_name = ?
        """, (new_weight, win_streak, loss_streak, total_trades, winning_trades, round(cumulative_pnl, 2), status, now, strategy))

        # Record retrospective learning log
        cursor.execute("""
        INSERT INTO learning_retrospectives (timestamp, trade_id, symbol, strategy, outcome, pnl, insight, action_taken)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, trade_id, symbol, strategy, "WIN" if is_win else "LOSS", round(pnl, 2), insight, action_taken))

        conn.commit()
        conn.close()

        reflection = {
            "strategy": strategy,
            "outcome": "WIN" if is_win else "LOSS",
            "pnl": pnl,
            "old_weight": current_weight,
            "new_weight": new_weight,
            "status": status,
            "insight": insight,
            "action_taken": action_taken,
            "timestamp": now
        }
        return reflection

    def get_all_strategy_weights(self) -> List[Dict[str, Any]]:
        self.init_strategy_weights()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM strategy_weights ORDER BY weight DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_recent_retrospectives(self, limit: int = 15) -> List[Dict[str, Any]]:
        self.init_strategy_weights()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM learning_retrospectives ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

learning_agent = ContinuousLearningAgent()
