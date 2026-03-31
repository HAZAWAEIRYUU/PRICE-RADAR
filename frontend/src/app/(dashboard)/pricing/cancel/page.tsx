"use client";

import { X, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function StripeCancelPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mb-8 animate-in zoom-in duration-500">
        <X className="w-10 h-10 text-red-400" />
      </div>

      <h1 className="text-3xl font-bold mb-4">
        決済がキャンセルされました
      </h1>
      
      <p className="text-muted-foreground max-w-md mb-8">
        アップグレード処理は中断されました。料金は発生していません。
        もしよろしければ、またのご利用をお待ちしております。
      </p>

      <Link href="/pricing">
        <Button variant="outline" size="lg">
          <ArrowLeft className="w-4 h-4 mr-2" />
          プラン一覧へ戻る
        </Button>
      </Link>
    </div>
  );
}
