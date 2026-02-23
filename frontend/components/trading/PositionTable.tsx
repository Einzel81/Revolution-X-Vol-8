"use client";

import React from "react";

type Position = {
  id?: string;
  symbol?: string;
  type?: string;
  volume?: number;
  pnl?: number;
};

export default function PositionTable({ positions = [] }: { positions?: Position[] }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <h3 className="text-white font-semibold mb-3">Positions</h3>

      {positions.length === 0 ? (
        <div className="text-sm text-gray-400">No open positions (stub).</div>
      ) : (
        <table className="w-full text-sm text-left text-gray-300">
          <thead className="text-xs text-gray-400 uppercase border-b border-gray-700">
            <tr>
              <th className="py-2">Symbol</th>
              <th className="py-2">Type</th>
              <th className="py-2">Volume</th>
              <th className="py-2">PnL</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((pos, idx) => (
              <tr key={pos.id ?? idx} className="border-b border-gray-700">
                <td className="py-2">{pos.symbol}</td>
                <td className="py-2">{pos.type}</td>
                <td className="py-2">{pos.volume}</td>
                <td className="py-2">{pos.pnl}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}