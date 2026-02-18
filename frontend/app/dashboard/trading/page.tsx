// frontend/app/dashboard/trading/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/auth';
import SignalCard from '@/components/trading/signal-card';
import { Loader2, RefreshCw } from 'lucide-react';

export default function TradingPage() {
  const [signal, setSignal] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    fetchSignal();
    const interval = setInterval(fetchSignal, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchSignal = async () => {
    try {
      const response = await api.post('/trading/signal');
      setSignal(response.data.signal);
    } catch (error) {
      console.error('Failed to fetch signal:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeTrade = async () => {
    if (!signal) return;
    
    setExecuting(true);
    try {
      const response = await api.post('/trading/execute', {
        symbol: 'XAUUSD',
        action: signal.action,
        entry: signal.entry_price,
        sl: signal.suggested_sl,
        tp: signal.suggested_tp,
      });
      
      alert(`Trade ${response.data.status}: ${JSON.stringify(response.data.position_size)}`);
    } catch (error) {
      console.error('Trade execution failed:', error);
      alert('Trade execution failed');
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-gold-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trading</h1>
          <p className="text-slate-400">AI-powered signal analysis</p>
        </div>
        <button
          onClick={fetchSignal}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SignalCard 
          signal={signal} 
          onExecute={executeTrade}
        />
        
        {/* Market Conditions */}
        <div className="bg-revolution-card border border-revolution-border rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Market Conditions</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-revolution-dark rounded-lg">
              <span className="text-slate-400">Session</span>
              <span className="text-gold-400 font-medium capitalize">
                {signal?.kill_zone?.session?.replace('_', ' ')}
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-revolution-dark rounded-lg">
              <span className="text-slate-400">Volatility</span>
              <div className="flex">
                {Array.from({ length: signal?.kill_zone?.volatility || 0 }).map((_, i) => (
                  <span key={i} className="text-gold-400">⚡</span>
                ))}
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-revolution-dark rounded-lg">
              <span className="text-slate-400">Liquidity</span>
              <div className="flex">
                {Array.from({ length: signal?.kill_zone?.liquidity || 0 }).map((_, i) => (
                  <span key={i} className="text-blue-400">💧</span>
                ))}
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-revolution-dark rounded-lg">
              <span className="text-slate-400">Can Trade</span>
              <span className={signal?.kill_zone?.can_trade ? 'text-emerald-400' : 'text-rose-400'}>
                {signal?.kill_zone?.can_trade ? 'Yes' : 'No'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
