"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Activity, RefreshCw, Play, ShieldAlert, ShieldCheck } from "lucide-react";

type PreviewResponse = {
  latest: any;
  gate: { status: "pass" | "fail"; reason: string; min_stability: number; max_age_min: number };
  equity: number[];
  pnl: number[];
  mc_paths: number[][];
  meta: { limit_trades: number; mc_runs: number };
};

function toFixedSafe(v: any, n = 2) {
  const x = Number(v);
  if (!Number.isFinite(x)) return "-";
  return x.toFixed(n);
}

function buildPolyline(points: number[], w: number, h: number, pad = 10) {
  if (!points || points.length < 2) return "";
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  return points
    .map((p, i) => {
      const x = pad + (i / (points.length - 1)) * (w - 2 * pad);
      const y = pad + (1 - (p - min) / range) * (h - 2 * pad);
      return `${x},${y}`;
    })
    .join(" ");
}

function computeDrawdown(equity: number[]): number[] {
  if (!equity || equity.length === 0) return [];
  let peak = equity[0];
  const dd: number[] = [];
  for (let i = 0; i < equity.length; i++) {
    peak = Math.max(peak, equity[i]);
    dd.push(equity[i] - peak); // <= 0
  }
  return dd;
}

function histogram(values: number[], bins = 20) {
  if (!values || values.length === 0) return { bins: [], min: 0, max: 0, maxCount: 0 };

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const counts = new Array(bins).fill(0);
  for (const v of values) {
    const idx = Math.min(bins - 1, Math.max(0, Math.floor(((v - min) / range) * bins)));
    counts[idx] += 1;
  }

  const maxCount = Math.max(...counts);
  return { bins: counts, min, max, maxCount };
}

