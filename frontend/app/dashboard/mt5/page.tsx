"use client";

import React, { useEffect, useState } from "react";
import { Plus, CheckCircle, Trash2, RefreshCw, Wifi } from "lucide-react";

type Conn = {
  id: string;
  name: string;
  host: string;
  port: number;
  token: string | null;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export default function MT5ConnectionsPage() {
  const [items, setItems] = useState<Conn[]>([]);
  const [loading, setLoading] = useState(false);
  const [ping, setPing] = useState<any>(null);
  const [msg, setMsg] = useState("");

  const [name, setName] = useState("My MT5");
  const [host, setHost] = useState("");
  const [port, setPort] = useState(9000);
  const [token, setToken] = useState("");

  const load = async () => {
    setLoading(true);
    setMsg("");
    try {
      const r = await fetch("/api/mt5/connections", { cache: "no-store" });
      const j = await r.json();
      setItems(j.items || []);
    } finally {
      setLoading(false);
    }
  };

  const create = async () => {
    setLoading(true);
    setMsg("");
    try {
      const r = await fetch("/api/mt5/connections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          host,
          port,
          token: token.trim() ? token.trim() : null,
          set_active: true,
        }),
      });
      const j = await r.json();
      setMsg(j.ok ? "Created and activated." : `Create failed: ${j.detail || "unknown"}`);
      await load();
    } finally {
      setLoading(false);
    }
  };

  const activate = async (id: string) => {
    setLoading(true);
    setMsg("");
    try {
      const r = await fetch(`/api/mt5/connections/${id}/activate`, { method: "POST" });
      const j = await r.json();
      setMsg(j.ok ? "Activated." : "Activate failed.");
      await load();
    } finally {
      setLoading(false);
    }
  };

  const del = async (id: string) => {
    setLoading(true);
    setMsg("");
    try {
      const r = await fetch(`/api/mt5/connections/${id}`, { method: "DELETE" });
      const j = await r.json();
      setMsg(j.ok ? "Deleted." : "Delete failed.");
      await load();
    } finally {
      setLoading(false);
    }
  };

  const pingActive = async () => {
    setLoading(true);
    setMsg("");
    try {
      const r = await fetch("/api/mt5/connections/active/ping", { cache: "no-store" });
      const j = await r.json();
      setPing(j);
      setMsg(j.ok ? "Ping OK." : `Ping failed: ${j.detail || "error"}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  return (
    <div className="p-6 text-white">
      <div className="flex items-center gap-3 mb-6">
        <Wifi className="w-7 h-7 text-amber-400" />
        <h1 className="text-2xl font-bold">MT5 Connections</h1>

        <button
          onClick={load}
          disabled={loading}
          className="ml-auto px-4 py-2 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>

        <button
          onClick={pingActive}
          disabled={loading}
          className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
        >
          <CheckCircle className="w-4 h-4" />
          Ping Active
        </button>
      </div>

      {msg && (
        <div className="mb-4 px-4 py-3 rounded border border-slate-700 bg-slate-800 text-slate-200 text-sm">
          {msg}
        </div>
      )}

      <div className="rounded bg-slate-900/40 border border-slate-800 p-5 mb-8">
        <div className="text-lg font-semibold mb-4">Add new connection</div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs text-slate-400">Name</label>
            <input className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
              value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-slate-400">Host</label>
            <input className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
              value={host} onChange={(e) => setHost(e.target.value)} placeholder="VPS IP / hostname" />
          </div>
          <div>
            <label className="text-xs text-slate-400">Port</label>
            <input type="number" className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
              value={port} onChange={(e) => setPort(parseInt(e.target.value || "9000", 10))} />
          </div>
          <div>
            <label className="text-xs text-slate-400">Token (optional)</label>
            <input className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
              value={token} onChange={(e) => setToken(e.target.value)} placeholder="shared secret" />
          </div>
        </div>

        <button
          onClick={create}
          disabled={loading || !host.trim()}
          className="mt-4 px-4 py-2 rounded bg-amber-600 hover:bg-amber-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create & Activate
        </button>

        <div className="text-xs text-slate-400 mt-3">
          Each user must run their own MT5 Bridge (EA) and expose host/port (prefer VPN).
        </div>
      </div>

      <div className="rounded bg-slate-800 border border-slate-700 overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/40">
            <tr className="text-slate-300">
              <th className="text-left p-3">Active</th>
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Host</th>
              <th className="text-left p-3">Port</th>
              <th className="text-left p-3">Token</th>
              <th className="text-left p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((x) => (
              <tr key={x.id} className="border-t border-slate-700">
                <td className="p-3">{x.is_active ? "YES" : ""}</td>
                <td className="p-3 font-medium">{x.name}</td>
                <td className="p-3 font-mono">{x.host}</td>
                <td className="p-3">{x.port}</td>
                <td className="p-3 font-mono">{x.token ?? ""}</td>
                <td className="p-3 flex gap-2">
                  <button
                    onClick={() => activate(x.id)}
                    disabled={loading}
                    className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700"
                  >
                    Set Active
                  </button>
                  <button
                    onClick={() => del(x.id)}
                    disabled={loading}
                    className="px-3 py-1.5 rounded bg-rose-600 hover:bg-rose-700 flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td className="p-3 text-slate-400" colSpan={6}>
                  No connections yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {ping && (
        <pre className="mt-6 p-4 rounded bg-slate-950 border border-slate-800 text-xs overflow-auto">
{JSON.stringify(ping, null, 2)}
        </pre>
      )}
    </div>
  );
}