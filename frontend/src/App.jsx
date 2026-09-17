import React, { useState, useEffect, useRef, useCallback } from 'react';
import Header from './components/Header';
import MetricsCards from './components/MetricsCards';
import LiveChart from './components/LiveChart';
import AgentTerminal from './components/AgentTerminal';
import PositionsTable from './components/PositionsTable';
import TradeHistory from './components/TradeHistory';
import BrowserMimicView from './components/BrowserMimicView';
import OrderBook from './components/OrderBook';
import LearningMatrix from './components/LearningMatrix';

const isLocalDev = typeof window !== 'undefined' && window.location.hostname === 'localhost' && window.location.port === '5173';
const API_BASE = isLocalDev 
  ? 'http://localhost:8080/api/v1' 
  : (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}/api/v1` : '/api/v1');

const WS_PROTOCOL = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_BASE = isLocalDev 
  ? 'ws://localhost:8080/api/v1/ws' 
  : (typeof window !== 'undefined' ? `${WS_PROTOCOL}//${window.location.host}/api/v1/ws` : 'ws://localhost:8080/api/v1/ws');

export default function App() {
  const [watchlist, setWatchlist] = useState([
    { symbol: 'NIFTY', name: 'NIFTY 50', category: 'F&O Index' },
    { symbol: 'BANKNIFTY', name: 'BANK NIFTY', category: 'F&O Index' },
    { symbol: 'FINNIFTY', name: 'FIN NIFTY', category: 'F&O Index' },
    { symbol: 'RELIANCE.NS', name: 'Reliance', category: 'F&O Stock' },
    { symbol: 'HDFCBANK.NS', name: 'HDFC Bank', category: 'F&O Stock' },
    { symbol: 'ICICIBANK.NS', name: 'ICICI Bank', category: 'F&O Stock' },
    { symbol: 'TATAMOTORS.NS', name: 'Tata Motors', category: 'F&O Stock' },
    { symbol: 'TCS.NS', name: 'TCS', category: 'F&O Stock' }
  ]);
  const [activeSymbol, setActiveSymbol] = useState('NIFTY');
  const [isRunning, setIsRunning] = useState(true);
  const [marketStatus, setMarketStatus] = useState(null);
  const [metrics, setMetrics] = useState({
    current_equity: 1000000.0,
    cash_balance: 1000000.0,
    margin_blocked: 0.0,
    realized_pnl: 0.0,
    unrealized_pnl: 0.0,
    total_fees_paid: 0.0,
    total_return_pct: 0.0,
    win_rate: 0.0,
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    sharpe_ratio: 0.0,
    max_drawdown_pct: 0.0,
    active_positions_count: 0
  });
  const [candles, setCandles] = useState([]);
  const [liveTick, setLiveTick] = useState(null);
  const [orderBook, setOrderBook] = useState(null);
  const [thoughts, setThoughts] = useState([]);
  const [positions, setPositions] = useState([]);
  const [trades, setTrades] = useState([]);
  const [strategyWeights, setStrategyWeights] = useState([]);
  const [retrospectives, setRetrospectives] = useState([]);
  const [browserStatus, setBrowserStatus] = useState(null);

  const activeSymbolRef = useRef(activeSymbol);
  activeSymbolRef.current = activeSymbol;

  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  // Initial Data Fetch
  const fetchData = useCallback(async (sym = activeSymbolRef.current) => {
    try {
      const [watchRes, statusRes, metricsRes, candlesRes, posRes, tradesRes, logsRes, browserRes, weightsRes, retroRes] = await Promise.all([
        fetch(`${API_BASE}/watchlist`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/status`).then(r => r.json()).catch(() => ({})),
        fetch(`${API_BASE}/metrics`).then(r => r.json()).catch(() => ({})),
        fetch(`${API_BASE}/candles?symbol=${sym}`).then(r => r.json()).catch(() => ({ candles: [] })),
        fetch(`${API_BASE}/positions`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/trades`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/agent-logs`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/browser/status`).then(r => r.json()).catch(() => ({})),
        fetch(`${API_BASE}/learning/weights`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/learning/retrospectives`).then(r => r.json()).catch(() => [])
      ]);

      if (watchRes.length > 0) setWatchlist(watchRes);
      if (statusRes.orchestrator_running !== undefined) setIsRunning(statusRes.orchestrator_running);
      if (statusRes.market) setMarketStatus(statusRes.market);
      if (metricsRes.current_equity !== undefined) setMetrics(metricsRes);
      if (candlesRes.candles) setCandles(candlesRes.candles);
      setPositions(posRes || []);
      setTrades(tradesRes || []);
      setBrowserStatus(browserRes);
      setStrategyWeights(weightsRes || []);
      setRetrospectives(retroRes || []);
      if (logsRes && logsRes.length > 0) {
        setThoughts(logsRes.reverse());
      }
    } catch (e) {
      console.error('Error fetching initial state:', e);
    }
  }, []);

  useEffect(() => {
    fetchData(activeSymbol);
  }, [activeSymbol, fetchData]);

  // Single Persistent WebSocket Connection Lifecycle
  useEffect(() => {
    let isSubscribed = true;

    const connectWebSocket = () => {
      if (!isSubscribed) return;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);

      try {
        const ws = new WebSocket(WS_BASE);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('⚡ Connected to AlphaHive Real-Time Stream');
        };

        ws.onmessage = (event) => {
          if (!isSubscribed) return;
          try {
            const msg = JSON.parse(event.data);
            const { type, data } = msg;

            if (type === 'MARKET_TICK') {
              if (data.symbol === activeSymbolRef.current) {
                setLiveTick(data);
                if (data.order_book) setOrderBook(data.order_book);
                setCandles(prev => {
                  if (!prev || prev.length === 0) return prev;
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  updated[lastIdx] = {
                    ...updated[lastIdx],
                    close: data.price,
                    high: Math.max(updated[lastIdx].high || data.price, data.price),
                    low: Math.min(updated[lastIdx].low || data.price, data.price),
                    volume: data.volume || updated[lastIdx].volume
                  };
                  return updated;
                });
              }
            } else if (type === 'AGENT_THOUGHT') {
              setThoughts(prev => [...prev.slice(-75), data]);
            } else if (type === 'PORTFOLIO_UPDATE') {
              setMetrics(data);
            } else if (type === 'ORDER_FILLED' || type === 'TRADE_CLOSED') {
              fetch(`${API_BASE}/positions`).then(r => r.json()).then(setPositions);
              fetch(`${API_BASE}/trades`).then(r => r.json()).then(setTrades);
              fetch(`${API_BASE}/browser/status`).then(r => r.json()).then(setBrowserStatus);
              fetch(`${API_BASE}/metrics`).then(r => r.json()).then(setMetrics);
              fetch(`${API_BASE}/learning/weights`).then(r => r.json()).then(setStrategyWeights);
              fetch(`${API_BASE}/learning/retrospectives`).then(r => r.json()).then(setRetrospectives);
            }
          } catch (err) {
            console.error('Error processing websocket message:', err);
          }
        };

        ws.onclose = () => {
          if (isSubscribed) {
            reconnectTimerRef.current = setTimeout(connectWebSocket, 2500);
          }
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        if (isSubscribed) {
          reconnectTimerRef.current = setTimeout(connectWebSocket, 3000);
        }
      }
    };

    connectWebSocket();

    return () => {
      isSubscribed = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, []);

  const handleSelectSymbol = async (sym) => {
    setActiveSymbol(sym);
    activeSymbolRef.current = sym;
    setCandles([]);
    try {
      await fetch(`${API_BASE}/symbol/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: sym })
      });
      fetchData(sym);
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleOrchestrator = async () => {
    const endpoint = isRunning ? 'stop' : 'start';
    try {
      const res = await fetch(`${API_BASE}/orchestrator/${endpoint}`, { method: 'POST' }).then(r => r.json());
      setIsRunning(res.running);
    } catch (e) {
      console.error(e);
    }
  };

  const handleResetLedger = async () => {
    if (window.confirm('Reset all trades and restore initial ₹10,00,000 capital?')) {
      await fetch(`${API_BASE}/trades/reset`, { method: 'POST' });
      fetchData(activeSymbolRef.current);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0e14] text-slate-100 flex flex-col font-sans">
      <Header
        watchlist={watchlist}
        activeSymbol={activeSymbol}
        onSelectSymbol={handleSelectSymbol}
        isRunning={isRunning}
        onToggleOrchestrator={handleToggleOrchestrator}
        onResetLedger={handleResetLedger}
        marketStatus={marketStatus}
      />

      <main className="flex-1 p-4 md:p-6 space-y-4 max-w-[1750px] mx-auto w-full">
        <MetricsCards metrics={metrics} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-7">
            <LiveChart 
              candles={candles} 
              symbol={activeSymbol} 
              liveTick={liveTick} 
            />
          </div>
          <div className="lg:col-span-5">
            <AgentTerminal thoughts={thoughts} />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-7">
            <BrowserMimicView browserStatus={browserStatus} />
          </div>
          <div className="lg:col-span-5">
            <OrderBook orderBook={orderBook} symbol={activeSymbol} />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-6">
            <PositionsTable positions={positions} />
          </div>
          <div className="lg:col-span-6">
            <TradeHistory trades={trades} />
          </div>
        </div>

        {/* Autonomous Continuous Learning & Strategy Matrix */}
        <LearningMatrix 
          strategyWeights={strategyWeights} 
          retrospectives={retrospectives} 
        />
      </main>
    </div>
  );
}
