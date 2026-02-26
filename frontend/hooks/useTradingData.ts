"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

export type BalanceResponse = {
  balance: number;
  equity: number;
  currency?: string;
};

export type BackendPosition = {
  ticket?: number;
  symbol: string;
  type?: string;
  volume?: number;
  price_open?: number;
  price_current?: number;
  sl?: number | null;
  tp?: number | null;
  profit?: number;
  swap?: number;
  commission?: number;
  time_open?: string;
};

export type PriceCandle = {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
};

export type Stats = {
  balance: number;
  equity: number;
  currency?: string;

  totalPnL: number;
  todayPnL: number;
  winRate: number;
  totalTrades: number;
  activeTrades: number;

  openPositions?: number;
};

export type Position = {
  id: string;
  symbol: string;

  type: "buy" | "sell";
  openTime: string;

  volume: number;

  entryPrice: number;
  currentPrice: number;

  stopLoss: number;
  takeProfit: number;

  pnl: number;
  pnlPercent: number;

  swap: number;
  commission: number;
};

// ? literal union ??????? ?? UI
export type ExitType = "manual" | "sl" | "tp";

export type Trade = {
  id: string;
  symbol: string;
  type: "buy" | "sell";

  entryPrice: number;
  exitPrice: number;

  volume: number;

  openTime: string;
  closeTime: string;

  pnl: number;
  pnlPercent: number;

  duration: string;
  strategy: string;

  exitType: ExitType; // ? FIXED

  stopLoss: number;
  takeProfit: number;

  status: "open" | "closed";

  comment?: string;
};

type TradingDataState = {
  loading: boolean;
  error: string | null;
  balance: BalanceResponse | null;
  backendPositions: BackendPosition[];
  trades: Trade[];
  priceHistory: PriceCandle[];
};

function getAuthToken(): string | null {
  try {
    if (typeof window === "undefined") return null;
    return (
      window.localStorage.getItem("access_token") ||
      window.localStorage.getItem("token") ||
      window.localStorage.getItem("auth_token")
    );
  } catch {
    return null;
  }
}

async function apiGet<T>(path: string): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { method: "GET", headers, cache: "no-store" });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const msg = text?.trim()
      ? `${res.status} ${res.statusText}: ${text}`
      : `${res.status} ${res.statusText}`;
    throw new Error(msg);
  }

  return (await res.json()) as T;
}

function safeNum(v: any, fallback = 0): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function normalizeTypeToBuySell(t?: string): "buy" | "sell" {
  const s = (t || "").toLowerCase();
  if (s.includes("buy") || s.includes("long")) return "buy";
  if (s.includes("sell") || s.includes("short")) return "sell";
  return "buy";
}

function normalizeExitType(v: any): ExitType {
  const s = String(v ?? "").toLowerCase().trim();

  // ????? ?????
  if (s === "tp" || s.includes("take") || s.includes("profit")) return "tp";
  if (s === "sl" || s.includes("stop") || s.includes("loss")) return "sl";
  if (s === "manual" || s.includes("manual") || s.includes("user")) return "manual";

  // fallback ???
  return "manual";
}

function startOfLocalDay(ts = Date.now()): number {
  const d = new Date(ts);
  d.setHours(0, 0, 0, 0);
  return d.getTime();
}

function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms <= 0) return "0m";
  const totalMin = Math.floor(ms / 60000);
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  if (h <= 0) return `${m}m`;
  if (m <= 0) return `${h}h`;
  return `${h}h ${m}m`;
}

function toUIPosition(p: BackendPosition): Position {
  const entry = safeNum(p.price_open, 0);
  const cur = safeNum(p.price_current, entry);
  const vol = safeNum(p.volume, 0);
  const pnl = safeNum(p.profit, 0);

  const pnlPercent = entry > 0 ? (pnl / (entry * Math.max(vol, 1))) * 100 : 0;
  const openTime = p.time_open ?? new Date().toISOString();

  return {
    id: String(p.ticket ?? `${p.symbol}-${openTime}`),
    symbol: p.symbol,
    type: normalizeTypeToBuySell(p.type),
    openTime,
    volume: vol,
    entryPrice: entry,
    currentPrice: cur,
    stopLoss: safeNum(p.sl, 0),
    takeProfit: safeNum(p.tp, 0),
    pnl,
    pnlPercent,
    swap: safeNum(p.swap, 0),
    commission: safeNum(p.commission, 0),
  };
}

