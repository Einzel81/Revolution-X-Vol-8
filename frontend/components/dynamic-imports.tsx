/**
 * Dynamic imports for code splitting and lazy loading
 */
import React from "react";
import dynamic from 'next/dynamic';
import { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import('./charts/RiskMetricsChart')
import('./charts/RiskMetricsChart')
import('./charts/RiskMetricsChart')

// Loading fallback components
const ChartSkeleton = () => (
  <div className="w-full h-[400px] flex items-center justify-center">
    <Skeleton className="w-full h-full" />
  </div>
);

const TableSkeleton = () => (
  <div className="space-y-2">
    <Skeleton className="h-8 w-full" />
    <Skeleton className="h-8 w-full" />
    <Skeleton className="h-8 w-full" />
  </div>
);

// Heavy visualization components
export const DynamicTradingView = dynamic(
  () => import('./charts/TradingViewChart'),
  {
    ssr: false,
    loading: () => <ChartSkeleton />,
  }
);

export const DynamicPerformanceChart = dynamic(
  () => import('./charts/PerformanceChart'),
  {
    ssr: false,
    loading: () => <ChartSkeleton />,
  }
);

export const DynamicRiskChart = dynamic(
  () => import('./charts/RiskMetricsChart'),
  {
    ssr: false,
    loading: () => <ChartSkeleton />,
  }
);

export const DynamicVolumeProfile = dynamic(
  () => import('./charts/VolumeProfile'),
  {
    ssr: false,
    loading: () => <ChartSkeleton />,
  }
);

// AI Components
export const DynamicAIPredictions = dynamic(
  () => import('./ai/PredictionPanel'),
  {
    ssr: false,
    loading: () => <div className="p-4"><Skeleton className="h-32 w-full" /></div>,
  }
);

export const DynamicModelPerformance = dynamic(
  () => import('./ai/ModelPerformance'),
  {
    ssr: false,
    loading: () => <TableSkeleton />,
  }
);

// Trading Components
export const DynamicOrderPanel = dynamic(
  () => import('./trading/OrderPanel'),
  {
    loading: () => <div className="p-4 space-y-4"><Skeleton className="h-12 w-full" /><Skeleton className="h-12 w-full" /></div>,
  }
);

export const DynamicPositionTable = dynamic(
  () => import('./trading/PositionTable'),
  {
    loading: () => <TableSkeleton />,
  }
);

export const DynamicMarketDepth = dynamic(
  () => import('./trading/MarketDepth'),
  {
    ssr: false,
    loading: () => <div className="h-64"><Skeleton className="h-full w-full" /></div>,
  }
);

// Dashboard Components
export const DynamicStatsCards = dynamic(
  () => import('./dashboard/StatsCards'),
  {
    loading: () => <div className="grid grid-cols-4 gap-4"><Skeleton className="h-24" /><Skeleton className="h-24" /><Skeleton className="h-24" /><Skeleton className="h-24" /></div>,
  }
);

export const DynamicRecentActivity = dynamic(
  () => import('./dashboard/RecentActivity'),
  {
    loading: () => <div className="space-y-2"><Skeleton className="h-16 w-full" /><Skeleton className="h-16 w-full" /></div>,
  }
);

// 3D Components (heaviest)
export const DynamicMarketGlobe = dynamic(
  () => import('./visualization/MarketGlobe'),
  {
    ssr: false,
    loading: () => <div className="h-[500px] flex items-center justify-center">Loading 3D Visualization...</div>,
  }
);

// Admin Components (rarely used)
export const DynamicUserManagement = dynamic(
  () => import('./admin/UserManagement'),
  {
    loading: () => <TableSkeleton />,
  }
);

export const DynamicSystemLogs = dynamic(
  () => import('./admin/SystemLogs'),
  {
    ssr: false,
    loading: () => <div className="h-96 bg-gray-900 rounded"><Skeleton className="h-full w-full" /></div>,
  }
);

// Wrap with Suspense boundary
export function withSuspense<P extends object>(
  Component: React.ComponentType<P>,
  fallback: React.ReactNode
) {
  return function SuspenseWrapper(props: P) {
    return (
      <Suspense fallback={fallback}>
        <Component {...props} />
      </Suspense>
    );
  };
}

// Preload function for critical components
export function preloadTradingComponents() {
  const DynamicTradingViewPreload = dynamic(
    () => import('./charts/TradingViewChart'),
    { ssr: false }
  );
  
  // Trigger preload
  DynamicTradingViewPreload;
}

// Intersection Observer based lazy loading hook
export function useLazyLoad<T extends HTMLElement>() {
  const ref = React.useRef<T>(null);
  return { ref, isVisible: true };
}