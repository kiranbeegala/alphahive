import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function LiveChart({ candles = [], symbol = 'NIFTY', liveTick }) {
  if (!candles || candles.length === 0) {
    return (
      <div className="bg-[#111622] rounded-xl border border-[#1f293d] p-6 h-80 flex items-center justify-center text-slate-500 font-mono text-xs">
        Loading AngelOne Market Data Stream...
      </div>
    );
  }

  // Slice recent 50 candles for clean visibility
  const visibleCandles = candles.slice(-50);
  const labels = visibleCandles.map(c => c.time || '');
  const prices = visibleCandles.map(c => Number(c.close ?? 0));
  const ema21 = visibleCandles.map(c => c.ema21 != null ? Number(c.ema21) : null);
  const ema200 = visibleCandles.map(c => c.ema200 != null ? Number(c.ema200) : null);
  const bbUpper = visibleCandles.map(c => c.bb_upper != null ? Number(c.bb_upper) : null);
  const bbLower = visibleCandles.map(c => c.bb_lower != null ? Number(c.bb_lower) : null);

  const currentPrice = liveTick ? liveTick.price : prices[prices.length - 1];

  const data = {
    labels,
    datasets: [
      {
        label: 'Price (NSE)',
        data: prices,
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.05)',
        borderWidth: 2,
        tension: 0.1,
        pointRadius: 0,
        fill: true,
      },
      {
        label: '21 EMA',
        data: ema21,
        borderColor: '#f59e0b',
        borderWidth: 1.5,
        borderDash: [4, 4],
        pointRadius: 0,
        tension: 0.1,
      },
      {
        label: '200 EMA',
        data: ema200,
        borderColor: '#ec4899',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.1,
      },
      {
        label: 'BB Upper',
        data: bbUpper,
        borderColor: 'rgba(148, 163, 184, 0.25)',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0.1,
      },
      {
        label: 'BB Lower',
        data: bbLower,
        borderColor: 'rgba(148, 163, 184, 0.25)',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0.1,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        align: 'end',
        labels: {
          color: '#94a3b8',
          font: { family: 'JetBrains Mono', size: 10 },
          boxWidth: 12,
          usePointStyle: true,
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        borderWidth: 1,
        titleFont: { family: 'JetBrains Mono', size: 11 },
        bodyFont: { family: 'JetBrains Mono', size: 10 },
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(30, 41, 59, 0.5)' },
        ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 9 }, maxTicksLimit: 8 }
      },
      y: {
        position: 'right',
        grid: { color: 'rgba(30, 41, 59, 0.5)' },
        ticks: {
          color: '#64748b',
          font: { family: 'JetBrains Mono', size: 10 },
          callback: (value) => `₹${Number(value).toLocaleString('en-IN')}`
        }
      }
    }
  };

  return (
    <div className="bg-[#111622] rounded-xl border border-[#1f293d] p-4 flex flex-col h-[380px]">
      <div className="flex items-center justify-between pb-2 border-b border-[#1f293d] mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-white font-mono">{symbol}</span>
          <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono">5m Chart</span>
          <span className="text-xs text-slate-500 font-mono">SMC & Wyckoff Overlays</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">LTP:</span>
          <span className="text-sm font-bold text-cyan-400 font-mono">
            ₹{currentPrice ? Number(currentPrice).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </span>
        </div>
      </div>
      <div className="flex-1 w-full relative">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}

export default React.memo(LiveChart);
