"use client";

import Link from "next/link";
import {
  Radar,
  TrendingDown,
  Bell,
  LineChart,
  Clock,
  Search,
  FileSpreadsheet,
  ArrowRight,
  Check,
  Zap,
  Shield,
} from "lucide-react";
import { PLANS } from "@/lib/constants";

const painPoints = [
  {
    icon: Search,
    title: "毎日、競合サイトを手動チェック",
    description:
      "Amazon・楽天・Yahoo を1つ1つ開いて価格を確認。商品が増えるほど時間が取られていませんか？",
  },
  {
    icon: TrendingDown,
    title: "値下げに気づかず、売上が減少",
    description:
      "競合が値下げしても気づくのは数日後。その間に顧客が流出し、売上機会を失っています。",
  },
  {
    icon: FileSpreadsheet,
    title: "スプレッドシートでの管理に限界",
    description:
      "手入力ではミスや抜け漏れが発生。リアルタイムの価格変動に追いつけません。",
  },
];

const features = [
  {
    icon: Radar,
    title: "リアルタイム価格監視",
    description:
      "Amazon・楽天・Yahoo ショッピングの競合価格を自動で定期取得。手動チェック不要。",
  },
  {
    icon: Bell,
    title: "価格アラート",
    description:
      "競合が自社より安い価格を設定したら即座に検知。ダッシュボードで一目で確認。",
  },
  {
    icon: LineChart,
    title: "価格推移グラフ",
    description:
      "過去の価格変動をグラフで可視化。トレンドを把握して最適な価格戦略を立案。",
  },
];

const ecSites = ["Amazon.co.jp", "楽天市場", "Yahoo! ショッピング", "その他EC サイト"];