export default function PredictivePage() {
  const [loading, setLoading] = useState(false);
  const [symbol, setSymbol] = useState("XAUUSD");
  const [timeframe, setTimeframe] = useState("M15");
  const [data, setData] = useState<PreviewResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setErr(null);
    try {
      const qs = new URLSearchParams();
      qs.set("symbol", symbol);
      qs.set("timeframe", timeframe);
      qs.set("limit_trades", "500");
      qs.set("mc_runs", "25");

      const r = await fetch(`/api/predictive/preview?${qs.toString()}`, { cache: "no-store" });
      const j = await r.json();
      if (!r.ok) throw new Error(j?.detail || "Failed to load predictive preview");
      setData(j);
    } catch (e: any) {
      setErr(e?.message || "Error");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const runNow = async () => {
    setLoading(true);
    setErr(null);
    try {
      const qs = new URLSearchParams();
      qs.set("symbol", symbol);
      qs.set("timeframe", timeframe);

      const r = await fetch(`/api/predictive/run?${qs.toString()}`, { method: "POST" });
      const j = await r.json();
      if (!r.ok) throw new Error(j?.detail || "Failed to run predictive report");
      await load();
    } catch (e: any) {
      setErr(e?.message || "Error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(console.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const gatePass = data?.gate?.status === "pass";

  // Chart dims
  const W = 900;
  const H = 220;
  const PAD = 12;

  const equityLine = useMemo(() => buildPolyline(data?.equity || [], W, H, PAD), [data]);
  const ddSeries = useMemo(() => computeDrawdown(data?.equity || []), [data]);
  const ddLine = useMemo(() => buildPolyline(ddSeries, W, H, PAD), [ddSeries]);

  const mcLines = useMemo(() => {
    return (data?.mc_paths || []).map((p) => buildPolyline(p, W, H, PAD));
  }, [data]);

  const mcEndValues = useMemo(() => {
    const paths = data?.mc_paths || [];
    return paths
      .map((p) => (p && p.length ? p[p.length - 1] : null))
      .filter((x): x is number => typeof x === "number" && Number.isFinite(x));
  }, [data]);

  const hist = useMemo(() => histogram(mcEndValues, 20), [mcEndValues]);

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="flex items-center gap-3 mb-6">
        <Activity className="w-7 h-7 text-cyan-400" />
        <h1 className="text-2xl font-bold">Predictive Analytics</h1>
      </div>

      <div className="flex flex-wrap gap-3 items-end mb-6">
        <div>
          <label className="text-xs text-slate-400">Symbol</label>
          <input
            className="block bg-slate-800 border border-slate-700 rounded px-3 py-2 w-36"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-slate-400">Timeframe</label>
          <input
            className="block bg-slate-800 border border-slate-700 rounded px-3 py-2 w-24"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
          />
        </div>

        <button
          onClick={load}
          className="px-4 py-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 flex items-center gap-2"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>

        <button
          onClick={runNow}
          className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
          disabled={loading}
        >
          <Play className="w-4 h-4" />
          Run Report Now
        </button>
      </div>

      {err && (
        <div className="mb-6 p-3 rounded border border-red-600/40 bg-red-600/10 text-red-200">
          {err}
        </div>
      )}

      {data && (
        <>
          {/* Gate */}
          <div
            className={`mb-6 p-4 rounded border ${
              gatePass ? "border-green-600/40 bg-green-600/10" : "border-red-600/40 bg-red-600/10"
            }`}
          >
            <div className="flex items-center gap-2 font-semibold">
              {gatePass ? (
                <ShieldCheck className="w-5 h-5 text-green-300" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-red-300" />
              )}
              Predictive Gate: {gatePass ? "PASS" : "FAIL"}
            </div>
            <div className="text-sm text-slate-200 mt-2">
              Reason: <span className="font-mono">{data.gate.reason}</span>
            </div>
            <div className="text-xs text-slate-300 mt-1">
              min_stability={data.gate.min_stability} | max_report_age_min={data.gate.max_age_min}
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 rounded bg-slate-800 border border-slate-700">
              <div className="text-slate-300 text-sm mb-2">Stability</div>
              <div className="text-2xl font-bold">{toFixedSafe(data.latest?.stability_score, 2)}</div>
              <div className="text-xs text-slate-400 mt-2">
                drift={toFixedSafe(data.latest?.drift_score, 4)}
              </div>
            </div>

            <div className="p-4 rounded bg-slate-800 border border-slate-700">
              <div className="text-slate-300 text-sm mb-2">Walk-Forward</div>
              <div className="text-sm text-slate-200">
                Sharpe: <span className="font-mono">{toFixedSafe(data.latest?.wf_sharpe, 2)}</span>
              </div>
              <div className="text-sm text-slate-200">
                Winrate:{" "}
                <span className="font-mono">
                  {toFixedSafe((data.latest?.wf_winrate ?? 0) * 100, 1)}%
                </span>
              </div>
              <div className="text-sm text-slate-200">
                AvgReturn: <span className="font-mono">{toFixedSafe(data.latest?.wf_avg_return, 4)}</span>
              </div>
            </div>

            <div className="p-4 rounded bg-slate-800 border border-slate-700">
              <div className="text-slate-300 text-sm mb-2">Monte Carlo</div>
              <div className="text-sm text-slate-200">
                MaxDD (median): <span className="font-mono">{toFixedSafe(data.latest?.mc_max_dd, 2)}</span>
              </div>
              <div className="text-sm text-slate-200">
                VaR 95% (end): <span className="font-mono">{toFixedSafe(data.latest?.mc_var_95, 2)}</span>
              </div>
              <div className="text-xs text-slate-400 mt-2">trades={data.latest?.meta?.trades ?? "-"}</div>
            </div>
          </div>

          {/* Equity + MC */}
          <div className="p-4 rounded bg-slate-800 border border-slate-700 mb-6">
            <div className="font-semibold mb-3">Equity Curve + Monte Carlo Paths</div>

            <div className="rounded bg-slate-900/60 border border-slate-700 overflow-auto p-3">
              <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
                {/* MC paths */}
                {mcLines.map((d, i) => (
                  <polyline
                    key={i}
                    points={d}
                    fill="none"
                    stroke="rgba(148,163,184,0.25)"
                    strokeWidth="1"
                  />
                ))}
                {/* Equity */}
                <polyline
                  points={equityLine}
                  fill="none"
                  stroke="rgba(34,197,94,0.9)"
                  strokeWidth="2"
                />
              </svg>
            </div>

            <div className="text-xs text-slate-400 mt-3">
              Equity from last {data.meta.limit_trades} trades (cumsum of pnl). Monte Carlo shows {data.meta.mc_runs} randomized paths.
            </div>
          </div>

          {/* Drawdown + Histogram */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            {/* Drawdown */}
            <div className="p-4 rounded bg-slate-800 border border-slate-700">
              <div className="font-semibold mb-3">Drawdown Curve</div>
              <div className="rounded bg-slate-900/60 border border-slate-700 overflow-auto p-3">
                <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
                  {/* baseline at 0 drawdown */}
                  <line
                    x1={PAD}
                    y1={PAD}
                    x2={W - PAD}
                    y2={PAD}
                    stroke="rgba(148,163,184,0.25)"
                    strokeWidth="1"
                    opacity="0"
                  />
                  <polyline
                    points={ddLine}
                    fill="none"
                    stroke="rgba(244,63,94,0.9)"
                    strokeWidth="2"
                  />
                </svg>
              </div>
              <div className="text-xs text-slate-400 mt-3">
                Drawdown = equity - running peak (always = 0). Lower is worse.
              </div>
            </div>

            {/* Histogram */}
            <div className="p-4 rounded bg-slate-800 border border-slate-700">
              <div className="font-semibold mb-3">Monte Carlo End Equity Histogram</div>
              <div className="rounded bg-slate-900/60 border border-slate-700 overflow-auto p-3">
                <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
                  {hist.bins.length > 0 && (
                    <>
                      {hist.bins.map((count, i) => {
                        const bins = hist.bins.length;
                        const barW = (W - 2 * PAD) / bins;
                        const x = PAD + i * barW;
                        const barH = hist.maxCount ? (count / hist.maxCount) * (H - 2 * PAD) : 0;
                        const y = H - PAD - barH;

                        return (
                          <rect
                            key={i}
                            x={x + 1}
                            y={y}
                            width={Math.max(1, barW - 2)}
                            height={barH}
                            fill="rgba(59,130,246,0.65)"
                          />
                        );
                      })}
                      {/* axis line */}
                      <line
                        x1={PAD}
                        y1={H - PAD}
                        x2={W - PAD}
                        y2={H - PAD}
                        stroke="rgba(148,163,184,0.35)"
                        strokeWidth="1"
                      />
                    </>
                  )}
                </svg>
              </div>
              <div className="text-xs text-slate-400 mt-3">
                Distribution of Monte Carlo ending equity (last point of each randomized path). Range:{" "}
                <span className="font-mono">
                  [{toFixedSafe(hist.min, 2)} .. {toFixedSafe(hist.max, 2)}]
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}