from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.core.config import settings
from app.core.database import get_db_connection, init_db
from app.core.event_bus import event_bus
from app.core.market_calendar import market_calendar
from app.core.angel_client import angel_client
from app.agents.sentinel import sentinel_agent
from app.agents.analytics_agent import analytics_agent
from app.agents.browser_mimic import browser_mimic_agent
from app.agents.learning_agent import learning_agent
from app.agents.orchestrator import orchestrator

router = APIRouter()

class SwitchSymbolRequest(BaseModel):
    symbol: str

@router.get("/status")
def get_system_status():
    market_info = market_calendar.get_market_status()
    return {
        "status": "ONLINE",
        "orchestrator_running": orchestrator.is_running,
        "active_symbol": orchestrator.active_symbol,
        "market": market_info,
        "angelone": {
            "is_configured": angel_client.has_valid_credentials(),
            "is_authenticated": angel_client.is_authenticated,
            "client_id": angel_client.client_id or "Unconfigured"
        },
        "desk_agents": [
            {"name": "Market Sentinel", "role": "Data Ingestion & Dynamic Ticks", "status": "ACTIVE"},
            {"name": "Quant & Pattern Analyst", "role": "SMC & Confluence Engine", "status": "ACTIVE"},
            {"name": "Macro & Sentiment Analyst", "role": "India Macro & Event Risk", "status": "ACTIVE"},
            {"name": "Chief Risk Officer (CRO)", "role": "Capital & F&O Lot Gatekeeper", "status": "ACTIVE"},
            {"name": "Virtual Broker Engine", "role": "Friction & Cash Flow Simulator", "status": "ACTIVE"},
            {"name": "Browser Mimic Agent", "role": "Zerodha Kite Web Automation", "status": "ACTIVE"},
            {"name": "Performance & Reflection Agent", "role": "Quantitative Alpha Analytics", "status": "ACTIVE"}
        ],
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@router.get("/market-calendar")
def get_market_calendar():
    return market_calendar.get_market_status()

@router.get("/angelone/test")
def test_angelone_connection():
    return angel_client.authenticate()

@router.get("/watchlist")
def get_watchlist():
    return settings.WATCHLIST

@router.post("/orchestrator/start")
async def start_orchestrator():
    await orchestrator.start()
    return {"status": "SUCCESS", "message": "AlphaHive Autonomous Trading Desk Started", "running": True}

@router.post("/orchestrator/stop")
async def stop_orchestrator():
    await orchestrator.stop()
    return {"status": "SUCCESS", "message": "AlphaHive Trading Desk Paused", "running": False}

@router.post("/symbol/switch")
def switch_symbol(req: SwitchSymbolRequest):
    orchestrator.set_active_symbol(req.symbol)
    return {"status": "SUCCESS", "active_symbol": req.symbol}

@router.get("/candles")
def get_candles(symbol: str = "NIFTY", interval: str = "5m", period: str = "5d"):
    df = sentinel_agent.fetch_market_data(symbol, interval=interval, period=period)
    candles = df.fillna(0).to_dict(orient="records")
    return {
        "symbol": symbol,
        "interval": interval,
        "count": len(candles),
        "candles": candles
    }

@router.get("/positions")
def get_positions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM positions")
    positions = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return positions

@router.get("/trades")
def get_trades(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades ORDER BY entry_time DESC LIMIT ?", (limit,))
    trades = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return trades

@router.get("/signals")
def get_signals(limit: int = 30):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?", (limit,))
    signals = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return signals

@router.get("/agent-logs")
def get_agent_logs(limit: int = 60):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?", (limit,))
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return logs

@router.get("/metrics")
def get_metrics():
    return analytics_agent.compute_metrics()

@router.get("/learning/weights")
def get_strategy_weights():
    return learning_agent.get_all_strategy_weights()

@router.get("/learning/retrospectives")
def get_learning_retrospectives(limit: int = 20):
    return learning_agent.get_recent_retrospectives(limit=limit)

@router.get("/browser/status")
def get_browser_status():
    return browser_mimic_agent.get_terminal_status()

@router.post("/trades/reset")
def reset_trades():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trades")
    cursor.execute("DELETE FROM positions")
    cursor.execute("DELETE FROM signals")
    cursor.execute("DELETE FROM agent_logs")
    cursor.execute("DELETE FROM portfolio")
    cursor.execute("""
    INSERT INTO portfolio (timestamp, equity, cash, margin_blocked, unrealized_pnl, realized_pnl, total_fees_paid, total_trades, winning_trades, losing_trades, win_rate, sharpe_ratio, max_drawdown)
    VALUES (?, ?, ?, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0)
    """, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), settings.INITIAL_BALANCE, settings.INITIAL_BALANCE))
    conn.commit()
    conn.close()
    return {"status": "SUCCESS", "message": "Simulation ledger reset to initial ₹10,00,000 balance"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await event_bus.register_websocket(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await event_bus.unregister_websocket(websocket)
    except Exception:
        await event_bus.unregister_websocket(websocket)
