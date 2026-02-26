'use client';

import Link from 'next/link';
import { TrendingUp, Bell, User } from 'lucide-react';
import { authService } from '@/lib/auth';
import { useLanguage } from '@/components/i18n/LanguageProvider';

export default function Navbar() {
  const user = authService.getUser();
  const { lang, cycleLang, t } = useLanguage();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-revolution-card/80 backdrop-blur border-b border-revolution-border">
      <div className="flex items-center justify-between h-16 px-6">
        <Link href="/dashboard" className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-br from-gold-400 to-gold-600 rounded-lg flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-gold-400 to-gold-200 bg-clip-text text-transparent">
            Revolution X
          </span>
        </Link>

        <div className="flex items-center space-x-4">
          <button
            onClick={cycleLang}
            className="px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 text-xs"
            title={t('lang')}
          >
            {lang.toUpperCase()}
          </button>

          <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-gold-500 rounded-full"></span>
          </button>

          <div className="flex items-center space-x-3 pl-4 border-l border-revolution-border">
            <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-slate-400" />
            </div>
            <div className="hidden md:block">
              <p className="text-sm font-medium text-white">{user?.full_name}</p>
              <p className="text-xs text-slate-400 capitalize">{user?.role}</p>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}