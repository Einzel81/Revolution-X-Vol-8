"use client";

import React, { useEffect, useMemo, useState } from "react";
import { RefreshCw, Play, Radar, Filter, Zap } from "lucide-react";

type ScanTop = {
  signal_id: string;
  symbol: string;
  timeframe: string;
  action: string;
  score: number;
  confidence: number;
  weight?: number;
};

type RecentItem = {
  id: string;
  symbol: string;
  timeframe: string;
  action: string;
  score: number | null;
  confidence: number | null;
  entry_price: number | null;
  suggested_sl: number | null;
  suggested_tp: number | null;
  created_at: string | null;
};

export default function ScannerPage() {
  const [running, setRunning] = useState(false);
  const [top, setTop] = useState<ScanTop[]>([]);
  const [recent, setRecent] = useState<RecentItem[]>([]);
  const [limit, setLimit] = useState(50);
  const [symbolFilter, setSymbolFilter] = useState("");
  const [tfFilter, setTfFilter] = useState("");

  const loadRecent = async () => {
    const qs = new URLSearchParams();
    qs.set("limit", String(limit));
    if (symbolFilter.trim()) qs.set("symbol", symbolFilter.trim());
    if (tfFilter.trim()) qs.set("timeframe", tfFilter.trim());

    const r = await fetch(`/api/scanner/recent?${qs.toString()}`, { cache: "no-store" });
    const data = await r.json();
    setRecent(data.items || []);
  };

  const runScan = async () => {
    setRunning(true);
    try {
      const r = await fetch("/api/scanner/run", { method: "POST" });
      const data = await r.json();
      setTop(data.top || []);
      await loadRecent();
    } finally {
      setRunning(false);
    }
  };

  const executeSignal = async (signalId: string) => {
    setRunning(true);
    try {
      await fetch(`/api/scanner/execute/${signalId}`, { method: "POST" });
      await loadRecent();
    } finally {
      setRunning(false);
    }
  };

  const executeBest = async () => {
    setRunning(true);
    try {
      // ?????????: ????? ??? ??? backend ?????????? (min_score=65, min_confidence=70)
      await fetch(`/api/scanner/execute-best`, { method: "POST" });
      await loadRecent();
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    loadRecent().catch(console.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const recentRows = useMemo(() => {
    return recent.map((x) => ({
      ...x,
      score: x.score ?? 0,
      confidence: x.confidence ?? 0,
    }));
  }, [recent]);

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="flex items-center gap-3 mb-6">
        <Radar className="w-7 h-7 text-amber-400" />
        <h1 className="text-2xl font-bold">Smart Opportunity Scanner</h1>
      </div>

      <div className="flex flex-wrap gap-3 items-end mb-6">
        <button
          onClick={runScan}
          className="px-4 py-2 rounded bg-amber-600 hover:bg-amber-700 flex items-center gap-2"
          disabled={running}
        >
          <Play className="w-4 h-4" />
          Run Scan Now
        </button>

        <button
          onClick={loadRecent}
          className="px-4 py-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 flex items-center gap-2"
          disabled={running}
        >
          <RefreshCw className={`w-4 h-4 ${running ? "animate-spin" : ""}`} />
          Refresh Feed
        </button>

        <button
          onClick={executeBest}
          className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 flex items-center gap-2"
          disabled={running}
          title="Auto execute best eligible signal"
        >
          <Zap className="w-4 h-4" />
          Auto Execute Best
        </button>

        <div className="ml-auto flex flex-wrap gap-3 items-end">
          <div className="flex items-center gap-2 text-slate-300">
            <Filter className="w-4 h-4" />
            <span className="text-sm">Filters</span>
          </div>

          <div>
            <label className="text-xs text-slate-400">Symbol</label>
            <input
              className="block bg-slate-800 border border-slate-700 rounded px-3 py-2 w-36"
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value)}
              placeholder="XAUUSD"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400">Timeframe</label>
            <input
              className="block bg-slate-800 border border-slate-700 rounded px-3 py-2 w-24"
              value={tfFilter}
              onChange={(e) => setTfFilter(e.target.value)}
              placeholder="M15"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400">Limit</label>
            <input
              type="number"
              className="block bg-slate-800 border border-slate-700 rounded px-3 py-2 w-24"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value || "50", 10))}
              min={10}
              max={500}
            />
          </div>

          <button
            onClick={async () => {
              await loadRecent();
            }}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700"
            disabled={running}
          >
            Apply
          </button>
        </div>
      </div>

      <div className="mb-8">
        <div className="text-lg font-semibold mb-3">Top Opportunities (Last Scan)</div>
        <div className="rounded bg-slate-800 border border-slate-700 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/40">
              <tr className="text-slate-300">
                <th className="text-left p-3">Execute</th>
                <th className="text-left p-3">Symbol</th>
                <th className="text-left p-3">TF</th>
                <th className="text-left p-3">Action</th>
                <th className="text-left p-3">Score</th>
                <th className="text-left p-3">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {top.map((t, i) => (
                <tr key={i} className="border-t border-slate-700">
                  <td className="p-3">
                    <button
                      className="px-3 py-1 rounded bg-green-600 hover:bg-green-700 text-xs"
                      onClick={() => executeSignal(t.signal_id)}
                      disabled={running || !(t.action === "BUY" || t.action === "SELL")}
                    >
                      Execute
                    </button>
                  </td>
                  <td className="p-3 font-mono">{t.symbol}</td>
                  <td className="p-3 font-mono">{t.timeframe}</td>
                  <td className="p-3">{t.action}</td>
                  <td className="p-3">{Number(t.score).toFixed(2)}</td>
                  <td className="p-3">{Number(t.confidence).toFixed(1)}</td>
                </tr>
              ))}
              {top.length === 0 && (
                <tr>
                  <td className="p-3 text-slate-400" colSpan={6}>
                    No scan results yet. Click "Run Scan Now".
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <div className="text-lg font-semibold mb-3">Recent Scanner Feed (DB)</div>
        <div className="rounded bg-slate-800 border border-slate-700 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/40">
              <tr className="text-slate-300">
                <th className="text-left p-3">Execute</th>
                <th className="text-left p-3">Time</th>
                <th className="text-left p-3">Symbol</th>
                <th className="text-left p-3">TF</th>
                <th className="text-left p-3">Action</th>
                <th className="text-left p-3">Score</th>
                <th className="text-left p-3">Entry</th>
                <th className="text-left p-3">SL</th>
                <th className="text-left p-3">TP</th>
              </tr>
            </thead>
            <tbody>
              {recentRows.map((x) => (
                <tr key={x.id} className="border-t border-slate-700">
                  <td className="p-3">
                    <button
                      className="px-3 py-1 rounded bg-green-600 hover:bg-green-700 text-xs"
                      onClick={() => executeSignal(x.id)}
                      disabled={running || !(x.action === "BUY" || x.action === "SELL")}
                    >
                      Execute
                    </button>
                  </td>
                  <td className="p-3 text-slate-400">{x.created_at ? new Date(x.created_at).toLocaleString() : ""}</td>
                  <td className="p-3 font-mono">{x.symbol}</td>
                  <td className="p-3 font-mono">{x.timeframe}</td>
                  <td className="p-3">{x.action}</td>
                  <td className="p-3">{Number(x.score).toFixed(2)}</td>
                  <td className="p-3">{x.entry_price ?? ""}</td>
                  <td className="p-3">{x.suggested_sl ?? ""}</td>
                  <td className="p-3">{x.suggested_tp ?? ""}</td>
                </tr>
              ))}
              {recentRows.length === 0 && (
                <tr>
                  <td className="p-3 text-slate-400" colSpan={9}>
                    No recent scanner signals stored yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="text-xs text-slate-400 mt-3">
          Note: Feed requires candles in Timescale + scanner job running (manual or Celery beat).
        </div>
      </div>
    </div>
  );
}