"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from "lightweight-charts";
import { motion } from "framer-motion";
import { 
  Settings, 
  Maximize2, 
  Crosshair,
  Layers,
  BarChart3
} from "lucide-react";
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

export function TradingChart({ symbol, timeframe }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const { lastMessage } = useWebSocket();
  
  const [showOrderBlocks, setShowOrderBlocks] = useState(true);
  const [showVolume, setShowVolume] = useState(true);
  const [showTradeMarkers, setShowTradeMarkers] = useState(true);
  const [orderBlocks, setOrderBlocks] = useState<OrderBlock[]>([]);
  const [tradeMarkers, setTradeMarkers] = useState<TradeMarker[]>([]);

  // Initialize Chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

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

    // Candlestick Series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    // Volume Series
    const volumeSeries = chart.addHistogramSeries({
      color: "#3b82f6",
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "",
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // Load initial data
    loadHistoricalData();

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: 500,
        });
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [symbol, timeframe]);

  // Load historical data
  const loadHistoricalData = async () => {
    try {
      const response = await fetch(
        `/api/market-data/historical?symbol=${symbol}&timeframe=${timeframe}`
      );
      const data = await response.json();
      
      if (candlestickSeriesRef.current && volumeSeriesRef.current) {
        const candleData = data.candles.map((c: any) => ({
          time: c.timestamp / 1000,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));
        
        const volumeData = data.candles.map((c: any, i: number) => ({
          time: c.timestamp / 1000,
          value: c.volume,
          color: c.close >= c.open ? "rgba(34, 197, 94, 0.5)" : "rgba(239, 68, 68, 0.5)",
        }));

        candlestickSeriesRef.current.setData(candleData);
        volumeSeriesRef.current.setData(volumeData);
        
        // Load order blocks
        setOrderBlocks(data.orderBlocks || []);
        setTradeMarkers(data.tradeMarkers || []);
      }
    } catch (error) {
      console.error("Error loading historical data:", error);
    }
  };

  // Real-time updates
  useEffect(() => {
    if (!lastMessage) return;
    
    const data = JSON.parse(lastMessage);
    if (data.type === "price_update" && data.symbol === symbol) {
      const candle = data.candle;
      
      if (candlestickSeriesRef.current) {
        candlestickSeriesRef.current.update({
          time: candle.timestamp / 1000,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        });
      }
      
      if (volumeSeriesRef.current) {
        volumeSeriesRef.current.update({
          time: candle.timestamp / 1000,
          value: candle.volume,
          color: candle.close >= candle.open ? "rgba(34, 197, 94, 0.5)" : "rgba(239, 68, 68, 0.5)",
        });
      }
    }
  }, [lastMessage, symbol]);

  // Draw Order Blocks
  useEffect(() => {
    if (!chartRef.current || !showOrderBlocks) return;
    
    // Clear previous order blocks
    // Note: In real implementation, you'd use chart primitives or overlays
    
    orderBlocks.forEach((block) => {
      // Implementation would use chart primitives
      console.log("Drawing order block:", block);
    });
  }, [orderBlocks, showOrderBlocks]);

  // Draw Trade Markers
  useEffect(() => {
    if (!chartRef.current || !showTradeMarkers) return;
    
    tradeMarkers.forEach((marker) => {
      // Implementation would use chart markers
      console.log("Drawing trade marker:", marker);
    });
  }, [tradeMarkers, showTradeMarkers]);

  const toggleFullscreen = () => {
    if (!chartContainerRef.current) return;
    
    if (!document.fullscreenElement) {
      chartContainerRef.current.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
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
          <span className="text-slate-400 text-sm">{timeframe}m</span>
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
          
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleFullscreen}
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Chart Container */}
      <div 
        ref={chartContainerRef} 
        className="w-full h-[500px] rounded-lg overflow-hidden"
      />

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs text-slate-400">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded-sm" />
          <span>شراء</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded-sm" />
          <span>بيع</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500/50 rounded-sm" />
          <span>OB صاعد</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-orange-500/50 rounded-sm" />
          <span>OB هابط</span>
        </div>
      </div>
    </motion.div>
  );
}