export default function LandingPage() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-emerald-950/20" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-emerald-500/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-[80px]" />
      <div className="absolute top-1/2 right-0 w-[500px] h-[500px] bg-emerald-500/3 rounded-full blur-[100px]" />
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="relative z-10">
        {/* Navigation */}
        <nav className="flex items-center justify-between max-w-6xl mx-auto px-4 py-5">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/25">
              <Radar className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Price-Radar
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login/"
              className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              ログイン
            </Link>
            <Link
              href="/signup/"
              className="px-5 py-2 text-sm font-medium bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white rounded-lg transition-all shadow-lg shadow-emerald-500/20"
            >
              無料で始める
            </Link>
          </div>
        </nav>

        {/* Hero */}
        <section className="max-w-5xl mx-auto px-4 pt-16 sm:pt-24 pb-20 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 text-sm font-medium mb-8">
            <Zap className="w-3.5 h-3.5" />
            EC事業者のための競合価格監視ツール
          </div>

          <h1 className="text-4xl sm:text-6xl font-bold tracking-tight leading-tight mb-6">
            競合の値下げ、
            <br />
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              見逃していませんか？
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            Amazon・楽天・Yahoo ショッピングの競合価格を自動監視。
            <br className="hidden sm:block" />
            価格変動をリアルタイムに検知し、最適な価格戦略をサポートします。
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/signup/"
              className="flex items-center gap-2 px-8 py-3.5 text-base font-semibold bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white rounded-xl transition-all shadow-xl shadow-emerald-500/25"
            >
              無料で始める
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/plans/"
              className="flex items-center gap-2 px-8 py-3.5 text-base font-medium border border-border/50 rounded-xl hover:bg-accent/50 transition-all"
            >
              プランを見る
            </Link>
          </div>

          {/* Dashboard mockup */}
          <div className="mt-16 relative">
            <div className="absolute -inset-4 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-2xl blur-xl" />
            <div className="relative rounded-xl border border-border/30 bg-card/90 backdrop-blur-xl shadow-2xl overflow-hidden p-6 sm:p-8">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                {[
                  { label: "監視中商品数", value: "12", color: "from-emerald-500 to-cyan-500" },
                  { label: "価格負け商品", value: "3", color: "from-red-500 to-orange-500" },
                  { label: "ステータス", value: "注意", color: "from-orange-500 to-amber-500" },
                ].map((kpi) => (
                  <div
                    key={kpi.label}
                    className="relative rounded-lg border border-border/20 bg-card/50 p-4 overflow-hidden"
                  >
                    <div className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${kpi.color}`} />
                    <p className="text-xs text-muted-foreground">{kpi.label}</p>
                    <p className="text-2xl font-bold mt-1">{kpi.value}</p>
                  </div>
                ))}
              </div>
              <div className="rounded-lg border border-border/20 bg-card/30 p-4">
                <p className="text-sm font-medium text-muted-foreground mb-3">要注意商品</p>
                {[
                  { name: "AirPods Pro 2", own: "39,800", comp: "35,900", diff: "+3,900" },
                  { name: "Sony WH-1000XM5", own: "44,000", comp: "39,800", diff: "+4,200" },
                ].map((item) => (
                  <div
                    key={item.name}
                    className="flex items-center justify-between py-2 border-b border-border/10 last:border-0 text-sm"
                  >
                    <span className="font-medium">{item.name}</span>
                    <div className="flex items-center gap-6 tabular-nums">
                      <span className="text-muted-foreground">¥{item.own}</span>
                      <span className="text-emerald-400">¥{item.comp}</span>
                      <span className="text-red-400 font-medium">{item.diff}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Pain Points */}
        <section className="max-w-5xl mx-auto px-4 py-20">
          <h2 className="text-3xl font-bold text-center mb-4">
            こんな
            <span className="bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">課題</span>
            、ありませんか？
          </h2>
          <p className="text-muted-foreground text-center mb-12 max-w-2xl mx-auto">
            EC事業で価格競争力を維持するのは大変です。多くの事業者が同じ悩みを抱えています。
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {painPoints.map((point) => (
              <div
                key={point.title}
                className="rounded-xl border border-border/30 bg-card/80 backdrop-blur-xl p-6 hover:border-red-500/20 transition-colors"
              >
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-red-500/10 mb-4">
                  <point.icon className="w-6 h-6 text-red-400" />
                </div>
                <h3 className="font-semibold mb-2">{point.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {point.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section className="max-w-5xl mx-auto px-4 py-20">
          <h2 className="text-3xl font-bold text-center mb-4">
            Price-Radar が
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              すべて解決
            </span>
          </h2>
          <p className="text-muted-foreground text-center mb-12 max-w-2xl mx-auto">
            自動で競合価格を収集・分析し、価格戦略の意思決定をサポートします。
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-xl border border-border/30 bg-card/80 backdrop-blur-xl p-6 hover:border-emerald-500/20 transition-colors"
              >
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/15 to-cyan-500/15 mb-4">
                  <feature.icon className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Supported EC Sites */}
        <section className="max-w-5xl mx-auto px-4 py-16">
          <h2 className="text-2xl font-bold text-center mb-8">対応ECサイト</h2>
          <div className="flex flex-wrap items-center justify-center gap-4">
            {ecSites.map((site) => (
              <div
                key={site}
                className="px-6 py-3 rounded-xl border border-border/30 bg-card/80 backdrop-blur-xl text-sm font-medium"
              >
                {site}
              </div>
            ))}
          </div>
        </section>

        {/* Pricing */}
        <section className="max-w-4xl mx-auto px-4 py-20">
          <h2 className="text-3xl font-bold text-center mb-4">料金プラン</h2>
          <p className="text-muted-foreground text-center mb-12">
            まずは無料プランで試して、必要に応じてアップグレード
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl border ${plan.borderColor} bg-card/80 backdrop-blur-xl overflow-hidden transition-all duration-300 hover:scale-[1.02] ${plan.shadowColor} shadow-xl ${
                  plan.highlight ? "ring-1 ring-emerald-500/30" : ""
                }`}
              >
                {plan.highlight && (
                  <div className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${plan.gradient}`} />
                )}
                {plan.highlight && (
                  <div className="absolute top-4 right-4">
                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border border-emerald-500/20">
                      <Zap className="w-3 h-3" />
                      おすすめ
                    </span>
                  </div>
                )}
                <div className="p-8">
                  <h3 className="text-lg font-semibold text-muted-foreground mb-2">
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span
                      className={`text-4xl font-bold tracking-tight ${
                        plan.highlight
                          ? "bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent"
                          : ""
                      }`}
                    >
                      {plan.price}
                    </span>
                    <span className="text-muted-foreground text-sm">{plan.period}</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-6">{plan.description}</p>
                  <Link
                    href="/signup/"
                    className={`flex items-center justify-center gap-2 w-full h-11 rounded-lg font-medium text-sm transition-all duration-200 ${
                      plan.highlight
                        ? "bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white shadow-lg shadow-emerald-500/20"
                        : "border border-border/50 text-foreground hover:bg-accent/50"
                    }`}
                  >
                    {plan.cta}
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
                <div className="px-8 pb-8">
                  <div className="border-t border-border/30 pt-6">
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4 flex items-center gap-2">
                      <Shield className="w-3.5 h-3.5" />
                      含まれる機能
                    </p>
                    <ul className="space-y-3">
                      {plan.features.map((feature, i) => (
                        <li key={i} className="flex items-center gap-3 text-sm">
                          <div
                            className={`flex items-center justify-center w-5 h-5 rounded-full ${
                              feature.included ? "bg-emerald-500/15" : "bg-muted/50"
                            }`}
                          >
                            <Check
                              className={`w-3 h-3 ${
                                feature.included ? "text-emerald-400" : "text-muted-foreground/50"
                              }`}
                            />
                          </div>
                          <span className={feature.included ? "text-foreground" : "text-muted-foreground/50"}>
                            {feature.text}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="max-w-3xl mx-auto px-4 py-20 text-center">
          <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5 backdrop-blur-xl p-12">
            <h2 className="text-3xl font-bold mb-4">
              今すぐ始めましょう
            </h2>
            <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
              3分で登録完了。無料プランで競合価格の監視を始められます。
              クレジットカード不要。
            </p>
            <Link
              href="/signup/"
              className="inline-flex items-center gap-2 px-8 py-4 text-lg font-semibold bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white rounded-xl transition-all shadow-xl shadow-emerald-500/25"
            >
              無料アカウントを作成
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="max-w-6xl mx-auto px-4 py-8 border-t border-border/20">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Radar className="w-4 h-4 text-emerald-400" />
              <span>Price-Radar</span>
            </div>
            <div className="flex items-center gap-6">
              <Link href="/privacy/" className="hover:text-foreground transition-colors">
                プライバシーポリシー
              </Link>
              <Link href="/terms/" className="hover:text-foreground transition-colors">
                利用規約
              </Link>
              <Link href="/login/" className="hover:text-foreground transition-colors">
                ログイン
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
