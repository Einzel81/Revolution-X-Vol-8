"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CandlestickChart,
  Radar,
  Briefcase,
  Activity,
  Settings,
  Shield,
  Cpu,
  Wifi,
} from "lucide-react";

import Navbar from "@/components/layout/Navbar";
import { AlertCenter } from "@/components/notifications/alert-center";
import { ToastProvider } from "@/components/notifications/toast-provider";
import { useLanguage } from "@/components/i18n/LanguageProvider";

type NavItem = {
  icon: any;
  labelKey: string;
  href: string;
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { dir, t } = useLanguage();

  const sidebarItems: NavItem[] = [
    { icon: LayoutDashboard, labelKey: "nav.overview", href: "/dashboard" },
    { icon: CandlestickChart, labelKey: "nav.charts", href: "/dashboard/charts" },
    { icon: Radar, labelKey: "nav.scanner", href: "/dashboard/scanner" },
    { icon: Briefcase, labelKey: "nav.positions", href: "/dashboard/positions" },
    { icon: Activity, labelKey: "nav.execution", href: "/dashboard/execution" },

    // NEW: Per-user MT5 Connections
    { icon: Wifi, labelKey: "nav.mt5", href: "/dashboard/mt5" },

    { icon: Shield, labelKey: "nav.dxy", href: "/dashboard/dxy-guardian" },
    { icon: Cpu, labelKey: "nav.ai", href: "/dashboard/ai" },
    { icon: Settings, labelKey: "nav.settings", href: "/dashboard/settings" },
  ];

  return (
    <ToastProvider>
      <div className="min-h-screen bg-revolution-dark" dir={dir}>
        <Navbar />

        <div className="pt-16 flex">
          {/* Sidebar */}
          <aside className="w-64 min-h-[calc(100vh-64px)] border-r border-revolution-border bg-revolution-card/20">
            <div className="p-4">
              <nav className="space-y-1">
                {sidebarItems.map((item) => {
                  const active = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={[
                        "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                        active
                          ? "bg-slate-800 text-white border border-slate-700"
                          : "text-slate-300 hover:bg-slate-800/60 hover:text-white",
                      ].join(" ")}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{t(item.labelKey)}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>
          </aside>

          {/* Content */}
          <main className="flex-1">
            <AlertCenter />
            {children}
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}