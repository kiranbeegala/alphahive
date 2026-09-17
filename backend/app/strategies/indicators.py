import pandas as pd
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 30:
            return df
            
        data = df.copy()
        
        # Exponential Moving Averages
        data['ema9'] = data['close'].ewm(span=9, adjust=False).mean()
        data['ema21'] = data['close'].ewm(span=21, adjust=False).mean()
        data['ema50'] = data['close'].ewm(span=50, adjust=False).mean()
        data['ema200'] = data['close'].ewm(span=200, adjust=False).mean()
        
        # RSI (14)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD (12, 26, 9)
        ema12 = data['close'].ewm(span=12, adjust=False).mean()
        ema26 = data['close'].ewm(span=26, adjust=False).mean()
        data['macd'] = ema12 - ema26
        data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
        data['macd_hist'] = data['macd'] - data['macd_signal']
        
        # Average True Range (ATR 14)
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = tr.rolling(window=14).mean()
        
        # Bollinger Bands (20, 2)
        data['bb_middle'] = data['close'].rolling(window=20).mean()
        bb_std = data['close'].rolling(window=20).std()
        data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
        data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
        data['bb_width'] = (data['bb_upper'] - data['bb_lower']) / (data['bb_middle'] + 1e-9)
        
        # Volume Moving Average & Volume Spike
        data['vol_sma20'] = data['volume'].rolling(window=20).mean()
        data['vol_spike'] = data['volume'] > (data['vol_sma20'] * 1.6)
        
        # Statistical Mean Reversion Z-Score
        data['zscore_20'] = (data['close'] - data['bb_middle']) / (bb_std + 1e-9)
        
        return data

    @staticmethod
    def detect_rsi_divergence(df: pd.DataFrame, lookback: int = 15) -> dict:
        if len(df) < lookback + 5:
            return {"bullish_div": False, "bearish_div": False}
            
        recent = df.iloc[-lookback:]
        
        # Bullish Divergence: Price Lower Low, RSI Higher Low
        price_low_idx1 = recent['low'].iloc[:-3].idxmin()
        price_low_idx2 = recent['low'].iloc[-3:].idxmin()
        
        bullish = False
        if recent.loc[price_low_idx2, 'low'] < recent.loc[price_low_idx1, 'low']:
            if recent.loc[price_low_idx2, 'rsi'] > recent.loc[price_low_idx1, 'rsi']:
                bullish = True
                
        # Bearish Divergence: Price Higher High, RSI Lower High
        price_high_idx1 = recent['high'].iloc[:-3].idxmax()
        price_high_idx2 = recent['high'].iloc[-3:].idxmax()
        
        bearish = False
        if recent.loc[price_high_idx2, 'high'] > recent.loc[price_high_idx1, 'high']:
            if recent.loc[price_high_idx2, 'rsi'] < recent.loc[price_high_idx1, 'rsi']:
                bearish = True
                
        return {"bullish_div": bullish, "bearish_div": bearish}
