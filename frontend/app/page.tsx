// frontend/app/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, Activity, DollarSign, BarChart3 } from 'lucide-react';

export default function LandingPage() {
  const [stats, setStats] = useState({
    balance: 12450.00,
    dailyProfit: 345.50,
    winRate: 68,
    activeTrades: 3
  });

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-revolution-border bg-revolution-card/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-gold-400 to-gold-600 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-gold-400 to-gold-200 bg-clip-text text-transparent">
                Revolution X
              </h1>
              <p className="text-xs text-slate-400">AI-Powered Gold Trading</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm text-slate-400">System Status</div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                <span className="text-emerald-400 font-medium">Operational</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard 
            title="Account Balance"
            value={`$${stats.balance.toLocaleString()}`}
            change="+2.8%"
            icon={DollarSign}
            color="gold"
          />
          <StatCard 
            title="Daily Profit"
            value={`+$${stats.dailyProfit.toFixed(2)}`}
            change="+2.77%"
            icon={TrendingUp}
            color="emerald"
          />
          <StatCard 
            title="Win Rate"
            value={`${stats.winRate}%`}
            change="+5% this week"
            icon={Activity}
            color="blue"
          />
          <StatCard 
            title="Active Trades"
            value={stats.activeTrades.toString()}
            change="3 long, 0 short"
            icon={BarChart3}
            color="purple"
          />
        </div>

        {/* Coming Soon */}
        <div className="bg-revolution-card border border-revolution-border rounded-xl p-8 text-center">
          <div className="w-16 h-16 bg-gold-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Activity className="w-8 h-8 text-gold-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Dashboard Coming Soon</h2>
          <p className="text-slate-400 max-w-md mx-auto">
            The full Revolution X dashboard is under development. 
            Check back for real-time trading, AI signals, and advanced analytics.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-revolution-border py-6">
        <div className="container mx-auto px-4 text-center text-slate-500 text-sm">
          © 2026 Revolution X. All rights reserved.
        </div>
      </footer>
    </div>
  );
}

// Stat Card Component
function StatCard({ 
  title, 
  value, 
  change, 
  icon: Icon,
  color 
}: { 
  title: string;
  value: string;
  change: string;
  icon: any;
  color: string;
}) {
  const colorClasses = {
    gold: 'from-gold-500/20 to-gold-600/20 text-gold-400',
    emerald: 'from-emerald-500/20 to-emerald-600/20 text-emerald-400',
    blue: 'from-blue-500/20 to-blue-600/20 text-blue-400',
    purple: 'from-purple-500/20 to-purple-600/20 text-purple-400',
  };

  return (
    <div className="bg-revolution-card border border-revolution-border rounded-xl p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-white">{value}</h3>
          <p className="text-emerald-400 text-sm mt-1">{change}</p>
        </div>
        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} flex items-center justify-center`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
