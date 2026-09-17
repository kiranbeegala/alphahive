import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from app.core.config import settings
from app.core.event_bus import event_bus
from app.agents.sentinel import sentinel_agent
from app.agents.technical_analyst import technical_analyst_agent
from app.agents.sentiment_analyst import sentiment_analyst_agent
from app.agents.cro_risk_manager import cro_risk_manager_agent
from app.agents.execution_engine import execution_engine_agent
from app.agents.browser_mimic import browser_mimic_agent
from app.agents.analytics_agent import analytics_agent
from app.agents.learning_agent import learning_agent

class TradingDeskOrchestrator:
    def __init__(self):
        self.is_running = False
        self.active_symbol = "NIFTY"
        self.interval_seconds = 2.5
        self.task = None

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        learning_agent.init_strategy_weights()
        self.task = asyncio.create_task(self._orchestration_loop())
        await self._broadcast_agent_thought(
            "Orchestrator", "Desk Conductor", "SYSTEM",
            f"AlphaHive Indian Equities & F&O Autonomous Desk Online. Monitoring {self.active_symbol} with AngelOne Data Feeds, Zerodha Kite UI Mimic, & Continuous Learning Loop."
        )

    async def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
        await self._broadcast_agent_thought(
            "Orchestrator", "Desk Conductor", "SYSTEM",
            "AlphaHive Trading Desk Paused."
        )

    def set_active_symbol(self, symbol: str):
        self.active_symbol = symbol
        browser_mimic_agent.switch_target_url(symbol)

    async def _broadcast_agent_thought(self, agent_name: str, role: str, thought_type: str, message: str, details: dict = None):
        sentinel_agent.log_thought(thought_type, f"[{agent_name}] {message}", details)
        await event_bus.broadcast("AGENT_THOUGHT", {
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "agent_name": agent_name,
            "role": role,
            "thought_type": thought_type,
            "message": message,
            "details": details or {}
        })

    async def _orchestration_loop(self):
        while self.is_running:
            try:
                symbol = self.active_symbol
                
                # 1. Perception Step: Dynamic Sentinel Ingestion
                df = sentinel_agent.fetch_market_data(symbol, interval="5m")
                if df.empty:
                    await asyncio.sleep(self.interval_seconds)
                    continue

                current_price = float(df.iloc[-1]['close'])
                order_book = sentinel_agent.get_simulated_order_book(symbol, current_price)
                
                # Broadcast Market Tick & NSE 5-Depth Ladder
                await event_bus.broadcast("MARKET_TICK", {
                    "symbol": symbol,
                    "price": current_price,
                    "high": float(df.iloc[-1]['high']),
                    "low": float(df.iloc[-1]['low']),
                    "volume": float(df.iloc[-1]['volume']),
                    "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
                    "order_book": order_book
                })

                # 2. Update Active Positions & Check TP/SL Exits
                closed_events = execution_engine_agent.update_positions_on_tick(symbol, current_price)
                for closed in closed_events:
                    pnl_color = "WIN" if closed['realized_pnl'] > 0 else "LOSS"
                    await self._broadcast_agent_thought(
                        "Execution Engine", "Virtual Broker", "EXECUTION",
                        f"Position Closed: {closed['symbol']} {closed['side']} hit {closed['exit_reason']} @ ₹{closed['exit_price']:,.2f}. "
                        f"Realized P&L: ₹{closed['realized_pnl']:+,.2f} ({closed['realized_pct']:+.2f}%) [{pnl_color}]",
                        closed
                    )
                    
                    # Broadcast Continuous Learning Adaptation
                    ref = closed.get("learning_reflection")
                    if ref:
                        await self._broadcast_agent_thought(
                            "Continuous Learning Agent", "Strategy Adaptation", "REFLECTION",
                            f"Adaptive Policy Update: Strategy '{ref['strategy']}' weight updated to {ref['new_weight']:.2f}x ({ref['status']}). {ref['insight']} -> {ref['action_taken']}",
                            ref
                        )

                    await event_bus.broadcast("TRADE_CLOSED", closed)

                # 3. Strategy Analysis: Technical & SMC Engine
                signal = technical_analyst_agent.analyze(symbol, df)
                
                if signal:
                    await self._broadcast_agent_thought(
                        "Quant & Pattern Analyst", "Technical Strategy", "ANALYSIS",
                        f"Signal Detected on {symbol} [{signal['direction']}]: {signal['strategy']} (Confidence: {signal['confidence']}%). "
                        f"Entry: ₹{signal['entry_price']:,.2f}, SL: ₹{signal['stop_loss']:,.2f}, TP: ₹{signal['take_profit']:,.2f}, Target R:R {signal['risk_reward_ratio']}:1",
                        signal
                    )

                    # 4. Macro Sentiment Assessment (RBI Policy / India VIX)
                    sentiment = sentiment_analyst_agent.evaluate_sentiment(symbol)
                    await self._broadcast_agent_thought(
                        "Macro & Sentiment Analyst", "Global Catalyst", "ANALYSIS",
                        f"India Macro Pulse: {sentiment['market_regime']} (VIX: {sentiment['india_vix']}, FII/DII: {sentiment['fii_dii_net']}). Catalyst: '{sentiment['top_catalyst'][:60]}...'",
                        sentiment
                    )

                    # 5. CRO Risk Evaluation & Position Sizing in Lots
                    is_approved, cro_note, quantity = cro_risk_manager_agent.evaluate_and_size_order(signal, sentiment)
                    
                    if is_approved:
                        await self._broadcast_agent_thought(
                            "Chief Risk Officer", "Capital Allocation", "RISK_CHECK",
                            f"APPROVED: {cro_note}",
                            {"approved": True, "quantity": quantity}
                        )

                        # 6. Zerodha Kite Browser Mimic UI Execution
                        ui_res = await browser_mimic_agent.simulate_ui_order_action(
                            signal['direction'], symbol, signal['entry_price'], quantity, signal['stop_loss'], signal['take_profit']
                        )
                        await self._broadcast_agent_thought(
                            "Browser Mimic Agent", "Zerodha Kite Automation", "EXECUTION",
                            f"Simulated Zerodha Kite Order Entry: Placed {signal['direction']} {quantity} units @ ₹{signal['entry_price']:,.2f} with GTT SL/TP triggers",
                            ui_res
                        )

                        # 7. Virtual Broker Execution
                        fill_report = execution_engine_agent.execute_order(signal, quantity, cro_note)
                        await self._broadcast_agent_thought(
                            "Execution Engine", "Virtual Broker", "EXECUTION",
                            f"ORDER FILLED: {fill_report['side']} {fill_report['quantity']} {symbol} @ ₹{fill_report['executed_price']:,.2f}. "
                            f"(Margin Reserved: ₹{fill_report['margin_reserved']:,.2f}, Charges: ₹{fill_report['fee_incurred']:,.2f})",
                            fill_report
                        )
                        await event_bus.broadcast("ORDER_FILLED", fill_report)
                    else:
                        await self._broadcast_agent_thought(
                            "Chief Risk Officer", "Capital Allocation", "RISK_CHECK",
                            f"REJECTED: {cro_note}",
                            {"approved": False}
                        )

                # 8. Compute and Broadcast Authentic Analytics & Portfolio State
                metrics = analytics_agent.compute_metrics()
                await event_bus.broadcast("PORTFOLIO_UPDATE", metrics)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Orchestrator Error]: {e}")

            await asyncio.sleep(self.interval_seconds)

orchestrator = TradingDeskOrchestrator()
