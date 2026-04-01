"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Check, ArrowRight, Loader2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

function SuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams.get("session_id");
  const [countdown, setCountdown] = useState(5);
  const [verified, setVerified] = useState<boolean | null>(null);

  useEffect(() => {
    if (!sessionId) {
      router.push("/pricing");
      return;
    }

    api
      .get("/api/stripe/verify-session", { params: { session_id: sessionId } })
      .then(() => setVerified(true))
      .catch(() => {
        setVerified(false);
        setTimeout(() => router.push("/pricing"), 3000);
      });
  }, [sessionId, router]);

  useEffect(() => {
    if (verified !== true) return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          router.push("/pricing");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [verified, router]);

  if (verified === null) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  if (verified === false) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mb-8">
          <XCircle className="w-10 h-10 text-red-400" />
        </div>
        <h1 className="text-2xl font-bold text-red-400 mb-4">
          決済の確認に失敗しました
        </h1>
        <p className="text-muted-foreground max-w-md mb-8">
          プラン管理画面へ戻ります...
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center mb-8 animate-in zoom-in duration-500">
        <Check className="w-10 h-10 text-emerald-400" />
      </div>

      <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent mb-4">
        アップグレード完了！
      </h1>

      <p className="text-muted-foreground max-w-md mb-8">
        Pro プランへのアップグレードが完了しました。
        商品登録枠が拡大され、すべての機能が利用可能になります。
        <br />
        <br />
        {countdown} 秒後にプラン管理画面へ戻ります...
      </p>

      <Button
        onClick={() => router.push("/pricing")}
        className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white"
        size="lg"
      >
        ダッシュボードへ戻る
        <ArrowRight className="w-4 h-4 ml-2" />
      </Button>
    </div>
  );
}

export default function StripeSuccessPage() {
  return (
    <Suspense fallback={
      <div className="flex justify-center items-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
      </div>
    }>
      <SuccessContent />
    </Suspense>
  );
}
