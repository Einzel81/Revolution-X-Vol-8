'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  MessageCircle, 
  CheckCircle2, 
  Copy, 
  RefreshCw, 
  Unlink,
  QrCode,
  Bot
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

export function TelegramConnect() {
  const { toast } = useToast();
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [botToken, setBotToken] = useState('');
  const [showQrCode, setShowQrCode] = useState(false);

  const handleConnect = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      setIsConnected(true);
      toast({
        title: "تم الربط بنجاح",
        description: "تم ربط حساب Telegram بنجاح",
      });
    } catch (error) {
      toast({
        title: "خطأ",
        description: "فشل ربط الحساب",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsConnected(false);
      toast({
        title: "تم فصل الربط",
        description: "تم فصل ربط Telegram بنجاح",
      });
    } catch (error) {
      toast({
        title: "خطأ",
        description: "فشل فصل الربط",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const copyBotLink = () => {
    const botLink = 'https://t.me/RevolutionXBot';
    navigator.clipboard.writeText(botLink);
    toast({
      title: "تم النسخ",
      description: "تم نسخ رابط البوت",
    });
  };

  const copyApiKey = () => {
    const apiKey = 'RX-API-' + Math.random().toString(36).substring(7).toUpperCase();
    navigator.clipboard.writeText(apiKey);
    toast({
      title: "تم النسخ",
      description: "تم نسخ مفتاح API",
    });
  };

  return (
    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/20 rounded-xl">
              <Bot className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <CardTitle className="text-white">ربط Telegram</CardTitle>
              <CardDescription>استلم التنبيهات عبر Telegram Bot</CardDescription>
            </div>
          </div>
          {isConnected ? (
            <Badge className="bg-green-500/20 text-green-500 border-green-500/50">
              <CheckCircle2 className="w-3 h-3 ml-1" />
              متصل
            </Badge>
          ) : (
            <Badge variant="outline" className="text-gray-400">
              غير متصل
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {!isConnected ? (
          <div className="space-y-4">
            <div className="bg-gray-800/50 p-4 rounded-lg space-y-3">
              <h4 className="text-white font-medium flex items-center gap-2">
                <QrCode className="w-4 h-4" />
                طريقة الربط السريعة
              </h4>
              <ol className="space-y-2 text-sm text-gray-400 list-decimal list-inside">
                <li>افتح بوت Revolution X على Telegram</li>
                <li>أرسل الأمر <code className="bg-gray-700 px-2 py-0.5 rounded">/start</code></li>
                <li>أرسل الأمر <code className="bg-gray-700 px-2 py-0.5 rounded">/connect</code></li>
                <li>أدخل مفتاح API الخاص بك</li>
              </ol>
            </div>

            <div className="flex gap-2">
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={copyBotLink}
              >
                <Copy className="w-4 h-4 ml-2" />
                نسخ رابط البوت
              </Button>
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => setShowQrCode(!showQrCode)}
              >
                <QrCode className="w-4 h-4 ml-2" />
                {showQrCode ? 'إخفاء QR' : 'عرض QR'}
              </Button>
            </div>

            {showQrCode && (
              <div className="flex justify-center p-4 bg-white rounded-lg">
                <div className="w-48 h-48 bg-gray-200 rounded-lg flex items-center justify-center">
                  <span className="text-gray-500 text-xs">QR Code Placeholder</span>
                </div>
              </div>
            )}

            <Separator className="bg-gray-800" />

            <div className="space-y-3">
              <Label className="text-white">أو أدخل مفتاح API يدوياً</Label>
              <div className="flex gap-2">
                <Input 
                  placeholder="أدخل مفتاح API من البوت"
                  value={botToken}
                  onChange={(e) => setBotToken(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white"
                />
                <Button 
                  onClick={handleConnect}
                  disabled={isLoading || !botToken}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'ربط'}
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-green-500/10 border border-green-500/30 p-4 rounded-lg">
              <div className="flex items-center gap-3 mb-3">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
                <span className="text-white font-medium">تم الربط بنجاح</span>
              </div>
              <div className="space-y-2 text-sm text-gray-400">
                <p>معرف المحادثة: <code className="bg-gray-800 px-2 py-0.5 rounded">123456789</code></p>
                <p>اسم المستخدم: <span className="text-white">@username</span></p>
                <p>تاريخ الربط: <span className="text-white">2024-01-20</span></p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => handleTestNotification('telegram')}
              >
                إرسال تنبيه تجريبي
              </Button>
              <Button 
                variant="destructive" 
                className="flex-1"
                onClick={handleDisconnect}
                disabled={isLoading}
              >
                <Unlink className="w-4 h-4 ml-2" />
                فصل الربط
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Separator({ className }: { className?: string }) {
  return <div className={`h-px ${className}`} />;
}

function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <label className={`text-sm font-medium ${className}`}>{children}</label>;
}
