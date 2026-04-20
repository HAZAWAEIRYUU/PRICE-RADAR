# Price-Radar

> 競合の値下げを LINE で即時通知。Amazon・楽天・Yahoo!ショッピングを 1 時間ごとに自動監視する、EC 事業者向けの価格監視 SaaS。

🌐 **Live**: <https://priceradar.space>

## なぜ作ったか

EC 事業者は毎朝 30 分かけて Amazon・楽天・Yahoo!ショッピングで競合価格を手動チェックし、スプレッドシートに転記しています。それでも気づくのは数日後で、その間に売上機会は失われています。Price-Radar はこの作業を完全に自動化します。

## 機能

- **1 時間ごとの自動スクレイピング** — Amazon.co.jp / 楽天市場 / Yahoo!ショッピング / その他汎用 EC サイト対応
- **LINE 即時通知** — 競合が自社より安くなった瞬間・在庫状況が変わった瞬間にプッシュ通知
- **価格推移グラフ** — 過去の価格変動を時系列で可視化
- **価格負け検知ダッシュボード** — 今すぐ対応が必要な商品だけを一画面に
- **Free / Pro プラン** — 無料で 3 商品、Pro (¥1,980/月) で 50 商品・履歴無制限

## アーキテクチャ

```
Frontend (Next.js 16, static export)                  Backend (FastAPI)
┌─────────────────────────┐  HttpOnly cookie  ┌─────────────────────────┐
│  priceradar.space       │──────────────────▶│  api.priceradar.space   │
│  Cloudflare Pages       │  + CSRF (Origin)  │  Render.com             │
│  + _headers (CSP/HSTS)  │                   │  + per-URL scraper      │
└─────────────────────────┘                   │  + apscheduler jobs     │
                                              └────────────┬────────────┘
                                                           │
                                          ┌────────────────┼────────────────┐
                                          ▼                ▼                ▼
                                    ┌──────────┐   ┌──────────────┐  ┌──────────────┐
                                    │ Supabase │   │  LINE Msg    │  │   Stripe     │
                                    │ Postgres │   │  API (push)  │  │  Billing     │
                                    │  (RLS)   │   └──────────────┘  └──────────────┘
                                    └──────────┘
```

### スタック

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 (App Router, static export), Tailwind CSS, shadcn/ui, Recharts |
| Backend | FastAPI, SQLAlchemy, Alembic, curl_cffi (Amazon bot-evasion), APScheduler |
| DB | Supabase Postgres (RLS on every public table) |
| Auth | Username/password (bcrypt), Google OAuth, LINE Login v2.1 (id_token verified), JWT in HttpOnly cookie |
| Payments | Stripe Checkout + Customer Portal + webhook idempotency table |
| Notifications | LINE Messaging API (push + Flex messages) |
| Hosting | Cloudflare Pages (frontend) + Render.com (backend) |
| CI/CD | Git-integrated auto-deploy on both platforms, Alembic runs in Render build |

## ローカル開発

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # then fill in
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend (別ターミナル)
cd frontend
npm install
npm run dev
# http://localhost:3000
```

必要な env 変数の一覧は `backend/render.yaml` を参照。ローカルでは Supabase の代わりに SQLite が自動で使われる。

## テスト

```bash
cd backend && python3 -m pytest tests/
```

現在 26 tests（認証、products、prices、URL 安全性、CSRF）。

## デプロイ

- **`main` に push すれば両方自動デプロイ**
- Backend: Render の build で `pip install && alembic upgrade head`、startup で gunicorn
- Frontend: Cloudflare Pages の build で `npm install && npm run build`、`out/` を配信

## セキュリティの立て付け

- **Row Level Security** 全 public テーブルで有効（PostgREST anon キー経由のアクセスを default-deny）
- **JWT は HttpOnly / Secure / SameSite=None cookie**、Authorization ヘッダは互換フォールバックのみ
- **CSRF 防御**: cookie を持つリクエストのみ Origin 検証。Bearer / 匿名 POST は通す
- **SSRF ガード**: スクレイパーは書き込み時と取得直前で URL 検証（loopback / link-local / AWS metadata / `.internal` 拒否）
- **Stripe webhook** は署名検証 + `processed_stripe_events` テーブルで idempotency
- **LINE id_token** は LINE verify エンドポイントで署名・aud・exp 検証
- **CSP / HSTS / X-Frame-Options** は Cloudflare Pages の `public/_headers` で配信

## プラン設定

| Plan | 商品数 | 競合 URL/商品 | 履歴保持 | 価格 |
|---|---|---|---|---|
| Free | 3 | 2 | 7 日 | ¥0 |
| Pro | 50 | 10 | 無制限 | ¥1,980 / 月 |
| Enterprise | 無制限 | 無制限 | 無制限 | 要相談 |

## ライセンス

Proprietary. All rights reserved.
