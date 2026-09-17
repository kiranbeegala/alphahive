import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from app.core.config import settings
from app.core.database import get_db_connection

class AnalyticsAgent:
    def __init__(self):
        self.name = "Performance & Reflection Agent"
        self.role = "Quantitative Metrics & Strategy Optimization"

    def compute_metrics(self) -> Dict[str, Any]:
        """
        Calculates authentic institutional performance metrics from trade ledger and portfolio snapshots.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch closed trades
        cursor.execute("SELECT * FROM trades WHERE status != 'OPEN' ORDER BY exit_time ASC")
        closed_trades = [dict(row) for row in cursor.fetchall()]

        # Fetch active positions
        cursor.execute("SELECT * FROM positions")
        active_positions = [dict(row) for row in cursor.fetchall()]

        # Fetch latest portfolio state
        cursor.execute("SELECT * FROM portfolio ORDER BY id DESC LIMIT 1")
        port_row = cursor.fetchone()
        
        # Fetch equity history for drawdown
        cursor.execute("SELECT equity FROM portfolio ORDER BY id ASC")
        equity_history = [r[0] for r in cursor.fetchall()]
        
        conn.close()

        total_trades = len(closed_trades)
        wins = [t for t in closed_trades if t['pnl'] > 0]
        losses = [t for t in closed_trades if t['pnl'] <= 0]
        
        gross_profit = sum(t['pnl'] for t in wins) if wins else 0.0
        gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0.0
        total_realized_pnl = sum(t['pnl'] for t in closed_trades) if closed_trades else 0.0
        total_fees = port_row['total_fees_paid'] if port_row else 0.0
        
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0
        profit_factor = round(gross_profit / (gross_loss + 1e-9), 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 0.0)
        
        # Authentic Sharpe & Sortino (requires at least 3 completed trades)
        if total_trades >= 3:
            returns = [t['pnl_pct'] for t in closed_trades]
            mean_ret = np.mean(returns)
            std_ret = np.std(returns) + 1e-9
            sharpe = round(float(np.sqrt(252) * (mean_ret / std_ret)), 2)
            
            downside = [r for r in returns if r < 0]
            if downside and len(downside) > 1:
                downside_std = np.std(downside) + 1e-9
                sortino = round(float(np.sqrt(252) * (mean_ret / downside_std)), 2)
            else:
                sortino = sharpe
        else:
            sharpe = 0.0
            sortino = 0.0

        # Real Max Drawdown calculation from actual equity trajectory
        max_drawdown = 0.0
        if len(equity_history) > 1:
            peaks = np.maximum.accumulate(equity_history)
            drawdowns = (peaks - equity_history) / (peaks + 1e-9)
            max_drawdown = round(float(np.max(drawdowns) * 100), 2)

        # Strategy breakdown
        strategy_stats = {}
        for t in closed_trades:
            strat = t['strategy']
            if strat not in strategy_stats:
                strategy_stats[strat] = {"trades": 0, "wins": 0, "pnl": 0.0}
            strategy_stats[strat]["trades"] += 1
            if t['pnl'] > 0:
                strategy_stats[strat]["wins"] += 1
            strategy_stats[strat]["pnl"] = round(strategy_stats[strat]["pnl"] + t['pnl'], 2)

        unrealized_total = sum(p['unrealized_pnl'] for p in active_positions)
        cash_balance = port_row['cash'] if port_row else settings.INITIAL_BALANCE
        margin_blocked = port_row['margin_blocked'] if port_row else 0.0
        
        # Real Total Equity = Cash + Margin Blocked + Unrealized MTM
        current_equity = round(cash_balance + margin_blocked + unrealized_total, 2)
        total_return_pct = round(((current_equity - settings.INITIAL_BALANCE) / settings.INITIAL_BALANCE) * 100, 2)

        return {
            "initial_balance": settings.INITIAL_BALANCE,
            "current_equity": current_equity,
            "cash_balance": round(cash_balance, 2),
            "margin_blocked": round(margin_blocked, 2),
            "unrealized_pnl": round(unrealized_total, 2),
            "realized_pnl": round(total_realized_pnl, 2),
            "total_fees_paid": round(total_fees, 2),
            "total_return_pct": total_return_pct,
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round(win_rate, 1),
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown_pct": max_drawdown,
            "strategy_breakdown": strategy_stats,
            "active_positions_count": len(active_positions),
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

    def generate_reflection_report(self) -> str:
        metrics = self.compute_metrics()
        report = (
            f"AlphaHive Performance Summary: Equity ₹{metrics['current_equity']:,.2f} "
            f"(P&L: ₹{metrics['realized_pnl']:+,.2f}, Return: {metrics['total_return_pct']:+.2f}%). "
            f"Win Rate: {metrics['win_rate']:.1f}% ({metrics['winning_trades']}W / {metrics['losing_trades']}L). "
            f"Sharpe Ratio: {metrics['sharpe_ratio']}, Max Drawdown: {metrics['max_drawdown_pct']:.2f}%. "
            f"Active Margin: ₹{metrics['margin_blocked']:,.2f}, Total Brokerage & Taxes Paid: ₹{metrics['total_fees_paid']:,.2f}."
        )
        return report

analytics_agent = AnalyticsAgent()
