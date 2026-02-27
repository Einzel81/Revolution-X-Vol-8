// frontend/components/layout/Sidebar.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  BarChart3,
  Activity,
  Shield,
  Settings,
  Users,
  Newspaper,
  LogOut,
} from "lucide-react";
import { authService } from "@/lib/auth";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/trading", label: "Trading", icon: TrendingUp },
  { href: "/dashboard/positions", label: "Positions", icon: BarChart3 },
  { href: "/dashboard/scanner", label: "Scanner", icon: Activity },

  // ? NEW: Predictive Analytics
  { href: "/dashboard/predictive", label: "Predictive", icon: BarChart3 },

  { href: "/dashboard/guardian", label: "AI Guardian", icon: Shield },
  { href: "/dashboard/dxy", label: "DXY Guardian", icon: Activity },
  { href: "/dashboard/news", label: "News", icon: Newspaper },
];

const adminItems = [
  { href: "/dashboard/admin/users", label: "Users", icon: Users },
  { href: "/dashboard/admin/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const user = authService.getUser();
  const isAdmin = user?.role === "admin" || user?.role === "manager";

  const handleLogout = () => {
    authService.logout();
    window.location.href = "/login";
  };

  return (
    <aside className="fixed left-0 top-16 w-64 h-[calc(100vh-4rem)] bg-revolution-card border-r border-revolution-border overflow-y-auto">
      <nav className="p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center space-x-3 px-4 py-3 rounded-lg transition-all",
                isActive
                  ? "bg-gold-500/20 text-gold-400 border border-gold-500/30"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              )}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}

        {isAdmin && (
          <>
            <div className="pt-4 mt-4 border-t border-revolution-border">
              <p className="px-4 text-xs font-semibold text-slate-500 uppercase mb-2">
                Admin
              </p>
              {adminItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center space-x-3 px-4 py-3 rounded-lg transition-all",
                      isActive
                        ? "bg-gold-500/20 text-gold-400 border border-gold-500/30"
                        : "text-slate-400 hover:text-white hover:bg-slate-800"
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </>
        )}
      </nav>

      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-revolution-border">
        <button
          onClick={handleLogout}
          className="flex items-center space-x-3 px-4 py-3 w-full text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all"
        >
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}