"use client";

import React, { useState } from "react";

export default function OrderPanel() {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [type, setType] = useState<"buy" | "sell">("buy");
  const [volume, setVolume] = useState(0.01);

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-semibold">Order Panel</h3>
        <span className="text-xs text-gray-400">stub</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Symbol</label>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as any)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white"
          >
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Volume</label>
          <input
            type="number"
            step="0.01"
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white"
          />
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          className="px-4 py-2 rounded bg-green-600/80 hover:bg-green-600 text-white text-sm"
          onClick={() => console.log("BUY (stub)", { symbol, volume })}
        >
          Place Buy
        </button>
        <button
          type="button"
          className="px-4 py-2 rounded bg-red-600/80 hover:bg-red-600 text-white text-sm"
          onClick={() => console.log("SELL (stub)", { symbol, volume })}
        >
          Place Sell
        </button>
      </div>

      <p className="text-xs text-gray-400 mt-3">
        This is a placeholder component to satisfy dynamic import. Replace with real trading UI.
      </p>
    </div>
  );
}