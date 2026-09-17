import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, Target, ShieldAlert, Award, Lock } from 'lucide-react';

function MetricsCards({ metrics }) {
  if (!metrics) return null;

  const totalReturn = Number(metrics.total_return_pct ?? 0);
  const isProfit = totalReturn >= 0;
  const equity = Number(metrics.current_equity ?? 1000000);
  const cash = Number(metrics.cash_balance ?? 1000000);
  const marginBlocked = Number(metrics.margin_blocked ?? 0);
  const realizedPnl = Number(metrics.realized_pnl ?? 0);
  const unrealizedPnl = Number(metrics.unrealized_pnl ?? 0);
  const totalFees = Number(metrics.total_fees_paid ?? 0);
  const winRate = Number(metrics.win_rate ?? 0);
  const sharpe = Number(metrics.sharpe_ratio ?? 0);
  const maxDd = Number(metrics.max_drawdown_pct ?? 0);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {/* Total Equity */}
      <div className="bg-[#111622] p-3.5 rounded-xl border border-[#1f293d] flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
          <span>PORTFOLIO EQUITY</span>
          <span className="text-cyan-400">₹ INR</span>
        </div>
        <div className="mt-2">
          <div className="text-lg font-bold text-white font-mono">
            ₹{equity.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className={`text-xs font-medium flex items-center gap-1 mt-0.5 ${isProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isProfit ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            <span>{totalReturn >= 0 ? `+${totalReturn.toFixed(2)}` : totalReturn.toFixed(2)}%</span>
          </div>
        </div>
      </div>

      {/* Free Cash & Blocked Margin */}
      <div className="bg-[#111622] p-3.5 rounded-xl border border-[#1f293d] flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
          <span>FREE CASH</span>
          <Lock size={12} className="text-amber-400" />
        </div>
        <div className="mt-2">
          <div className="text-lg font-bold text-slate-200 font-mono">
            ₹{cash.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-amber-400 font-mono mt-0.5">
            Margin: ₹{marginBlocked.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </div>
        </div>
      </div>

      {/* Realized P&L & Charges */}
      <div className="bg-[#111622] p-3.5 rounded-xl border border-[#1f293d] flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
          <span>REALIZED P&L</span>
          <DollarSign size={13} className="text-emerald-400" />
        </div>
        <div className="mt-2">
          <div className={`text-lg font-bold font-mono ${realizedPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {realizedPnl >= 0 ? `+₹${realizedPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : `₹${realizedPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          </div>
          <div className="text-xs text-slate-400 font-mono mt-0.5">
            Taxes/Fees: ₹{totalFees.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Active MTM Unrealized PnL */}
      <div className="bg-[#111622] p-3.5 rounded-xl border border-[#1f293d] flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
          <span>ACTIVE MTM P&L</span>
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
        </div>
        <div className="mt-2">
          <div className={`text-lg font-bold font-mono ${unrealizedPnl >= 0 ? 'text-cyan-400' : 'text-rose-400'}`}>
            {unrealizedPnl >= 0 ? `+₹${unrealizedPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : `₹${unrealizedPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          </div>
          <div className="text-xs text-slate-400 font-mono mt-0.5">
            {metrics.active_positions_count ?? 0} Active Positions
          </div>
        </div>
      </div>

      {/* Win Rate & Trades */}
      <div className="bg-[#111622] p-3.5 rounded-xl border border-[#1f293d] flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
          <span>WIN RATE</span>
          <Target size={13} className="text-amber-400" />
        </div>
        <div className="mt-2">
          <div className="text-lg font-bold text-amber-300 font-mono">
            {winRate.toFixed(1)}%
          </div>
          <div className="text-xs text-slate-400 font-mono mt-0.5">
            {metrics.winning_trades ?? 0}W / {metrics.losing_trades ?? 0}L ({metrics.total_trades ?? 0} Total)
          </div>
        </div>
      </div>

      {/* Sharpe Ratio & Max Drawdown */}
      <div className="bg-[#111622] p-3.5 rounded-xl border border-[#1f293d] flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
          <span>SHARPE / DRAWDOWN</span>
          <Award size={13} className="text-purple-400" />
        </div>
        <div className="mt-2">
          <div className="text-lg font-bold text-purple-300 font-mono">
            {sharpe > 0 ? sharpe.toFixed(2) : '--'}
          </div>
          <div className="text-xs text-slate-300 font-mono mt-0.5">
            Max DD: <span className={maxDd > 2.0 ? 'text-rose-400' : 'text-emerald-400'}>{maxDd.toFixed(2)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default React.memo(MetricsCards);