function positionToTrade(pos: Position): Trade {
  const now = new Date();
  const open = new Date(pos.openTime);
  const openMs = Number.isNaN(open.getTime()) ? now.getTime() : open.getTime();

  return {
    id: `open-${pos.id}`,
    symbol: pos.symbol,
    type: pos.type,
    entryPrice: pos.entryPrice,
    exitPrice: pos.currentPrice,
    volume: pos.volume,
    openTime: pos.openTime,
    closeTime: now.toISOString(),
    pnl: pos.pnl,
    pnlPercent: pos.pnlPercent,
    duration: formatDuration(now.getTime() - openMs),
    strategy: "unknown",
    exitType: "manual", // ? literal
    stopLoss: pos.stopLoss,
    takeProfit: pos.takeProfit,
    status: "open",
    comment: "derived-from-open-position",
  };
}

function normalizeTrade(t: any): Trade {
  const entryPrice = safeNum(t?.entryPrice, 0);
  const exitPrice = safeNum(t?.exitPrice, entryPrice);
  const volume = safeNum(t?.volume, 0);
  const pnl = safeNum(t?.pnl, 0);

  const pnlPercent =
    typeof t?.pnlPercent === "number"
      ? t.pnlPercent
      : entryPrice > 0
      ? (pnl / (entryPrice * Math.max(volume, 1))) * 100
      : 0;

  const openTime =
    typeof t?.openTime === "string" ? t.openTime : new Date().toISOString();
  const closeTime =
    typeof t?.closeTime === "string" ? t.closeTime : openTime;

  const open = new Date(openTime).getTime();
  const close = new Date(closeTime).getTime();
  const duration =
    typeof t?.duration === "string" ? t.duration : formatDuration(close - open);

  return {
    id: String(t?.id ?? `${t?.symbol ?? "XAUUSD"}-${openTime}`),
    symbol: String(t?.symbol ?? "XAUUSD"),
    type: (t?.type === "sell" ? "sell" : "buy") as "buy" | "sell",
    entryPrice,
    exitPrice,
    volume,
    openTime,
    closeTime,
    pnl,
    pnlPercent,
    duration,
    strategy: String(t?.strategy ?? "unknown"),
    exitType: normalizeExitType(t?.exitType), // ? normalized literal
    stopLoss: safeNum(t?.stopLoss, 0),
    takeProfit: safeNum(t?.takeProfit, 0),
    status: t?.status === "closed" ? "closed" : "open",
    comment: typeof t?.comment === "string" ? t.comment : undefined,
  };
}

export function useTradingData() {
  const [state, setState] = useState<TradingDataState>({
    loading: true,
    error: null,
    balance: null,
    backendPositions: [],
    trades: [],
    priceHistory: [],
  });

  const refresh = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));

    try {
      const [balance, backendPositions] = await Promise.all([
        apiGet<BalanceResponse>("/api/trading/balance"),
        apiGet<BackendPosition[]>("/api/trading/positions"),
      ]);

      let trades: Trade[] = [];
      try {
        const raw = await apiGet<any[]>("/api/trading/trades?limit=200");
        trades = Array.isArray(raw) ? raw.map(normalizeTrade) : [];
      } catch {
        trades = [];
      }

      let priceHistory: PriceCandle[] = [];
      try {
        priceHistory = await apiGet<PriceCandle[]>(
          "/api/market-data/historical?symbol=XAUUSD&tf=1h&limit=200"
        );
      } catch {
        priceHistory = [];
      }

      setState({
        loading: false,
        error: null,
        balance,
        backendPositions: Array.isArray(backendPositions) ? backendPositions : [],
        trades,
        priceHistory: Array.isArray(priceHistory) ? priceHistory : [],
      });
    } catch (e: any) {
      setState((s) => ({
        ...s,
        loading: false,
        error: e?.message || "Failed to load trading data",
      }));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const positions: Position[] = useMemo(() => {
    return (state.backendPositions ?? []).map(toUIPosition);
  }, [state.backendPositions]);

  const history: Trade[] = useMemo(() => {
    if (state.trades && state.trades.length > 0) return state.trades;
    return positions.map(positionToTrade);
  }, [state.trades, positions]);

  const stats: Stats = useMemo(() => {
    const bal = state.balance?.balance ?? 0;
    const eq = state.balance?.equity ?? bal;
    const currency = state.balance?.currency;

    const totalPnL = positions.reduce((sum, p) => sum + safeNum(p.pnl, 0), 0);

    const sod = startOfLocalDay();
    const todayPnL = positions.reduce((sum, p) => {
      const t = p.openTime ? new Date(p.openTime).getTime() : NaN;
      if (!Number.isNaN(t) && t >= sod) return sum + safeNum(p.pnl, 0);
      return sum;
    }, 0);

    const activeTrades = positions.length;
    const winRate = 0;
    const totalTrades = history.length;

    return {
      balance: bal,
      equity: eq,
      currency,
      totalPnL,
      todayPnL,
      winRate,
      totalTrades,
      activeTrades,
      openPositions: positions.length,
    };
  }, [state.balance, positions, history.length]);

  return {
    stats,
    positions,
    history,
    isLoading: state.loading,
    error: state.error,
    refresh,
    priceHistory: state.priceHistory,
  };
}