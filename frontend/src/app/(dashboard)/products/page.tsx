"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import axios from "axios";
import { toast } from "sonner";
import { Product, ProductCreate, CompetitorUrlCreate, ProductUpdate } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import {
  Plus,
  Pencil,
  Trash2,
  Search,
  Link2,
  ExternalLink,
  Loader2,
  Package,
  X,
  Crown,
  AlertTriangle,
} from "lucide-react";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [saving, setSaving] = useState(false);
  const [planLimitError, setPlanLimitError] = useState<string | null>(null);
  const router = useRouter();

  // Form state
  const [formName, setFormName] = useState("");
  const [formCategory, setFormCategory] = useState("");
  const [formPrice, setFormPrice] = useState("");
  const [formUrls, setFormUrls] = useState<CompetitorUrlCreate[]>([
    { competitor_name: "", url: "" },
  ]);

  const fetchProducts = useCallback(async () => {
    try {
      const res = await api.get("/api/products");
      setProducts(res.data);
    } catch (err) {
      console.error("Failed to fetch products:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const resetForm = () => {
    setFormName("");
    setFormCategory("");
    setFormPrice("");
    setFormUrls([{ competitor_name: "", url: "" }]);
    setEditingProduct(null);
  };

  const openCreateDialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const openEditDialog = (product: Product) => {
    setEditingProduct(product);
    setFormName(product.product_name);
    setFormCategory(product.category || "");
    setFormPrice(parseFloat(product.own_price).toString());
    
    // Check if the backend gave us competitor_urls
    if (product.competitor_urls && product.competitor_urls.length > 0) {
      setFormUrls(
        product.competitor_urls.map((u) => ({
          competitor_name: u.competitor_name,
          url: u.url,
        }))
      );
    } else {
      setFormUrls([{ competitor_name: "", url: "" }]);
    }
    
    setDialogOpen(true);
  };

  const addUrlRow = () => {
    setFormUrls([...formUrls, { competitor_name: "", url: "" }]);
  };

  const removeUrlRow = (index: number) => {
    setFormUrls(formUrls.filter((_, i) => i !== index));
  };

  const updateUrlRow = (
    index: number,
    field: keyof CompetitorUrlCreate,
    value: string
  ) => {
    const updated = [...formUrls];
    updated[index] = { ...updated[index], [field]: value };
    setFormUrls(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    const validUrls = formUrls.filter((u) => u.competitor_name && u.url);

    try {
      if (editingProduct) {
        const updateData: ProductUpdate = {
          product_name: formName,
          own_price: parseFloat(formPrice),
          category: formCategory || null,
        };
        await api.put(`/api/products/${editingProduct.id}`, updateData);
        // Add new URLs concurrently (avoiding N+1 sequentially)
        const results = await Promise.allSettled(
          validUrls.map((url) =>
            api.post(`/api/products/${editingProduct.id}/competitors`, url)
          )
        );
        const failedCount = results.filter((r) => r.status === "rejected").length;
        if (failedCount > 0) {
          toast.warning("一部のURL追加に失敗", {
            description: `${failedCount}件の競合URLが追加できませんでした（登録済み、または制限超過）。`
          });
        }
      } else {
        const productData: ProductCreate = {
          product_name: formName,
          own_price: parseFloat(formPrice),
          category: formCategory || null,
          is_active: true,
          competitor_urls: validUrls
        };
        await api.post("/api/products", productData);
      }
      setDialogOpen(false);
      resetForm();
      setPlanLimitError(null);
      fetchProducts();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 403) {
          setPlanLimitError(err.response.data?.detail || "プラン制限に達しました");
          setDialogOpen(false);
        } else {
          toast.error("処理エラー", {
            description: err.response?.data?.detail || err.message
          });
        }
      } else {
        console.error("Failed to save product:", err);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingProduct) return;
    setSaving(true);
    try {
      await api.delete(`/api/products/${deletingProduct.id}`);
      setDeleteDialogOpen(false);
      setDeletingProduct(null);
      fetchProducts();
    } catch (err) {
      console.error("Failed to delete product:", err);
    } finally {
      setSaving(false);
    }
  };

  const filteredProducts = products.filter(
    (p) =>
      p.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.category && p.category.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-36 bg-muted rounded" />
        <div className="h-12 bg-muted/50 rounded-lg" />
        <div className="h-96 bg-muted rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">商品管理</h1>
          <p className="text-muted-foreground mt-1">
            商品マスタと競合URLの管理
          </p>
        </div>
        <Button
          onClick={openCreateDialog}
          className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white shadow-lg shadow-emerald-500/20"
        >
          <Plus className="w-4 h-4 mr-2" />
          商品追加
        </Button>
      </div>

      {/* Plan Limit Error Banner */}
      {planLimitError && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-orange-500/10 to-amber-500/10 border border-orange-500/20 animate-in fade-in slide-in-from-top-2 duration-300">
          <AlertTriangle className="w-5 h-5 text-orange-400 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-orange-400">{planLimitError}</p>
          </div>
          <Button
            size="sm"
            onClick={() => router.push("/pricing")}
            className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white text-xs shrink-0"
          >
            <Crown className="w-3 h-3 mr-1" />
            アップグレード
          </Button>
          <button
            onClick={() => setPlanLimitError(null)}
            className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="商品名またはカテゴリで検索..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10 h-11 bg-card/80 border-border/30"
        />
      </div>

      {/* Products Table */}
      <Card className="border-border/30 bg-card/80 backdrop-blur shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Package className="w-5 h-5 text-emerald-400" />
            商品一覧
            <Badge variant="secondary" className="ml-2">
              {filteredProducts.length}件
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredProducts.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <Package className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg font-medium mb-1">商品がありません</p>
              <p className="text-sm">
                「商品追加」ボタンから最初の商品を追加しましょう
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-border/30 hover:bg-transparent">
                    <TableHead>商品名</TableHead>
                    <TableHead>カテゴリ</TableHead>
                    <TableHead className="text-right">自社価格</TableHead>
                    <TableHead className="text-center">競合URL数</TableHead>
                    <TableHead className="text-right">アクション</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProducts.map((product) => (
                    <TableRow
                      key={product.id}
                      className="border-border/20 hover:bg-accent/30 transition-colors"
                    >
                      <TableCell className="font-medium">
                        <Link
                          href={`/prices?id=${product.id}`}
                          className="hover:text-emerald-400 transition-colors"
                        >
                          {product.product_name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {product.category || "-"}
                      </TableCell>
                      <TableCell className="text-right tabular-nums font-medium">
                        ¥{parseFloat(product.own_price).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge
                          variant="secondary"
                          className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                        >
                          <Link2 className="w-3 h-3 mr-1" />
                          {product.competitor_urls?.length || 0}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Link
                            href={`/prices?id=${product.id}`}
                            className="p-2 rounded-lg text-muted-foreground hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </Link>
                          <button
                            onClick={() => openEditDialog(product)}
                            className="p-2 rounded-lg text-muted-foreground hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              setDeletingProduct(product);
                              setDeleteDialogOpen(true);
                            }}
                            className="p-2 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) resetForm();
        }}
      >
        <DialogContent className="sm:max-w-lg bg-card border-border/50">
          <DialogHeader>
            <DialogTitle>
              {editingProduct ? "商品を編集" : "商品を追加"}
            </DialogTitle>
            <DialogDescription>
              {editingProduct
                ? "商品情報を編集してください"
                : "新しい商品と競合URLを登録してください"}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">商品名</Label>
              <Input
                id="name"
                placeholder="例: ワイヤレスイヤホン A100"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
                className="bg-background/50 border-border/50"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="category">カテゴリ</Label>
                <Input
                  id="category"
                  placeholder="例: 家電"
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                  className="bg-background/50 border-border/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="price">自社価格 (¥)</Label>
                <Input
                  id="price"
                  type="number"
                  placeholder="3980"
                  value={formPrice}
                  onChange={(e) => setFormPrice(e.target.value)}
                  required
                  className="bg-background/50 border-border/50 tabular-nums"
                />
              </div>
            </div>

            {/* Competitor URLs */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>競合URL</Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={addUrlRow}
                  className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  追加
                </Button>
              </div>
              {formUrls.map((urlRow, index) => (
                <div key={index} className="flex gap-2 items-start">
                  <Input
                    placeholder="競合名"
                    value={urlRow.competitor_name}
                    onChange={(e) =>
                      updateUrlRow(index, "competitor_name", e.target.value)
                    }
                    className="w-32 bg-background/50 border-border/50 text-sm"
                  />
                  <Input
                    placeholder="https://..."
                    value={urlRow.url}
                    onChange={(e) =>
                      updateUrlRow(index, "url", e.target.value)
                    }
                    className="flex-1 bg-background/50 border-border/50 text-sm"
                  />
                  {formUrls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeUrlRow(index)}
                      className="p-2 text-muted-foreground hover:text-red-400 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setDialogOpen(false)}
              >
                キャンセル
              </Button>
              <Button
                type="submit"
                disabled={saving}
                className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    保存中...
                  </>
                ) : editingProduct ? (
                  "更新"
                ) : (
                  "追加"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="sm:max-w-md bg-card border-border/50">
          <DialogHeader>
            <DialogTitle>商品を削除</DialogTitle>
            <DialogDescription>
              「{deletingProduct?.product_name}」を削除してもよろしいですか？
              この操作は取り消せません。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setDeleteDialogOpen(false)}
            >
              キャンセル
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={saving}
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  削除中...
                </>
              ) : (
                "削除"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
