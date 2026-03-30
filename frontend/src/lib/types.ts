// Product types (matches real backend schema)
export interface Product {
  id: number;
  user_id: number;
  product_name: string;
  own_price: string; // Decimal as string from backend
  category: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  competitor_urls: CompetitorUrl[];
}

export interface CompetitorUrl {
  id: number;
  product_id: number;
  competitor_name: string;
  url: string;
  created_at: string;
}

export interface ProductCreate {
  product_name: string;
  own_price: number;
  category?: string | null;
  is_active?: boolean;
  competitor_urls?: CompetitorUrlCreate[];
}

export interface ProductUpdate {
  product_name?: string | null;
  own_price?: number | null;
  category?: string | null;
  is_active?: boolean | null;
}

export interface CompetitorUrlCreate {
  competitor_name: string;
  url: string;
}

// Price types
export interface PriceHistoryRecord {
  id: number;
  competitor_url_id: number;
  price: string; // Decimal as string
  stock_status: string;
  scraped_at: string;
  created_at: string;
}

// Dashboard types
export interface PriceAlertItem {
  product_id: number;
  product_name: string;
  own_price: string;
  competitor_name: string;
  competitor_price: string;
  price_diff: string;
  stock_status: string;
}

export interface PriceComparisonItem {
  product_id: number;
  product_name: string;
  own_price: string;
  category: string | null;
  competitors: Record<string, unknown>[];
}

export interface ProductCount {
  count: number;
}

// SaaS User types
export interface UserProfile {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
  plan: "free" | "pro" | "enterprise";
  created_at: string;
}

// Plan types
export interface PlanUsage {
  current_products: number;
  max_products: number | null;
  max_competitors_per_product: number | null;
  history_retention_days: number | null;
}

export interface PlanInfo {
  plan: string;
  label: string;
  price: number | null;
  usage: PlanUsage;
}

