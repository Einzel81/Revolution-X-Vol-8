"use client";

import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { 
  Download, 
  Filter, 
  Calendar,
  TrendingUp,
  TrendingDown,
  Search
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";

interface Trade {
  id: string;
  symbol: string;
  type: "buy" | "sell";
  entryPrice: number;
  exitPrice: number;
  volume: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  closeTime: string;
  duration: string;
  strategy: string;
  exitType: "tp" | "sl" | "manual";
}

interface TradeHistoryProps {
  trades: Trade[];
}

export function TradeHistory({ trades }: TradeHistoryProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<"all" | "buy" | "sell">("all");
  const [filterResult, setFilterResult] = useState<"all" | "win" | "loss">("all");
  const [dateRange, setDateRange] = useState("7");

  const filteredTrades = useMemo(() => {
    return trades.filter((trade) => {
      const matchesSearch = trade.symbol.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = filterType === "all" || trade.type === filterType;
      const matchesResult = filterResult === "all" || 
        (filterResult === "win" && trade.pnl > 0) || 
        (filterResult === "loss" && trade.pnl <= 0);
      
      return matchesSearch && matchesType && matchesResult;
    });
  }, [trades, searchTerm, filterType, filterResult]);

  const stats = useMemo(() => {
    const total = filteredTrades.length;
    const wins = filteredTrades.filter(t => t.pnl > 0).length;
    const losses = total - wins;
    const winRate = total > 0 ? (wins / total) * 100 : 0;
    const totalPnL = filteredTrades.reduce((sum, t) => sum + t.pnl, 0);
    const avgPnL = total > 0 ? totalPnL / total : 0;
    
    return { total, wins, losses, winRate, totalPnL, avgPnL };
  }, [filteredTrades]);

  const exportToCSV = () => {
    const headers = [
      "ID", "Symbol", "Type", "Entry Price", "Exit Price", 
      "Volume", "P&L", "P&L %", "Open Time", "Close Time", 
      "Duration", "Strategy", "Exit Type"
    ];
    
    const rows = filteredTrades.map(trade => [
      trade.id,
      trade.symbol,
      trade.type,
      trade.entryPrice,
      trade.exitPrice,
      trade.volume,
      trade.pnl,
      trade.pnlPercent,
      trade.openTime,
      trade.closeTime,
      trade.duration,
      trade.strategy,
      trade.exitType
    ]);
    
    const csvContent = [
      headers.join(","),
      ...rows.map(row => row.join(","))
    ].join("\n");
    
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `trade_history_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
  };

  const getExitTypeBadge = (type: string) => {
    switch (type) {
      case "tp":
        return <Badge className="bg-green-600">TP</Badge>;
      case "sl":
        return <Badge variant="destructive">SL</Badge>;
      default:
        return <Badge variant="outline">يدوي</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="bg-slate-700/30 border-slate-600">
          <CardContent className="p-3">
            <p className="text-xs text-slate-400">إجمالي الصفقات</p>
            <p className="text-lg font-bold text-white">{stats.total}</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-700/30 border-slate-600">
          <CardContent className="p-3">
            <p className="text-xs text-slate-400">نسبة النجاح</p>
            <p className={`text-lg font-bold ${stats.winRate >= 50 ? "text-green-400" : "text-red-400"}`}>
              {stats.winRate.toFixed(1)}%
            </p>
          </CardContent>
        </Card>
        <Card className="bg-slate-700/30 border-slate-600">
          <CardContent className="p-3">
            <p className="text-xs text-slate-400">إجمالي الربح</p>
            <p className={`text-lg font-bold ${stats.totalPnL >= 0 ? "text-green-400" : "text-red-400"}`}>
              {stats.totalPnL >= 0 ? "+" : ""}${stats.totalPnL.toFixed(2)}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-slate-700/30 border-slate-600">
          <CardContent className="p-3">
            <p className="text-xs text-slate-400">متوسط الربح</p>
            <p className={`text-lg font-bold ${stats.avgPnL >= 0 ? "text-green-400" : "text-red-400"}`}>
              {stats.avgPnL >= 0 ? "+" : ""}${stats.avgPnL.toFixed(2)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="بحث بالزوج..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-slate-700/50 border-slate-600 text-white"
          />
        </div>
        
        <Select value={filterType} onValueChange={(v: any) => setFilterType(v)}>
          <SelectTrigger className="w-[120px] bg-slate-700/50 border-slate-600 text-white">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue placeholder="النوع" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-700">
            <SelectItem value="all">الكل</SelectItem>
            <SelectItem value="buy">شراء</SelectItem>
            <SelectItem value="sell">بيع</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filterResult} onValueChange={(v: any) => setFilterResult(v)}>
          <SelectTrigger className="w-[120px] bg-slate-700/50 border-slate-600 text-white">
            <TrendingUp className="w-4 h-4 mr-2" />
            <SelectValue placeholder="النتيجة" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-700">
            <SelectItem value="all">الكل</SelectItem>
            <SelectItem value="win">ربح</SelectItem>
            <SelectItem value="loss">خسارة</SelectItem>
          </SelectContent>
        </Select>

        <Select value={dateRange} onValueChange={setDateRange}>
          <SelectTrigger className="w-[120px] bg-slate-700/50 border-slate-600 text-white">
            <Calendar className="w-4 h-4 mr-2" />
            <SelectValue placeholder="الفترة" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-700">
            <SelectItem value="7">7 أيام</SelectItem>
            <SelectItem value="30">30 يوم</SelectItem>
            <SelectItem value="90">3 أشهر</SelectItem>
            <SelectItem value="365">سنة</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          onClick={exportToCSV}
          className="border-slate-600 text-slate-300 hover:bg-slate-700"
        >
          <Download className="w-4 h-4 mr-2" />
          تصدير CSV
        </Button>
      </div>

      {/* Table */}
      <ScrollArea className="h-[300px]">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-transparent">
              <TableHead className="text-slate-400">الزوج</TableHead>
              <TableHead className="text-slate-400">النوع</TableHead>
              <TableHead className="text-slate-400">الدخول/الخروج</TableHead>
              <TableHead className="text-slate-400">الربح/الخسارة</TableHead>
              <TableHead className="text-slate-400">المدة</TableHead>
              <TableHead className="text-slate-400">الاستراتيجية</TableHead>
              <TableHead className="text-slate-400">نوع الإغلاق</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTrades.map((trade, index) => (
              <motion.tr
                key={trade.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.03 }}
                className="border-slate-700 hover:bg-slate-700/30"
              >
                <TableCell className="font-medium text-white">
                  {trade.symbol}
                </TableCell>
                <TableCell>
                  <Badge 
                    variant={trade.type === "buy" ? "default" : "destructive"}
                    className={trade.type === "buy" ? "bg-green-600" : "bg-red-600"}
                  >
                    {trade.type === "buy" ? (
                      <TrendingUp className="w-3 h-3 mr-1" />
                    ) : (
                      <TrendingDown className="w-3 h-3 mr-1" />
                    )}
                    {trade.type === "buy" ? "شراء" : "بيع"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="text-xs text-slate-400">
                    <div className="text-slate-300">{trade.entryPrice.toFixed(5)}</div>
                    <div className="text-slate-300">{trade.exitPrice.toFixed(5)}</div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className={`font-bold ${trade.pnl > 0 ? "text-green-400" : "text-red-400"}`}>
                    {trade.pnl > 0 ? "+" : ""}${trade.pnl.toFixed(2)}
                    <span className="text-xs block">
                      ({trade.pnlPercent > 0 ? "+" : ""}{trade.pnlPercent.toFixed(2)}%)
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-slate-300 text-xs">
                  {trade.duration}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs">
                    {trade.strategy}
                  </Badge>
                </TableCell>
                <TableCell>
                  {getExitTypeBadge(trade.exitType)}
                </TableCell>
              </motion.tr>
            ))}
            
            {filteredTrades.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                  لا توجد صفقات مطابقة للفلاتر المحددة
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </ScrollArea>
    </div>
  );
}
