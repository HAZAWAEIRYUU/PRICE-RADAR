"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Package,
  LogOut,
  Radar,
  Menu,
  X,
  Crown,
} from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { PlanInfo } from "@/lib/types";
import api from "@/lib/api";

const navItems = [
  { href: "/", label: "ダッシュボード", icon: LayoutDashboard },
  { href: "/products", label: "商品管理", icon: Package },
  { href: "/pricing", label: "プラン", icon: Crown },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { logout } = useAuth();
  const [planInfo, setPlanInfo] = useState<PlanInfo | null>(null);

  useEffect(() => {
    api.get<PlanInfo>("/api/plan").then(res => setPlanInfo(res.data)).catch(() => {});
  }, []);

  return (
    <>
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/25">
          <Radar className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Price-Radar
          </h1>
          <p className="text-[10px] text-muted-foreground tracking-widest uppercase">
            競合価格監視
          </p>
        </div>
      </div>

      <Separator className="opacity-50" />

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-gradient-to-r from-emerald-500/15 to-cyan-500/15 text-emerald-400 shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              <item.icon
                className={cn(
                  "w-4 h-4 transition-colors",
                  isActive ? "text-emerald-400" : ""
                )}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <Separator className="opacity-50" />

      {/* Plan Badge */}
      {planInfo && (
        <div className="px-4 py-3">
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium ${
            planInfo.plan === "pro" || planInfo.plan === "enterprise"
              ? "bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 text-emerald-400 border border-emerald-500/20"
              : "bg-muted/50 text-muted-foreground"
          }`}>
            <Crown className={`w-3.5 h-3.5 ${
              planInfo.plan === "pro" || planInfo.plan === "enterprise" ? "text-emerald-400" : "text-muted-foreground"
            }`} />
            {planInfo.label} プラン
            {planInfo.usage.max_products && (
              <span className="ml-auto tabular-nums">
                {planInfo.usage.current_products}/{planInfo.usage.max_products}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Logout */}
      <div className="px-3 py-4">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-all duration-200 w-full"
        >
          <LogOut className="w-4 h-4" />
          ログアウト
        </button>
      </div>
    </>
  );
}

export function MobileHeader() {
  const [open, setOpen] = useState(false);

  // Close menu on route change
  const pathname = usePathname();
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Prevent body scroll when menu is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      {/* Mobile header bar */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 border-b border-border/50 bg-card/80 backdrop-blur-xl sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/25">
            <Radar className="w-4 h-4 text-white" />
          </div>
          <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Price-Radar
          </h1>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center justify-center w-9 h-9 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all duration-200"
          aria-label="メニューを開く"
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </header>

      {/* Mobile menu overlay */}
      {open && (
        <div className="md:hidden fixed inset-0 z-50" style={{ top: 0 }}>
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />
          {/* Slide-in panel */}
          <aside
            className="absolute top-0 left-0 h-full w-72 flex flex-col bg-card/95 backdrop-blur-xl border-r border-border/50 shadow-2xl shadow-black/50 animate-in slide-in-from-left duration-300"
          >
            <SidebarContent onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}
    </>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden md:flex md:w-64 flex-col border-r border-border/50 bg-card/50 backdrop-blur-xl">
      <SidebarContent />
    </aside>
  );
}
