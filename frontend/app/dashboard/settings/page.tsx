"use client";

import React, { useEffect, useState } from "react";
import { Save, RefreshCw, Settings as SettingsIcon } from "lucide-react";

export default function SettingsPage() {
  const [universeJson, setUniverseJson] = useState<string>("");
  const [loading, setLoading] = useState(false);

  // Auto-Select
  const [autoEnabled, setAutoEnabled] = useState(false);
  const [minScore, setMinScore] = useState("65");
  const [minConf, setMinConf] = useState("70");
  const [maxPerHour, setMaxPerHour] = useState("2");

  // Predictive Gate
  const [predictiveMinStability, setPredictiveMinStability] = useState("120");
  const [predictiveMaxAge, setPredictiveMaxAge] = useState("360");

  const load = async () => {
    setLoading(true);
    try {
      const fetchSetting = async (key: string) =>
        fetch(`/api/admin/settings/${key}`, { cache: "no-store" }).then((r) => r.json());

      const uni = await fetchSetting("SCANNER_UNIVERSE_JSON");
      const a = await fetchSetting("AUTO_SELECT_ENABLED");
      const s = await fetchSetting("AUTO_SELECT_MIN_SCORE");
      const c = await fetchSetting("AUTO_SELECT_MIN_CONFIDENCE");
      const m = await fetchSetting("AUTO_SELECT_MAX_TRADES_PER_HOUR");

      const pMin = await fetchSetting("PREDICTIVE_STABILITY_MIN");
      const pAge = await fetchSetting("PREDICTIVE_MAX_REPORT_AGE_MIN");

      setUniverseJson(uni.value || "");

      setAutoEnabled((a.value || "false").toLowerCase() === "true");
      setMinScore(s.value || "65");
      setMinConf(c.value || "70");
      setMaxPerHour(m.value || "2");

      setPredictiveMinStability(pMin.value || "120");
      setPredictiveMaxAge(pAge.value || "360");
    } finally {
      setLoading(false);
    }
  };

  const save = async () => {
    setLoading(true);
    try {
      if (universeJson.trim()) JSON.parse(universeJson);

      const post = (key: string, value: string) =>
        fetch(`/api/admin/settings/${key}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ value, is_secret: false }),
        });

      await post("SCANNER_UNIVERSE_JSON", universeJson);
      await post("AUTO_SELECT_ENABLED", autoEnabled ? "true" : "false");
      await post("AUTO_SELECT_MIN_SCORE", minScore);
      await post("AUTO_SELECT_MIN_CONFIDENCE", minConf);
      await post("AUTO_SELECT_MAX_TRADES_PER_HOUR", maxPerHour);

      await post("PREDICTIVE_STABILITY_MIN", predictiveMinStability);
      await post("PREDICTIVE_MAX_REPORT_AGE_MIN", predictiveMaxAge);

      await load();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="flex items-center gap-3 mb-6">
        <SettingsIcon className="w-7 h-7 text-purple-400" />
        <h1 className="text-2xl font-bold">System Settings</h1>
      </div>

      <div className="flex gap-3 mb-6">
        <button
          onClick={load}
          className="px-4 py-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
        <button
          onClick={save}
          className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          Save All
        </button>
      </div>

      {/* AUTO SELECT */}
      <div className="p-4 rounded bg-slate-800 border border-slate-700 mb-6">
        <div className="font-semibold mb-3">Auto-Select Execution</div>

        <label className="flex items-center gap-3 text-sm mb-4">
          <input
            type="checkbox"
            checked={autoEnabled}
            onChange={(e) => setAutoEnabled(e.target.checked)}
          />
          Enable Auto-Select
        </label>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-slate-400">Min Score</label>
            <input
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2"
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-slate-400">Min Confidence</label>
            <input
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2"
              value={minConf}
              onChange={(e) => setMinConf(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-slate-400">Max Trades / Hour</label>
            <input
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2"
              value={maxPerHour}
              onChange={(e) => setMaxPerHour(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* PREDICTIVE GATE */}
      <div className="p-4 rounded bg-slate-800 border border-slate-700 mb-6">
        <div className="font-semibold mb-3">Predictive Safety Gate</div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-400">Minimum Stability Score</label>
            <input
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2"
              value={predictiveMinStability}
              onChange={(e) => setPredictiveMinStability(e.target.value)}
            />
          </div>

          <div>
            <label className="text-xs text-slate-400">Max Report Age (minutes)</label>
            <input
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2"
              value={predictiveMaxAge}
              onChange={(e) => setPredictiveMaxAge(e.target.value)}
            />
          </div>
        </div>

        <div className="text-xs text-slate-400 mt-3">
          If stability score is below threshold or report is older than max age,
          Auto-Select will be disabled automatically.
        </div>
      </div>

      {/* SCANNER UNIVERSE */}
      <div className="p-4 rounded bg-slate-800 border border-slate-700">
        <div className="text-sm text-slate-300 mb-2">SCANNER_UNIVERSE_JSON</div>
        <textarea
          className="w-full h-[380px] bg-slate-900 border border-slate-700 rounded p-3 font-mono text-sm"
          value={universeJson}
          onChange={(e) => setUniverseJson(e.target.value)}
        />
      </div>
    </div>
  );
}