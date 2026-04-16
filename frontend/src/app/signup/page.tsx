"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { register, googleLogin, getGoogleAuthUrl, lineLogin, getLineAuthUrl } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Radar, Eye, EyeOff, Loader2 } from "lucide-react";
import { GoogleIcon } from "@/components/google-icon";
import { LineIcon } from "@/components/line-icon";


function SignupContent() {
  const searchParams = useSearchParams();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [lineLoading, setLineLoading] = useState(false);

  // Handle Google or LINE OAuth callback
  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) return;

    const provider = searchParams.get("state")?.startsWith("line:") ? "line" : "google";
    const redirectUri = `${window.location.origin}/signup/`;

    if (provider === "line") {
      setLineLoading(true);
      lineLogin(code, redirectUri)
        .then(() => {
          window.location.href = "/dashboard/";
        })
        .catch((err) => {
          console.error("LINE auth failed:", err?.response?.data || err);
          setError("LINEアカウントでの登録に失敗しました。");
          setLineLoading(false);
          window.history.replaceState({}, "", "/signup/");
        });
    } else {
      setGoogleLoading(true);
      googleLogin(code, redirectUri)
        .then(() => {
          window.location.href = "/dashboard/";
        })
        .catch((err) => {
          console.error("Google auth failed:", err?.response?.data || err);
          setError("Googleアカウントでの登録に失敗しました。");
          setGoogleLoading(false);
          window.history.replaceState({}, "", "/signup/");
        });
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("パスワードが一致しません。");
      return;
    }

    setLoading(true);

    try {
      await register(username, password, email || undefined);
      window.location.href = "/dashboard/";
    } catch {
      setError("登録に失敗しました。（ユーザー名が既に存在する可能性があります）");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = () => {
    const redirectUri = `${window.location.origin}/signup/`;
    const url = getGoogleAuthUrl(redirectUri);
    if (url) {
      window.location.href = url;
    } else {
      setError("Google認証が利用できません。");
    }
  };

  const handleLineSignup = () => {
    const redirectUri = `${window.location.origin}/signup/`;
    const state = `line:${Math.random().toString(36).substring(2, 15)}`;
    const url = getLineAuthUrl(redirectUri, state);
    if (url) {
      window.location.href = url;
    } else {
      setError("LINE認証が利用できません。");
    }
  };

  if (googleLoading || lineLoading) {
    const providerLabel = lineLoading ? "LINE" : "Google";
    return (
      <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-emerald-950/20" />
        <Card className="relative w-full max-w-md mx-4 border-border/50 bg-card/80 backdrop-blur-xl shadow-2xl shadow-black/40">
          <CardContent className="py-16 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-400 mx-auto mb-4" />
            <p className="text-muted-foreground">{providerLabel}アカウントで登録中...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-emerald-950/20" />
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl" />

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <Card className="relative w-full max-w-md mx-4 border-border/50 bg-card/80 backdrop-blur-xl shadow-2xl shadow-black/40">
        <CardHeader className="space-y-4 text-center pb-2">
          {/* Logo */}
          <div className="flex justify-center">
            <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/25">
              <Radar className="w-7 h-7 text-white" />
            </div>
          </div>
          <div>
            <CardTitle className="text-2xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              Price-Radar
            </CardTitle>
            <CardDescription className="text-muted-foreground mt-1">
              新規アカウント登録
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="pt-4">
          {/* Google Signup Button */}
          <Button
            type="button"
            variant="outline"
            onClick={handleGoogleSignup}
            className="w-full h-11 mb-3 bg-white hover:bg-gray-50 text-gray-700 border-gray-300 font-medium transition-all duration-200"
          >
            <GoogleIcon className="w-5 h-5 mr-2" />
            Googleで新規登録
          </Button>

          {/* LINE Signup Button */}
          <Button
            type="button"
            onClick={handleLineSignup}
            className="w-full h-11 mb-5 bg-[#06C755] hover:bg-[#05B04C] text-white font-medium transition-all duration-200"
          >
            <LineIcon className="w-5 h-5 mr-2" />
            LINEで新規登録
          </Button>

          {/* Separator */}
          <div className="relative mb-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border/50" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">または</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center animate-in fade-in slide-in-from-top-1 duration-200">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium">
                ユーザー名
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="ユーザー名を入力"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="h-11 bg-background/50 border-border/50 focus:border-emerald-500/50 focus:ring-emerald-500/20 transition-colors"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">
                メールアドレス（任意）
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 bg-background/50 border-border/50 focus:border-emerald-500/50 focus:ring-emerald-500/20 transition-colors"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">
                パスワード
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-11 pr-10 bg-background/50 border-border/50 focus:border-emerald-500/50 focus:ring-emerald-500/20 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium">
                パスワード（確認用）
              </Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="h-11 bg-background/50 border-border/50 focus:border-emerald-500/50 focus:ring-emerald-500/20 transition-colors"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-medium shadow-lg shadow-emerald-500/20 transition-all duration-200 mt-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  登録中...
                </>
              ) : (
                "アカウントを作成"
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            既にアカウントをお持ちですか？{" "}
            <a href="/login" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
              ログイン
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
      </div>
    }>
      <SignupContent />
    </Suspense>
  );
}
