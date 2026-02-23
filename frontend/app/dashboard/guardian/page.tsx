'use client';

import React, { useEffect, useState } from 'react';
import { Shield, Activity, AlertTriangle, Clock, GitPullRequest, TrendingUp } from 'lucide-react';
import { GuardianStatus } from './status';
import { PendingChanges } from './changes';
import { ApprovalQueue } from './approvals';

interface GuardianStats {
  status: string;
  last_check: string;
  active_models: string[];
  pending_changes_count: number;
  active_alerts_count: number;
  uptime_hours: number;
}

export default function GuardianDashboard() {
  const [stats, setStats] = useState<GuardianStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // ????? ?? 30 ?????
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/guardian/status', { cache: 'no-store' });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching guardian stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'text-green-400';
      case 'maintenance':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      case 'learning':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const activeModelsCount = stats?.active_models?.length ?? 0;
  const activeModelsList = stats?.active_models?.join(', ') ?? '';
  const pendingChanges = stats?.pending_changes_count ?? 0;
  const activeAlerts = stats?.active_alerts_count ?? 0;
  const uptimeHours = Math.floor(stats?.uptime_hours ?? 0);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-8 h-8 text-blue-400" />
          <h1 className="text-3xl font-bold">AI Code Guardian</h1>
          <span className={`px-3 py-1 rounded-full text-sm font-medium bg-gray-800 ${getStatusColor(stats?.status ?? '')}`}>
            {stats?.status ?? 'Unknown'}
          </span>
        </div>
        <p className="text-gray-400">???? ?????? ?????? ??? ???? 24/7</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={<Activity className="w-6 h-6 text-green-400" />}
          title="??????? ??????"
          value={activeModelsCount}
          subtitle={activeModelsList}
        />
        <StatCard
          icon={<GitPullRequest className="w-6 h-6 text-yellow-400" />}
          title="??????? ??????"
          value={pendingChanges}
          subtitle="??????? ????????"
          alert={pendingChanges > 0}
        />
        <StatCard
          icon={<AlertTriangle className="w-6 h-6 text-red-400" />}
          title="??????? ????"
          value={activeAlerts}
          subtitle="????? ????????"
          alert={activeAlerts > 0}
        />
        <StatCard
          icon={<Clock className="w-6 h-6 text-blue-400" />}
          title="??? ???????"
          value={`${uptimeHours}h`}
          subtitle="??? ??? ????? ?????"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <GuardianStatus />
          <PendingChanges />
        </div>

        <div className="space-y-6">
          <ApprovalQueue />
          <PerformanceTrends />
        </div>
      </div>

      {/* Last Check */}
      <div className="mt-8 text-center text-gray-500 text-sm">
        ??? ???:{' '}
        {stats?.last_check ? new Date(stats.last_check).toLocaleString('ar-SA') : '-'}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  title,
  value,
  subtitle,
  alert = false,
}: {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  subtitle: string;
  alert?: boolean;
}) {
  return (
    <div className={`bg-gray-800 rounded-lg p-6 border ${alert ? 'border-red-500/50' : 'border-gray-700'}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm mb-1">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-gray-500 text-xs mt-1">{subtitle}</p>
        </div>
        <div className="p-3 bg-gray-700/50 rounded-lg">{icon}</div>
      </div>
    </div>
  );
}

type GuardianTrends = {
  early_warning?: boolean;
  trend?: 'improving' | 'declining' | string;
  current_win_rate?: number;
  win_rate_change?: number;
};

function PerformanceTrends() {
  const [trends, setTrends] = useState<GuardianTrends | null>(null);

  useEffect(() => {
    fetch('/api/v1/guardian/trends', { cache: 'no-store' })
      .then((res) => res.json())
      .then((data) => setTrends(data))
      .catch((err) => console.error('Error fetching trends:', err));
  }, []);

  const trendLabel = trends?.trend === 'improving' ? '????? ??' : '????? ??';
  const winRate = ((trends?.current_win_rate ?? 0) * 100).toFixed(1);
  const winRateChange = ((trends?.win_rate_change ?? 0) * 100).toFixed(2);

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-blue-400" />
        <h2 className="text-lg font-semibold">??????? ??????</h2>
      </div>

      {trends?.early_warning && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-2 text-red-400">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">????? ????!</span>
          </div>
          <p className="text-red-300 text-sm mt-1">
            ?? ?????? ????? ?? ??????. ????? ??????? ????????????.
          </p>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-gray-400">??????? ?????</span>
          <span className={`font-medium ${trends?.trend === 'improving' ? 'text-green-400' : 'text-yellow-400'}`}>
            {trendLabel}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-400">???? ????? ??????</span>
          <span className="font-medium text-green-400">{winRate}%</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-400">???????</span>
          <span className={`font-medium ${(trends?.win_rate_change ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {winRateChange}%
          </span>
        </div>
      </div>
    </div>
  );
}