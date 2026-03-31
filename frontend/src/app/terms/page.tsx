"use client";

import { Radar } from "lucide-react";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <div className="flex items-center gap-3 mb-8">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500">
            <Radar className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Price-Radar 利用規約
          </h1>
        </div>

        <div className="space-y-6 text-muted-foreground leading-relaxed">
          <p className="text-sm">最終更新日：2026年3月31日</p>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">1. サービスの概要</h2>
            <p>
              Price-Radar（以下「本サービス」）は、競合商品の価格を監視・比較するためのウェブアプリケーションです。
              本サービスを利用することにより、本利用規約に同意したものとみなします。
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">2. アカウント</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>ユーザーは正確な情報を提供してアカウントを作成する必要があります</li>
              <li>アカウントの管理責任はユーザーにあります</li>
              <li>不正利用が発覚した場合、アカウントを停止する場合があります</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">3. 利用プラン</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Freeプラン</strong>：無料で基本機能を利用可能（監視商品数3件、競合URL 2件/商品）</li>
              <li><strong>Proプラン</strong>：月額¥1,980で高度な機能を利用可能（監視商品数50件、競合URL 10件/商品）</li>
              <li>有料プランはStripeを通じて決済されます</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">4. 禁止事項</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>不正アクセスやシステムへの攻撃</li>
              <li>他のユーザーへの迷惑行為</li>
              <li>法令に違反する利用</li>
              <li>サービスの逆コンパイルやリバースエンジニアリング</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">5. 免責事項</h2>
            <p>
              本サービスは「現状有姿」で提供されます。価格情報の正確性や完全性について保証するものではありません。
              本サービスの利用により生じた損害について、当社は一切の責任を負いません。
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">6. 規約の変更</h2>
            <p>
              本規約は予告なく変更される場合があります。変更後も本サービスを利用した場合、
              変更後の規約に同意したものとみなします。
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">7. お問い合わせ</h2>
            <p>
              本規約に関するお問い合わせは、以下までご連絡ください。<br />
              メール：kim.young.rong.23.4.18@gmail.com
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
