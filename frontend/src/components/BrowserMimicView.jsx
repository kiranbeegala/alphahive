import React, { useRef, useEffect } from 'react';
import { Globe, Monitor, MousePointer, ShieldCheck, Radio } from 'lucide-react';

function BrowserMimicView({ browserStatus }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [browserStatus?.recent_actions]);

  if (!browserStatus) return null;

  return (
    <div className="bg-[#111622] rounded-xl border border-[#1f293d] p-4 flex flex-col h-[340px]">
      <div className="flex items-center justify-between pb-2 border-b border-[#1f293d] mb-3">
        <div className="flex items-center gap-2">
          <Monitor size={15} className="text-amber-400" />
          <span className="text-xs font-bold text-white font-mono uppercase tracking-wider">
            Zerodha Kite Web Shadow Operator
          </span>
          <span className="px-2 py-0.5 text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-md flex items-center gap-1">
            <Radio size={10} className="animate-pulse" />
            HEADLESS MIMIC
          </span>
        </div>
        <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
          <Globe size={12} className="text-cyan-400" />
          <span className="text-slate-300 font-medium">kite.zerodha.com</span>
        </div>
      </div>

      {/* Terminal Viewport Mock */}
      <div className="bg-[#0b0e14] rounded-lg border border-[#1f293d] p-3 flex-1 flex flex-col justify-between font-mono text-xs overflow-hidden">
        {/* Top URL Bar */}
        <div className="flex items-center gap-2 pb-2 border-b border-[#1f293d]/60 text-[11px]">
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/60"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/60"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/60"></span>
          </div>
          <div className="flex-1 bg-[#161d2d] px-2.5 py-1 rounded text-slate-400 truncate text-[10px]">
            {browserStatus.current_target_url}
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold">CDP 18ms</span>
        </div>

        {/* DOM Actions Stream */}
        <div ref={scrollRef} className="my-2 space-y-1.5 overflow-y-auto max-h-[160px] pr-1 scrollbar-thin">
          {browserStatus.recent_actions && browserStatus.recent_actions.length > 0 ? (
            browserStatus.recent_actions.map((act, idx) => (
              <div key={`${act.timestamp}-${idx}`} className="flex items-start gap-1.5 text-[11px]">
                <MousePointer size={11} className="text-cyan-400 mt-0.5 flex-shrink-0" />
                <span className="text-slate-400 text-[10px] flex-shrink-0">{act.timestamp}</span>
                <span className="text-slate-200">{act.step}</span>
              </div>
            ))
          ) : (
            <div className="text-slate-500 text-center py-6 text-[11px]">
              Kite Web session initialized. Observing Marketwatch & Level 2 Depth...
            </div>
          )}
        </div>

        {/* Status Footer */}
        <div className="pt-2 border-t border-[#1f293d]/60 flex items-center justify-between text-[10px] text-slate-400">
          <div className="flex items-center gap-2">
            <span className="text-amber-400 font-semibold">Active:</span>
            <span>{browserStatus.active_tab}</span>
          </div>
          <div className="flex items-center gap-1 text-emerald-400">
            <ShieldCheck size={12} />
            <span>Virtual Execution Sandbox</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default React.memo(BrowserMimicView);
