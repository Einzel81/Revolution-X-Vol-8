"use client";

import React, { useEffect, useState } from "react";
import { RefreshCw, Play, Brain, CheckCircle2 } from "lucide-react";

type ActiveModel = {
  model_type: string;
  symbol: string;
  timeframe: string;
  version: string;
  artifact_path: string;
  metrics?: any;
  created_at?: string | null;
};

export default function AIPage() {
  const [models, setModels] = useState<ActiveModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [symbol, setSymbol] = useState("XAUUSD");
  const [timeframe, setTimeframe] = useState("M15");
  const [lastTaskId, setLastTaskId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadModels = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const r = await fetch(
        `/api/admin/models/active?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}`,
        { cache: "no-store" }
      );
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setModels(Array.isArray(data.models) ? data.models : []);
    } catch (e: any) {
      setErrorMsg(e?.message || "Failed to load models");
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  const trainNow = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const r = await fetch("/api/admin/train-models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ symbol, timeframe }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setLastTaskId(data.task_id || null);
      await loadModels();
    } catch (e: any) {
      setErrorMsg(e?.message || "Failed to queue training");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels().catch(() => void 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="flex items-center gap-3 mb-6">
        <Brain className="w-7 h-7 text-blue-400" />
        <h1 className="text-2xl font-bold">AI System - Model Registry</h1>
      </div>

      <div className="flex flex-wrap gap-3 items-end mb-6">
        <div>
          <label className="text-sm text-slate-300">Symbol</label>
          <input
            className="block bg-slate-800 border border-slate-700 rounded px-3 py-2"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          />
        </div>

        <div>
          <label className="text-sm text-slate-300">Timeframe</label>
          <input
            className="block bg-slate-800 border border-slate-700 rounded px-3 py-2"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
          />
        </div>

        <button
          onClick={loadModels}
          className="px-4 py-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 flex items-center gap-2"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>

        <button
          onClick={trainNow}
          className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
          disabled={loading}
        >
          <Play className="w-4 h-4" />
          Train Now
        </button>
      </div>

      {errorMsg && (
        <div className="mb-6 p-3 rounded border border-red-600/40 bg-red-600/10 text-red-200">
          {errorMsg}
        </div>
      )}

      {lastTaskId && (
        <div className="mb-6 p-3 rounded border border-green-600/40 bg-green-600/10 text-green-200 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          Training queued. Task ID: <span className="font-mono">{lastTaskId}</span>
        </div>
      )}

      <div className="space-y-3">
        {models.map((m, idx) => (
          <div key={idx} className="p-4 rounded bg-slate-800 border border-slate-700">
            <div className="flex justify-between">
              <div className="font-semibold">
                {String(m.model_type || "").toUpperCase()} - {m.symbol} {m.timeframe}
              </div>
              <div className="text-slate-400 text-sm">{m.created_at || ""}</div>
            </div>

            <div className="text-sm text-slate-300 mt-2">
              <div>
                Version: <span className="font-mono">{m.version}</span>
              </div>
              <div>
                Artifact: <span className="font-mono">{m.artifact_path}</span>
              </div>
              {m.metrics && (
                <pre className="mt-2 text-xs bg-slate-900/60 p-2 rounded border border-slate-700 overflow-auto">
                  {JSON.stringify(m.metrics, null, 2)}
                </pre>
              )}
            </div>
          </div>
        ))}

        {models.length === 0 && !loading && !errorMsg && (
          <div className="text-slate-400">No active models found (train first).</div>
        )}
      </div>
    </div>
  );
}