"use client";

import React, { useEffect, useState } from "react";
import { Activity, RefreshCw } from "lucide-react";

type Health = {
  bridge: { connected: boolean; ping: any };
  last_hour: { total: number; success: number; bad: number; success_rate: number | null };
};

type EventItem = {
  id: string;
  created_at: string | null;
  symbol: string;
  side: string;
  volume: number;
  requested_price: number | null;
  fill_price: number | null;
  slippage: number | null;
  latency_ms: number | null;
  status: string;
  ticket: string | null;
  error: string | null;
};

export default function ExecutionPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const h = await fetch("/api/execution/health", { cache: "no-store" }).then((r) => r.json());
      const e = await fetch("/api/execution/events?limit=50", { cache: "no-store" }).then((r) => r.json());
      setHealth(h);
      setEvents(e.items || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(console.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="p-6 text-white">
      <div className="flex items-center gap-3 mb-6">
        <Activity className="w-7 h-7 text-amber-400" />
        <h1 className="text-2xl font-bold">Execution Health</h1>

        <button
          onClick={load}
          disabled={loading}
          className="ml-auto px-4 py-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="rounded bg-slate-800 border border-slate-700 p-4">
          <div className="text-sm text-slate-400">Bridge</div>
          <div className="mt-2 text-lg font-semibold">
            {health?.bridge.connected ? "CONNECTED" : "DISCONNECTED"}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Ping: {health?.bridge.ping?.ok ? `${Number(health.bridge.ping.latency_ms).toFixed(0)}ms` : "n/a"}
          </div>
        </div>

        <div className="rounded bg-slate-800 border border-slate-700 p-4">
          <div className="text-sm text-slate-400">Last hour</div>
          <div className="mt-2 text-lg font-semibold">{health?.last_hour.total ?? 0} attempts</div>
          <div className="mt-2 text-xs text-slate-400">
            Success: {health?.last_hour.success ?? 0} | Bad: {health?.last_hour.bad ?? 0}
          </div>
        </div>

        <div className="rounded bg-slate-800 border border-slate-700 p-4">
          <div className="text-sm text-slate-400">Success rate</div>
          <div className="mt-2 text-lg font-semibold">
            {health?.last_hour.success_rate == null ? "n/a" : `${(health.last_hour.success_rate * 100).toFixed(1)}%`}
          </div>
          <div className="mt-2 text-xs text-slate-400">Includes blocked + errors</div>
        </div>
      </div>

      <div className="rounded bg-slate-800 border border-slate-700 overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/40">
            <tr className="text-slate-300">
              <th className="text-left p-3">Time</th>
              <th className="text-left p-3">Symbol</th>
              <th className="text-left p-3">Side</th>
              <th className="text-left p-3">Vol</th>
              <th className="text-left p-3">Req</th>
              <th className="text-left p-3">Fill</th>
              <th className="text-left p-3">Slip</th>
              <th className="text-left p-3">Latency</th>
              <th className="text-left p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {events.map((x) => (
              <tr key={x.id} className="border-t border-slate-700">
                <td className="p-3 text-slate-400">{x.created_at ? new Date(x.created_at).toLocaleString() : ""}</td>
                <td className="p-3 font-mono">{x.symbol}</td>
                <td className="p-3">{x.side}</td>
                <td className="p-3">{Number(x.volume).toFixed(2)}</td>
                <td className="p-3">{x.requested_price ?? ""}</td>
                <td className="p-3">{x.fill_price ?? ""}</td>
                <td className="p-3">{x.slippage == null ? "" : Number(x.slippage).toFixed(2)}</td>
                <td className="p-3">{x.latency_ms == null ? "" : `${Number(x.latency_ms).toFixed(0)}ms`}</td>
                <td className="p-3">
                  <span className="px-2 py-1 rounded bg-slate-900/50 border border-slate-700">{x.status}</span>
                </td>
              </tr>
            ))}
            {events.length === 0 && (
              <tr>
                <td className="p-3 text-slate-400" colSpan={9}>
                  No execution events yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
