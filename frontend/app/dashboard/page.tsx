"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  Target, 
  Clock,
  Plus,
  RefreshCw,
  AlertCircle
} from "lucide-react";
import { StatsGrid } from "@/components/dashboard/stats-grid";
import { TradingChart } from "@/components/charts/trading-chart";
import { PositionsTable } from "@/components/positions/positions-table";
import { TradeHistory } from "@/components/history/trade-history";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useTradingData } from "@/hooks/useTradingData";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface DashboardStats {
  balance: number;
  totalPnL: number;
  winRate: number;
  activeTrades: number;
  todayPnL: number;
  totalTrades: number;
}

interface Activity {
  id: string;
  type: "trade_opened" | "trade_closed" | "alert" | "system";
  message: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export default function DashboardPage() {
  const { isConnected, lastMessage } = useWebSocket();
  const { stats, positions, history, isLoading } = useTradingData();
  const [activities, setActivities] = useState<Activity[]>([]);

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage);
      if (data.type === "activity") {
        setActivities(prev => [data.payload, ...prev].slice(0, 50));
      }
    }
  }, [lastMessage]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 100
      }
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "trade_opened":
        return <Plus className="w-4 h-4 text-green-500" />;
      case "trade_closed":
        return <DollarSign className="w-4 h-4 text-blue-500" />;
      case "alert":
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <motion.div
      className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">
              لوحة التحكم الرئيسية
            </h1>
            <p className="text-slate-400">
              نظرة شاملة على أداء حسابك والفرص المتاحة
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Badge 
              variant={isConnected ? "default" : "destructive"}
              className="px-4 py-2"
            >
              {isConnected ? "🟢 متصل بالخادم" : "🔴 غير متصل"}
            </Badge>
            <Button variant="outline" size="icon">
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div variants={itemVariants}>
        <StatsGrid stats={stats} isLoading={isLoading} />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        {/* Chart Section */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-500" />
                الرسم البياني المتقدم
              </CardTitle>
              <div className="flex gap-2">
                <Badge variant="outline" className="text-xs">
                  EUR/USD
                </Badge>
                <Badge variant="outline" className="text-xs">
                  M15
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <TradingChart symbol="EURUSD" timeframe="15" />
            </CardContent>
          </Card>
        </motion.div>

        {/* Activity Feed */}
        <motion.div variants={itemVariants}>
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-xl h-full">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Clock className="w-5 h-5 text-purple-500" />
                النشاط الأخير
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-4">
                  {activities.map((activity) => (
                    <motion.div
                      key={activity.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-start gap-3 p-3 rounded-lg bg-slate-700/30 border border-slate-600/30"
                    >
                      <div className="mt-1">
                        {getActivityIcon(activity.type)}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-slate-200">
                          {activity.message}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">
                          {new Date(activity.timestamp).toLocaleTimeString("ar-SA")}
                        </p>
                      </div>
                    </motion.div>
                  ))}
                  {activities.length === 0 && (
                    <div className="text-center text-slate-500 py-8">
                      لا يوجد نشاط حديث
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Positions & History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <motion.div variants={itemVariants}>
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-xl">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-green-500" />
                المراكز المفتوحة
              </CardTitle>
            </CardHeader>
            <CardContent>
              <PositionsTable positions={positions} />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-xl">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-orange-500" />
                سجل التداول
              </CardTitle>
            </CardHeader>
            <CardContent>
              <TradeHistory trades={history} />
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div variants={itemVariants} className="mt-8">
        <Card className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-blue-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white mb-2">
                  إجراءات سريعة
                </h3>
                <p className="text-slate-300">
                  الوصول السريع إلى أهم الأدوات والميزات
                </p>
              </div>
              <div className="flex gap-3">
                <Button className="bg-green-600 hover:bg-green-700">
                  <Plus className="w-4 h-4 ml-2" />
                  صفقة جديدة
                </Button>
                <Button variant="outline">
                  <Target className="w-4 h-4 ml-2" />
                  الفرص المتاحة
                </Button>
                <Button variant="outline">
                  <Activity className="w-4 h-4 ml-2" />
                  التحليل الفني
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
