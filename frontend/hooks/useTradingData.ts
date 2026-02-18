"use client";

import { useState, useEffect, useCallback } from "react";
import { useWebSocket } from "./useWebSocket";

interface Position {
  id: string;
  symbol: string;
  type: "buy" | "sell";
  entryPrice: number;
  currentPrice: number;
  volume: number;
  stopLoss: number;
  takeProfit: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  swap: number;
  commission: number;
}

interface Trade {
  id: string;
  symbol: string;
  type: "buy" | "sell";
  entryPrice: number;
  exitPrice: number;
  volume: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  closeTime: string;
  duration: string;
  strategy: string;
  exitType: "tp" | "sl" | "manual";
}

interface DashboardStats {
  balance: number;
  totalPnL: number;
  winRate: number;
  activeTrades: number;
  todayPnL: number;
  totalTrades: number;
}

export function useTradingData() {
  const { lastMessage, isConnected } = useWebSocket();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [history, setHistory] = useState<Trade[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch initial data
  const fetchInitialData = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Fetch stats
      const statsRes = await fetch("/api/dashboard/stats");
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch positions
      const positionsRes = await fetch("/api/positions");
      const positionsData = await positionsRes.json();
      setPositions(positionsData);

      // Fetch history
      const historyRes = await fetch("/api/trades/history");
      const historyData = await historyRes.json();
      setHistory(historyData);
    } catch (error) {
      console.error("Error fetching trading data:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchInitialData, 30000);
    return () => clearInterval(interval);
  }, [fetchInitialData]);

  // Handle WebSocket updates
  useEffect(() => {
    if (!lastMessage) return;

    const data = JSON.parse(lastMessage);
    
    switch (data.type) {
      case "position_update":
        setPositions(prev => {
          const index = prev.findIndex(p => p.id === data.payload.id);
          if (index >= 0) {
            const updated = [...prev];
            updated[index] = { ...updated[index], ...data.payload };
            return updated;
          }
          return [...prev, data.payload];
        });
        break;
        
      case "position_closed":
        setPositions(prev => prev.filter(p => p.id !== data.payload.id));
        // Add to history
        setHistory(prev => [data.payload, ...prev]);
        break;
        
      case "stats_update":
        setStats(prev => prev ? { ...prev, ...data.payload } : data.payload);
        break;
        
      case "new_trade":
        setHistory(prev => [data.payload, ...prev]);
        break;
    }
  }, [lastMessage]);

  const refreshData = useCallback(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  return {
    stats,
    positions,
    history,
    isLoading,
    isConnected,
    refreshData
  };
}
