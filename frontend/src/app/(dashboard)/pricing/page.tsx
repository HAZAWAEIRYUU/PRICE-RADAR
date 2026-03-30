"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PlanInfo } from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Check,
  X,
  Zap,
  Shield,
  Crown,
  Loader2,
  Package,
  Link2,
  Clock,
  TrendingUp,
} from "lucide-react";

const planFeatures = {
  free: [
    { text: "監視商品数 3件", icon: Package },
    { text: "競合URL 2件/商品", icon: Link2 },
    { text: "価格履歴 7日間", icon: Clock },
    { text: "ダッシュボード", icon: TrendingUp },
  ],
  pro: [
    { text: "監視商品数 50件", icon: Package },
    { text: "競合URL 10件/商品", icon: Link2 },
    { text: "価格履歴 無制限", icon: Clock },
    { text: "ダッシュボード", icon: TrendingUp },
    { text: "優先サポート", icon: Shield },
  ],
};

export default function DashboardPricingPage() {
  const [planInfo, setPlanInfo] = useState<PlanInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [successOpen, setSuccessOpen] = useState(false);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const res = await api.get<PlanInfo>("/api/plan");
        setPlanInfo(res.data);
      } catch (err) {
        console.error("Failed to fetch plan info:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPlan();
  }, []);

  const handleUpgrade = async () => {
    setUpgrading(true);
    try {
      const res = await api.post<PlanInfo>("/api/plan/upgrade");
      setPlanInfo(res.data);
      setConfirmOpen(false);
      setSuccessOpen(true);
    } catch (err) {
      console.error("Failed to upgrade:", err);
    } finally {
      setUpgrading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-8 w-48 bg-muted rounded" />
        <div className="grid md:grid-cols-2 gap-6">
          <div className="h-96 bg-muted rounded-xl" />
          <div className="h-96 bg-muted rounded-xl" />
        </div>
      </div>
    );
  }

  const isFreePlan = planInfo?.plan === "free";
  const isProPlan = planInfo?.plan === "pro" || planInfo?.plan === "enterprise";
  const usage = planInfo?.usage;

  const usagePercent =
    usage && usage.max_products
      ? Math.round((usage.current_products / usage.max_products) * 100)
      : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">プラン</h1>
        <p className="text-muted-foreground mt-1">
          現在のプランと使用状況の確認
        </p>
      </div>

      {/* Current Usage Card */}
      <Card className="border-border/30 bg-card/80 backdrop-blur shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              使用状況
            </CardTitle>
            <Badge
              className={`text-xs ${
                isProPlan
                  ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border-emerald-500/20"
                  : "bg-secondary text-secondary-foreground"
              }`}
            >
              {isProPlan && <Crown className="w-3 h-3 mr-1" />}
              {planInfo?.label} プラン
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-muted-foreground mb-1">監視商品数</p>
              <p className="text-2xl font-bold tabular-nums">
                {usage?.current_products ?? 0}
                <span className="text-sm font-normal text-muted-foreground">
                  {" "}
                  / {usage?.max_products ?? "∞"}
                </span>
              </p>
              {usage?.max_products && (
                <div className="mt-2 h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      usagePercent >= 90
                        ? "bg-red-500"
                        : usagePercent >= 70
                          ? "bg-orange-500"
                          : "bg-gradient-to-r from-emerald-500 to-cyan-500"
                    }`}
                    style={{ width: `${Math.min(usagePercent, 100)}%` }}
                  />
                </div>
              )}
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">
                競合URL上限/商品
              </p>
              <p className="text-2xl font-bold tabular-nums">
                {usage?.max_competitors_per_product ?? "∞"}
                <span className="text-sm font-normal text-muted-foreground">
                  {" "}
                  件
                </span>
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">
                価格履歴保持
              </p>
              <p className="text-2xl font-bold tabular-nums">
                {usage?.history_retention_days ?? "∞"}
                <span className="text-sm font-normal text-muted-foreground">
                  {" "}
                  {usage?.history_retention_days ? "日間" : ""}
                </span>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Plan Comparison */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Free Plan */}
        <Card
          className={`relative border-border/30 bg-card/80 backdrop-blur shadow-lg transition-all duration-300 ${
            isFreePlan ? "ring-1 ring-border/50" : "opacity-75"
          }`}
        >
          {isFreePlan && (
            <div className="absolute top-4 right-4">
              <Badge variant="secondary" className="text-xs">
                現在のプラン
              </Badge>
            </div>
          )}
          <CardHeader className="pb-4">
            <CardTitle className="text-lg text-muted-foreground">
              Free
            </CardTitle>
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold">¥0</span>
              <span className="text-sm text-muted-foreground">永久無料</span>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {planFeatures.free.map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-sm">
                  <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-muted/50">
                    <f.icon className="w-3.5 h-3.5 text-muted-foreground" />
                  </div>
                  {f.text}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Pro Plan */}
        <Card
          className={`relative border-emerald-500/30 bg-card/80 backdrop-blur shadow-xl shadow-emerald-500/10 transition-all duration-300 ${
            isProPlan ? "ring-1 ring-emerald-500/30" : ""
          }`}
        >
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 to-cyan-500" />

          {isProPlan && (
            <div className="absolute top-4 right-4">
              <Badge className="text-xs bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border-emerald-500/20">
                <Crown className="w-3 h-3 mr-1" />
                現在のプラン
              </Badge>
            </div>
          )}

          {!isProPlan && (
            <div className="absolute top-4 right-4">
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border border-emerald-500/20">
                <Zap className="w-3 h-3" />
                おすすめ
              </span>
            </div>
          )}

          <CardHeader className="pb-4">
            <CardTitle className="text-lg bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Pro
            </CardTitle>
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                ¥1,980
              </span>
              <span className="text-sm text-muted-foreground">/月</span>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <ul className="space-y-3">
              {planFeatures.pro.map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-sm">
                  <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-emerald-500/10">
                    <f.icon className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  {f.text}
                </li>
              ))}
            </ul>

            {isFreePlan && (
              <Button
                onClick={() => setConfirmOpen(true)}
                className="w-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white shadow-lg shadow-emerald-500/20"
              >
                <Zap className="w-4 h-4 mr-2" />
                Pro にアップグレード
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Upgrade Confirmation Dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-md bg-card border-border/50">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Crown className="w-5 h-5 text-emerald-400" />
              Pro プランにアップグレード
            </DialogTitle>
            <DialogDescription>
              Pro プラン（¥1,980/月）にアップグレードしますか？
              商品登録数が50件に拡大され、すべての機能が利用可能になります。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setConfirmOpen(false)}>
              キャンセル
            </Button>
            <Button
              onClick={handleUpgrade}
              disabled={upgrading}
              className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white"
            >
              {upgrading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  処理中...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  アップグレード
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Success Dialog */}
      <Dialog open={successOpen} onOpenChange={setSuccessOpen}>
        <DialogContent className="sm:max-w-md bg-card border-border/50 text-center">
          <div className="py-4">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center">
                <Check className="w-8 h-8 text-emerald-400" />
              </div>
            </div>
            <h3 className="text-xl font-bold mb-2">
              アップグレード完了 🎉
            </h3>
            <p className="text-muted-foreground text-sm">
              Pro プランが有効になりました。
              すべての機能をお楽しみください！
            </p>
          </div>
          <DialogFooter className="justify-center">
            <Button
              onClick={() => setSuccessOpen(false)}
              className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white"
            >
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
