import sqlite3
import os
from datetime import datetime
from app.core.config import settings

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alphahive.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Portfolio State Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        equity REAL NOT NULL,
        cash REAL NOT NULL,
        margin_blocked REAL NOT NULL DEFAULT 0.0,
        unrealized_pnl REAL NOT NULL DEFAULT 0.0,
        realized_pnl REAL NOT NULL DEFAULT 0.0,
        total_fees_paid REAL NOT NULL DEFAULT 0.0,
        total_trades INTEGER NOT NULL DEFAULT 0,
        winning_trades INTEGER NOT NULL DEFAULT 0,
        losing_trades INTEGER NOT NULL DEFAULT 0,
        win_rate REAL NOT NULL DEFAULT 0.0,
        sharpe_ratio REAL NOT NULL DEFAULT 0.0,
        max_drawdown REAL NOT NULL DEFAULT 0.0
    )
    """)

    # Trades Table (Closed & Active orders)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        entry_time TEXT NOT NULL,
        exit_time TEXT,
        entry_price REAL NOT NULL,
        exit_price REAL,
        quantity REAL NOT NULL,
        margin_blocked REAL NOT NULL DEFAULT 0.0,
        stop_loss REAL NOT NULL,
        take_profit REAL NOT NULL,
        pnl REAL DEFAULT 0.0,
        pnl_pct REAL DEFAULT 0.0,
        fee REAL DEFAULT 0.0,
        slippage REAL DEFAULT 0.0,
        status TEXT NOT NULL, -- OPEN, CLOSED_TP, CLOSED_SL, CLOSED_MANUAL
        strategy TEXT NOT NULL,
        rationale TEXT NOT NULL,
        risk_reward_ratio REAL NOT NULL
    )
    """)

    # Active Positions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        symbol TEXT PRIMARY KEY,
        side TEXT NOT NULL,
        size REAL NOT NULL,
        entry_price REAL NOT NULL,
        mark_price REAL NOT NULL,
        margin_blocked REAL NOT NULL DEFAULT 0.0,
        unrealized_pnl REAL NOT NULL DEFAULT 0.0,
        unrealized_pnl_pct REAL NOT NULL DEFAULT 0.0,
        stop_loss REAL NOT NULL,
        take_profit REAL NOT NULL,
        opened_at TEXT NOT NULL,
        strategy TEXT NOT NULL
    )
    """)

    # Agent Logs & Thoughts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        role TEXT NOT NULL,
        thought_type TEXT NOT NULL, -- PERCEPTION, ANALYSIS, RISK_CHECK, EXECUTION, REFLECTION
        message TEXT NOT NULL,
        details_json TEXT
    )
    """)

    # Strategy Signals Generated
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        symbol TEXT NOT NULL,
        direction TEXT NOT NULL, -- BUY, SELL, NEUTRAL
        strategy TEXT NOT NULL,
        confidence REAL NOT NULL,
        entry_price REAL NOT NULL,
        stop_loss REAL NOT NULL,
        take_profit REAL NOT NULL,
        timeframe TEXT NOT NULL,
        confluence_details TEXT,
        status TEXT NOT NULL -- APPROVED, REJECTED_BY_CRO, EXECUTED
    )
    """)

    # Strategy Weights (Continuous Learning & Reinforcement)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS strategy_weights (
        strategy_name TEXT PRIMARY KEY,
        weight REAL NOT NULL DEFAULT 1.0,
        win_streak INTEGER NOT NULL DEFAULT 0,
        loss_streak INTEGER NOT NULL DEFAULT 0,
        total_trades INTEGER NOT NULL DEFAULT 0,
        winning_trades INTEGER NOT NULL DEFAULT 0,
        realized_pnl REAL NOT NULL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        last_adapted TEXT NOT NULL
    )
    """)

    # Continuous Learning Retrospectives Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning_retrospectives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        trade_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        strategy TEXT NOT NULL,
        outcome TEXT NOT NULL,
        pnl REAL NOT NULL,
        insight TEXT NOT NULL,
        action_taken TEXT NOT NULL
    )
    """)

    # Seed default strategies if not exists
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
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    for strat in strategies:
        cursor.execute("""
        INSERT OR IGNORE INTO strategy_weights (strategy_name, weight, win_streak, loss_streak, total_trades, winning_trades, realized_pnl, status, last_adapted)
        VALUES (?, 1.0, 0, 0, 0, 0, 0.0, 'ACTIVE', ?)
        """, (strat, now_str))

    # Insert initial portfolio state if empty
    cursor.execute("SELECT COUNT(*) FROM portfolio")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO portfolio (timestamp, equity, cash, margin_blocked, unrealized_pnl, realized_pnl, total_fees_paid, total_trades, winning_trades, losing_trades, win_rate, sharpe_ratio, max_drawdown)
        VALUES (?, ?, ?, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0)
        """, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), settings.INITIAL_BALANCE, settings.INITIAL_BALANCE))
        
    conn.commit()
    conn.close()

init_db()
