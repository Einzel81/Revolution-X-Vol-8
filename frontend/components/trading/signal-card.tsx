// frontend/components/trading/signal-card.tsx
'use client';

import { ArrowUp, ArrowDown, Minus, AlertTriangle, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SignalCardProps {
  signal: {
    action: string;
    confidence: number;
    score: number;
    reasons: string[];
    entry_price: number;
    suggested_sl: number;
    suggested_tp: number;
  };
  onExecute?: () => void;
}

export default function SignalCard({ signal, onExecute }: SignalCardProps) {
  const getSignalConfig = (action: string) => {
    const configs: Record<string, any> = {
      'STRONG_BUY': {
        icon: ArrowUp,
        color: 'text-emerald-400',
        bgColor: 'bg-emerald-500/20',
        borderColor: 'border-emerald-500/30',
        label: 'Strong Buy',
      },
      'BUY': {
        icon: ArrowUp,
        color: 'text-emerald-400',
        bgColor: 'bg-emerald-500/20',
        borderColor: 'border-emerald-500/30',
        label: 'Buy',
      },
      'STRONG_SELL': {
        icon: ArrowDown,
        color: 'text-rose-400',
        bgColor: 'bg-rose-500/20',
        borderColor: 'border-rose-500/30',
        label: 'Strong Sell',
      },
      'SELL': {
        icon: ArrowDown,
        color: 'text-rose-400',
        bgColor: 'bg-rose-500/20',
        borderColor: 'border-rose-500/30',
        label: 'Sell',
      },
      'NEUTRAL': {
        icon: Minus,
        color: 'text-slate-400',
        bgColor: 'bg-slate-500/20',
        borderColor: 'border-slate-500/30',
        label: 'Neutral',
      },
    };
    
    return configs[action] || configs['NEUTRAL'];
  };

  const config = getSignalConfig(signal.action);
  const Icon = config.icon;

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return 'bg-emerald-500';
    if (confidence >= 50) return 'bg-gold-500';
    return 'bg-slate-500';
  };

  return (
    <div className={cn(
      'bg-revolution-card border-2 rounded-xl p-6',
      config.borderColor
    )}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={cn(
            'w-12 h-12 rounded-xl flex items-center justify-center',
            config.bgColor
          )}>
            <Icon className={cn('w-6 h-6', config.color)} />
          </div>
          <div>
            <h3 className={cn('text-2xl font-bold', config.color)}>
              {config.label}
            </h3>
            <p className="text-slate-400 text-sm">
              Confidence: {signal.confidence}%
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-3xl font-bold text-white">
            ${signal.entry_price?.toFixed(2) || '--'}
          </div>
          <div className="text-slate-400 text-sm">XAU/USD</div>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-slate-400">Signal Strength</span>
          <span className="text-white font-medium">{signal.confidence}%</span>
        </div>
        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all duration-500', getConfidenceColor(signal.confidence))}
            style={{ width: `${signal.confidence}%` }}
          />
        </div>
      </div>

      {/* Price Levels */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-revolution-dark rounded-lg p-3 text-center">
          <div className="text-slate-400 text-xs mb-1">Entry</div>
          <div className="text-white font-bold">${signal.entry_price?.toFixed(2)}</div>
        </div>
        <div className="bg-rose-500/10 rounded-lg p-3 text-center border border-rose-500/20">
          <div className="text-rose-400 text-xs mb-1">Stop Loss</div>
          <div className="text-white font-bold">${signal.suggested_sl?.toFixed(2)}</div>
        </div>
        <div className="bg-emerald-500/10 rounded-lg p-3 text-center border border-emerald-500/20">
          <div className="text-emerald-400 text-xs mb-1">Take Profit</div>
          <div className="text-white font-bold">${signal.suggested_tp?.toFixed(2)}</div>
        </div>
      </div>

      {/* Reasons */}
      <div className="space-y-2 mb-4">
        <p className="text-slate-400 text-sm">Analysis:</p>
        {signal.reasons?.map((reason, idx) => (
          <div key={idx} className="flex items-center space-x-2 text-sm text-slate-300">
            <TrendingUp className="w-4 h-4 text-gold-400" />
            <span>{reason}</span>
          </div>
        ))}
      </div>

      {/* Execute Button */}
      {signal.action !== 'NEUTRAL' && (
        <button
          onClick={onExecute}
          className={cn(
            'w-full py-3 rounded-lg font-semibold transition-all',
            signal.action.includes('BUY')
              ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
              : 'bg-rose-500 hover:bg-rose-600 text-white'
          )}
        >
          Execute {signal.action.includes('BUY') ? 'Long' : 'Short'} Position
        </button>
      )}
    </div>
  );
}
