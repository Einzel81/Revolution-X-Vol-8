"use client";

import React, { useEffect, useRef } from "react";
import { IChartApi, ISeriesApi, LineStyle } from "lightweight-charts";

interface OrderBlock {
  id: string;
  top: number;
  bottom: number;
  left: number;
  right: number;
  type: "bullish" | "bearish";
  strength: "weak" | "moderate" | "strong";
  mitigated: boolean;
}

interface FairValueGap {
  id: string;
  top: number;
  bottom: number;
  left: number;
  right?: number;
  type: "bullish" | "bearish";
  filled: boolean;
}

interface LiquidityPool {
  id: string;
  level: number;
  type: "buy_side" | "sell_side";
  strength: number;
  hits: number;
}

interface BreakerBlock {
  id: string;
  top: number;
  bottom: number;
  left: number;
  right: number;
  type: "bullish" | "bearish";
  activated: boolean;
}

interface ChartOverlaysProps {
  chart: IChartApi | null;
  candlestickSeries: ISeriesApi<"Candlestick"> | null;
  orderBlocks?: OrderBlock[];
  fvgs?: FairValueGap[];
  liquidityPools?: LiquidityPool[];
  breakerBlocks?: BreakerBlock[];
  visibleOverlays: {
    orderBlocks: boolean;
    fvgs: boolean;
    liquidityPools: boolean;
    breakerBlocks: boolean;
  };
}

export function ChartOverlays({
  chart,
  candlestickSeries,
  orderBlocks = [],
  fvgs = [],
  liquidityPools = [],
  breakerBlocks = [],
  visibleOverlays,
}: ChartOverlaysProps) {
  const primitivesRef = useRef<any[]>([]);

  // Clear existing primitives
  const clearPrimitives = () => {
    primitivesRef.current.forEach((primitive) => {
      if (candlestickSeries) {
        // Remove primitive logic here
      }
    });
    primitivesRef.current = [];
  };

  // Draw Order Blocks
  useEffect(() => {
    if (!chart || !candlestickSeries || !visibleOverlays.orderBlocks) {
      clearPrimitives();
      return;
    }

    orderBlocks.forEach((ob) => {
      if (ob.mitigated) return;

      const color =
        ob.type === "bullish"
          ? "rgba(34, 197, 94, 0.2)"
          : "rgba(239, 68, 68, 0.2)";
      const borderColor =
        ob.type === "bullish"
          ? "rgba(34, 197, 94, 0.6)"
          : "rgba(239, 68, 68, 0.6)";

      // Create rectangle primitive for order block
      const primitive = {
        type: "rectangle",
        price1: ob.top,
        price2: ob.bottom,
        time1: ob.left,
        time2: ob.right || Date.now() / 1000,
        color: color,
        borderColor: borderColor,
        borderWidth: 1,
        borderStyle: LineStyle.Solid,
      };

      // Add to chart (implementation depends on lightweight-charts version)
      // candlestickSeries.attachPrimitive(primitive);
      primitivesRef.current.push(primitive);
    });

    return () => clearPrimitives();
  }, [chart, candlestickSeries, orderBlocks, visibleOverlays.orderBlocks]);

  // Draw Fair Value Gaps
  useEffect(() => {
    if (!chart || !candlestickSeries || !visibleOverlays.fvgs) return;

    fvgs.forEach((fvg) => {
      if (fvg.filled) return;

      const color =
        fvg.type === "bullish"
          ? "rgba(34, 197, 94, 0.15)"
          : "rgba(239, 68, 68, 0.15)";

      // Create FVG rectangle
      const primitive = {
        type: "rectangle",
        price1: fvg.top,
        price2: fvg.bottom,
        time1: fvg.left,
        time2: fvg.right || Date.now() / 1000,
        color: color,
        borderColor:
          fvg.type === "bullish"
            ? "rgba(34, 197, 94, 0.4)"
            : "rgba(239, 68, 68, 0.4)",
        borderWidth: 1,
        borderStyle: LineStyle.Dashed,
      };

      primitivesRef.current.push(primitive);
    });
  }, [chart, candlestickSeries, fvgs, visibleOverlays.fvgs]);

  // Draw Liquidity Pools
  useEffect(() => {
    if (!chart || !candlestickSeries || !visibleOverlays.liquidityPools) return;

    liquidityPools.forEach((pool) => {
      const color =
        pool.type === "buy_side"
          ? "rgba(34, 197, 94, 0.3)"
          : "rgba(239, 68, 68, 0.3)";

      // Create horizontal line with width based on strength
      const primitive = {
        type: "horizontal_line",
        price: pool.level,
        color: color,
        lineWidth: Math.max(2, pool.strength * 3),
        lineStyle: LineStyle.LargeDashed,
        title: `Liquidity (${pool.hits} hits)`,
      };

      primitivesRef.current.push(primitive);
    });
  }, [chart, candlestickSeries, liquidityPools, visibleOverlays.liquidityPools]);

  // Draw Breaker Blocks
  useEffect(() => {
    if (!chart || !candlestickSeries || !visibleOverlays.breakerBlocks) return;

    breakerBlocks.forEach((bb) => {
      if (!bb.activated) return;

      const color =
        bb.type === "bullish"
          ? "rgba(168, 85, 247, 0.2)"
          : "rgba(236, 72, 153, 0.2)";

      const primitive = {
        type: "rectangle",
        price1: bb.top,
        price2: bb.bottom,
        time1: bb.left,
        time2: bb.right || Date.now() / 1000,
        color: color,
        borderColor:
          bb.type === "bullish"
            ? "rgba(168, 85, 247, 0.6)"
            : "rgba(236, 72, 153, 0.6)",
        borderWidth: 2,
        borderStyle: LineStyle.Solid,
      };

      primitivesRef.current.push(primitive);
    });
  }, [chart, candlestickSeries, breakerBlocks, visibleOverlays.breakerBlocks]);

  return null; // This is a logic-only component
}

// Overlay Controls Component
export function OverlayControls({
  visibleOverlays,
  onToggle,
}: {
  visibleOverlays: {
    orderBlocks: boolean;
    fvgs: boolean;
    liquidityPools: boolean;
    breakerBlocks: boolean;
  };
  onToggle: (key: keyof typeof visibleOverlays) => void;
}) {
  const controls = [
    {
      key: "orderBlocks" as const,
      label: "Order Blocks",
      color: "bg-blue-500",
      description: "مناطق طلبات الذكاء المؤسسي",
    },
    {
      key: "fvgs" as const,
      label: "FVG",
      color: "bg-purple-500",
      description: "فجوات القيمة العادلة",
    },
    {
      key: "liquidityPools" as const,
      label: "Liquidity",
      color: "bg-orange-500",
      description: "تجمعات السيولة",
    },
    {
      key: "breakerBlocks" as const,
      label: "Breaker Blocks",
      color: "bg-pink-500",
      description: "مناطق الكسر والاعادة",
    },
  ];

  return (
    <div className="flex flex-wrap gap-2 p-2 bg-slate-800/50 rounded-lg">
      {controls.map((control) => (
        <button
          key={control.key}
          onClick={() => onToggle(control.key)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            visibleOverlays[control.key]
              ? "bg-slate-700 text-white"
              : "bg-transparent text-slate-400 hover:text-slate-200"
          }`}
          title={control.description}
        >
          <div
            className={`w-2 h-2 rounded-full ${control.color} ${
              visibleOverlays[control.key] ? "opacity-100" : "opacity-30"
            }`}
          />
          {control.label}
        </button>
      ))}
    </div>
  );
}
