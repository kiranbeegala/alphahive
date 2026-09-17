import React from 'react';
import { AlignLeft } from 'lucide-react';

export default function OrderBook({ orderBook, symbol }) {
  if (!orderBook) return null;

  return (
    <div className="bg-[#111622] rounded-xl border border-[#1f293d] p-4 flex flex-col h-[340px]">
      <div className="flex items-center justify-between pb-2 border-b border-[#1f293d] mb-2">
        <div className="flex items-center gap-2">
          <AlignLeft size={15} className="text-cyan-400" />
          <span className="text-xs font-bold text-white font-mono uppercase tracking-wider">
            NSE 5-Depth Market Ladder
          </span>
        </div>
        <div className="text-[11px] text-slate-400 font-mono">
          Spread: <span className="text-cyan-300 font-bold">₹{orderBook.spread?.toFixed(2) || '0.05'}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 flex-1 font-mono text-xs">
        {/* Bid Side */}
        <div className="bg-[#0b0e14] p-2.5 rounded-lg border border-emerald-500/20 flex flex-col justify-between">
          <div>
            <div className="flex justify-between text-[10px] text-slate-400 border-b border-[#1f293d] pb-1 mb-1">
              <span>Orders</span>
              <span>Qty</span>
              <span className="text-emerald-400">Bid (₹)</span>
            </div>
            <div className="space-y-1">
              {orderBook.bids?.map((b, idx) => (
                <div key={idx} className="flex justify-between text-[11px]">
                  <span className="text-slate-500">{b.orders}</span>
                  <span className="text-slate-300">{b.quantity}</span>
                  <span className="text-emerald-400 font-semibold">{b.price.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="pt-2 border-t border-[#1f293d] flex justify-between text-[10px] text-slate-400">
            <span>Total Buy Qty:</span>
            <span className="text-emerald-400 font-bold">{orderBook.total_bid_qty?.toLocaleString('en-IN')}</span>
          </div>
        </div>

        {/* Ask Side */}
        <div className="bg-[#0b0e14] p-2.5 rounded-lg border border-rose-500/20 flex flex-col justify-between">
          <div>
            <div className="flex justify-between text-[10px] text-slate-400 border-b border-[#1f293d] pb-1 mb-1">
              <span className="text-rose-400">Ask (₹)</span>
              <span>Qty</span>
              <span>Orders</span>
            </div>
            <div className="space-y-1">
              {orderBook.asks?.map((a, idx) => (
                <div key={idx} className="flex justify-between text-[11px]">
                  <span className="text-rose-400 font-semibold">{a.price.toFixed(2)}</span>
                  <span className="text-slate-300">{a.quantity}</span>
                  <span className="text-slate-500">{a.orders}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="pt-2 border-t border-[#1f293d] flex justify-between text-[10px] text-slate-400">
            <span>Total Sell Qty:</span>
            <span className="text-rose-400 font-bold">{orderBook.total_ask_qty?.toLocaleString('en-IN')}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
