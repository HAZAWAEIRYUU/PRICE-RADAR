"use client";

import { Radar } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <div className="flex items-center gap-3 mb-8">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500">
            <Radar className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Price-Radar プライバシーポリシー
          </h1>
        </div>

        <div className="space-y-6 text-muted-foreground leading-relaxed">
          <p className="text-sm">最終更新日：2026年3月31日</p>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">1. はじめに</h2>
            <p>
              Price-Radar（以下「本サービス」）は、ユーザーのプライバシーを尊重し、個人情報の保護に努めます。
              本プライバシーポリシーは、本サービスが収集する情報とその利用方法について説明します。
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">2. 収集する情報</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>アカウント情報</strong>：ユーザー名、メールアドレス</li>
              <li><strong>Google認証情報</strong>：Googleアカウントのメールアドレス、表示名（Google認証利用時）</li>
              <li><strong>利用データ</strong>：登録した商品情報、競合URL、価格履歴</li>
              <li><strong>決済情報</strong>：Stripeを通じて処理され、本サービスではクレジットカード情報を直接保持しません</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">3. 情報の利用目的</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>本サービスの提供・維持・改善</li>
              <li>ユーザーアカウントの認証・管理</li>
              <li>価格監視機能の提供</li>
              <li>お問い合わせへの対応</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">4. 情報の第三者提供</h2>
            <p>
              法令に基づく場合を除き、ユーザーの個人情報を第三者に提供することはありません。
              ただし、以下のサービスプロバイダーを利用しています：
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Google</strong>：OAuth認証</li>
              <li><strong>Stripe</strong>：決済処理</li>
              <li><strong>Supabase</strong>：データベースホスティング</li>
              <li><strong>Cloudflare</strong>：ウェブホスティング・CDN</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">5. データの保護</h2>
            <p>
              ユーザーの情報は暗号化された通信（SSL/TLS）を通じて送受信され、
              パスワードはハッシュ化して保存されます。
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">6. お問い合わせ</h2>
            <p>
              プライバシーに関するお問い合わせは、以下までご連絡ください。<br />
              メール：kim.young.rong.23.4.18@gmail.com
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
