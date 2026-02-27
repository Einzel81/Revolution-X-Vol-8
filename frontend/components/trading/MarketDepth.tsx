"use client";

import React from "react";

export default function MarketDepth() {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <h3 className="text-white font-semibold mb-3">Market Depth</h3>
      <div className="text-sm text-gray-400">
        Market depth visualization is not implemented yet.
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div className="bg-gray-900 p-2 rounded border border-gray-700">
          Bid side (stub)
        </div>
        <div className="bg-gray-900 p-2 rounded border border-gray-700">
          Ask side (stub)
        </div>
      </div>
    </div>
  );
}