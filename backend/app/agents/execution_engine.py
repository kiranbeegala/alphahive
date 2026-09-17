import uuid
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.database import get_db_connection
from app.agents.learning_agent import learning_agent

class ExecutionEngineAgent:
    def __init__(self):
        self.name = "Virtual Broker Execution Engine"
        self.role = "Indian Market Realistic Friction & Fill Simulator"
        self.flat_brokerage = settings.BROKERAGE_FLAT_INR
        self.base_slippage = settings.BASE_SLIPPAGE_BPS / 10000.0

    def _calculate_statutory_charges(self, turnover: float, side: str, is_option: bool = False) -> Dict[str, float]:
        """
        Calculates authentic Indian NSE F&O transaction friction:
        - Brokerage: ₹20 flat
        - STT: 0.0125% on Futures SELL side ONLY (or 0.0625% on Option SELL side)
        - Exchange Txn Charge: 0.00345%
        - GST: 18% on (Brokerage + Exchange Txn Charge)
        - Stamp Duty: 0.002% on BUY side ONLY
        - SEBI Turnover: ₹10 / crore (0.0001%)
        """
        brokerage = self.flat_brokerage
        
        if side == "SELL":
            stt_rate = settings.STT_OPTIONS_SELL_PCT if is_option else settings.STT_FUTURES_SELL_PCT
            stt = turnover * stt_rate
        else:
            stt = 0.0
            
        exchange_txn = turnover * settings.EXCHANGE_TXN_FEE_PCT
        gst = (brokerage + exchange_txn) * settings.GST_PCT
        stamp_duty = turnover * settings.STAMP_DUTY_BUY_PCT if side == "BUY" else 0.0
        sebi_charges = turnover * settings.SEBI_FEE_PCT
        
        total_charges = round(brokerage + stt + exchange_txn + gst + stamp_duty + sebi_charges, 2)
        return {
            "total_charges": total_charges,
            "brokerage": brokerage,
            "stt": round(stt, 2),
            "exchange_txn": round(exchange_txn, 2),
            "gst": round(gst, 2),
            "stamp_duty": round(stamp_duty, 2),
            "sebi_charges": round(sebi_charges, 2)
        }

    def _get_margin_rate(self, symbol: str) -> float:
        match = next((item for item in settings.WATCHLIST if item["symbol"] == symbol or symbol in item["symbol"]), None)
        return match.get("margin_pct", 0.15) if match else 0.15

    def execute_order(self, signal: Dict[str, Any], quantity: float, cro_note: str) -> Optional[Dict[str, Any]]:
        """
        Executes Indian F&O order with margin reservation, spread crossing, slippage, and statutory charges.
        """
        raw_price = signal['entry_price']
        direction = signal['direction']
        symbol = signal['symbol']

        spread_half = 0.05
        slippage_pct = self.base_slippage + random.uniform(0.00005, 0.00015)
        slippage_cost = round(raw_price * slippage_pct / 0.05) * 0.05

        if direction == "BUY":
            fill_price = round((raw_price + spread_half + slippage_cost) / 0.05) * 0.05
        else:
            fill_price = round((raw_price - spread_half - slippage_cost) / 0.05) * 0.05

        turnover = fill_price * quantity
        charges = self._calculate_statutory_charges(turnover, direction)
        entry_fee = charges['total_charges']
        slippage_total = round(slippage_cost * quantity, 2)
        
        margin_rate = self._get_margin_rate(symbol)
        margin_required = round(turnover * margin_rate, 2)

        trade_id = f"trd-{uuid.uuid4().hex[:8]}"
        opened_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update Portfolio State: Deduct fee and reserve margin
        cursor.execute("SELECT equity, cash, margin_blocked, total_fees_paid FROM portfolio ORDER BY id DESC LIMIT 1")
        port = cursor.fetchone()
        current_equity = port['equity'] if port else settings.INITIAL_BALANCE
        current_cash = port['cash'] if port else settings.INITIAL_BALANCE
        current_margin = port['margin_blocked'] if port else 0.0
        current_fees = port['total_fees_paid'] if port else 0.0

        new_cash = current_cash - margin_required - entry_fee
        new_margin = current_margin + margin_required
        new_equity = current_equity - entry_fee
        new_fees = current_fees + entry_fee

        cursor.execute("""
        UPDATE portfolio SET equity = ?, cash = ?, margin_blocked = ?, total_fees_paid = ?
        WHERE id = (SELECT id FROM portfolio ORDER BY id DESC LIMIT 1)
        """, (round(new_equity, 2), round(new_cash, 2), round(new_margin, 2), round(new_fees, 2)))

        # Insert into trades
        cursor.execute("""
        INSERT INTO trades (id, symbol, side, entry_time, entry_price, quantity, margin_blocked, stop_loss, take_profit, fee, slippage, status, strategy, rationale, risk_reward_ratio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id,
            symbol,
            direction,
            opened_at,
            fill_price,
            quantity,
            margin_required,
            signal['stop_loss'],
            signal['take_profit'],
            entry_fee,
            slippage_total,
            "OPEN",
            signal['strategy'],
            f"{cro_note} | Rationale: {signal['rationale']}",
            signal.get('risk_reward_ratio', 2.0)
        ))

        # Insert active position
        cursor.execute("""
        INSERT OR REPLACE INTO positions (symbol, side, size, entry_price, mark_price, margin_blocked, unrealized_pnl, unrealized_pnl_pct, stop_loss, take_profit, opened_at, strategy)
        VALUES (?, ?, ?, ?, ?, ?, 0.0, 0.0, ?, ?, ?, ?)
        """, (
            symbol,
            direction,
            quantity,
            fill_price,
            fill_price,
            margin_required,
            signal['stop_loss'],
            signal['take_profit'],
            opened_at,
            signal['strategy']
        ))

        conn.commit()
        conn.close()

        fill_report = {
            "trade_id": trade_id,
            "symbol": symbol,
            "side": direction,
            "quantity": quantity,
            "requested_price": raw_price,
            "executed_price": fill_price,
            "margin_reserved": margin_required,
            "spread_incurred": round(spread_half * 2, 2),
            "slippage_incurred": slippage_total,
            "fee_incurred": entry_fee,
            "charges_breakdown": charges,
            "stop_loss": signal['stop_loss'],
            "take_profit": signal['take_profit'],
            "opened_at": opened_at,
            "strategy": signal['strategy']
        }
        return fill_report

    def update_positions_on_tick(self, symbol: str, current_price: float) -> List[Dict[str, Any]]:
        """
        Updates Mark-to-Market P&L on live price tick, trails stop-loss to break-even at +1.0R, checks TP/SL triggers, and triggers Reinforcement Learning.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM positions WHERE symbol = ?", (symbol,))
        pos = cursor.fetchone()
        
        closed_events = []

        if pos:
            side = pos['side']
            size = pos['size']
            entry_price = pos['entry_price']
            margin_blocked = pos['margin_blocked']
            sl = pos['stop_loss']
            tp = pos['take_profit']
            strategy = pos['strategy']
            opened_at = pos['opened_at']

            # Calculate Unrealized PnL in INR
            if side == "BUY":
                u_pnl = (current_price - entry_price) * size
                u_pnl_pct = ((current_price - entry_price) / entry_price) * 100
                hit_tp = current_price >= tp
                hit_sl = current_price <= sl
                # Break-Even Trail: If price moves >= +1.0R (halfway to TP), trail SL to Entry
                risk_dist = abs(entry_price - sl)
                if (current_price - entry_price) >= risk_dist and sl < entry_price:
                    sl = entry_price
            else: # SELL / SHORT
                u_pnl = (entry_price - current_price) * size
                u_pnl_pct = ((entry_price - current_price) / entry_price) * 100
                hit_tp = current_price <= tp
                hit_sl = current_price >= sl
                # Break-Even Trail for Short
                risk_dist = abs(sl - entry_price)
                if (entry_price - current_price) >= risk_dist and sl > entry_price:
                    sl = entry_price

            if hit_tp or hit_sl:
                exit_reason = "CLOSED_TP" if hit_tp else "CLOSED_SL"
                exit_price = tp if hit_tp else sl
                turnover = exit_price * size
                exit_charges = self._calculate_statutory_charges(turnover, "SELL" if side == "BUY" else "BUY")
                exit_fee = exit_charges['total_charges']
                
                gross_pnl = (exit_price - entry_price) * size if side == "BUY" else (entry_price - exit_price) * size
                net_realized_pnl = round(gross_pnl - exit_fee, 2)
                realized_pct = round((gross_pnl / (entry_price * size)) * 100, 2)
                closed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                # Update Trade Record
                cursor.execute("""
                UPDATE trades SET 
                    exit_time = ?, exit_price = ?, pnl = ?, pnl_pct = ?, fee = fee + ?, status = ?
                WHERE symbol = ? AND status = 'OPEN'
                """, (closed_at, exit_price, net_realized_pnl, realized_pct, exit_fee, exit_reason, symbol))

                # Remove from Active Positions
                cursor.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))

                # Release Margin and Settle Cash Flows in Portfolio
                self._settle_portfolio_on_close(cursor, margin_blocked, net_realized_pnl, exit_fee)

                closed_data = {
                    "event": "POSITION_CLOSED",
                    "symbol": symbol,
                    "side": side,
                    "exit_reason": exit_reason,
                    "exit_price": exit_price,
                    "realized_pnl": net_realized_pnl,
                    "realized_pct": realized_pct,
                    "strategy": strategy,
                    "timestamp": closed_at
                }

                # 🧠 Continuous Reinforcement Learning Loop
                learning_reflection = learning_agent.process_closed_trade(closed_data)
                closed_data["learning_reflection"] = learning_reflection

                closed_events.append(closed_data)
            else:
                # Update Mark Price, Stop Loss (trailed), & Unrealized PnL
                cursor.execute("""
                UPDATE positions SET mark_price = ?, stop_loss = ?, unrealized_pnl = ?, unrealized_pnl_pct = ?
                WHERE symbol = ?
                """, (current_price, sl, round(u_pnl, 2), round(u_pnl_pct, 2), symbol))

        conn.commit()
        conn.close()
        return closed_events

    def _settle_portfolio_on_close(self, cursor, margin_released: float, net_pnl: float, exit_fee: float):
        cursor.execute("SELECT equity, cash, margin_blocked, total_trades, winning_trades, losing_trades, realized_pnl, total_fees_paid FROM portfolio ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            new_margin = max(0.0, row['margin_blocked'] - margin_released)
            new_cash = row['cash'] + margin_released + net_pnl
            new_realized_pnl = row['realized_pnl'] + net_pnl
            new_fees = row['total_fees_paid'] + exit_fee
            
            new_equity = new_cash + new_margin
            
            total_trades = row['total_trades'] + 1
            winning_trades = row['winning_trades'] + (1 if net_pnl > 0 else 0)
            losing_trades = row['losing_trades'] + (1 if net_pnl <= 0 else 0)
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0

            cursor.execute("SELECT MAX(equity) FROM portfolio")
            max_past_equity = cursor.fetchone()[0] or settings.INITIAL_BALANCE
            peak_equity = max(max_past_equity, new_equity)
            drawdown = max(0.0, ((peak_equity - new_equity) / peak_equity) * 100)

            cursor.execute("""
            INSERT INTO portfolio (timestamp, equity, cash, margin_blocked, unrealized_pnl, realized_pnl, total_fees_paid, total_trades, winning_trades, losing_trades, win_rate, sharpe_ratio, max_drawdown)
            VALUES (?, ?, ?, ?, 0.0, ?, ?, ?, ?, ?, ?, 0.0, ?)
            """, (
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                round(new_equity, 2),
                round(new_cash, 2),
                round(new_margin, 2),
                round(new_realized_pnl, 2),
                round(new_fees, 2),
                total_trades,
                winning_trades,
                losing_trades,
                round(win_rate, 1),
                round(drawdown, 2)
            ))

execution_engine_agent = ExecutionEngineAgent()
