import asyncio
import random
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from app.core.config import settings
from app.core.database import get_db_connection
from app.strategies.indicators import TechnicalIndicators

class SentinelAgent:
    def __init__(self):
        self.name = "Market Sentinel"
        self.role = "AngelOne / NSE Ingestion & Dynamic Tick Engine"
        self.cache = {}
        self.cache_timestamp = {}
        self.live_state = {}  # Holds current evolving price and candle series per symbol
        self.order_books = {}

    def _resolve_ticker(self, symbol: str) -> str:
        symbol_map = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
            "RELIANCE": "RELIANCE.NS",
            "HDFCBANK": "HDFCBANK.NS",
            "ICICIBANK": "ICICIBANK.NS",
            "TATAMOTORS": "TATAMOTORS.NS",
            "TCS": "TCS.NS"
        }
        return symbol_map.get(symbol, symbol)

    def fetch_market_data(self, symbol: str, interval: str = "5m", period: str = "5d") -> pd.DataFrame:
        """
        Fetches base historical candles (cached for 60s) and applies real-time micro-price evolution.
        """
        now = time.time()
        cache_key = f"{symbol}_{interval}"

        # 1. Initialize or refresh base historical data from yfinance if cache expired (>60s)
        if cache_key not in self.cache or (now - self.cache_timestamp.get(cache_key, 0)) > 60:
            try:
                ticker_symbol = self._resolve_ticker(symbol)
                ticker = yf.Ticker(ticker_symbol)
                df = ticker.history(period=period, interval=interval)
                
                if df is None or df.empty or len(df) < 10:
                    df = self._generate_synthetic_candles(symbol)
                else:
                    df = df.reset_index()
                    df.columns = [c.lower() for c in df.columns]
                    if 'datetime' in df.columns:
                        df['time'] = df['datetime'].astype(str)
                    elif 'date' in df.columns:
                        df['time'] = df['date'].astype(str)
                    else:
                        df['time'] = [datetime.utcnow().isoformat()] * len(df)
            except Exception:
                df = self._generate_synthetic_candles(symbol)

            # Store in cache
            self.cache[cache_key] = df
            self.cache_timestamp[cache_key] = now

        # 2. Apply Live Tick Evolution: Evolve the latest candle with realistic micro-ticks
        df = self.cache[cache_key].copy()
        df = self._evolve_live_tick(symbol, df)
        
        # 3. Recompute all technical indicators dynamically
        df = TechnicalIndicators.calculate_all(df)
        return df

    def _evolve_live_tick(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Evolves the current price with authentic NSE 0.05 tick fluctuations and volume accumulation.
        """
        if df.empty:
            return df

        last_row = df.iloc[-1].copy()
        current_close = float(last_row['close'])

        # Initialize live state if needed
        if symbol not in self.live_state:
            self.live_state[symbol] = {
                "price": current_close,
                "ticks_in_candle": 0,
                "candle_start": datetime.utcnow()
            }

        # Generate realistic tick drift (slight random walk with mean-reversion pull)
        volatility_factor = current_close * 0.00018
        random_delta = np.random.normal(0, volatility_factor)
        
        # Snap to 0.05 NSE tick
        tick_delta = round(random_delta / 0.05) * 0.05
        if tick_delta == 0:
            tick_delta = random.choice([-0.05, 0.05, 0.0, 0.05])

        new_price = round((self.live_state[symbol]["price"] + tick_delta) / 0.05) * 0.05
        self.live_state[symbol]["price"] = new_price
        self.live_state[symbol]["ticks_in_candle"] += 1

        # Update last candle's High, Low, Close, Volume
        df.loc[df.index[-1], 'close'] = new_price
        df.loc[df.index[-1], 'high'] = max(float(last_row['high']), new_price)
        df.loc[df.index[-1], 'low'] = min(float(last_row['low']), new_price)
        df.loc[df.index[-1], 'volume'] = float(last_row['volume']) + random.randint(250, 1500)
        df.loc[df.index[-1], 'time'] = datetime.utcnow().strftime("%H:%M:%S")

        # Roll over to new candle after 30 ticks (~90 seconds in simulation)
        if self.live_state[symbol]["ticks_in_candle"] >= 30:
            new_candle = pd.DataFrame([{
                "time": datetime.utcnow().strftime("%H:%M:%S"),
                "open": new_price,
                "high": new_price,
                "low": new_price,
                "close": new_price,
                "volume": 500
            }])
            df = pd.concat([df, new_candle], ignore_index=True)
            self.cache[f"{symbol}_5m"] = df
            self.live_state[symbol]["ticks_in_candle"] = 0

        return df

    def _generate_synthetic_candles(self, symbol: str, n_candles: int = 100) -> pd.DataFrame:
        match = next((item for item in settings.WATCHLIST if item["symbol"] == symbol or symbol in item["symbol"]), None)
        base_price = match["base_price"] if match else 24850.0
        
        times = [datetime.utcnow() - timedelta(minutes=5 * (n_candles - i)) for i in range(n_candles)]
        
        # Use random seed that changes per run
        np.random.seed(int(time.time() * 1000) % 2**32)
        returns = np.random.normal(0.0001, 0.002, n_candles)
        price_series = base_price * np.exp(np.cumsum(returns))
        
        opens = np.round(price_series * (1 + np.random.normal(0, 0.0004, n_candles)) / 0.05) * 0.05
        highs = np.round(np.maximum(opens, price_series) * (1 + np.abs(np.random.normal(0, 0.001, n_candles))) / 0.05) * 0.05
        lows = np.round(np.minimum(opens, price_series) * (1 - np.abs(np.random.normal(0, 0.001, n_candles))) / 0.05) * 0.05
        closes = np.round(price_series / 0.05) * 0.05
        volumes = np.random.uniform(50000, 350000, n_candles)

        df = pd.DataFrame({
            "time": [t.strftime("%H:%M") for t in times],
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes
        })
        return df

    def get_simulated_order_book(self, symbol: str, mid_price: float, depth: int = 5) -> dict:
        """
        Generates realistic NSE 5-Depth Order Book with dynamic volume distribution.
        """
        spread_tick = 0.05
        best_bid = round((mid_price - (spread_tick / 2)) / 0.05) * 0.05
        best_ask = round((mid_price + (spread_tick / 2)) / 0.05) * 0.05
        
        bids = []
        asks = []
        
        for i in range(depth):
            bid_p = round((best_bid - (i * spread_tick)) / 0.05) * 0.05
            bid_orders = random.randint(4, 55)
            bid_v = random.randint(250, 5000) * (i + 1)
            bids.append({"price": bid_p, "orders": bid_orders, "quantity": bid_v})
            
            ask_p = round((best_ask + (i * spread_tick)) / 0.05) * 0.05
            ask_orders = random.randint(4, 55)
            ask_v = random.randint(250, 5000) * (i + 1)
            asks.append({"price": ask_p, "orders": ask_orders, "quantity": ask_v})
            
        total_bid_qty = sum(b['quantity'] for b in bids)
        total_ask_qty = sum(a['quantity'] for a in asks)

        self.order_books[symbol] = {
            "symbol": symbol,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": round(best_ask - best_bid, 2),
            "total_bid_qty": total_bid_qty,
            "total_ask_qty": total_ask_qty,
            "bids": bids,
            "asks": asks,
            "exchange": "NSE",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S")
        }
        return self.order_books[symbol]

    def log_thought(self, thought_type: str, message: str, details: dict = None):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO agent_logs (timestamp, agent_name, role, thought_type, message, details_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            self.name,
            self.role,
            thought_type,
            message,
            str(details) if details else None
        ))
        conn.commit()
        conn.close()

sentinel_agent = SentinelAgent()
