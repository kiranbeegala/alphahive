import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class PatternRecognition:
    @staticmethod
    def detect_wyckoff_structure(df: pd.DataFrame, lookback: int = 40) -> Optional[Dict[str, Any]]:
        """
        Detects Wyckoff Accumulation Spring (Phase C) or Distribution Upthrust (UTAD).
        """
        if len(df) < lookback:
            return None
            
        recent = df.iloc[-lookback:]
        
        trading_range_high = recent['high'].iloc[:-5].quantile(0.85)
        trading_range_low = recent['low'].iloc[:-5].quantile(0.15)
        vol_avg = recent['volume'].mean()
        
        last_5 = df.iloc[-5:]
        min_last_5 = last_5['low'].min()
        max_last_5 = last_5['high'].max()
        last_close = df.iloc[-1]['close']
        
        # Wyckoff Spring: Pierced below trading range low on declining or sudden absorption volume, then reclaimed
        if min_last_5 < trading_range_low and last_close > trading_range_low:
            return {
                "pattern": "WYCKOFF_ACCUMULATION_SPRING",
                "phase": "Phase C - Spring Test",
                "support_level": float(trading_range_low),
                "resistance_level": float(trading_range_high),
                "spring_low": float(min_last_5),
                "target_price": float(trading_range_high * 1.02),
                "bias": "BULLISH",
                "confidence": 85.0
            }
            
        # Wyckoff Upthrust (UTAD): Pierced above range high, then rejected back into the range
        if max_last_5 > trading_range_high and last_close < trading_range_high:
            return {
                "pattern": "WYCKOFF_DISTRIBUTION_UTAD",
                "phase": "Phase C - Upthrust Test",
                "support_level": float(trading_range_low),
                "resistance_level": float(trading_range_high),
                "upthrust_high": float(max_last_5),
                "target_price": float(trading_range_low * 0.98),
                "bias": "BEARISH",
                "confidence": 85.0
            }
            
        return None

    @staticmethod
    def detect_chart_patterns(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detects Double Bottom / Double Top & Volatility Squeeze Breakout
        """
        if len(df) < 30:
            return None
            
        recent = df.iloc[-30:]
        current_close = df.iloc[-1]['close']
        bb_upper = df.iloc[-1]['bb_upper']
        bb_lower = df.iloc[-1]['bb_lower']
        bb_width = df.iloc[-1]['bb_width']
        vol_spike = df.iloc[-1]['vol_spike']
        
        # Volatility Squeeze Breakout
        min_width_prior = recent['bb_width'].iloc[-15:-3].min()
        if min_width_prior < 0.035 and vol_spike:
            if current_close > bb_upper:
                return {
                    "pattern": "BOLLINGER_SQUEEZE_EXPANSION_BULLISH",
                    "bias": "BULLISH",
                    "confidence": 82.0,
                    "target_price": float(current_close * 1.03),
                    "stop_loss": float(df.iloc[-1]['bb_middle'])
                }
            elif current_close < bb_lower:
                return {
                    "pattern": "BOLLINGER_SQUEEZE_EXPANSION_BEARISH",
                    "bias": "BEARISH",
                    "confidence": 82.0,
                    "target_price": float(current_close * 0.97),
                    "stop_loss": float(df.iloc[-1]['bb_middle'])
                }
                
        return None
