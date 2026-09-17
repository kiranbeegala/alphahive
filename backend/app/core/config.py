import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AlphaHive Indian Equities & F&O Autonomous Desk"
    VERSION: str = "1.1.0"
    API_PREFIX: str = "/api/v1"
    
    # Capital & Portfolio Defaults (Indian Rupees)
    INITIAL_BALANCE: float = 1000000.0  # ₹10,00,000 INR (10 Lakhs Virtual Capital)
    CURRENCY: str = "INR"
    CURRENCY_SYMBOL: str = "₹"
    
    # Risk Parameters (CRO Agent Defaults)
    MAX_RISK_PER_TRADE_PCT: float = 0.015   # 1.5% max risk per trade (₹15,000 on ₹10L)
    MAX_DAILY_DRAWDOWN_PCT: float = 0.030   # 3.0% daily drawdown circuit breaker (₹30,000 max daily loss)
    MAX_OPEN_POSITIONS: int = 4
    MIN_RISK_REWARD_RATIO: float = 1.8      # 1:1.8 minimum R:R ratio
    MAX_PORTFOLIO_MARGIN_PCT: float = 0.70  # Max 70% total capital allocated to margin
    
    # Authentic Indian Market Friction (NSE Equity / F&O Breakdown)
    BROKERAGE_FLAT_INR: float = 20.0       # ₹20 flat per executed order
    STT_FUTURES_SELL_PCT: float = 0.000125 # 0.0125% STT on Futures sell side only
    STT_OPTIONS_SELL_PCT: float = 0.000625 # 0.0625% STT on Options premium sell side
    STT_EQUITY_INTRADAY_SELL: float = 0.00025 # 0.025% on Intraday equity sell
    EXCHANGE_TXN_FEE_PCT: float = 0.0000345 # 0.00345% NSE transaction charge
    GST_PCT: float = 0.18                  # 18% GST on (Brokerage + Txn Charges + SEBI)
    STAMP_DUTY_BUY_PCT: float = 0.00002    # 0.002% Stamp duty on buy side only
    SEBI_FEE_PCT: float = 0.000001         # ₹10 per crore (0.0001%)
    BASE_SLIPPAGE_BPS: float = 1.5         # 1.5 bps realistic fill slippage
    
    # Target Web Platform & Data Feed
    TARGET_PLATFORM: str = "Zerodha Kite Web"
    TARGET_BASE_URL: str = "https://kite.zerodha.com"
    DATA_PROVIDER: str = "AngelOne SmartAPI & NSE Feed"
    
    # Supported Indian Equities & F&O Watchlist
    WATCHLIST: list = [
        {"symbol": "NIFTY", "name": "NIFTY 50 Index / Futures", "category": "F&O Index", "lot_size": 25, "base_price": 24850.0, "tick_size": 0.05, "margin_pct": 0.12},
        {"symbol": "BANKNIFTY", "name": "BANK NIFTY Index / Futures", "category": "F&O Index", "lot_size": 15, "base_price": 51400.0, "tick_size": 0.05, "margin_pct": 0.14},
        {"symbol": "FINNIFTY", "name": "FIN NIFTY Index / Futures", "category": "F&O Index", "lot_size": 25, "base_price": 23600.0, "tick_size": 0.05, "margin_pct": 0.12},
        {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "category": "F&O Stock", "lot_size": 250, "base_price": 2980.0, "tick_size": 0.05, "margin_pct": 0.18},
        {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "category": "F&O Stock", "lot_size": 550, "base_price": 1640.0, "tick_size": 0.05, "margin_pct": 0.18},
        {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "category": "F&O Stock", "lot_size": 700, "base_price": 1210.0, "tick_size": 0.05, "margin_pct": 0.18},
        {"symbol": "TATAMOTORS.NS", "name": "Tata Motors Ltd", "category": "F&O Stock", "lot_size": 575, "base_price": 1060.0, "tick_size": 0.05, "margin_pct": 0.20},
        {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "category": "F&O Stock", "lot_size": 175, "base_price": 4450.0, "tick_size": 0.05, "margin_pct": 0.18},
    ]
    
    DATABASE_URL: str = "sqlite:///alphahive.db"
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

settings = Settings()
