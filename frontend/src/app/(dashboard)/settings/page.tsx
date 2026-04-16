"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import api from "@/lib/api";
import { lineLogin, getLineAuthUrl } from "@/lib/auth";
import { NotificationSettings, LineLinkStatus } from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Loader2, Bell, MessageCircle, ExternalLink, Trash2, Send, CheckCircle2 } from "lucide-react";
import { LineIcon } from "@/components/line-icon";
import { toast } from "sonner";

function SettingsContent() {
  const searchParams = useSearchParams();
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [lineStatus, setLineStatus] = useState<LineLinkStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [linking, setLinking] = useState(false);
  const [testing, setTesting] = useState(false);

  // LINE 連携コールバック処理（state="line:link:..." のときに連携実行）
  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state") || "";
    if (code && state.startsWith("line:link:")) {
      setLinking(true);
      const redirectUri = `${window.location.origin}/settings/`;
      lineLogin(code, redirectUri)
        .then(() => {
          toast.success("LINE連携が完了しました");
          window.history.replaceState({}, "", "/settings/");
          fetchAll();
        })
        .catch((err) => {
          console.error("LINE link failed:", err?.response?.data || err);
          toast.error(
            err?.response?.data?.detail ||
              "LINE連携に失敗しました。もう一度お試しください。"
          );
          window.history.replaceState({}, "", "/settings/");
        })
        .finally(() => setLinking(false));
    }
  }, [searchParams]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [s, l] = await Promise.all([
        api.get<NotificationSettings>("/api/notifications/settings"),
        api.get<LineLinkStatus>("/api/notifications/line-status"),
      ]);
      setSettings(s.data);
      setLineStatus(l.data);
    } catch (err) {
      console.error("Failed to load settings:", err);
      toast.error("設定の読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleToggle = async (key: keyof NotificationSettings, value: boolean) => {
    if (!settings) return;
    const previous = settings[key];
    setSettings({ ...settings, [key]: value });
    setSaving(true);
    try {
      await api.put("/api/notifications/settings", { [key]: value });
    } catch (err) {
      console.error("Failed to update setting:", err);
      setSettings({ ...settings, [key]: previous });
      toast.error("設定の保存に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  const handleLineLink = () => {
    const redirectUri = `${window.location.origin}/settings/`;
    const state = `line:link:${Math.random().toString(36).substring(2, 15)}`;
    const url = getLineAuthUrl(redirectUri, state);
    if (!url) {
      toast.error("LINE連携が利用できません。環境設定をご確認ください。");
      return;
    }
    window.location.href = url;
  };

  const handleLineUnlink = async () => {
    if (!confirm("LINE連携を解除しますか？通知は届かなくなります。")) return;
    try {
      await api.delete("/api/notifications/line-link");
      toast.success("LINE連携を解除しました");
      fetchAll();
    } catch (err) {
      console.error("Failed to unlink LINE:", err);
      toast.error("連携解除に失敗しました");
    }
  };

  const handleTestNotification = async () => {
    setTesting(true);
    try {
      await api.post("/api/notifications/test");
      toast.success("テスト通知を送信しました。LINEをご確認ください。");
    } catch (err) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      const detail =
        errorObj?.response?.data?.detail ||
        "送信に失敗しました。Botを友達追加しているかご確認ください。";
      toast.error(detail);
    } finally {
      setTesting(false);
    }
  };

  if (loading || linking) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  const friendAddUrl = lineStatus?.bot_basic_id
    ? `https://line.me/R/ti/p/${lineStatus.bot_basic_id.startsWith("@") ? lineStatus.bot_basic_id : "@" + lineStatus.bot_basic_id}`
    : null;

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">設定</h1>
        <p className="text-muted-foreground mt-1">LINE連携と通知設定の管理</p>
      </div>

      {/* LINE 連携セクション */}
      <Card className="border-border/30 bg-card/80 backdrop-blur shadow-lg">
        <CardHeader>
          <div className="flex items-center gap-2">
            <LineIcon className="w-5 h-5 text-[#06C755]" />
            <CardTitle className="text-lg">LINE連携</CardTitle>
          </div>
          <CardDescription>
            LINEと連携するとリアルタイムで通知を受け取れます
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {lineStatus?.linked ? (
            <>
              <div className="flex items-center gap-3 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">連携済み</p>
                  <p className="text-xs text-muted-foreground truncate">
                    {lineStatus.line_display_name || "LINEユーザー"}
                  </p>
                </div>
                <Badge variant="secondary" className="text-xs bg-emerald-500/15 text-emerald-400 border-emerald-500/20">
                  Active
                </Badge>
              </div>

              {friendAddUrl && (
                <div className="rounded-lg border border-border/30 bg-muted/30 p-4 text-sm space-y-2">
                  <p className="font-medium flex items-center gap-2">
                    <MessageCircle className="w-4 h-4" />
                    通知を受け取るには Bot を友達追加してください
                  </p>
                  <a
                    href={friendAddUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs"
                  >
                    友達追加リンク <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={handleTestNotification}
                  disabled={testing}
                  variant="outline"
                  className="border-emerald-500/50 text-emerald-400 hover:bg-emerald-500/10"
                >
                  {testing ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4 mr-2" />
                  )}
                  テスト通知を送信
                </Button>
                <Button
                  onClick={handleLineUnlink}
                  variant="ghost"
                  className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  連携解除
                </Button>
              </div>
            </>
          ) : (
            <Button
              onClick={handleLineLink}
              className="w-full sm:w-auto bg-[#06C755] hover:bg-[#05B04C] text-white"
            >
              <LineIcon className="w-5 h-5 mr-2" />
              LINEと連携する
            </Button>
          )}
        </CardContent>
      </Card>

      {/* 通知設定セクション */}
      <Card className="border-border/30 bg-card/80 backdrop-blur shadow-lg">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-emerald-400" />
            <CardTitle className="text-lg">通知設定</CardTitle>
          </div>
          <CardDescription>
            受け取る通知の種類を選択できます
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!lineStatus?.linked && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-sm text-amber-400">
              通知を受け取るには先にLINEと連携してください
            </div>
          )}

          <SettingRow
            label="通知を有効化"
            description="マスタースイッチ。OFFにするとすべての通知が停止します"
            checked={settings?.notification_enabled ?? false}
            disabled={!lineStatus?.linked || saving}
            onChange={(v) => handleToggle("notification_enabled", v)}
            highlight
          />
          <SettingRow
            label="🚨 価格負け検知"
            description="競合が自社価格を下回ったときに通知"
            checked={settings?.notify_price_loss ?? false}
            disabled={!lineStatus?.linked || !settings?.notification_enabled || saving}
            onChange={(v) => handleToggle("notify_price_loss", v)}
          />
          <SettingRow
            label="✅ 価格優位回復"
            description="競合が値上げして自社が安くなったときに通知"
            checked={settings?.notify_price_recovery ?? false}
            disabled={!lineStatus?.linked || !settings?.notification_enabled || saving}
            onChange={(v) => handleToggle("notify_price_recovery", v)}
          />
          <SettingRow
            label="📦 品切れ検知"
            description="競合商品が品切れになったときに通知"
            checked={settings?.notify_stock_change ?? false}
            disabled={!lineStatus?.linked || !settings?.notification_enabled || saving}
            onChange={(v) => handleToggle("notify_stock_change", v)}
          />
          <SettingRow
            label="💳 プラン変更通知"
            description="Pro加入/解約時に通知"
            checked={settings?.notify_subscription ?? false}
            disabled={!lineStatus?.linked || !settings?.notification_enabled || saving}
            onChange={(v) => handleToggle("notify_subscription", v)}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function SettingRow({
  label,
  description,
  checked,
  disabled,
  onChange,
  highlight,
}: {
  label: string;
  description: string;
  checked: boolean;
  disabled: boolean;
  onChange: (v: boolean) => void;
  highlight?: boolean;
}) {
  return (
    <div
      className={`flex items-start gap-4 p-3 rounded-lg ${
        highlight ? "bg-emerald-500/5 border border-emerald-500/20" : "border border-border/20"
      }`}
    >
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{label}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onChange} disabled={disabled} />
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center items-center min-h-[60vh]">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        </div>
      }
    >
      <SettingsContent />
    </Suspense>
  );
}
