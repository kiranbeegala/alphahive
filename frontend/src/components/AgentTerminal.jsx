import React, { useState, useRef, useEffect } from 'react';
import { Terminal, Shield, Brain, Cpu, Globe, Zap } from 'lucide-react';

function AgentTerminal({ thoughts = [] }) {
  const [filter, setFilter] = useState('ALL');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [thoughts]);

  const getAgentBadge = (name) => {
    switch (name) {
      case 'Market Sentinel':
        return { bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30', icon: Zap };
      case 'Quant & Pattern Analyst':
        return { bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', icon: Brain };
      case 'Macro & Sentiment Analyst':
        return { bg: 'bg-purple-500/10 text-purple-400 border-purple-500/30', icon: Globe };
      case 'Chief Risk Officer':
      case 'Chief Risk Officer (CRO)':
        return { bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30', icon: Shield };
      case 'Browser Mimic Agent':
        return { bg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30', icon: Globe };
      case 'Execution Engine':
      case 'Virtual Broker':
        return { bg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30', icon: Cpu };
      default:
        return { bg: 'bg-slate-800 text-slate-300 border-slate-700', icon: Terminal };
    }
  };

  const filteredThoughts = thoughts.filter((t) => {
    if (filter === 'ALL') return true;
    if (filter === 'SIGNALS') return t.thought_type === 'ANALYSIS';
    if (filter === 'RISK') return t.thought_type === 'RISK_CHECK';
    if (filter === 'EXECUTION') return t.thought_type === 'EXECUTION';
    return true;
  });

  return (
    <div className="bg-[#111622] rounded-xl border border-[#1f293d] flex flex-col h-[380px]">
      {/* Header & Filter Tabs */}
      <div className="px-4 py-2.5 border-b border-[#1f293d] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal size={15} className="text-cyan-400" />
          <span className="text-xs font-bold text-white font-mono uppercase tracking-wider">
            Agent Reasoning & Collaboration Stream
          </span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        </div>
        <div className="flex items-center gap-1 bg-[#0b0e14] p-0.5 rounded-lg border border-[#1f293d]">
          {['ALL', 'SIGNALS', 'RISK', 'EXECUTION'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded text-[10px] font-mono font-medium transition-all ${
                filter === f
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Live Stream Terminal */}
      <div ref={scrollRef} className="flex-1 p-3 overflow-y-auto font-mono text-xs space-y-2.5 scrollbar-thin">
        {filteredThoughts.length === 0 ? (
          <div className="text-slate-500 text-center py-12">
            Waiting for multi-agent reasoning events...
          </div>
        ) : (
          filteredThoughts.map((item, idx) => {
            const badge = getAgentBadge(item.agent_name);
            const IconComponent = badge.icon;
            const msg = item.message || '';
            const isApproved = msg.includes('APPROVED');
            const isRejected = msg.includes('REJECTED');
            const isWin = msg.includes('[WIN]');
            const isLoss = msg.includes('[LOSS]');

            return (
              <div 
                key={item.id || `${item.timestamp}-${idx}`} 
                className={`p-2 rounded-lg border transition-all ${
                  isApproved ? 'bg-emerald-950/20 border-emerald-500/30' :
                  isRejected ? 'bg-rose-950/20 border-rose-500/30' :
                  isWin ? 'bg-cyan-950/20 border-cyan-500/30' :
                  isLoss ? 'bg-amber-950/20 border-amber-500/30' :
                  'bg-[#0b0e14]/60 border-[#1f293d]'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-1.5">
                    <span className={`px-2 py-0.5 rounded-md border text-[10px] font-semibold flex items-center gap-1 ${badge.bg}`}>
                      <IconComponent size={11} />
                      {item.agent_name}
                    </span>
                    <span className="text-[10px] text-slate-500">[{item.role}]</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{item.timestamp}</span>
                </div>
                <div className="text-slate-200 leading-relaxed pl-1 text-[11px]">
                  {msg}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default React.memo(AgentTerminal);
