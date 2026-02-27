"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Settings,
  Bell,
  Palette,
  Globe,
  Shield,
  Moon,
  Sun,
  Volume2,
  VolumeX,
  Save,
  RefreshCw
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/notifications/toast-provider";

interface UserPreferences {
  theme: "dark" | "light" | "system";
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    sound: boolean;
    tradingAlerts: boolean;
    priceAlerts: boolean;
    aiInsights: boolean;
  };
  trading: {
    defaultLotSize: number;
    maxRiskPerTrade: number;
    autoTrading: boolean;
    confirmationDialogs: boolean;
  };
  chart: {
    defaultTimeframe: string;
    showVolume: boolean;
    showOrderBlocks: boolean;
    colorScheme: string;
  };
  privacy: {
    shareAnalytics: boolean;
    publicProfile: boolean;
  };
}

export function PreferencesPanel() {
  const { success, error } = useToast();
  const [preferences, setPreferences] = useState<UserPreferences>({
    theme: "dark",
    language: "ar",
    notifications: {
      email: true,
      push: true,
      sound: true,
      tradingAlerts: true,
      priceAlerts: true,
      aiInsights: true,
    },
    trading: {
      defaultLotSize: 0.1,
      maxRiskPerTrade: 2,
      autoTrading: false,
      confirmationDialogs: true,
    },
    chart: {
      defaultTimeframe: "15",
      showVolume: true,
      showOrderBlocks: true,
      colorScheme: "default",
    },
    privacy: {
      shareAnalytics: false,
      publicProfile: false,
    },
  });
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Load preferences on mount
  useEffect(() => {
    const saved = localStorage.getItem("userPreferences");
    if (saved) {
      setPreferences(JSON.parse(saved));
    }
  }, []);

  const updatePreference = <K extends keyof UserPreferences>(
    section: K,
    key: keyof UserPreferences[K],
    value: any
  ) => {
    setPreferences((prev) => ({
      ...prev,
      [section]: {
        ...(typeof prev?.[section] === "object" && prev?.[section] !== null ? prev[section] : {}),
        [key]: value,
      },
    }));
    setHasChanges(true);
  };

  const savePreferences = async () => {
    try {
      setIsSaving(true);
      
      // Save to localStorage
      localStorage.setItem("userPreferences", JSON.stringify(preferences));
      
      // Save to API
      await fetch("/api/user/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preferences),
      });
      
      success("تم الحفظ", "تم حفظ الإعدادات بنجاح");
      setHasChanges(false);
    } catch (err) {
      error("خطأ", "فشل في حفظ الإعدادات");
    } finally {
      setIsSaving(false);
    }
  };

  const resetPreferences = () => {
    const defaultPrefs: UserPreferences = {
      theme: "dark",
      language: "ar",
      notifications: {
        email: true,
        push: true,
        sound: true,
        tradingAlerts: true,
        priceAlerts: true,
        aiInsights: true,
      },
      trading: {
        defaultLotSize: 0.1,
        maxRiskPerTrade: 2,
        autoTrading: false,
        confirmationDialogs: true,
      },
      chart: {
        defaultTimeframe: "15",
        showVolume: true,
        showOrderBlocks: true,
        colorScheme: "default",
      },
      privacy: {
        shareAnalytics: false,
        publicProfile: false,
      },
    };
    
    setPreferences(defaultPrefs);
    setHasChanges(true);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Settings className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold text-white">الإعدادات</h2>
        </div>
        {hasChanges && (
          <Badge variant="outline" className="text-yellow-400 border-yellow-400">
            تغييرات غير محفوظة
          </Badge>
        )}
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="grid grid-cols-4 bg-slate-800">
          <TabsTrigger value="general">عام</TabsTrigger>
          <TabsTrigger value="notifications">الإشعارات</TabsTrigger>
          <TabsTrigger value="trading">التداول</TabsTrigger>
          <TabsTrigger value="privacy">الخصوصية</TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="general" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Palette className="w-5 h-5" />
                المظهر واللغة
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-white">المظهر</Label>
                  <p className="text-xs text-slate-400">اختر المظهر المناسب لك</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant={preferences.theme === "light" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setPreferences(p => ({ ...p, theme: "light" }))}
                  >
                    <Sun className="w-4 h-4 mr-1" />
                    فاتح
                  </Button>
                  <Button
                    variant={preferences.theme === "dark" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setPreferences(p => ({ ...p, theme: "dark" }))}
                  >
                    <Moon className="w-4 h-4 mr-1" />
                    داكن
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-white">اللغة</Label>
                  <p className="text-xs text-slate-400">لغة واجهة المستخدم</p>
                </div>
                <Select
                  value={preferences.language}
                  onValueChange={(v) => setPreferences(p => ({ ...p, language: v }))}
                >
                  <SelectTrigger className="w-[180px] bg-slate-700 border-slate-600">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="ar">العربية</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Settings */}
        <TabsContent value="notifications" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Bell className="w-5 h-5" />
                إعدادات الإشعارات
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(preferences.notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="text-white">
                      {key === "email" && "البريد الإلكتروني"}
                      {key === "push" && "إشعارات المتصفح"}
                      {key === "sound" && "الأصوات"}
                      {key === "tradingAlerts" && "تنبيهات التداول"}
                      {key === "priceAlerts" && "تنبيهات الأسعار"}
                      {key === "aiInsights" && "رؤى الذكاء الاصطناعي"}
                    </Label>
                  </div>
                  <Switch
                    checked={value}
                    onCheckedChange={(checked) =>
                      updatePreference("notifications", key as any, checked)
                    }
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trading Settings */}
        <TabsContent value="trading" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">إعدادات التداول</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label className="text-white">حجم اللوت الافتراضي</Label>
                <Slider
                  value={[preferences.trading.defaultLotSize]}
                  onValueChange={([v]) => updatePreference("trading", "defaultLotSize", v)}
                  max={10}
                  step={0.01}
                  className="w-full"
                />
                <p className="text-sm text-slate-400">{preferences.trading.defaultLotSize} lot</p>
              </div>

              <div className="space-y-2">
                <Label className="text-white">الحد الأقصى للمخاطرة (%)</Label>
                <Slider
                  value={[preferences.trading.maxRiskPerTrade]}
                  onValueChange={([v]) => updatePreference("trading", "maxRiskPerTrade", v)}
                  max={10}
                  step={0.5}
                  className="w-full"
                />
                <p className="text-sm text-slate-400">{preferences.trading.maxRiskPerTrade}%</p>
              </div>

              <div className="flex items-center justify-between">
                <Label className="text-white">التداول الآلي</Label>
                <Switch
                  checked={preferences.trading.autoTrading}
                  onCheckedChange={(checked) =>
                    updatePreference("trading", "autoTrading", checked)
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Privacy Settings */}
        <TabsContent value="privacy" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Shield className="w-5 h-5" />
                الخصوصية والأمان
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-white">مشاركة التحليلات</Label>
                  <p className="text-xs text-slate-400">مشاركة بيانات الاستخدام لتحسين الخدمة</p>
                </div>
                <Switch
                  checked={preferences.privacy.shareAnalytics}
                  onCheckedChange={(checked) =>
                    updatePreference("privacy", "shareAnalytics", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-white">الملف الشخصي العام</Label>
                  <p className="text-xs text-slate-400">جعل إحصائياتك مرئية للآخرين</p>
                </div>
                <Switch
                  checked={preferences.privacy.publicProfile}
                  onCheckedChange={(checked) =>
                    updatePreference("privacy", "publicProfile", checked)
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 mt-6">
        <Button
          variant="outline"
          onClick={resetPreferences}
          disabled={isSaving}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          إعادة الضبط
        </Button>
        <Button
          onClick={savePreferences}
          disabled={!hasChanges || isSaving}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Save className="w-4 h-4 mr-2" />
          {isSaving ? "جاري الحفظ..." : "حفظ التغييرات"}
        </Button>
      </div>
    </motion.div>
  );
}
