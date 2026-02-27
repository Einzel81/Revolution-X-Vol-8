"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Target,
  Zap,
  BarChart3,
  Clock,
  RefreshCw,
  ChevronRight,
  Sparkles
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useWebSocket } from "@/hooks/useWebSocket";

interface AIInsight {
  id: string;
  type: "prediction" | "sentiment" | "pattern" | "recommendation";
  symbol: string;
  title: string;
  description: string;
  confidence: number;
  direction: "bullish" | "bearish" | "neutral";
  timestamp: string;
  timeframe: string;
  indicators: string[];
}

interface MarketSentiment {
  overall: "bullish" | "bearish" | "neutral";
  score: number;
  factors: {
    name: string;
    impact: number;
    trend: "up" | "down" | "stable";
  }[];
}

export function AIInsightsPanel() {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { lastMessage } = useWebSocket();

  // Fetch initial insights
  useEffect(() => {
    fetchInsights();
    const interval = setInterval(fetchInsights, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  // Handle real-time updates
  useEffect(() => {
    if (!lastMessage) return;
    
    const data = JSON.parse(lastMessage);
    if (data.type === "ai_insight") {
      setInsights((prev) => [data.payload, ...prev].slice(0, 20));
    } else if (data.type === "sentiment_update") {
      setSentiment(data.payload);
    }
  }, [lastMessage]);

  const fetchInsights = async () => {
    try {
      setIsLoading(true);
      const [insightsRes, sentimentRes] = await Promise.all([
        fetch("/api/ai/insights"),
        fetch("/api/ai/sentiment"),
      ]);
      
      const insightsData = await insightsRes.json();
      const sentimentData = await sentimentRes.json();
      
      setInsights(insightsData);
      setSentiment(sentimentData);
    } catch (error) {
      console.error("Error fetching AI insights:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case "bullish":
        return "text-green-400 bg-green-500/10 border-green-500/30";
      case "bearish":
        return "text-red-400 bg-red-500/10 border-red-500/30";
      default:
        return "text-yellow-400 bg-yellow-500/10 border-yellow-500/30";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "prediction":
        return <Target className="w-4 h-4" />;
      case "sentiment":
        return <BarChart3 className="w-4 h-4" />;
      case "pattern":
        return <Zap className="w-4 h-4" />;
      case "recommendation":
        return <Sparkles className="w-4 h-4" />;
      default:
        return <Brain className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6 text-purple-500" />
          <h2 className="text-xl font-bold text-white">تحليل الذكاء الاصطناعي</h2>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchInsights}
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          تحديث
        </Button>
      </div>

      {/* Market Sentiment Card */}
      {sentiment && (
        <Card className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border-purple-500/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm flex items-center justify-between">
              <span>المشاعر السوقية العامة</span>
              <Badge className={getDirectionColor(sentiment.overall)}>
                {sentiment.overall === "bullish" ? "صاعد" : 
                 sentiment.overall === "bearish" ? "هابط" : "محايد"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1">
                <Progress 
                  value={sentiment.score} 
                  className="h-2"
                />
              </div>
              <span className="text-lg font-bold text-white">
                {sentiment.score.toFixed(0)}%
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              {sentiment.factors.slice(0, 4).map((factor, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-slate-800/50 rounded">
                  <span className="text-xs text-slate-300">{factor.name}</span>
                  <div className="flex items-center gap-1">
                    {factor.trend === "up" && <TrendingUp className="w-3 h-3 text-green-400" />}
                    {factor.trend === "down" && <TrendingDown className="w-3 h-3 text-red-400" />}
                    <span className={`text-xs ${
                      factor.impact > 0 ? "text-green-400" : "text-red-400"
                    }`}>
                      {factor.impact > 0 ? "+" : ""}{factor.impact}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Insights List */}
      <ScrollArea className="h-[400px]">
        <div className="space-y-3">
          <AnimatePresence>
            {insights.map((insight, index) => (
              <motion.div
                key={insight.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -100 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800 transition-colors cursor-pointer group">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={`p-2 rounded-lg ${getDirectionColor(insight.direction)}`}>
                          {getTypeIcon(insight.type)}
                        </div>
                        <div>
                          <h4 className="font-semibold text-white text-sm">
                            {insight.title}
                          </h4>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {insight.symbol}
                            </Badge>
                            <span className="text-xs text-slate-500">
                              {insight.timeframe}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={`${getDirectionColor(insight.direction)} text-xs`}>
                          {insight.confidence}% ثقة
                        </Badge>
                      </div>
                    </div>
                    
                    <p className="text-slate-300 text-xs mb-3 line-clamp-2">
                      {insight.description}
                    </p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex gap-1">
                        {insight.indicators.slice(0, 3).map((indicator, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] px-2 py-0.5 bg-slate-700 rounded text-slate-300"
                          >
                            {indicator}
                          </span>
                        ))}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500">
                          <Clock className="w-3 h-3 inline mr-1" />
                          {new Date(insight.timestamp).toLocaleTimeString("ar-SA")}
                        </span>
                        <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {insights.length === 0 && !isLoading && (
            <div className="text-center py-12 text-slate-500">
              <Brain className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>لا توجد تحليلات متاحة حالياً</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-2">
        <Card className="bg-slate-800/30 border-slate-700">
          <CardContent className="p-3 text-center">
            <p className="text-2xl font-bold text-green-400">
              {insights.filter(i => i.direction === "bullish").length}
            </p>
            <p className="text-xs text-slate-400">فرص شراء</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/30 border-slate-700">
          <CardContent className="p-3 text-center">
            <p className="text-2xl font-bold text-red-400">
              {insights.filter(i => i.direction === "bearish").length}
            </p>
            <p className="text-xs text-slate-400">فرص بيع</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/30 border-slate-700">
          <CardContent className="p-3 text-center">
            <p className="text-2xl font-bold text-blue-400">
              {insights.filter(i => i.type === "pattern").length}
            </p>
            <p className="text-xs text-slate-400">أنماط</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
