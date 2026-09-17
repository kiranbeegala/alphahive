import React from 'react';
import { Layers } from 'lucide-react';

function PositionsTable({ positions = [] }) {
  return (
    <div className="bg-[#111622] rounded-xl border border-[#1f293d] overflow-hidden">
      <div className="px-4 py-3 border-b border-[#1f293d] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers size={15} className="text-cyan-400" />
          <span className="text-xs font-bold text-white font-mono uppercase tracking-wider">
            Active F&O & Equity Positions
          </span>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {positions.length} Open
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-[#0b0e14] text-slate-400 border-b border-[#1f293d] text-[11px]">
            <tr>
              <th className="py-2.5 px-4">Instrument</th>
              <th className="py-2.5 px-3">Side</th>
              <th className="py-2.5 px-3">Lots / Qty</th>
              <th className="py-2.5 px-3">Entry Price</th>
              <th className="py-2.5 px-3">Mark Price</th>
              <th className="py-2.5 px-3">Margin (₹)</th>
              <th className="py-2.5 px-3">Stop Loss</th>
              <th className="py-2.5 px-3">Take Profit</th>
              <th className="py-2.5 px-4 text-right">Unrealized P&L</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f293d]">
            {positions.length === 0 ? (
              <tr>
                <td colSpan="9" className="py-8 text-center text-slate-500">
                  No active open positions. Desk in scanning mode.
                </td>
              </tr>
            ) : (
              positions.map((pos) => {
                const isBuy = pos.side === 'BUY';
                const uPnl = Number(pos.unrealized_pnl ?? 0);
                const isProfit = uPnl >= 0;
                const pnlPct = Number(pos.unrealized_pnl_pct ?? 0);

                return (
                  <tr key={pos.symbol} className="hover:bg-[#161d2d] transition-colors">
                    <td className="py-3 px-4 font-bold text-white">
                      {pos.symbol}
                      <span className="block text-[10px] text-slate-500 font-normal">{pos.strategy}</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isBuy ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                      }`}>
                        {pos.side}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-200">{pos.size}</td>
                    <td className="py-3 px-3 text-slate-300">₹{Number(pos.entry_price ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className="py-3 px-3 text-cyan-300 font-semibold">₹{Number(pos.mark_price ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className="py-3 px-3 text-amber-300">₹{Number(pos.margin_blocked ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                    <td className="py-3 px-3 text-rose-400">₹{Number(pos.stop_loss ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className="py-3 px-3 text-emerald-400">₹{Number(pos.take_profit ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className={`py-3 px-4 text-right font-bold ${isProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {isProfit ? `+₹${uPnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : `₹${uPnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                      <span className="block text-[10px] font-normal">
                        ({pnlPct >= 0 ? `+${pnlPct.toFixed(2)}` : pnlPct.toFixed(2)}%)
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default React.memo(PositionsTable);
