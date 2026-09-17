# AlphaHive | Autonomous Multi-Agent Trading & Simulation Ecosystem
### Indian Equities & F&O Desk (NSE / NIFTY / BANKNIFTY) with Zerodha Kite Web Mimicking & AngelOne Data Feeds

AlphaHive is an institutional-grade, multi-agent autonomous trading ecosystem designed to analyze Indian financial markets, recognize leading trading patterns (Smart Money Concepts, Wyckoff, Momentum/Mean Reversion), execute realistic paper trades (with STT, GST, SEBI charges, flat ₹20 brokerage, slippage, and spread), and run shadow-mode mimicking over Zerodha Kite Web and AngelOne live market feeds.

---

## 🏛 Multi-Agent Architecture

1. **Market Sentinel Agent (`sentinel.py`)**:
   - Ingests real-time tick/OHLCV data for Indian Equities & F&O (`NIFTY`, `BANKNIFTY`, `FINNIFTY`, `RELIANCE`, `HDFCBANK`, `ICICIBANK`, `TATAMOTORS`, `TCS`).
   - Computes multi-timeframe candle regimes and generates realistic NSE 5-Depth Market Ladders.

2. **Quant & Pattern Strategy Agent (`technical_analyst.py`)**:
   - **Smart Money Concepts (SMC)**: Fair Value Gaps (FVG), Bullish/Bearish Order Blocks, Liquidity Sweeps, and Reclaims.
   - **Wyckoff Method**: Phase C Accumulation Springs & Distribution Upthrusts (UTAD).
   - **Technical Indicators**: 21/50/200 EMA trend regimes, RSI Divergence, ATR Volatility, Bollinger Squeeze Breakouts.

3. **Macro & Sentiment Analyst Agent (`sentiment_analyst.py`)**:
   - Monitors RBI monetary policy, global handover catalysts, inflation indices, and market sentiment polarity.
   - Flags high-volatility event barriers to shield capital.

4. **Chief Risk Officer - CRO Agent (`cro_risk_manager.py`)**:
   - **Capital Sizing**: Enforces fixed 1.5% maximum risk per trade (e.g. ₹15,000 risk on ₹10,00,000 fund) calibrated to Indian F&O lot sizes (Nifty 25, BankNifty 15, Reliance 250, etc.).
   - **Drawdown Circuit Breaker**: Strict 3.0% daily maximum drawdown limit.
   - **Risk-Reward Barrier**: Mandates at least 1:1.8+ risk-to-reward ratio.

5. **Browser Mimic Agent (`browser_mimic.py`)**:
   - Automates and monitors the **Zerodha Kite Web Platform** (`kite.zerodha.com`).
   - Simulates DOM interactions: Marketwatch navigation, MIS/CNC lot configuration, GTT Target/Stoploss placement, and order confirmation.

6. **Virtual Broker & Execution Engine (`execution_engine.py`)**:
   - Ultra-realistic Indian market friction simulation:
     - ₹20 Flat Brokerage (Zerodha / AngelOne schedule)
     - STT / CTT (0.0125% - 0.0625%)
     - NSE Exchange Turnover Charges (0.00345%)
     - GST (18% on Brokerage + Txn Charges)
     - Stamp Duty & SEBI Turnover fees
     - Dynamic slippage and 0.05 tick bid/ask spread modeling.

7. **Performance Analytics Agent (`analytics_agent.py`)**:
   - Real-time quantitative alpha tracking: Sharpe Ratio, Sortino Ratio, Profit Factor, Win Rate %, Maximum Drawdown, and P&L attribution.

---

## 🚀 Quickstart & Running AlphaHive

### 1. Launch Backend (FastAPI & Agent Loop)
```bash
cd backend
/Users/kiranbeegala/.gemini/antigravity/scratch/stockpulse-india/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Launch Frontend (React + Vite Dashboard)
```bash
cd frontend
export PATH=/Users/kiranbeegala/.nvm/versions/node/v24.18.0/bin:$PATH
npm run dev
```

The unified dashboard will be accessible at:
- Frontend Cockpit: `http://localhost:5173` or `http://localhost:8000`
- REST API Documentation: `http://localhost:8000/docs`
- Real-Time WebSocket Stream: `ws://localhost:8000/api/v1/ws`

---

## 📊 Shadow Run & 2-Week Performance Tracking
- The system starts with an initial virtual capital of **₹10,00,000 (10 Lakhs INR)**.
- Every simulated trade records entry, exit, slippage, STT/brokerage fees, and strategy rationale into the persistent SQLite database (`alphahive.db`).
- Live metrics and logs update continuously in the dashboard without manual intervention.
