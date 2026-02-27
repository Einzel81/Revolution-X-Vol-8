'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  AlertTriangle, 
  Bot, 
  DollarSign, 
  BarChart3, 
  Activity,
  Bell
} from 'lucide-react';

interface NotificationPreferencesProps {
  settings: {
    newTrades: boolean;
    closedTrades: boolean;
    dailySummary: boolean;
    weeklyReport: boolean;
    riskAlerts: boolean;
    guardianUpdates: boolean;
    priceAlerts: boolean;
    systemStatus: boolean;
  };
  onToggle: (key: keyof NotificationPreferencesProps['settings']) => void;
}

export function NotificationPreferences({ settings, onToggle }: NotificationPreferencesProps) {
  const alertCategories = [
    {
      id: 'newTrades' as const,
      title: 'صفقات جديدة',
      description: 'إشعار عند فتح صفقة جديدة',
      icon: TrendingUp,
      color: 'text-green-500',
      bgColor: 'bg-green-500/20',
    },
    {
      id: 'closedTrades' as const,
      title: 'إغلاق الصفقات',
      description: 'إشعار عند إغلاق صفقة (ربح/خسارة)',
      icon: DollarSign,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/20',
    },
    {
      id: 'dailySummary' as const,
      title: 'الملخص اليومي',
      description: 'ملخص الأداء اليومي في وقت محدد',
      icon: BarChart3,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/20',
    },
    {
      id: 'weeklyReport' as const,
      title: 'التقرير الأسبوعي',
      description: 'تقرير شامل أسبوعي',
      icon: Activity,
      color: 'text-indigo-500',
      bgColor: 'bg-indigo-500/20',
    },
    {
      id: 'riskAlerts' as const,
      title: 'تنبيهات المخاطر',
      description: 'تنبيهات الانخفاض والخسائر',
      icon: AlertTriangle,
      color: 'text-red-500',
      bgColor: 'bg-red-500/20',
      recommended: true,
    },
    {
      id: 'guardianUpdates' as const,
      title: 'تحديثات AI Guardian',
      description: 'تحسينات وتعديلات الاستراتيجية',
      icon: Bot,
      color: 'text-cyan-500',
      bgColor: 'bg-cyan-500/20',
    },
    {
      id: 'priceAlerts' as const,
      title: 'تنبيهات الأسعار',
      description: 'عند الوصول لسعر مستهدف',
      icon: Bell,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/20',
    },
    {
      id: 'systemStatus' as const,
      title: 'حالة النظام',
      description: 'تنبيهات الاتصال والصيانة',
      icon: Activity,
      color: 'text-gray-500',
      bgColor: 'bg-gray-500/20',
    },
  ];

  return (
    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Bell className="w-5 h-5 text-green-500" />
          أنواع التنبيهات
        </CardTitle>
        <CardDescription>اختر التنبيهات التي تريد استلامها</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {alertCategories.map((category) => {
            const Icon = category.icon;
            return (
              <div 
                key={category.id}
                className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800/70 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 ${category.bgColor} rounded-lg`}>
                    <Icon className={`w-5 h-5 ${category.color}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <Label className="text-white font-medium cursor-pointer">
                        {category.title}
                      </Label>
                      {category.recommended && (
                        <Badge variant="outline" className="text-xs bg-blue-500/10 text-blue-500 border-blue-500/30">
                          موصى به
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-400 mt-0.5">{category.description}</p>
                  </div>
                </div>
                <Switch 
                  checked={settings[category.id]}
                  onCheckedChange={() => onToggle(category.id)}
                />
              </div>
            );
          })}
        </div>

        <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <p className="text-sm text-blue-400">
            💡 <span className="font-medium">نصيحة:</span> نوصي بتفعيل تنبيهات المخاطر على الأقل 
            لضمان متابعة سلامة حسابك.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
