"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
} from "lightweight-charts";
import { motion } from "framer-motion";
import { Settings, Maximize2, Crosshair, Layers, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Toggle } from "@/components/ui/toggle";
import { useWebSocket } from "@/hooks/useWebSocket";

interface TradingChartProps {
  symbol: string;
  timeframe: string;
}

interface OrderBlock {
  id: string;
  top: number;
  bottom: number;
  type: "bullish" | "bearish";
  timestamp: number;
}

interface TradeMarker {
  id: string;
  time: number;
  price: number;
  type: "entry" | "sl" | "tp";
  position: "buy" | "sell";
}

type UTCTimestamp = import("lightweight-charts").UTCTimestamp;

function toUTCTimestampMs(ms: number): UTCTimestamp {
  // lightweight-charts expects seconds (integer)
  return Math.floor(ms / 1000) as UTCTimestamp;
}

export function TradingChart({ symbol, timeframe }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  const { lastMessage, isConnected, connectionError } = useWebSocket();

  const [showOrderBlocks, setShowOrderBlocks] = useState(true);
  const [showVolume, setShowVolume] = useState(true);
  const [showTradeMarkers, setShowTradeMarkers] = useState(true);

  const [orderBlocks, setOrderBlocks] = useState<OrderBlock[]>([]);
  const [tradeMarkers, setTradeMarkers] = useState<TradeMarker[]>([]);

  // Load historical data (stable callback)
  const loadHistoricalData = useCallback(async () => {
    try {
      const url = `/api/market-data/historical?symbol=${encodeURIComponent(
        symbol
      )}&timeframe=${encodeURIComponent(timeframe)}`;

      const response = await fetch(url);

      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(`HTTP ${response.status} ${response.statusText} - ${text}`);
      }

      const data = await response.json();

      const candles = Array.isArray(data?.candles) ? data.candles : [];

      if (candlestickSeriesRef.current) {
        const candleData = candles.map((c: any) => ({
          time: toUTCTimestampMs(Number(c.timestamp)),
          open: Number(c.open),
          high: Number(c.high),
          low: Number(c.low),
          close: Number(c.close),
        }));

        candlestickSeriesRef.current.setData(candleData);
      }

      if (volumeSeriesRef.current) {
        const volumeData = candles.map((c: any) => ({
          time: toUTCTimestampMs(Number(c.timestamp)),
          value: Number(c.volume),
          color:
            Number(c.close) >= Number(c.open)
              ? "rgba(34, 197, 94, 0.5)"
              : "rgba(239, 68, 68, 0.5)",
        }));

        volumeSeriesRef.current.setData(volumeData);
      }

      setOrderBlocks(Array.isArray(data?.orderBlocks) ? data.orderBlocks : []);
      setTradeMarkers(Array.isArray(data?.tradeMarkers) ? data.tradeMarkers : []);
    } catch (error) {
      console.error("Error loading historical data:", error);
    }
  }, [symbol, timeframe]);

  // Initialize / re-init chart when symbol/timeframe changes
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Cleanup existing chart if any
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
      candlestickSeriesRef.current = null;
      volumeSeriesRef.current = null;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: "transparent" },
        textColor: "#d1d5db",
      },
      grid: {
        vertLines: { color: "rgba(75, 85, 99, 0.2)" },
        horzLines: { color: "rgba(75, 85, 99, 0.2)" },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: "#60a5fa",
          labelBackgroundColor: "#60a5fa",
        },
        horzLine: {
          color: "#60a5fa",
          labelBackgroundColor: "#60a5fa",
        },
      },
      rightPriceScale: {
        borderColor: "rgba(75, 85, 99, 0.3)",
      },
      timeScale: {
        borderColor: "rgba(75, 85, 99, 0.3)",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const volumeSeries = chart.addHistogramSeries({
      color: "#3b82f6",
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    // Apply current visibility settings
    volumeSeries.applyOptions({ visible: showVolume });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // Load initial candles
    loadHistoricalData();

    const handleResize = () => {
      if (!chartContainerRef.current || !chartRef.current) return;
      chartRef.current.applyOptions({
        width: chartContainerRef.current.clientWidth,
        height: 500,
      });
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [symbol, timeframe, loadHistoricalData, showVolume]);

  // Toggle volume visibility
  useEffect(() => {
    if (volumeSeriesRef.current) {
      volumeSeriesRef.current.applyOptions({ visible: showVolume });
    }
  }, [showVolume]);

  // Real-time updates via WebSocket
  useEffect(() => {
    if (!lastMessage) return;

    let msg: any;
    try {
      msg = JSON.parse(lastMessage);
    } catch {
      return;
    }

    if (msg?.type !== "price_update") return;
    if (msg?.symbol !== symbol) return;

    const candle = msg?.candle;
    if (!candle) return;

    const update = {
      time: toUTCTimestampMs(Number(candle.timestamp)),
      open: Number(candle.open),
      high: Number(candle.high),
      low: Number(candle.low),
      close: Number(candle.close),
    };

    candlestickSeriesRef.current?.update(update);

    if (showVolume) {
      volumeSeriesRef.current?.update({
        time: toUTCTimestampMs(Number(candle.timestamp)),
        value: Number(candle.volume),
        color:
          Number(candle.close) >= Number(candle.open)
            ? "rgba(34, 197, 94, 0.5)"
            : "rgba(239, 68, 68, 0.5)",
      });
    }
  }, [lastMessage, symbol, showVolume]);

  // Order Blocks (placeholder)
  useEffect(() => {
    if (!chartRef.current || !showOrderBlocks) return;
    // TODO: implement primitives/overlays
    // console.log("OrderBlocks:", orderBlocks);
  }, [orderBlocks, showOrderBlocks]);

  // Trade Markers (placeholder)
  useEffect(() => {
    if (!chartRef.current || !showTradeMarkers) return;
    // TODO: implement series.setMarkers once you define marker schema
    // console.log("TradeMarkers:", tradeMarkers);
  }, [tradeMarkers, showTradeMarkers]);

  const toggleFullscreen = () => {
    if (!chartContainerRef.current) return;
    if (!document.fullscreenElement) chartContainerRef.current.requestFullscreen();
    else document.exitFullscreen();
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="relative"
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-4 p-2 bg-slate-700/30 rounded-lg">
        <div className="flex items-center gap-2">
          <span className="text-white font-bold text-lg">{symbol}</span>
          <span className="text-slate-400 text-sm">|</span>
          <span className="text-slate-400 text-sm">{timeframe}</span>

          {/* WS status (????) */}
          <span className="ml-3 text-xs text-slate-400">
            WS:{" "}
            <span className={isConnected ? "text-green-400" : "text-red-400"}>
              {isConnected ? "connected" : "disconnected"}
            </span>
            {connectionError ? (
              <span className="ml-2 text-red-400">({connectionError})</span>
            ) : null}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Toggle
            pressed={showOrderBlocks}
            onPressedChange={setShowOrderBlocks}
            className="data-[state=on]:bg-blue-600"
          >
            <Layers className="w-4 h-4 mr-1" />
            <span className="text-xs">OB</span>
          </Toggle>

          <Toggle
            pressed={showVolume}
            onPressedChange={setShowVolume}
            className="data-[state=on]:bg-blue-600"
          >
            <BarChart3 className="w-4 h-4 mr-1" />
            <span className="text-xs">Vol</span>
          </Toggle>

          <Toggle
            pressed={showTradeMarkers}
            onPressedChange={setShowTradeMarkers}
            className="data-[state=on]:bg-blue-600"
          >
            <Crosshair className="w-4 h-4 mr-1" />
            <span className="text-xs">Trades</span>
          </Toggle>

          <Button variant="ghost" size="icon" onClick={toggleFullscreen}>
            <Maximize2 className="w-4 h-4" />
          </Button>

          <Button variant="ghost" size="icon">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Chart Container */}
      <div ref={chartContainerRef} className="w-full h-[500px] rounded-lg overflow-hidden" />

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs text-slate-400">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded-sm" />
          <span>????</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded-sm" />
          <span>???</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500/50 rounded-sm" />
          <span>OB ????</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-orange-500/50 rounded-sm" />
          <span>OB ????</span>
        </div>
      </div>
    </motion.div>
  );
}