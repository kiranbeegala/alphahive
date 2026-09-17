import React from 'react';
import { History } from 'lucide-react';

function TradeHistory({ trades = [] }) {
  return (
    <div className="bg-[#111622] rounded-xl border border-[#1f293d] overflow-hidden">
      <div className="px-4 py-3 border-b border-[#1f293d] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History size={15} className="text-cyan-400" />
          <span className="text-xs font-bold text-white font-mono uppercase tracking-wider">
            Closed Trade Journal & Attribution
          </span>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {trades.length} Executed
        </span>
      </div>

      <div className="overflow-x-auto max-h-[300px] scrollbar-thin">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-[#0b0e14] text-slate-400 border-b border-[#1f293d] text-[11px] sticky top-0 z-10">
            <tr>
              <th className="py-2.5 px-4">Instrument</th>
              <th className="py-2.5 px-3">Side</th>
              <th className="py-2.5 px-3">Qty</th>
              <th className="py-2.5 px-3">Entry / Exit</th>
              <th className="py-2.5 px-3">Exit Reason</th>
              <th className="py-2.5 px-3">Charges (STT/GST)</th>
              <th className="py-2.5 px-4 text-right">Net Realized P&L</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f293d]">
            {trades.length === 0 ? (
              <tr>
                <td colSpan="7" className="py-8 text-center text-slate-500">
                  No completed trades in ledger yet.
                </td>
              </tr>
            ) : (
              trades.map((t) => {
                const isWin = Number(t.pnl ?? 0) > 0;
                const pnlVal = Number(t.pnl ?? 0);
                const pnlPct = Number(t.pnl_pct ?? 0);

                return (
                  <tr key={t.id} className="hover:bg-[#161d2d] transition-colors">
                    <td className="py-2.5 px-4 font-bold text-white">
                      {t.symbol}
                      <span className="block text-[10px] text-slate-500 font-normal">{t.strategy}</span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        t.side === 'BUY' ? 'text-emerald-400' : 'text-rose-400'
                      }`}>
                        {t.side}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{t.quantity}</td>
                    <td className="py-2.5 px-3 text-slate-300">
                      ₹{Number(t.entry_price ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })} → ₹{Number(t.exit_price ?? t.entry_price ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        t.status === 'CLOSED_TP' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {t.status === 'CLOSED_TP' ? 'TARGET (TP)' : 'STOPLOSS (SL)'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">₹{Number(t.fee ?? 20).toFixed(2)}</td>
                    <td className={`py-2.5 px-4 text-right font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {isWin ? `+₹${pnlVal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : `₹${pnlVal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
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

export default React.memo(TradeHistory);
