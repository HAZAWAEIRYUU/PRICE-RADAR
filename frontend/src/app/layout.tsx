import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// All absolute URLs in OpenGraph/Twitter tags resolve against this base.
// Keep it in sync with the production domain.
const SITE_URL = "https://priceradar.space";
const SITE_NAME = "Price-Radar";
const SITE_TITLE = "Price-Radar | 競合が値下げした瞬間に LINE 通知";
const SITE_DESCRIPTION =
  "Amazon・楽天・Yahoo!ショッピングの競合価格を1時間ごとに自動監視。自社より安くなった瞬間に LINE へ即時通知し、毎日の価格チェック作業をゼロにする EC 事業者向け SaaS。";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: SITE_TITLE,
    template: "%s | Price-Radar",
  },
  description: SITE_DESCRIPTION,
  applicationName: SITE_NAME,
  keywords: [
    "競合価格",
    "価格監視",
    "EC",
    "Amazon",
    "楽天",
    "Yahoo!ショッピング",
    "price tracker",
    "price radar",
  ],
  authors: [{ name: SITE_NAME }],
  // Index the landing page; protected routes remain unlinked and robots
  // shouldn't end up behind the login wall.
  robots: { index: true, follow: true },
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: SITE_NAME,
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    locale: "ja_JP",
    // The `opengraph-image.tsx` convention populates the images array
    // automatically, but we keep alt/type here for platforms that prefer
    // explicit tags.
  },
  twitter: {
    card: "summary_large_image",
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    // images also auto-populated from opengraph-image.tsx
  },
};

import { AuthProvider } from "@/components/auth-provider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ja"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AuthProvider>{children}</AuthProvider>
        <Toaster position="bottom-right" richColors />
      </body>
    </html>
  );
}
