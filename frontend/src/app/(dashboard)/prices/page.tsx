"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import api from "@/lib/api";
import { Product, PriceHistoryRecord } from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Package,
  TrendingUp,
  TrendingDown,
  Calendar,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const CHART_COLORS = [
  "#10b981", // emerald (our price)
  "#06b6d4", // cyan
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#14b8a6", // teal
  "#f97316", // orange
];

type CombinedChartData = {
  date: string;
  our_price: number;
} & Record<string, number | string>;

export default function PricesPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const productId = searchParams.get("id");

  const [product, setProduct] = useState<Product | null>(null);
  const [chartData, setChartData] = useState<CombinedChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [competitors, setCompetitors] = useState<string[]>([]);

  useEffect(() => {
    if (!productId) {
      setLoading(false);
      return;
    }
    const fetchData = async () => {
      try {
        const [productRes, historyRes] = await Promise.all([
          api.get(`/api/products/${productId}`),
          api.get(`/api/prices/${productId}/history`),
        ]);
        const p: Product = productRes.data;
        setProduct(p);

        const rawHistory: PriceHistoryRecord[] = historyRes.data;
        
        const urlIdToName: Record<number, string> = {};
        if (p.competitor_urls) {
          p.competitor_urls.forEach((url) => {
            urlIdToName[url.id] = url.competitor_name;
          });
        }
        
        const compNames = new Set(Object.values(urlIdToName));
        setCompetitors(Array.from(compNames));

        const grouped: Record<string, CombinedChartData> = {};
        
        rawHistory.forEach((record) => {
          const date = new Date(record.scraped_at).toLocaleDateString();
          if (!grouped[date]) {
            grouped[date] = {
              date,
              our_price: parseFloat(p.own_price),
            };
          }
          const compName = urlIdToName[record.competitor_url_id] || `Unknown (${record.competitor_url_id})`;
          grouped[date][compName] = parseFloat(record.price);
        });

        const sortedData = Object.values(grouped).sort((a, b) => 
          new Date(a.date).getTime() - new Date(b.date).getTime()
        );
        
        setChartData(sortedData);

      } catch (err) {
        console.error("Failed to fetch price history:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [productId]);

  const latestData = chartData[chartData.length - 1];
  const lowestCompetitor =
    latestData && competitors.length > 0
      ? competitors.reduce(
          (min, c) => {
            const price = latestData[c] as number;
            if (price && (min.price === 0 || price < min.price)) {
              return { name: c, price };
            }
            return min;
          },
          { name: "", price: 0 }
        )
      : null;

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-24 bg-muted rounded" />
        <div className="h-40 bg-muted rounded-xl" />
        <div className="h-96 bg-muted rounded-xl" />
      </div>
    );
  }

  if (!productId || !product) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <Package className="w-16 h-16 mb-4 opacity-20" />
        <p className="text-lg font-medium">商品が見つかりません</p>
        <Button
          variant="ghost"
          onClick={() => router.push("/products")}
          className="mt-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          商品一覧に戻る
        </Button>
      </div>
    );
  }

  const ownPriceNum = parseFloat(product.own_price);
  const isLosing =
    lowestCompetitor &&
    latestData &&
    lowestCompetitor.price > 0 &&
    ownPriceNum > lowestCompetitor.price;

  return (
    <div className="space-y-6">
      {/* Back button */}
      <Button
        variant="ghost"
        onClick={() => router.back()}
        className="text-muted-foreground hover:text-foreground -ml-2"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        戻る
      </Button>

      {/* Product Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="md:col-span-2 border-border/30 bg-card/80 backdrop-blur shadow-lg">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-xl">{product.product_name}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  カテゴリ: {product.category || "-"}
                </p>
              </div>
              {isLosing ? (
                <Badge className="bg-red-500/15 text-red-400 border-red-500/20">
                  <TrendingDown className="w-3 h-3 mr-1" />
                  価格負け中
                </Badge>
              ) : (
                <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/20">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  価格優位
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">
                  自社価格
                </p>
                <p className="text-2xl font-bold tabular-nums mt-1">
                  ¥{ownPriceNum.toLocaleString()}
                </p>
              </div>
              {lowestCompetitor && lowestCompetitor.price > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">
                    最安競合価格
                  </p>
                  <p className="text-2xl font-bold tabular-nums mt-1 text-cyan-400">
                    ¥{lowestCompetitor.price.toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {lowestCompetitor.name}
                  </p>
                </div>
              )}
              {lowestCompetitor && lowestCompetitor.price > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">
                    価格差
                  </p>
                  <p
                    className={`text-2xl font-bold tabular-nums mt-1 ${
                      isLosing ? "text-red-400" : "text-emerald-400"
                    }`}
                  >
                    {isLosing ? "+" : "-"}¥
                    {Math.abs(ownPriceNum - lowestCompetitor.price).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/30 bg-card/80 backdrop-blur shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              データ期間
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">過去の推移</p>
            <p className="text-sm text-muted-foreground mt-1">
              {chartData.length > 0
                ? `${chartData[0].date} 〜 ${chartData[chartData.length - 1].date}`
                : "データなし"}
            </p>
            <div className="mt-3">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">
                監視中の競合
              </p>
              <div className="flex flex-wrap gap-1 mt-1.5">
                {product.competitor_urls?.map((c, i) => (
                  <Badge
                    key={c.id}
                    variant="secondary"
                    className="text-xs"
                    style={{
                      borderColor: CHART_COLORS[i + 1] + "33",
                      color: CHART_COLORS[i + 1],
                      backgroundColor: CHART_COLORS[i + 1] + "15",
                    }}
                  >
                    {c.competitor_name}
                  </Badge>
                ))}
                {(!product.competitor_urls || product.competitor_urls.length === 0) && (
                  <span className="text-sm text-muted-foreground">
                    競合データなし
                  </span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Price Chart */}
      <Card className="border-border/30 bg-card/80 backdrop-blur shadow-lg">
        <CardHeader>
          <CardTitle className="text-lg">価格推移グラフ</CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <TrendingUp className="w-16 h-16 mb-4 opacity-20" />
              <p className="text-lg font-medium">価格データがありません</p>
              <p className="text-sm mt-1">
                スクレイピングが実行されるとここにグラフが表示されます
              </p>
            </div>
          ) : (
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.05)"
                  />
                  <XAxis
                    dataKey="date"
                    stroke="rgba(255,255,255,0.3)"
                    tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12 }}
                    tickFormatter={(value) => {
                      const d = new Date(value);
                      return `${d.getMonth() + 1}/${d.getDate()}`;
                    }}
                  />
                  <YAxis
                    stroke="rgba(255,255,255,0.3)"
                    tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12 }}
                    tickFormatter={(value) => `¥${value.toLocaleString()}`}
                    domain={["dataMin - 100", "dataMax + 100"]}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(240 10% 14%)",
                      borderColor: "hsl(240 10% 25%)",
                      borderRadius: "8px",
                      color: "white",
                    }}
                    labelStyle={{ color: "rgba(255,255,255,0.7)" }}
                    formatter={(value) => [
                      `¥${Number(value).toLocaleString()}`,
                    ]}
                  />
                  <Legend
                    wrapperStyle={{ color: "rgba(255,255,255,0.7)" }}
                  />
                  {/* Our price line */}
                  <Line
                    type="monotone"
                    dataKey="our_price"
                    name="自社価格"
                    stroke={CHART_COLORS[0]}
                    strokeWidth={3}
                    dot={{ r: 3 }}
                    activeDot={{ r: 6 }}
                  />
                  {/* Competitor lines */}
                  {competitors.map((competitor, index) => (
                    <Line
                      key={competitor}
                      type="monotone"
                      dataKey={competitor}
                      name={competitor}
                      stroke={CHART_COLORS[index + 1]}
                      strokeWidth={2}
                      dot={{ r: 2 }}
                      activeDot={{ r: 5 }}
                      strokeDasharray={index > 3 ? "5 5" : undefined}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
