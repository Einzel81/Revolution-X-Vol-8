"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Save, RefreshCw } from "lucide-react";

type PublicSettings = Record<string, { is_secret: boolean; value?: string; is_set?: boolean }>;

const keys = [
  "MT5_HOST",
  "MT5_PORT",
  "TRADING_MODE",
  "EXECUTION_BRIDGE",
  "AUTO_SELECT_ENABLED",
  "EXEC_TIMEOUT_MS",
  "EXEC_MAX_LATENCY_MS",
  "EXEC_MAX_SLIPPAGE",
  "EXEC_GUARD_ENABLED",
  "EXEC_DISABLE_AUTO_ON_VIOLATION",
  "EXEC_VIOLATION_WINDOW_MIN",
  "EXEC_MAX_VIOLATIONS_IN_WINDOW",
];

export default function SettingsPage() {
  const [loading, setLoading] = useState(false);
  const [savingKey, setSavingKey] = useState<string>("");
  const [msg, setMsg] = useState<string>("");
  const [data, setData] = useState<PublicSettings>({});
  const [form, setForm] = useState<Record<string, string>>({});

  const load = async () => {
    setLoading(true);
    setMsg("");
    try {
      const r = await fetch("/api/admin/settings/settings", { cache: "no-store" });
      const j = await r.json();
      setData(j || {});
      const initial: Record<string, string> = {};
      for (const k of keys) {
        const v = j?.[k]?.value;
        initial[k] = v != null ? String(v) : "";
      }
      setForm(initial);
    } finally {
      setLoading(false);
    }
  };

  const save = async (key: string) => {
    setSavingKey(key);
    setMsg("");
    try {
      const payload = { key, value: form[key] === "" ? null : form[key], is_secret: false };
      const r = await fetch("/api/admin/settings/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const j = await r.json();
      setMsg(j?.ok ? `Saved: ${key}` : `Save failed: ${key}`);
      await load();
    } finally {
      setSavingKey("");
    }
  };

  useEffect(() => {
    load().catch(console.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const input = (k: string, placeholder?: string) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-slate-400">{k}</label>
      <div className="flex gap-2">
        <input
          className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
          value={form[k] ?? ""}
          onChange={(e) => setForm((p) => ({ ...p, [k]: e.target.value }))}
          placeholder={placeholder || ""}
        />
        <button
          onClick={() => save(k)}
          disabled={savingKey === k}
          className="px-3 py-2 rounded bg-blue-600 hover:bg-blue-700 text-sm flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {savingKey === k ? "Saving..." : "Save"}
        </button>
      </div>
    </div>
  );

  return (
    <div className="p-6 text-white">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold">Settings</h1>
        <button
          onClick={load}
          disabled={loading}
          className="ml-auto px-4 py-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {msg && (
        <div className="mb-4 px-4 py-3 rounded border border-slate-700 bg-slate-800 text-slate-200 text-sm">
          {msg}
        </div>
      )}

      <div className="rounded bg-slate-900/40 border border-slate-800 p-5">
        <div className="text-lg font-semibold mb-4">Execution & MT5</div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {input("MT5_HOST", "127.0.0.1")}
          {input("MT5_PORT", "9000")}
          {input("TRADING_MODE", "paper | live")}
          {input("EXECUTION_BRIDGE", "simulated | mt5_zmq")}
          {input("AUTO_SELECT_ENABLED", "true | false")}
          {input("EXEC_TIMEOUT_MS", "2000")}
          {input("EXEC_MAX_LATENCY_MS", "1500")}
          {input("EXEC_MAX_SLIPPAGE", "2.5")}
          {input("EXEC_GUARD_ENABLED", "true | false")}
          {input("EXEC_DISABLE_AUTO_ON_VIOLATION", "true | false")}
          {input("EXEC_VIOLATION_WINDOW_MIN", "15")}
          {input("EXEC_MAX_VIOLATIONS_IN_WINDOW", "3")}
        </div>

        <div className="text-xs text-slate-400 mt-4">
          Note: These settings are stored in DB. Execution endpoints read them at runtime and apply to MT5 connector + guards.
        </div>
      </div>
    </div>
  );
}