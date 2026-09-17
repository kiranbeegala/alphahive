import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

class SMCPatterns:
    @staticmethod
    def find_fair_value_gaps(df: pd.DataFrame, min_gap_pct: float = 0.001) -> List[Dict[str, Any]]:
        """
        Detects 3-candle Fair Value Gaps (FVG) / Imbalances.
        Bullish FVG: Candle 1 High < Candle 3 Low (Gap between C1 High and C3 Low)
        Bearish FVG: Candle 1 Low > Candle 3 High (Gap between C1 Low and C3 High)
        """
        if len(df) < 5:
            return []
            
        fvgs = []
        for i in range(2, len(df)):
            c1 = df.iloc[i-2]
            c2 = df.iloc[i-1] # Expansion candle
            c3 = df.iloc[i]
            
            # Bullish FVG
            if c3['low'] > c1['high']:
                gap_size = c3['low'] - c1['high']
                gap_pct = gap_size / c2['close']
                if gap_pct >= min_gap_pct:
                    fvgs.append({
                        "type": "BULLISH_FVG",
                        "top": float(c3['low']),
                        "bottom": float(c1['high']),
                        "size": float(gap_size),
                        "index": i,
                        "time": str(c2.get('time', i)),
                        "mitigated": False
                    })
                    
            # Bearish FVG
            elif c3['high'] < c1['low']:
                gap_size = c1['low'] - c3['high']
                gap_pct = gap_size / c2['close']
                if gap_pct >= min_gap_pct:
                    fvgs.append({
                        "type": "BEARISH_FVG",
                        "top": float(c1['low']),
                        "bottom": float(c3['high']),
                        "size": float(gap_size),
                        "index": i,
                        "time": str(c2.get('time', i)),
                        "mitigated": False
                    })
                    
        return fvgs

    @staticmethod
    def find_order_blocks(df: pd.DataFrame, lookback: int = 40) -> List[Dict[str, Any]]:
        """
        Detects Institutional Order Blocks:
        Bullish Order Block: Last down candle before an aggressive upward displacement breaking structure.
        Bearish Order Block: Last up candle before an aggressive downward displacement breaking structure.
        """
        if len(df) < lookback:
            return []
            
        obs = []
        recent = df.iloc[-lookback:].copy().reset_index(drop=True)
        
        for i in range(2, len(recent) - 2):
            c_current = recent.iloc[i]
            c_next1 = recent.iloc[i+1]
            c_next2 = recent.iloc[i+2]
            
            # Check Bullish OB (Down candle followed by strong bullish breakout)
            if c_current['close'] < c_current['open']: # Red candle
                displacement = (c_next2['close'] - c_current['high']) / c_current['close']
                if displacement > 0.006 and c_next1['close'] > c_current['high']:
                    obs.append({
                        "type": "BULLISH_OB",
                        "top": float(c_current['high']),
                        "bottom": float(c_current['low']),
                        "open_price": float(c_current['open']),
                        "close_price": float(c_current['close']),
                        "index": i,
                        "strength": float(displacement * 100)
                    })
                    
            # Check Bearish OB (Up candle followed by strong bearish displacement)
            elif c_current['close'] > c_current['open']: # Green candle
                displacement = (c_current['low'] - c_next2['close']) / c_current['close']
                if displacement > 0.006 and c_next1['close'] < c_current['low']:
                    obs.append({
                        "type": "BEARISH_OB",
                        "top": float(c_current['high']),
                        "bottom": float(c_current['low']),
                        "open_price": float(c_current['open']),
                        "close_price": float(c_current['close']),
                        "index": i,
                        "strength": float(displacement * 100)
                    })
                    
        return obs

    @staticmethod
    def detect_liquidity_sweep(df: pd.DataFrame, lookback: int = 25) -> Optional[Dict[str, Any]]:
        """
        Detects Liquidity Sweeps / Turtle Soups (False Breakout of key Highs/Lows with rapid wick rejection)
        """
        if len(df) < lookback + 5:
            return None
            
        recent = df.iloc[-lookback:]
        current_candle = df.iloc[-1]
        
        prior_high = recent['high'].iloc[:-2].max()
        prior_low = recent['low'].iloc[:-2].min()
        
        # Bullish Sweep: Price pierced below prior low but closed above it (Wick sweep)
        if current_candle['low'] < prior_low and current_candle['close'] > prior_low:
            wick_ratio = (current_candle['close'] - current_candle['low']) / (current_candle['high'] - current_candle['low'] + 1e-9)
            if wick_ratio > 0.45:
                return {
                    "type": "BULLISH_LIQUIDITY_SWEEP",
                    "level_swept": float(prior_low),
                    "sweep_low": float(current_candle['low']),
                    "close": float(current_candle['close']),
                    "confidence": float(min(wick_ratio * 100, 95))
                }
                
        # Bearish Sweep: Price pierced above prior high but closed below it
        if current_candle['high'] > prior_high and current_candle['close'] < prior_high:
            wick_ratio = (current_candle['high'] - current_candle['close']) / (current_candle['high'] - current_candle['low'] + 1e-9)
            if wick_ratio > 0.45:
                return {
                    "type": "BEARISH_LIQUIDITY_SWEEP",
                    "level_swept": float(prior_high),
                    "sweep_high": float(current_candle['high']),
                    "close": float(current_candle['close']),
                    "confidence": float(min(wick_ratio * 100, 95))
                }
                
        return None
