"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { PriceAlertItem, ProductCount } from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Package,
  TrendingDown,
  AlertTriangle,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";

export default function DashboardPage() {
  const [productCount, setProductCount] = useState(0);
  const [alerts, setAlerts] = useState<PriceAlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [countRes, alertsRes] = await Promise.all([
          api.get<ProductCount>("/api/products/count"),
          api.get<PriceAlertItem[]>("/api/prices/alerts"),
        ]);
        setProductCount(countRes.data.count);
        setAlerts(alertsRes.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const kpiCards = [
    {
      title: "監視中商品数",
      value: productCount,
      icon: Package,
      gradient: "from-emerald-500 to-cyan-500",
      shadowColor: "shadow-emerald-500/10",
    },
    {
      title: "価格負け商品",
      value: alerts.length,
      icon: TrendingDown,
      gradient: "from-red-500 to-orange-500",
      shadowColor: "shadow-red-500/10",
    },
    {
      title: "ステータス",
      value: alerts.length === 0 ? "安全" : "注意",
      icon: alerts.length === 0 ? ShieldCheck : AlertTriangle,
      gradient:
        alerts.length === 0
          ? "from-emerald-500 to-green-500"
          : "from-orange-500 to-amber-500",
      shadowColor:
        alerts.length === 0
          ? "shadow-emerald-500/10"
          : "shadow-orange-500/10",
    },
  ];

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div>
          <div className="h-8 w-48 bg-muted rounded mb-2" />
          <div className="h-4 w-72 bg-muted/50 rounded" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-muted rounded-xl" />
          ))}
        </div>
        <div className="h-96 bg-muted rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">ダッシュボード</h1>
        <p className="text-muted-foreground mt-1">
          競合価格の監視状況を一目で確認
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {kpiCards.map((kpi) => (
          <Card
            key={kpi.title}
            className={`relative overflow-hidden border-border/30 bg-card/80 backdrop-blur ${kpi.shadowColor} shadow-lg hover:shadow-xl transition-shadow duration-300`}
          >
            <div
              className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${kpi.gradient}`}
            />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {kpi.title}
              </CardTitle>
              <div
                className={`p-2 rounded-lg bg-gradient-to-br ${kpi.gradient} opacity-80`}
              >
                <kpi.icon className="w-4 h-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold tracking-tight">
                {kpi.value}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Alerts Table */}
      <Card className="border-border/30 bg-card/80 backdrop-blur shadow-lg">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-400" />
            <CardTitle className="text-lg">要注意商品</CardTitle>
          </div>
          <p className="text-sm text-muted-foreground">
            自社が価格で負けている商品一覧
          </p>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <ShieldCheck className="w-12 h-12 mx-auto mb-3 opacity-30 text-emerald-500" />
              <p className="text-lg font-medium">すべて価格優位です 🎉</p>
              <p className="text-sm mt-1">
                価格で負けている商品はありません
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-border/30 hover:bg-transparent">
                    <TableHead>商品名</TableHead>
                    <TableHead className="text-right">自社価格</TableHead>
                    <TableHead className="text-right">競合価格</TableHead>
                    <TableHead>競合名</TableHead>
                    <TableHead className="text-right">価格差</TableHead>
                    <TableHead>在庫</TableHead>
                    <TableHead className="w-10" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alerts.map((item, index) => {
                    const diff = parseFloat(item.price_diff);
                    const ownPrice = parseFloat(item.own_price);
                    const diffPercent =
                      ownPrice > 0 ? (diff / ownPrice) * 100 : 0;
                    const severity =
                      diffPercent > 15
                        ? "high"
                        : diffPercent > 5
                          ? "medium"
                          : "low";

                    return (
                      <TableRow
                        key={`${item.product_id}-${item.competitor_name}-${index}`}
                        className={`border-border/20 transition-colors ${
                          severity === "high"
                            ? "bg-red-500/5 hover:bg-red-500/10"
                            : severity === "medium"
                              ? "bg-orange-500/5 hover:bg-orange-500/10"
                              : "hover:bg-accent/50"
                        }`}
                      >
                        <TableCell className="font-medium">
                          {item.product_name}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          ¥
                          {parseFloat(item.own_price).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right tabular-nums text-emerald-400">
                          ¥
                          {parseFloat(
                            item.competitor_price
                          ).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="text-xs">
                            {item.competitor_name}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right tabular-nums text-red-400 font-medium">
                          +¥{diff.toLocaleString()}
                          <span className="text-xs text-muted-foreground ml-1">
                            ({diffPercent.toFixed(1)}%)
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={
                              item.stock_status === "在庫あり"
                                ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/20"
                                : "bg-red-500/15 text-red-400 border-red-500/20"
                            }
                          >
                            {item.stock_status === "在庫あり"
                              ? "在庫あり"
                              : "品切れ"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Link
                            href={`/prices?id=${item.product_id}`}
                            className="text-muted-foreground hover:text-emerald-400 transition-colors"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </Link>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
