"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
  Wallet, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Activity,
  Percent
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface Stats {
  balance: number;
  totalPnL: number;
  winRate: number;
  activeTrades: number;
  todayPnL: number;
  totalTrades: number;
}

interface StatsGridProps {
  stats: Stats | null;
  isLoading: boolean;
}

const statItems = [
  {
    key: "balance",
    label: "الرصيد الحالي",
    icon: Wallet,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    format: (val: number) => `$${val.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
  },
  {
    key: "totalPnL",
    label: "إجمالي الربح/الخسارة",
    icon: TrendingUp,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    format: (val: number) => {
      const prefix = val >= 0 ? "+" : "";
      return `${prefix}$${val.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
    },
    trend: true
  },
  {
    key: "winRate",
    label: "نسبة النجاح",
    icon: Target,
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
    format: (val: number) => `${val.toFixed(1)}%`,
    suffix: "معدل الفوز"
  },
  {
    key: "activeTrades",
    label: "الصفقات النشطة",
    icon: Activity,
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
    format: (val: number) => val.toString(),
    suffix: "صفقة"
  },
  {
    key: "todayPnL",
    label: "ربح/خسارة اليوم",
    icon: TrendingDown,
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
    format: (val: number) => {
      const prefix = val >= 0 ? "+" : "";
      return `${prefix}$${val.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
    },
    trend: true
  },
  {
    key: "totalTrades",
    label: "إجمالي الصفقات",
    icon: Percent,
    color: "text-pink-500",
    bgColor: "bg-pink-500/10",
    format: (val: number) => val.toString(),
    suffix: "صفقة"
  }
];

export function StatsGrid({ stats, isLoading }: StatsGridProps) {
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

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-32 bg-slate-800" />
        ))}
      </div>
    );
  }

  return (
    <motion.div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {statItems.map((item) => {
        const Icon = item.icon;
        const value = stats?.[item.key as keyof Stats] ?? 0;
        const isPositive = typeof value === "number" && value >= 0;
        
        return (
          <motion.div key={item.key} variants={itemVariants}>
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-xl hover:bg-slate-800/70 transition-all duration-300 group">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-slate-400 text-sm mb-1">{item.label}</p>
                    <h3 className={`text-2xl font-bold ${
                      item.trend 
                        ? (isPositive ? "text-green-400" : "text-red-400")
                        : "text-white"
                    }`}>
                      {item.format(value)}
                    </h3>
                    {item.suffix && (
                      <p className="text-xs text-slate-500 mt-1">{item.suffix}</p>
                    )}
                  </div>
                  <div className={`p-3 rounded-xl ${item.bgColor} group-hover:scale-110 transition-transform`}>
                    <Icon className={`w-6 h-6 ${item.color}`} />
                  </div>
                </div>
                
                {item.trend && (
                  <div className="mt-4 flex items-center gap-2">
                    <div className={`flex items-center text-xs ${
                      isPositive ? "text-green-400" : "text-red-400"
                    }`}>
                      {isPositive ? (
                        <TrendingUp className="w-3 h-3 mr-1" />
                      ) : (
                        <TrendingDown className="w-3 h-3 mr-1" />
                      )}
                      {isPositive ? "إيجابي" : "سلبي"}
                    </div>
                    <span className="text-xs text-slate-500">مقارنة بالأمس</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
