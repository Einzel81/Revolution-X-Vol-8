'use client';

import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  MessageCircle, 
  Mail, 
  Smartphone, 
  Volume2, 
  VolumeX,
  Clock,
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Save
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { TelegramConnect } from '@/components/notifications/telegram-connect';
import { NotificationPreferences } from '@/components/notifications/notification-preferences';
import { useToast } from '@/components/ui/use-toast';

interface NotificationSettings {
  channels: {
    telegram: boolean;
    email: boolean;
    push: boolean;
    inApp: boolean;
  };
  alerts: {
    newTrades: boolean;
    closedTrades: boolean;
    dailySummary: boolean;
    weeklyReport: boolean;
    riskAlerts: boolean;
    guardianUpdates: boolean;
    priceAlerts: boolean;
    systemStatus: boolean;
  };
  quietHours: {
    enabled: boolean;
    start: string;
    end: string;
  };
  riskThresholds: {
    drawdown: number;
    consecutiveLosses: number;
    dailyLoss: number;
  };
}

export default function NotificationsPage() {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState<NotificationSettings>({
    channels: {
      telegram: true,
      email: false,
      push: true,
      inApp: true,
    },
    alerts: {
      newTrades: true,
      closedTrades: true,
      dailySummary: true,
      weeklyReport: true,
      riskAlerts: true,
      guardianUpdates: true,
      priceAlerts: false,
      systemStatus: true,
    },
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00',
    },
    riskThresholds: {
      drawdown: 10,
      consecutiveLosses: 3,
      dailyLoss: 5,
    },
  });

  const handleChannelToggle = (channel: keyof typeof settings.channels) => {
    setSettings(prev => ({
      ...prev,
      channels: {
        ...prev.channels,
        [channel]: !prev.channels[channel],
      },
    }));
  };

  const handleAlertToggle = (alert: keyof typeof settings.alerts) => {
    setSettings(prev => ({
      ...prev,
      alerts: {
        ...prev.alerts,
        [alert]: !prev.alerts[alert],
      },
    }));
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      // API call to save settings
      await fetch('/api/v1/notifications/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      
      toast({
        title: "تم الحفظ بنجاح",
        description: "تم تحديث إعدادات التنبيهات",
      });
    } catch (error) {
      toast({
        title: "خطأ",
        description: "فشل حفظ الإعدادات",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestNotification = async (channel: string) => {
    try {
      await fetch('/api/v1/notifications/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel }),
      });
      
      toast({
        title: "تم الإرسال",
        description: `تم إرسال تنبيه تجريبي عبر ${channel}`,
      });
    } catch (error) {
      toast({
        title: "خطأ",
        description: "فشل إرسال التنبيه التجريبي",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6" dir="rtl">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">إعدادات التنبيهات</h1>
          <p className="text-gray-400">إدارة قنوات الإشعارات والتنبيهات</p>
        </div>
        <Button 
          onClick={handleSave} 
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Save className="w-4 h-4 ml-2" />
          {isLoading ? 'جاري الحفظ...' : 'حفظ الإعدادات'}
        </Button>
      </div>

      {/* Telegram Connection */}
      <TelegramConnect />

      {/* Notification Channels */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-blue-500" />
            قنوات الإشعارات
          </CardTitle>
          <CardDescription>اختر كيفية استلام التنبيهات</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Telegram */}
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <MessageCircle className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <Label className="text-white font-medium">Telegram</Label>
                  <p className="text-sm text-gray-400">تنبيهات فورية عبر البوت</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleTestNotification('telegram')}
                >
                  اختبار
                </Button>
                <Switch 
                  checked={settings.channels.telegram}
                  onCheckedChange={() => handleChannelToggle('telegram')}
                />
              </div>
            </div>

            {/* Email */}
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Mail className="w-5 h-5 text-purple-500" />
                </div>
                <div>
                  <Label className="text-white font-medium">البريد الإلكتروني</Label>
                  <p className="text-sm text-gray-400">تقارير يومية وأسبوعية</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleTestNotification('email')}
                >
                  اختبار
                </Button>
                <Switch 
                  checked={settings.channels.email}
                  onCheckedChange={() => handleChannelToggle('email')}
                />
              </div>
            </div>

            {/* Push Notifications */}
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-500/20 rounded-lg">
                  <Bell className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <Label className="text-white font-medium">إشعارات المتصفح</Label>
                  <p className="text-sm text-gray-400">Push notifications</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleTestNotification('push')}
                >
                  اختبار
                </Button>
                <Switch 
                  checked={settings.channels.push}
                  onCheckedChange={() => handleChannelToggle('push')}
                />
              </div>
            </div>

            {/* In-App */}
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-500/20 rounded-lg">
                  <Smartphone className="w-5 h-5 text-orange-500" />
                </div>
                <div>
                  <Label className="text-white font-medium">داخل التطبيق</Label>
                  <p className="text-sm text-gray-400">إشعارات داخل اللوحة</p>
                </div>
              </div>
              <Switch 
                checked={settings.channels.inApp}
                onCheckedChange={() => handleChannelToggle('inApp')}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alert Types */}
      <NotificationPreferences 
        settings={settings.alerts}
        onToggle={handleAlertToggle}
      />

      {/* Quiet Hours */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-500" />
            ساعات الصمت
          </CardTitle>
          <CardDescription>تعطيل الإشعارات في أوقات محددة</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {settings.quietHours.enabled ? (
                <VolumeX className="w-5 h-5 text-red-500" />
              ) : (
                <Volume2 className="w-5 h-5 text-green-500" />
              )}
              <span className="text-white">تفعيل ساعات الصمت</span>
            </div>
            <Switch 
              checked={settings.quietHours.enabled}
              onCheckedChange={(checked) => 
                setSettings(prev => ({
                  ...prev,
                  quietHours: { ...prev.quietHours, enabled: checked }
                }))
              }
            />
          </div>
          
          {settings.quietHours.enabled && (
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="space-y-2">
                <Label className="text-gray-400">من</Label>
                <input
                  type="time"
                  value={settings.quietHours.start}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    quietHours: { ...prev.quietHours, start: e.target.value }
                  }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-gray-400">إلى</Label>
                <input
                  type="time"
                  value={settings.quietHours.end}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    quietHours: { ...prev.quietHours, end: e.target.value }
                  }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Risk Thresholds */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-red-500" />
            عتبات المخاطرة
          </CardTitle>
          <CardDescription>تخصيص مستويات تنبيهات المخاطر</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <Label className="text-white">نسبة الانخفاض (Drawdown)</Label>
                <Badge variant="outline">{settings.riskThresholds.drawdown}%</Badge>
              </div>
              <Slider
                value={[settings.riskThresholds.drawdown]}
                onValueChange={(value) => setSettings(prev => ({
                  ...prev,
                  riskThresholds: { ...prev.riskThresholds, drawdown: value[0] }
                }))}
                max={50}
                min={5}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                إرسال تنبيه عندما يصل الانخفاض إلى هذه النسبة
              </p>
            </div>

            <Separator className="bg-gray-800" />

            <div>
              <div className="flex justify-between mb-2">
                <Label className="text-white">الخسائر المتتالية</Label>
                <Badge variant="outline">{settings.riskThresholds.consecutiveLosses} صفقات</Badge>
              </div>
              <Slider
                value={[settings.riskThresholds.consecutiveLosses]}
                onValueChange={(value) => setSettings(prev => ({
                  ...prev,
                  riskThresholds: { ...prev.riskThresholds, consecutiveLosses: value[0] }
                }))}
                max={10}
                min={2}
                step={1}
                className="w-full"
              />
            </div>

            <Separator className="bg-gray-800" />

            <div>
              <div className="flex justify-between mb-2">
                <Label className="text-white">حد الخسارة اليومي</Label>
                <Badge variant="outline">{settings.riskThresholds.dailyLoss}%</Badge>
              </div>
              <Slider
                value={[settings.riskThresholds.dailyLoss]}
                onValueChange={(value) => setSettings(prev => ({
                  ...prev,
                  riskThresholds: { ...prev.riskThresholds, dailyLoss: value[0] }
                }))}
                max={20}
                min={1}
                step={0.5}
                className="w-full"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
