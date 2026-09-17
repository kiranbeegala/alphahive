import React from 'react';
import { BrainCircuit, TrendingUp, ShieldAlert, Sparkles, CheckCircle2, AlertTriangle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function LearningMatrix({ strategyWeights = [], retrospectives = [] }) {
  return (
    <div className="bg-[#111622] border border-slate-800 rounded-xl p-5 flex flex-col gap-5 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <BrainCircuit className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-100 text-base tracking-wide">
                Autonomous Continuous Learning & Policy Reinforcement
              </h3>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Active Learning Loop
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Reinforcement engine dynamically adjusts capital allocations (0.35x - 1.75x) and indicator sensitivity based on trade feedback.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>Adaptive Regime: <strong>Dynamic SMC Volatility</strong></span>
          </div>
        </div>
      </div>

      {/* Strategy Allocation Weights Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Strategy Reinforcement Multipliers & Win/Loss Streaks
          </span>
          <span className="text-xs text-slate-500">
            Base Weight: 1.00x | Cap: 1.75x | Floor: 0.35x
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {strategyWeights && strategyWeights.length > 0 ? (
            strategyWeights.map((strat, idx) => {
              const weight = Number(strat.weight || 1.0);
              const isBoosted = weight > 1.0;
              const isReduced = weight < 1.0;
              const totalTrades = Number(strat.total_trades || 0);
              const winningTrades = Number(strat.winning_trades || 0);
              const winRate = totalTrades > 0 ? ((winningTrades / totalTrades) * 100).toFixed(0) : '0';
              const pnl = Number(strat.realized_pnl || 0);

              let statusBadge = (
                <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  ACTIVE
                </span>
              );
              if (strat.status === 'BOOSTED' || isBoosted) {
                statusBadge = (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    BOOSTED
                  </span>
                );
              } else if (strat.status === 'COOLING_DOWN' || isReduced) {
                statusBadge = (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    COOLING DOWN
                  </span>
                );
              }

              return (
                <div
                  key={strat.strategy_name || idx}
                  className={`p-3.5 rounded-xl border flex flex-col justify-between gap-3 transition-all ${
                    isBoosted
                      ? 'bg-emerald-950/15 border-emerald-500/30 shadow-sm shadow-emerald-950/50'
                      : isReduced
                      ? 'bg-amber-950/10 border-amber-500/30'
                      : 'bg-[#161c28]/70 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <h4 className="text-xs font-semibold text-slate-200 line-clamp-1" title={strat.strategy_name}>
                        {strat.strategy_name}
                      </h4>
                      <div className="mt-1 flex items-center gap-1.5">
                        {statusBadge}
                        <span className="text-[11px] text-slate-400">
                          Win Rate: <strong className="text-slate-200">{winRate}%</strong> ({winningTrades}/{totalTrades})
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-end justify-between pt-2 border-t border-slate-800/60">
                    <div>
                      <div className="text-[10px] uppercase font-semibold text-slate-400">Allocation Weight</div>
                      <div className="flex items-center gap-1 mt-0.5">
                        <span className={`text-base font-extrabold ${isBoosted ? 'text-emerald-400' : isReduced ? 'text-amber-400' : 'text-slate-200'}`}>
                          {weight.toFixed(2)}x
                        </span>
                        {isBoosted && <ArrowUpRight className="w-4 h-4 text-emerald-400" />}
                        {isReduced && <ArrowDownRight className="w-4 h-4 text-amber-400" />}
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-[10px] uppercase font-semibold text-slate-400">Strategy P&L</div>
                      <span className={`text-xs font-bold ${pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {pnl >= 0 ? `+₹${pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : `-₹${Math.abs(pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="col-span-full py-6 text-center text-xs text-slate-500">
              Initializing strategy reinforcement weights...
            </div>
          )}
        </div>
      </div>

      {/* Autonomous Learning Retrospectives Feed */}
      <div className="pt-3 border-t border-slate-800/80">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Recent Retrospective Learnings & Parameter Adaptations
            </span>
          </div>
          <span className="text-xs text-slate-500">Auto-recorded after every closed trade</span>
        </div>

        <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
          {retrospectives && retrospectives.length > 0 ? (
            retrospectives.map((retro, idx) => {
              const isWin = retro.outcome === 'WIN';
              return (
                <div
                  key={retro.id || idx}
                  className="p-3 rounded-lg bg-[#0e121a] border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                >
                  <div className="flex items-start gap-2.5">
                    {isWin ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200">{retro.strategy}</span>
                        <span className="text-slate-500 font-mono text-[10px]">[{retro.symbol}]</span>
                        <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${isWin ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                          {isWin ? `+₹${retro.pnl}` : `-₹${Math.abs(retro.pnl)}`}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] mt-0.5">{retro.insight}</p>
                    </div>
                  </div>

                  <div className="sm:text-right shrink-0">
                    <span className="inline-block px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[10px] font-medium">
                      {retro.action_taken}
                    </span>
                    <div className="text-[10px] text-slate-500 mt-0.5 font-mono">{retro.timestamp}</div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-4 rounded-lg bg-[#0e121a] border border-dashed border-slate-800 text-center text-xs text-slate-500">
              No closed trade retrospectives yet. The agent will analyze, reflect, and adapt weights after the next trade lifecycle completes.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
