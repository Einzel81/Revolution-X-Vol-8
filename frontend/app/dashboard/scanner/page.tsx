'use client';

import React, { useState, useEffect } from 'react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell
} from 'recharts';
import { 
  Scan, 
  Zap, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  RefreshCw,
  Settings,
  AlertCircle,
  CheckCircle2,
  Target,
  Activity,
  BarChart3
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Opportunity {
  symbol: string;
  name: string;
  current_price: number;
  daily_change: number;
  ai_score: number;
  trend_score: number;
  momentum_score: number;
  volume_score: number;
  smc_score: number;
  risk_level: string;
  recommended_action: string;
  confidence: number;
  last_update: string;
}

export default function ScannerPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoMode, setAutoMode] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Opportunity | null>(null);
  const [minScore, setMinScore] = useState(60);

  useEffect(() => {
    fetchOpportunities();
    const interval = setInterval(fetchOpportunities, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [minScore]);

  const fetchOpportunities = async () => {
    try {
      const response = await fetch(`/api/v1/ai/scanner/opportunities?min_score=${minScore}`);
      const data = await response.json();
      setOpportunities(data.opportunities);
    } catch (error) {
      console.error('Failed to fetch opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  const getActionIcon = (action: string) => {
    switch(action) {
      case 'BUY': return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'SELL': return <TrendingDown className="w-5 h-5 text-red-500" />;
      default: return <Minus className="w-5 h-5 text-gray-500" />;
    }
  };

  const radarData = selectedAsset ? [
    { subject: 'AI Score', A: selectedAsset.ai_score, fullMark: 100 },
    { subject: 'Trend', A: selectedAsset.trend_score, fullMark: 100 },
    { subject: 'Momentum', A: selectedAsset.momentum_score, fullMark: 100 },
    { subject: 'Volume', A: selectedAsset.volume_score, fullMark: 100 },
    { subject: 'SMC', A: selectedAsset.smc_score, fullMark: 100 },
  ] : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl">
              <Scan className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Smart Opportunity Scanner
              </h1>
              <p className="text-slate-400 mt-1">AI-Powered Multi-Asset Analysis</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-slate-800/50 px-4 py-2 rounded-lg border border-slate-700">
              <span className="text-sm text-slate-400">Auto-Select</span>
              <button
                onClick={() => setAutoMode(!autoMode)}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  autoMode ? 'bg-green-500' : 'bg-slate-600'
                }`}
              >
                <motion.div
                  className="absolute top-1 w-4 h-4 bg-white rounded-full"
                  animate={{ left: autoMode ? '28px' : '4px' }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              </button>
            </div>
            
            <button
              onClick={fetchOpportunities}
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Opportunities List */}
        <div className="col-span-12 lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              Top Opportunities
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-400">Min Score:</span>
              <input
                type="range"
                min="0"
                max="100"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-32 accent-purple-500"
              />
              <span className="text-sm font-mono bg-slate-800 px-2 py-1 rounded">{minScore}</span>
            </div>
          </div>

          <AnimatePresence>
            {opportunities.map((opp, index) => (
              <motion.div
                key={opp.symbol}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => setSelectedAsset(opp)}
                className={`p-6 rounded-xl border cursor-pointer transition-all ${
                  selectedAsset?.symbol === opp.symbol
                    ? 'bg-gradient-to-r from-purple-900/50 to-pink-900/50 border-purple-500'
                    : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl font-bold text-white">{opp.symbol}</div>
                    <div>
                      <div className="text-slate-400">{opp.name}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-2xl font-mono">${opp.current_price.toFixed(2)}</span>
                        <span className={`text-sm ${opp.daily_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {opp.daily_change >= 0 ? '+' : ''}{opp.daily_change}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    {/* AI Score Circle */}
                    <div className="relative w-20 h-20">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle
                          cx="40"
                          cy="40"
                          r="36"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="transparent"
                          className="text-slate-700"
                        />
                        <circle
                          cx="40"
                          cy="40"
                          r="36"
                          stroke={getScoreColor(opp.ai_score)}
                          strokeWidth="8"
                          fill="transparent"
                          strokeDasharray={`${opp.ai_score * 2.26} 226`}
                          className="transition-all duration-1000"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-xl font-bold">{opp.ai_score}</span>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <div className="flex items-center gap-2">
                        {getActionIcon(opp.recommended_action)}
                        <span className={`font-semibold ${
                          opp.recommended_action === 'BUY' ? 'text-green-400' :
                          opp.recommended_action === 'SELL' ? 'text-red-400' : 'text-gray-400'
                        }`}>
                          {opp.recommended_action}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-sm text-slate-400">
                        <Activity className="w-4 h-4" />
                        {(opp.confidence * 100).toFixed(0)}% confidence
                      </div>
                      <div className={`px-2 py-0.5 rounded text-xs ${
                        opp.risk_level === 'low' ? 'bg-green-500/20 text-green-400' :
                        opp.risk_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {opp.risk_level} risk
                      </div>
                    </div>
                  </div>
                </div>

                {/* Component Scores */}
                <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-slate-700">
                  {[
                    { label: 'Trend', value: opp.trend_score, icon: TrendingUp },
                    { label: 'Momentum', value: opp.momentum_score, icon: Zap },
                    { label: 'Volume', value: opp.volume_score, icon: BarChart3 },
                    { label: 'SMC', value: opp.smc_score, icon: Target },
                  ].map((item) => (
                    <div key={item.label} className="text-center">
                      <div className="flex items-center justify-center gap-1 text-slate-400 text-sm mb-1">
                        <item.icon className="w-3 h-3" />
                        {item.label}
                      </div>
                      <div className="text-lg font-semibold" style={{ color: getScoreColor(item.value) }}>
                        {item.value}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Detail Panel */}
        <div className="col-span-12 lg:col-span-5 space-y-6">
          {selectedAsset ? (
            <>
              {/* Radar Chart */}
              <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-purple-400" />
                  Analysis Breakdown
                </h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                      <Radar
                        name={selectedAsset.symbol}
                        dataKey="A"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        fill="#8b5cf6"
                        fillOpacity={0.3}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                        itemStyle={{ color: '#fff' }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* AI Consensus */}
              <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
                <h3 className="text-lg font-semibold mb-4">Model Consensus</h3>
                <div className="space-y-3">
                  {['LSTM Neural Net', 'XGBoost', 'LightGBM'].map((model, idx) => (
                    <div key={model} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                      <span className="text-slate-300">{model}</span>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                        <span className="text-sm text-slate-400">Agree</span>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 p-4 bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-lg border border-purple-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-5 h-5 text-purple-400" />
                    <span className="font-semibold">Recommendation</span>
                  </div>
                  <p className="text-slate-300 text-sm">
                    {selectedAsset.recommended_action === 'BUY' 
                      ? 'Strong buying opportunity detected. All models show bullish alignment with high confidence.'
                      : selectedAsset.recommended_action === 'SELL'
                      ? 'Bearish signals across models. Consider short position or exiting longs.'
                      : 'Mixed signals. Recommend waiting for clearer directional bias.'}
                  </p>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="grid grid-cols-2 gap-4">
                <button className="p-4 bg-green-600 hover:bg-green-700 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Execute Trade
                </button>
                <button className="p-4 bg-slate-700 hover:bg-slate-600 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2">
                  <Target className="w-5 h-5" />
                  Set Alert
                </button>
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500">
              <div className="text-center">
                <Scan className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Select an asset to view detailed analysis</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
