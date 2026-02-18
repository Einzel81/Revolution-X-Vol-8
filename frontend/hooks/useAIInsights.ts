"use client";

import { useState, useEffect, useCallback } from "react";

interface AIInsight {
  id: string;
  type: "prediction" | "pattern" | "sentiment" | "recommendation";
  symbol: string;
  direction: "bullish" | "bearish" | "neutral";
  confidence: number;
  title: string;
  description: string;
  timeframe: string;
  indicators: string[];
  timestamp: string;
  expiresAt: string;
}

interface ModelPerformance {
  model: string;
  accuracy: number;
  predictions: number;
  lastUpdated: string;
}

export function useAIInsights() {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [performance, setPerformance] = useState<ModelPerformance[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = useCallback(async (symbol?: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const url = symbol 
        ? `/api/ai/insights?symbol=${symbol}` 
        : "/api/ai/insights";
      
      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch insights");
      
      const data = await response.json();
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchPerformance = useCallback(async () => {
    try {
      const response = await fetch("/api/ai/performance");
      if (!response.ok) throw new Error("Failed to fetch performance");
      
      const data = await response.json();
      setPerformance(data);
    } catch (err) {
      console.error("Error fetching AI performance:", err);
    }
  }, []);

  const getInsightById = useCallback((id: string) => {
    return insights.find((i) => i.id === id);
  }, [insights]);

  const getLatestInsight = useCallback((symbol?: string) => {
    if (symbol) {
      return insights.find((i) => i.symbol === symbol);
    }
    return insights[0];
  }, [insights]);

  const getInsightsByType = useCallback((type: AIInsight["type"]) => {
    return insights.filter((i) => i.type === type);
  }, [insights]);

  const getHighConfidenceInsights = useCallback((threshold: number = 80) => {
    return insights.filter((i) => i.confidence >= threshold);
  }, [insights]);

  // Auto-refresh insights
  useEffect(() => {
    fetchInsights();
    fetchPerformance();
    
    const interval = setInterval(() => {
      fetchInsights();
    }, 60000); // Every minute

    return () => clearInterval(interval);
  }, [fetchInsights, fetchPerformance]);

  return {
    insights,
    performance,
    isLoading,
    error,
    fetchInsights,
    fetchPerformance,
    getInsightById,
    getLatestInsight,
    getInsightsByType,
    getHighConfidenceInsights,
  };
}
