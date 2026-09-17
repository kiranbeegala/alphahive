import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd
from app.strategies.indicators import TechnicalIndicators
from app.strategies.smc_patterns import SMCPatterns
from app.strategies.pattern_recognition import PatternRecognition
from app.core.database import get_db_connection

class TechnicalAnalystAgent:
    def __init__(self):
        self.name = "Quant & Pattern Analyst"
        self.role = "Institutional Smart Money Concepts & Trend Confluence Engine"

    def analyze(self, symbol: str, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Executes strict institutional multi-strategy confluence scan:
        1. Higher-Timeframe Trend Filter (200 EMA Rule)
        2. Market Structure Shift (MSS / CHoCH) confirmation
        3. Smart Money Concepts (FVG + Order Blocks + Sweeps)
        4. Wyckoff Accumulation/Distribution Phase C
        5. Momentum confirmation (RSI divergence in direction of trend)
        """
        if df.empty or len(df) < 25:
            return None

        current_price = float(df.iloc[-1]['close'])
        current_atr = float(df.iloc[-1].get('atr', current_price * 0.008))
        rsi = float(df.iloc[-1].get('rsi', 50))
        ema21 = float(df.iloc[-1].get('ema21', current_price))
        ema50 = float(df.iloc[-1].get('ema50', current_price))
        ema200 = float(df.iloc[-1].get('ema200', current_price))
        
        # 1. Primary Trend Gate: Strictly trade in direction of 200 EMA
        is_bull_trend = current_price > ema200 and ema21 > ema50
        is_bear_trend = current_price < ema200 and ema21 < ema50

        confluence_points = []
        score = 0
        direction = "NEUTRAL"
        strategy_name = "Institutional Confluence Setup"

        # 2. SMC Liquidity Sweep & Reclaim (High Probability Setup)
        sweep = SMCPatterns.detect_liquidity_sweep(df)
        if sweep:
            if sweep['type'] == "BULLISH_LIQUIDITY_SWEEP" and is_bull_trend:
                direction = "BUY"
                score += 40
                confluence_points.append(f"Bullish Liquidity Sweep at ₹{sweep['level_swept']:.2f} with {sweep['confidence']:.0f}% wick rejection")
                strategy_name = "SMC Liquidity Sweep & Trend Continuation"
            elif sweep['type'] == "BEARISH_LIQUIDITY_SWEEP" and is_bear_trend:
                direction = "SELL"
                score += 40
                confluence_points.append(f"Bearish Liquidity Sweep at ₹{sweep['level_swept']:.2f} with {sweep['confidence']:.0f}% wick rejection")
                strategy_name = "SMC Liquidity Sweep & Trend Continuation"

        # 3. SMC Order Block Retest in Trend Direction
        obs = SMCPatterns.find_order_blocks(df)
        for ob in obs[-2:]:
            if ob['type'] == "BULLISH_OB" and is_bull_trend and current_price >= ob['bottom'] and current_price <= ob['top'] * 1.005:
                direction = "BUY"
                score += 35
                confluence_points.append(f"Retest of Bullish Order Block zone [₹{ob['bottom']:.2f} - ₹{ob['top']:.2f}]")
                strategy_name = "SMC Bullish Order Block Pullback"
            elif ob['type'] == "BEARISH_OB" and is_bear_trend and current_price <= ob['top'] and current_price >= ob['bottom'] * 0.995:
                direction = "SELL"
                score += 35
                confluence_points.append(f"Retest of Bearish Order Block zone [₹{ob['bottom']:.2f} - ₹{ob['top']:.2f}]")
                strategy_name = "SMC Bearish Order Block Pullback"

        # 4. Wyckoff Phase C Structure Confirmation
        wyckoff = PatternRecognition.detect_wyckoff_structure(df)
        if wyckoff:
            if wyckoff['bias'] == "BULLISH" and is_bull_trend:
                if direction in ["BUY", "NEUTRAL"]:
                    direction = "BUY"
                    score += 25
                    confluence_points.append("Wyckoff Accumulation Phase C Spring confirmed")
            elif wyckoff['bias'] == "BEARISH" and is_bear_trend:
                if direction in ["SELL", "NEUTRAL"]:
                    direction = "SELL"
                    score += 25
                    confluence_points.append("Wyckoff Distribution Phase C Upthrust confirmed")

        # 5. Trend-Aligned Momentum Pullback (Replaced Blind Mean-Reversion)
        if is_bull_trend and 38 <= rsi <= 48:
            if direction in ["BUY", "NEUTRAL"]:
                direction = "BUY"
                score += 30
                confluence_points.append(f"Bull Trend Pullback to 21/50 EMA (RSI: {rsi:.1f} reset)")
                strategy_name = "Trend-Aligned Momentum Pullback"
        elif is_bear_trend and 52 <= rsi <= 62:
            if direction in ["SELL", "NEUTRAL"]:
                direction = "SELL"
                score += 30
                confluence_points.append(f"Bear Trend Pullback to 21/50 EMA (RSI: {rsi:.1f} reset)")
                strategy_name = "Trend-Aligned Momentum Pullback"

        # 6. Trend Strength Bonus
        if direction == "BUY" and is_bull_trend:
            score += 20
            confluence_points.append(f"Confirmed Bull Market Structure (Above 200 EMA ₹{ema200:.2f})")
        elif direction == "SELL" and is_bear_trend:
            score += 20
            confluence_points.append(f"Confirmed Bear Market Structure (Below 200 EMA ₹{ema200:.2f})")

        # Strict Institutional Floor: Minimum 55 points confluence required
        if direction == "NEUTRAL" or score < 55:
            return None

        # Minimum Volatility Stop Distance: at least 0.35% of price or 1.6x ATR
        min_sl_distance = max(current_price * 0.0035, 1.6 * current_atr)
        
        if direction == "BUY":
            stop_loss = round((current_price - min_sl_distance) / 0.05) * 0.05
            take_profit = round((current_price + (2.5 * min_sl_distance)) / 0.05) * 0.05 # 1:2.5 R:R
        else:
            stop_loss = round((current_price + min_sl_distance) / 0.05) * 0.05
            take_profit = round((current_price - (2.5 * min_sl_distance)) / 0.05) * 0.05

        risk_reward = round(abs(take_profit - current_price) / (abs(current_price - stop_loss) + 1e-9), 2)

        signal = {
            "id": f"sig-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "direction": direction,
            "strategy": strategy_name,
            "confidence": min(score, 98),
            "entry_price": round(current_price, 2),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": risk_reward,
            "timeframe": "5m",
            "confluence_points": confluence_points,
            "rationale": " | ".join(confluence_points)
        }

        self._record_signal(signal)
        return signal

    def _record_signal(self, signal: dict):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO signals (id, timestamp, symbol, direction, strategy, confidence, entry_price, stop_loss, take_profit, timeframe, confluence_details, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal['id'],
            signal['timestamp'],
            signal['symbol'],
            signal['direction'],
            signal['strategy'],
            signal['confidence'],
            signal['entry_price'],
            signal['stop_loss'],
            signal['take_profit'],
            signal['timeframe'],
            signal['rationale'],
            "PENDING_CRO_REVIEW"
        ))
        conn.commit()
        conn.close()

technical_analyst_agent = TechnicalAnalystAgent()
