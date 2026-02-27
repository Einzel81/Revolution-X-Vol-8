'use client';

import React, { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  AreaChart,
  Area
} from 'recharts';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Shield,
  Activity,
  ArrowRight,
  Bell,
  BarChart3,
  GitCompare
} from 'lucide-react';
import { motion } from 'framer-motion';

interface DXYData {
  timestamp: string;
  price: number;
  support?: number;
  resistance?: number;
}

interface CorrelationData {
  timeframe: string;
  correlation: number;
  reliability: string;
}

export default function DXYGuardianPage() {
  const [dxyPrice, setDxyPrice] = useState<number>(104.25);
  const [trend, setTrend] = useState<string>('bearish');
  const [correlation, setCorrelation] = useState<number>(-0.82);
  const [selectedTimeframe, setSelectedTimeframe] = useState('medium');
  const [alerts, setAlerts] = useState([
    { id: 1, type: 'resistance', message: 'DXY approaching resistance at 104.50', severity: 'warning' },
    { id: 2, type: 'support', message: 'Strong support holding at 103.00', severity: 'info' },
  ]);

  // Mock chart data
  const chartData: DXYData[] = Array.from({ length: 50 }, (_, i) => ({
    timestamp: new Date(Date.now() - (50 - i) * 3600000).toISOString(),
    price: 104 + Math.sin(i * 0.2) * 0.5 + Math.random() * 0.2,
    support: 103.0,
    resistance: 105.0,
  }));

  const correlationData: CorrelationData[] = [
    { timeframe: 'Short (20)', correlation: -0.75, reliability: 'high' },
    { timeframe: 'Medium (60)', correlation: -0.82, reliability: 'high' },
    { timeframe: 'Long (200)', correlation: -0.78, reliability: 'high' },
  ];

  const getImpactColor = (impact: string) => {
    switch(impact) {
      case 'bullish': return 'text-green-400';
      case 'bearish': return 'text-red-400';
      default: return 'text-yellow-400';
    }
  };

  const getImpactBg = (impact: string) => {
    switch(impact) {
      case 'bullish': return 'bg-green-500/20 border-green-500/30';
      case 'bearish': return 'bg-red-500/20 border-red-500/30';
      default: return 'bg-yellow-500/20 border-yellow-500/30';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
                DXY Guardian
              </h1>
              <p className="text-slate-400 mt-1">Dollar Index Monitor & Gold Correlation</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm text-slate-400">Current DXY</div>
              <div className="text-3xl font-mono font-bold text-white">{dxyPrice.toFixed(2)}</div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
              trend === 'bullish' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
            }`}>
              {trend === 'bullish' ? <TrendingUp className="w-4 h-4 inline mr-1" /> : <TrendingDown className="w-4 h-4 inline mr-1" />}
              {trend}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Main Chart */}
        <div className="col-span-12 lg:col-span-8">
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-400" />
                DXY Price Action
              </h2>
              <div className="flex gap-2">
                {['1H', '4H', '1D', '1W'].map((tf) => (
                  <button
                    key={tf}
                    className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(str) => new Date(str).getHours() + ':00'}
                    stroke="#64748b"
                  />
                  <YAxis domain={[102, 106]} stroke="#64748b" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                    formatter={(value: number) => value.toFixed(3)}
                  />
                  <ReferenceLine y={105} stroke="#ef4444" strokeDasharray="3 3" label="Resistance" />
                  <ReferenceLine y={103} stroke="#22c55e" strokeDasharray="3 3" label="Support" />
                  <Area 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#10b981" 
                    fillOpacity={1} 
                    fill="url(#colorPrice)" 
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Key Levels */}
            <div className="grid grid-cols-3 gap-4 mt-6">
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                <div className="text-red-400 text-sm mb-1">Major Resistance</div>
                <div className="text-2xl font-bold">105.00</div>
                <div className="text-xs text-slate-400 mt-1">Strong selling pressure</div>
              </div>
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <div className="text-yellow-400 text-sm mb-1">Pivot Point</div>
                <div className="text-2xl font-bold">104.00</div>
                <div className="text-xs text-slate-400 mt-1">Decision level</div>
              </div>
              <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                <div className="text-green-400 text-sm mb-1">Major Support</div>
                <div className="text-2xl font-bold">103.00</div>
                <div className="text-xs text-slate-400 mt-1">Strong buying interest</div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* Gold Impact Card */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`p-6 rounded-xl border ${getImpactBg(trend === 'bullish' ? 'bearish' : 'bullish')}`}
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <GitCompare className="w-5 h-5" />
              Impact on Gold (XAUUSD)
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Current Correlation</span>
                <span className="text-2xl font-bold text-purple-400">{correlation}</span>
              </div>
              
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                  style={{ width: `${Math.abs(correlation) * 100}%` }}
                />
              </div>
              
              <div className={`p-4 rounded-lg ${getImpactBg(trend === 'bullish' ? 'bearish' : 'bullish')}`}>
                <div className="flex items-center gap-2 mb-2">
                  {trend === 'bullish' ? <TrendingDown className="w-5 h-5 text-red-400" /> : <TrendingUp className="w-5 h-5 text-green-400" />}
                  <span className="font-semibold">
                    {trend === 'bullish' ? 'Bearish for Gold' : 'Bullish for Gold'}
                  </span>
                </div>
                <p className="text-sm text-slate-300">
                  {trend === 'bullish' 
                    ? 'DXY strength typically pressures Gold prices lower. Consider caution on long positions.'
                    : 'DXY weakness supports Gold prices. Favorable environment for long positions.'}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 bg-slate-900/50 rounded-lg">
                  <div className="text-slate-400">Beta to Gold</div>
                  <div className="text-lg font-semibold text-white">-0.85</div>
                </div>
                <div className="p-3 bg-slate-900/50 rounded-lg">
                  <div className="text-slate-400">R-Squared</div>
                  <div className="text-lg font-semibold text-white">0.72</div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Correlation Matrix */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              Correlation by Timeframe
            </h3>
            
            <div className="space-y-3">
              {correlationData.map((data) => (
                <div 
                  key={data.timeframe}
                  onClick={() => setSelectedTimeframe(data.timeframe.toLowerCase().split(' ')[0])}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedTimeframe === data.timeframe.toLowerCase().split(' ')[0]
                      ? 'bg-blue-500/20 border border-blue-500/30'
                      : 'bg-slate-900/50 hover:bg-slate-700/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-300">{data.timeframe}</span>
                    <span className={`text-sm px-2 py-0.5 rounded ${
                      data.reliability === 'high' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {data.reliability}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500"
                        style={{ width: `${Math.abs(data.correlation) * 100}%` }}
                      />
                    </div>
                    <span className="font-mono text-sm">{data.correlation}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Alerts */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Bell className="w-5 h-5 text-yellow-400" />
              Active Alerts
            </h3>
            
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div 
                  key={alert.id}
                  className={`p-3 rounded-lg border ${
                    alert.severity === 'warning' 
                      ? 'bg-yellow-500/10 border-yellow-500/30' 
                      : 'bg-blue-500/10 border-blue-500/30'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className={`w-5 h-5 ${
                      alert.severity === 'warning' ? 'text-yellow-400' : 'text-blue-400'
                    }`} />
                    <div>
                      <div className="font-medium text-sm">{alert.message}</div>
                      <div className="text-xs text-slate-400 mt-1">2 minutes ago</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section - Trading Recommendations */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded-xl border border-slate-600 p-6">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            Signal Adjustment
          </h4>
          <p className="text-sm text-slate-300">
            Current DXY trend suggests adjusting Gold signals by 
            <span className="text-yellow-400 font-semibold mx-1">-10% confidence</span>
            on buy signals.
          </p>
        </div>
        
        <div className="bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded-xl border border-slate-600 p-6">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-400" />
            Hedging Suggestion
          </h4>
          <p className="text-sm text-slate-300">
            Strong inverse correlation detected. Consider 
            <span className="text-green-400 font-semibold mx-1">Long Gold + Short DXY</span>
            hedge position.
          </p>
        </div>
        
        <div className="bg-gradient-to-r from-slate-800/50 to-slate-700/50 rounded-xl border border-slate-600 p-6">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <ArrowRight className="w-5 h-5 text-blue-400" />
            Next Key Event
          </h4>
          <p className="text-sm text-slate-300">
            Watch for DXY reaction at 
            <span className="text-white font-semibold mx-1">105.00</span>
            resistance. Break above could pressure Gold significantly lower.
          </p>
        </div>
      </div>
    </div>
  );
}
