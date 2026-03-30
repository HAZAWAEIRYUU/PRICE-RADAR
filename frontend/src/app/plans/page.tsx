"use client";

import { Radar, Check, X, Zap, Shield, ArrowRight } from "lucide-react";

const plans = [
  {
    name: "Free",
    price: "¥0",
    period: "永久無料",
    description: "まずは無料で競合価格の監視を始めましょう",
    gradient: "from-slate-500 to-zinc-600",
    shadowColor: "shadow-slate-500/10",
    borderColor: "border-border/50",
    features: [
      { text: "監視商品数 3件", included: true },
      { text: "競合URL 2件/商品", included: true },
      { text: "ダッシュボード", included: true },
      { text: "価格アラート", included: true },
      { text: "価格履歴 7日間", included: true },
      { text: "無制限の商品登録", included: false },
      { text: "無制限の競合URL", included: false },
      { text: "無制限の価格履歴", included: false },
    ],
    cta: "無料で始める",
    ctaVariant: "outline" as const,
    highlight: false,
  },
  {
    name: "Pro",
    price: "¥1,980",
    period: "/月",
    description: "本格的な競合分析で価格戦略を最適化",
    gradient: "from-emerald-500 to-cyan-500",
    shadowColor: "shadow-emerald-500/20",
    borderColor: "border-emerald-500/30",
    features: [
      { text: "監視商品数 50件", included: true },
      { text: "競合URL 10件/商品", included: true },
      { text: "ダッシュボード", included: true },
      { text: "価格アラート", included: true },
      { text: "価格履歴 無制限", included: true },
      { text: "優先サポート", included: true },
      { text: "CSV エクスポート", included: true },
      { text: "API アクセス", included: true },
    ],
    cta: "Proを始める",
    ctaVariant: "default" as const,
    highlight: true,
  },
];

export default function PublicPricingPage() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-emerald-950/20" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-emerald-500/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-[80px]" />

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="relative z-10 max-w-5xl mx-auto px-4 py-16 sm:py-24">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/25">
              <Radar className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Price-Radar
            </span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            競合価格をリアルタイムに監視し、
            <br className="hidden sm:block" />
            価格戦略を最適化するダッシュボード
          </p>
        </div>

        {/* Plans */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {plans.map((plan) => (
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
                  <span className={`text-4xl font-bold tracking-tight ${
                    plan.highlight
                      ? "bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent"
                      : ""
                  }`}>
                    {plan.price}
                  </span>
                  <span className="text-muted-foreground text-sm">
                    {plan.period}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mb-6">
                  {plan.description}
                </p>

                <a
                  href="/signup"
                  className={`flex items-center justify-center gap-2 w-full h-11 rounded-lg font-medium text-sm transition-all duration-200 ${
                    plan.highlight
                      ? "bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white shadow-lg shadow-emerald-500/20"
                      : "border border-border/50 text-foreground hover:bg-accent/50"
                  }`}
                >
                  {plan.cta}
                  <ArrowRight className="w-4 h-4" />
                </a>
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
                        {feature.included ? (
                          <div className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/15">
                            <Check className="w-3 h-3 text-emerald-400" />
                          </div>
                        ) : (
                          <div className="flex items-center justify-center w-5 h-5 rounded-full bg-muted/50">
                            <X className="w-3 h-3 text-muted-foreground/50" />
                          </div>
                        )}
                        <span
                          className={
                            feature.included
                              ? "text-foreground"
                              : "text-muted-foreground/50"
                          }
                        >
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

        {/* Footer CTA */}
        <div className="text-center mt-16">
          <p className="text-muted-foreground text-sm">
            既にアカウントをお持ちですか？{" "}
            <a
              href="/login"
              className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
            >
              ログイン
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
