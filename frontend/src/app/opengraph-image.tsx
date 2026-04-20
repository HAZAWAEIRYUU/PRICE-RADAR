import { ImageResponse } from "next/og";

// Standard Open Graph image size. Twitter, LinkedIn, Slack, Discord, Facebook
// all accept this; Twitter's summary_large_image card requires at least 300x157
// and a 2:1-ish ratio, which this satisfies.
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Price-Radar — 競合が値下げした瞬間に LINE で通知する EC 向け価格監視 SaaS";

// Keeps prerender at `next build` time so `output: "export"` drops a static PNG
// into out/opengraph-image.png, which Cloudflare Pages then serves.
export const dynamic = "force-static";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "80px 96px",
          background:
            "linear-gradient(135deg, #0b0f19 0%, #0f172a 45%, #0d2a2e 100%)",
          color: "#e2e8f0",
          fontFamily: "system-ui, -apple-system, sans-serif",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Radar arc decoration */}
        <div
          style={{
            position: "absolute",
            top: -200,
            right: -200,
            width: 720,
            height: 720,
            borderRadius: "50%",
            border: "2px solid rgba(16, 185, 129, 0.15)",
            display: "flex",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: -80,
            right: -80,
            width: 480,
            height: 480,
            borderRadius: "50%",
            border: "2px solid rgba(16, 185, 129, 0.2)",
            display: "flex",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: 40,
            right: 40,
            width: 240,
            height: 240,
            borderRadius: "50%",
            border: "2px solid rgba(16, 185, 129, 0.3)",
            display: "flex",
          }}
        />

        {/* Top: brand */}
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: 16,
              background: "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 8px 32px rgba(16, 185, 129, 0.4)",
              fontSize: 36,
            }}
          >
            📡
          </div>
          <div
            style={{
              fontSize: 32,
              fontWeight: 600,
              letterSpacing: "0.02em",
              color: "#94a3b8",
            }}
          >
            Price-Radar
          </div>
        </div>

        {/* Bottom: main headline */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div
            style={{
              fontSize: 80,
              fontWeight: 800,
              lineHeight: 1.05,
              letterSpacing: "-0.02em",
              color: "#f8fafc",
              display: "flex",
            }}
          >
            競合の値下げを LINE で即時通知
          </div>
          <div
            style={{
              fontSize: 34,
              fontWeight: 500,
              lineHeight: 1.3,
              color: "#94a3b8",
              display: "flex",
            }}
          >
            EC 事業者向け、1 時間ごとの自動価格監視 SaaS
          </div>
          <div
            style={{
              display: "flex",
              gap: 24,
              marginTop: 16,
              fontSize: 22,
              color: "#10b981",
              fontWeight: 600,
            }}
          >
            <span>Amazon</span>
            <span style={{ color: "#475569" }}>·</span>
            <span>楽天市場</span>
            <span style={{ color: "#475569" }}>·</span>
            <span>Yahoo!ショッピング</span>
            <span style={{ color: "#475569" }}>·</span>
            <span>LINE通知</span>
          </div>
        </div>
      </div>
    ),
    { ...size },
  );
}
