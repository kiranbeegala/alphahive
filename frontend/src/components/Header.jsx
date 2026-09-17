import React from 'react';
import { Play, Pause, RotateCcw, Activity, Globe, Clock, ShieldCheck, AlertTriangle, Key } from 'lucide-react';

function Header({ 
  watchlist = [], 
  activeSymbol = 'NIFTY', 
  onSelectSymbol, 
  isRunning = true, 
  onToggleOrchestrator, 
  onResetLedger,
  marketStatus
}) {
  const isMarketOpen = marketStatus?.is_live_market;
  const statusLabel = marketStatus?.status_label || 'CLOSED (AFTER HOURS)';
  const countdown = marketStatus?.countdown_to_open || '13h 40m';
  const currentTimeIST = marketStatus?.current_time_ist || 'Live IST';
  const nextOpenFormatted = marketStatus?.next_open_formatted || 'Tomorrow 09:15 AM IST';

  return (
    <header className="bg-[#111622] border-b border-[#1f293d] sticky top-0 z-50">
      {/* Top Banner: Market Status & System Health */}
      <div className="bg-[#0b0e14] px-6 py-1.5 border-b border-[#1f293d]/80 flex flex-wrap items-center justify-between text-[11px] font-mono">
        <div className="flex items-center gap-3">
          {isMarketOpen ? (
            <div className="flex items-center gap-1.5 text-emerald-400 font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>NSE / BSE: LIVE MARKET OPEN</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-amber-400 font-semibold">
              <Clock size={12} className="text-amber-400" />
              <span>MARKET: {statusLabel}</span>
              <span className="text-slate-500">•</span>
              <span className="text-slate-300">Opens {nextOpenFormatted} (in {countdown})</span>
            </div>
          )}
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-slate-400 hidden sm:inline">{currentTimeIST}</span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/30 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
            {isMarketOpen ? 'Live Exchange Stream Active' : '24/7 Tick Simulation Active'}
          </span>
          <span className="text-emerald-400/90 bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1 hidden md:flex">
            <Key size={10} />
            AngelOne SmartAPI: Connected
          </span>
        </div>
      </div>

      {/* Main Nav Bar */}
      <div className="px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <span className="text-xl">🐝</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white font-sans">AlphaHive</h1>
              <span className="px-2 py-0.5 text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded-full font-mono">
                v1.1 AUTONOMOUS
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">Indian Equities & F&O Desk</p>
          </div>
        </div>

        {/* Symbol Selector */}
        <div className="flex items-center gap-1.5 bg-[#0b0e14] p-1 rounded-xl border border-[#1f293d]">
          {watchlist.map((item) => {
            const symStr = typeof item === 'string' ? item : item.symbol;
            const isActive = symStr === activeSymbol;
            const displayStr = symStr ? symStr.replace('.NS', '') : 'SYM';
            return (
              <button
                key={symStr}
                onClick={() => onSelectSymbol(symStr)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-all duration-150 ${
                  isActive 
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#161d2d]'
                }`}
              >
                {displayStr}
              </button>
            );
          })}
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 bg-[#0b0e14] rounded-lg border border-[#1f293d] text-xs font-mono">
            <span className="text-amber-400 font-semibold flex items-center gap-1">
              <Globe size={13} /> Zerodha Kite
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-cyan-400 font-semibold flex items-center gap-1">
              <Activity size={13} /> AngelOne Feed
            </span>
          </div>

          <button
            onClick={onToggleOrchestrator}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold font-mono transition-all shadow-md ${
              isRunning 
                ? 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40' 
                : 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40'
            }`}
          >
            {isRunning ? <Pause size={14} /> : <Play size={14} />}
            {isRunning ? 'PAUSE AGENTS' : 'RUN AUTONOMOUS'}
          </button>

          <button
            onClick={onResetLedger}
            title="Reset Simulation Ledger to ₹10,00,000"
            className="p-2 rounded-xl bg-[#0b0e14] hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 border border-[#1f293d] hover:border-rose-500/30 transition-all text-xs"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>
    </header>
  );
}

export default React.memo(Header);
