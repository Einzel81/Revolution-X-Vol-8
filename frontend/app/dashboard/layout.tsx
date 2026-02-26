"use client";

import React, { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Menu,
  Home,
  BarChart3,
  Target,
  Settings,
  User,
  TrendingUp,
  Shield,
  Zap,
  Activity,
  Languages,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { AlertCenter } from "@/components/notifications/alert-center";
import { ToastProvider } from "@/components/notifications/toast-provider";
import { useLanguage } from "@/components/i18n/LanguageProvider";

type NavItem = {
  icon: any;
  labelKey: string;
  href: string;
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  const { lang, dir, cycleLang, t } = useLanguage();

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Sidebar (Main)
  const sidebarItems: NavItem[] = useMemo(
    () => [
      { icon: Home, labelKey: "nav.overview", href: "/dashboard" },
      { icon: BarChart3, labelKey: "nav.charts", href: "/dashboard/charts" },
      { icon: Target, labelKey: "nav.scanner", href: "/dashboard/scanner" },
      { icon: TrendingUp, labelKey: "nav.positions", href: "/dashboard/positions" },
      // ? NEW: Execution Health (System #8)
      { icon: Activity, labelKey: "nav.execution", href: "/dashboard/execution" },

      { icon: Shield, labelKey: "nav.dxy", href: "/dashboard/dxy" },
      { icon: Zap, labelKey: "nav.ai", href: "/dashboard/ai" },
      { icon: Settings, labelKey: "nav.settings", href: "/dashboard/settings" },
    ],
    []
  );

  // Bottom nav (Mobile)
  const bottomNavItems: NavItem[] = useMemo(
    () => [
      { icon: Home, labelKey: "nav.overview", href: "/dashboard" },
      { icon: BarChart3, labelKey: "nav.charts", href: "/dashboard/charts" },
      { icon: Target, labelKey: "nav.scanner", href: "/dashboard/scanner" },
      // optional: execution instead of profile (choose what you prefer)
      { icon: Activity, labelKey: "nav.execution", href: "/dashboard/execution" },
    ],
    []
  );

  const currentTitle = useMemo(() => {
    const hit = sidebarItems.find((x) => x.href === pathname);
    return hit ? t(hit.labelKey) : t("dashboard.title");
  }, [pathname, sidebarItems, t]);

  const isRtl = dir === "rtl";
  const desktopSidebarWidth = "w-64";

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-6 border-b border-slate-700">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Revolution X</h1>
            <p className="text-xs text-slate-400">{t("app.tagline")}</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {sidebarItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{t(item.labelKey)}</span>
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className={`${isRtl ? "ml-auto" : "mr-auto"} w-1.5 h-1.5 rounded-full bg-white`}
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Profile Summary */}
      <div className="p-4 border-t border-slate-700">
        <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
          <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-slate-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">{t("user.label")}</p>
            <p className="text-xs text-slate-400">{t("user.status")}</p>
          </div>
          <div className="w-2 h-2 rounded-full bg-green-500" />
        </div>
      </div>
    </div>
  );

  return (
    <ToastProvider>
      <div className="min-h-screen bg-slate-900">
        {/* Desktop Sidebar */}
        {!isMobile && (
          <aside
            className={`fixed top-0 h-full ${desktopSidebarWidth} bg-slate-900 border-slate-800 z-40 ${
              isRtl ? "right-0 border-l" : "left-0 border-r"
            }`}
          >
            <SidebarContent />
          </aside>
        )}

        {/* Mobile Header */}
        {isMobile && (
          <header className="fixed top-0 left-0 right-0 h-16 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800 z-40 flex items-center justify-between px-4">
            <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Menu className="w-6 h-6 text-white" />
                </Button>
              </SheetTrigger>

              <SheetContent
                side={isRtl ? "right" : "left"}
                className="w-64 bg-slate-900 border-slate-800 p-0"
              >
                <SidebarContent />
              </SheetContent>
            </Sheet>

            <div className="flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-blue-500" />
              <span className="font-bold text-white">Revolution X</span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={cycleLang}
                title={t("lang")}
              >
                <Languages className="w-5 h-5 text-slate-300" />
              </Button>
              <AlertCenter />
            </div>
          </header>
        )}

        {/* Desktop Header */}
        {!isMobile && (
          <header
            className={`fixed top-0 h-16 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800 z-30 flex items-center justify-between px-6 ${
              isRtl ? "left-0 right-64" : "left-64 right-0"
            }`}
          >
            <div>
              <h2 className="text-lg font-semibold text-white">{currentTitle}</h2>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={cycleLang}
                title={t("lang")}
              >
                <Languages className="w-5 h-5 text-slate-300" />
              </Button>

              <AlertCenter />

              <Button variant="ghost" size="icon" title={t("nav.settings")}>
                <Settings className="w-5 h-5 text-slate-400" />
              </Button>
            </div>
          </header>
        )}

        {/* Main Content */}
        <main
          className={`${
            isMobile
              ? "pt-20 pb-24 px-4"
              : isRtl
              ? "pr-64 pt-20 px-6"
              : "pl-64 pt-20 px-6"
          } min-h-screen`}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Mobile Bottom Navigation */}
        {isMobile && (
          <nav className="fixed bottom-0 left-0 right-0 h-16 bg-slate-900/95 backdrop-blur-xl border-t border-slate-800 z-40">
            <div className="grid grid-cols-4 h-full">
              {bottomNavItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`relative flex flex-col items-center justify-center gap-1 transition-colors ${
                      isActive ? "text-blue-500" : "text-slate-400"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-[10px]">{t(item.labelKey)}</span>
                    {isActive && (
                      <motion.div
                        layoutId="mobileIndicator"
                        className="absolute bottom-1 w-1 h-1 rounded-full bg-blue-500"
                      />
                    )}
                  </Link>
                );
              })}
            </div>
          </nav>
        )}
      </div>
    </ToastProvider>
  );
}