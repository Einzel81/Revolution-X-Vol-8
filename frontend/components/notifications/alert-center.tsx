"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bell,
  X,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Trash2,
  Settings,
  Filter
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useWebSocket } from "@/hooks/useWebSocket";

interface Alert {
  id: string;
  type: "price" | "signal" | "system" | "risk";
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  message: string;
  symbol?: string;
  timestamp: string;
  read: boolean;
  action?: {
    label: string;
    url: string;
  };
}

export function AlertCenter() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState<"all" | "unread" | "price" | "signal">("all");
  const { lastMessage } = useWebSocket();

  // Receive alerts from WebSocket
  React.useEffect(() => {
    if (!lastMessage) return;
    
    const data = JSON.parse(lastMessage);
    if (data.type === "alert") {
      const newAlert: Alert = {
        id: Math.random().toString(36).substring(2, 9),
        ...data.payload,
        timestamp: new Date().toISOString(),
        read: false,
      };
      
      setAlerts((prev) => [newAlert, ...prev]);
    }
  }, [lastMessage]);

  const markAsRead = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, read: true } : a))
    );
  };

  const markAllAsRead = () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, read: true })));
  };

  const deleteAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  const clearAll = () => {
    setAlerts([]);
  };

  const unreadCount = alerts.filter((a) => !a.read).length;

  const filteredAlerts = alerts.filter((alert) => {
    if (filter === "unread") return !alert.read;
    if (filter === "price") return alert.type === "price";
    if (filter === "signal") return alert.type === "signal";
    return true;
  });

  const getAlertIcon = (type: string, severity: string) => {
    const colorClass = {
      low: "text-blue-400",
      medium: "text-yellow-400",
      high: "text-orange-400",
      critical: "text-red-400",
    }[severity];

    switch (type) {
      case "price":
        return severity === "high" ? (
          <TrendingUp className={`w-5 h-5 ${colorClass}`} />
        ) : (
          <TrendingDown className={`w-5 h-5 ${colorClass}`} />
        );
      case "signal":
        return <CheckCircle className={`w-5 h-5 ${colorClass}`} />;
      case "risk":
        return <AlertTriangle className={`w-5 h-5 ${colorClass}`} />;
      default:
        return <Bell className={`w-5 h-5 ${colorClass}`} />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      case "high":
        return "bg-orange-500/20 text-orange-400 border-orange-500/30";
      case "medium":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      default:
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 bg-red-500">
              {unreadCount}
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      
      <SheetContent side="left" className="w-[400px] bg-slate-900 border-slate-700">
        <SheetHeader>
          <SheetTitle className="text-white flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              مركز التنبيهات
            </span>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={markAllAsRead}
              >
                <CheckCircle className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-red-400"
                onClick={clearAll}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </SheetTitle>
        </SheetHeader>

        <Tabs defaultValue="all" className="mt-6">
          <TabsList className="grid grid-cols-4 bg-slate-800">
            <TabsTrigger value="all" onClick={() => setFilter("all")}>
              الكل
            </TabsTrigger>
            <TabsTrigger value="unread" onClick={() => setFilter("unread")}>
              غير مقروء
            </TabsTrigger>
            <TabsTrigger value="price" onClick={() => setFilter("price")}>
              الأسعار
            </TabsTrigger>
            <TabsTrigger value="signal" onClick={() => setFilter("signal")}>
              الإشارات
            </TabsTrigger>
          </TabsList>

          <TabsContent value={filter} className="mt-4">
            <ScrollArea className="h-[calc(100vh-200px)]">
              <AnimatePresence>
                {filteredAlerts.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12 text-slate-500"
                  >
                    <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>لا توجد تنبيهات</p>
                  </motion.div>
                ) : (
                  <div className="space-y-3">
                    {filteredAlerts.map((alert) => (
                      <motion.div
                        key={alert.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, x: -100 }}
                        className={`p-4 rounded-lg border ${
                          alert.read
                            ? "bg-slate-800/50 border-slate-700"
                            : "bg-slate-800 border-slate-600"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-1">
                            {getAlertIcon(alert.type, alert.severity)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-semibold text-white text-sm">
                                {alert.title}
                              </h4>
                              <Badge
                                variant="outline"
                                className={`text-xs ${getSeverityColor(
                                  alert.severity
                                )}`}
                              >
                                {alert.severity}
                              </Badge>
                            </div>
                            <p className="text-slate-300 text-xs mb-2">
                              {alert.message}
                            </p>
                            {alert.symbol && (
                              <Badge variant="secondary" className="text-xs mb-2">
                                {alert.symbol}
                              </Badge>
                            )}
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-xs text-slate-500">
                                {new Date(alert.timestamp).toLocaleTimeString(
                                  "ar-SA"
                                )}
                              </span>
                              <div className="flex gap-1">
                                {!alert.read && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 text-xs"
                                    onClick={() => markAsRead(alert.id)}
                                  >
                                    تحديد كمقروء
                                  </Button>
                                )}
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6 text-slate-400"
                                  onClick={() => deleteAlert(alert.id)}
                                >
                                  <X className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </AnimatePresence>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
