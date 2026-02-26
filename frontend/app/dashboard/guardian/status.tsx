'use client';

import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  CheckCircle, 
  XCircle, 
  Loader2,
  Play,
  Square
} from 'lucide-react';

interface SystemStatus {
  component: string;
  status: 'operational' | 'degraded' | 'down';
  lastUpdate: string;
  details?: string;
}

export function GuardianStatus() {
  const [statuses, setStatuses] = useState<SystemStatus[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    // محاكاة - في الإنتاج يجب جلب من API
    setStatuses([
      {
        component: 'Performance Monitor',
        status: 'operational',
        lastUpdate: new Date().toISOString(),
        details: 'جمع البيانات كل 5 دقائق'
      },
      {
        component: 'Code Analyzer',
        status: 'operational',
        lastUpdate: new Date().toISOString(),
        details: 'GPT-4 متصل'
      },
      {
        component: 'Auto-Fixer',
        status: 'operational',
        lastUpdate: new Date().toISOString(),
        details: 'وضع: شبه تلقائي'
      },
      {
        component: 'Safe Tester',
        status: 'operational',
        lastUpdate: new Date().toISOString(),
        details: 'Sandbox جاهز'
      },
      {
        component: 'Knowledge Base',
        status: 'operational',
        lastUpdate: new Date().toISOString(),
        details: '1,245 نمط مخزن'
      }
    ]);
  };

  const toggleMonitoring = async () => {
    setLoading(true);
    try {
      const endpoint = isMonitoring ? '/api/guardian/stop-monitoring' : '/api/guardian/start-monitoring';
      await fetch(endpoint, { method: 'POST' });
      setIsMonitoring(!isMonitoring);
    } catch (error) {
      console.error('Error toggling monitoring:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'degraded':
        return <Loader2 className="w-5 h-5 text-yellow-400 animate-spin" />;
      case 'down':
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'degraded':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'down':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold">حالة المكونات</h2>
        </div>
        <button
          onClick={toggleMonitoring}
          disabled={loading}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            isMonitoring 
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
              : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
          }`}
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : isMonitoring ? (
            <>
              <Square className="w-4 h-4" />
              إيقاف المراقبة
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              بدء المراقبة
            </>
          )}
        </button>
      </div>

      <div className="space-y-3">
        {statuses.map((status, index) => (
          <div
            key={index}
            className={`flex items-center justify-between p-3 rounded-lg border ${getStatusColor(status.status)}`}
          >
            <div className="flex items-center gap-3">
              {getStatusIcon(status.status)}
              <div>
                <p className="font-medium">{status.component}</p>
                <p className="text-xs opacity-80">{status.details}</p>
              </div>
            </div>
            <span className="text-xs opacity-60">
              {new Date(status.lastUpdate).toLocaleTimeString('ar-SA')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
