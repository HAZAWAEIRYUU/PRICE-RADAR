"""
Price-Radar スクレイピングエンジン
Amazon / 楽天 / Yahoo Shopping / 汎用サイト対応

curl_cffi を使用してブラウザのTLSフィンガープリントを模倣し、
Amazon等のボット検出を回避する。
Playwright をフォールバックとして使用（Yahoo Shopping等のJS依存サイト向け）。
"""

import re
import json
import logging
from typing import Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger("priceradar.scraper")


# ============================================================
# ユーティリティ
# ============================================================

def extract_price_number(text: str) -> Optional[float]:
    """価格テキストから数値を抽出する。'￥18,000' → 18000.0"""
    if not text:
        return None
    # 全角数字を半角に
    text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    # カンマ・通貨記号等を除去して数値だけ取り出す
    cleaned = re.sub(r'[^\d.]', '', text)
    if cleaned:
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def extract_price_from_ld_json(soup) -> Optional[float]:
    """LD+JSON (schema.org) からProduct.offers.priceを取り出す"""
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            raw = script.string
            if not raw:
                continue
            data = json.loads(raw)
            prices = _find_prices_in_schema(data)
            if prices:
                # 0円は除外（無効データ）
                valid = [p for p in prices if p > 0]
                if valid:
                    return min(valid)  # 最安値を返す
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    return None


def _find_prices_in_schema(data, depth=0) -> list:
    """schema.org のネスト構造から再帰的に価格を探す"""
    if depth > 5:
        return []
    prices = []
    if isinstance(data, dict):
        schema_type = data.get('@type', '')
        # Product直下のoffersを探す
        if schema_type in ('Product', 'IndividualProduct'):
            offers = data.get('offers')
            if offers:
                prices.extend(_find_prices_in_schema(offers, depth + 1))
        # Offer/AggregateOffer
        elif schema_type in ('Offer', 'AggregateOffer'):
            price = data.get('price') or data.get('lowPrice')
            if price is not None:
                try:
                    p = float(price)
                    if p > 0:
                        prices.append(p)
                except (ValueError, TypeError):
                    pass
        else:
            # 再帰探索
            for v in data.values():
                if isinstance(v, (dict, list)):
                    prices.extend(_find_prices_in_schema(v, depth + 1))
    elif isinstance(data, list):
        for item in data:
            prices.extend(_find_prices_in_schema(item, depth + 1))
    return prices


# ============================================================
# HTTP クライアント
# ============================================================

async def fetch_with_curl_cffi(url: str, warmup_url: str = None, max_retries: int = 3) -> Optional[str]:
    """curl_cffi でChrome TLSフィンガープリントを模倣してHTML取得
    
    warmup_url: セッションCookieを事前取得するためのURL（Amazon等で必要）
    max_retries: 最大リトライ回数
    """
    import asyncio
    import random
    import time
    from curl_cffi import requests as cffi_requests

    # impersonation profiles をローテーション
    profiles = ['chrome', 'chrome110', 'chrome116', 'chrome120']

    def _fetch():
        for attempt in range(max_retries):
            try:
                profile = profiles[attempt % len(profiles)]
                session = cffi_requests.Session(impersonate=profile)
                headers = {
                    'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                # セッションウォームアップ（Cookie取得）
                if warmup_url:
                    try:
                        session.get(warmup_url, headers=headers, timeout=15)
                        # ウォームアップ後に短い遅延
                        time.sleep(random.uniform(0.5, 1.5))
                    except Exception as e:
                        logger.debug(f"Warmup request failed (non-fatal): {e}")
                
                resp = session.get(url, headers=headers, timeout=20)
                if resp.status_code == 200 and len(resp.text) > 5000:
                    return resp.text
                
                logger.info(f"Attempt {attempt+1}/{max_retries}: status={resp.status_code}, len={len(resp.text)} for {url}")
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {e}")
            
            # リトライ前にランダム遅延
            if attempt < max_retries - 1:
                delay = random.uniform(2.0, 5.0)
                logger.debug(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
        
        logger.warning(f"All {max_retries} attempts failed for {url}")
        return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch)


async def fetch_with_playwright(url: str) -> Optional[str]:
    """Playwright でヘッドレスブラウザによりJS描画後のHTMLを取得"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed, skipping browser fallback")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            ctx = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                locale='ja-JP',
                viewport={'width': 1920, 'height': 1080},
            )
            await ctx.add_init_script(
                'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            )
            page = await ctx.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(3000)
            html = await page.content()
            await browser.close()
            return html if len(html) > 2000 else None
    except Exception as e:
        logger.error(f"Playwright fallback failed for {url}: {e}")
        return None


# ============================================================
# サイト別スクレイパー
# ============================================================

class BaseScraper(ABC):
    """全スクレイパーの基底クラス"""

    @abstractmethod
    async def extract_price(self, soup) -> Optional[float]:
        pass

    @abstractmethod
    async def extract_stock(self, soup) -> str:
        pass

    async def fetch_html(self, url: str) -> Optional[str]:
        """HTML取得（サブクラスでオーバーライド可能）"""
        return await fetch_with_curl_cffi(url)

    async def scrape(self, url: str) -> Tuple[Optional[float], str]:
        try:
            html = await self.fetch_html(url)
            if not html:
                return None, "取得エラー"

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            price = await self.extract_price(soup)
            stock = await self.extract_stock(soup)

            return price, stock
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}")
            return None, "取得エラー"


class AmazonScraper(BaseScraper):
    """Amazon.co.jp / Amazon.com スクレイパー"""

    async def fetch_html(self, url: str) -> Optional[str]:
        """Amazon専用のフェッチ。検索ページ→商品ページの2段階セッションフローを使用"""
        import asyncio
        import random
        import time
        from curl_cffi import requests as cffi_requests

        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        ]
        profiles = ['chrome', 'chrome110', 'chrome116', 'chrome120']
        domain = 'https://www.amazon.co.jp' if 'amazon.co.jp' in url else 'https://www.amazon.com'

        def _fetch():
            for attempt in range(3):
                try:
                    profile = profiles[attempt % len(profiles)]
                    ua = user_agents[attempt % len(user_agents)]
                    session = cffi_requests.Session(impersonate=profile)
                    headers = {
                        'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'user-agent': ua,
                    }

                    # Step 1: 検索ページでCookie取得
                    search_url = f'{domain}/s?k=product'
                    try:
                        session.get(search_url, headers=headers, timeout=15)
                        time.sleep(random.uniform(1.0, 2.0))
                    except Exception:
                        pass

                    # Step 2: 商品ページ取得 (Referer付き)
                    headers['referer'] = search_url
                    resp = session.get(url, headers=headers, timeout=20)

                    if resp.status_code == 200 and len(resp.text) > 10000:
                        return resp.text

                    logger.info(f"Amazon attempt {attempt+1}/3: status={resp.status_code}, len={len(resp.text)}")
                except Exception as e:
                    logger.warning(f"Amazon attempt {attempt+1}/3 error: {e}")

                if attempt < 2:
                    delay = random.uniform(3.0, 8.0)
                    time.sleep(delay)

            logger.warning(f"All Amazon fetch attempts failed for {url}")
            return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _fetch)

    async def extract_price(self, soup) -> Optional[float]:
        # 1. CSSセレクタ（優先度順）
        selectors = [
            # Buy Box メイン価格
            '#corePrice_feature_div .a-offscreen',
            '#corePriceDisplay_desktop_feature_div .a-offscreen',
            'span.priceToPay .a-offscreen',
            '.a-price .a-offscreen',
            # 価格の数字部分
            '.a-price-whole',
            # 旧レイアウト
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '#newBuyBoxPrice',
            '#price_inside_buybox',
            # フォールバック
            '.a-color-price',
        ]
        for sel in selectors:
            els = soup.select(sel)
            if els:
                price = extract_price_number(els[0].get_text())
                if price and price > 0:
                    logger.debug(f"Amazon price via {sel}: {price}")
                    return price

        # 2. hidden input
        price_input = soup.select_one('input#attach-base-product-price')
        if price_input:
            val = price_input.get('value', '')
            price = extract_price_number(val)
            if price and price > 0:
                return price

        # 3. LD+JSON フォールバック
        price = extract_price_from_ld_json(soup)
        if price:
            return price

        return None

    async def extract_stock(self, soup) -> str:
        availability = soup.find(id="availability")
        if availability:
            text = availability.get_text().strip().lower()
            if "在庫あり" in text or "in stock" in text:
                return "在庫あり"
            if "入荷未定" in text or "currently unavailable" in text:
                return "品切れ"
            if "残り" in text:
                return "在庫わずか"
        if soup.find(id="add-to-cart-button"):
            return "在庫あり"
        if soup.find(id="buyNow_feature_div"):
            return "在庫あり"
        return "状態不明"


class RakutenScraper(BaseScraper):
    """楽天市場 (item.rakuten.co.jp) スクレイパー"""

    async def extract_price(self, soup) -> Optional[float]:
        # 1. .productPrice（商品メイン価格テキスト）
        el = soup.select_one('.productPrice')
        if el:
            price = extract_price_number(el.get_text())
            if price and price > 0:
                return price

        # 2. span.price（表示価格）
        els = soup.select('span.price')
        if els:
            price = extract_price_number(els[0].get_text())
            if price and price > 0:
                return price

        # 3. p.price（関連商品にも出るが、最初の要素を使用）
        el = soup.select_one('p.price')
        if el:
            price = extract_price_number(el.get_text())
            if price and price > 0:
                return price

        # 4. 楽天books 用 class
        el = soup.select_one('.price2')
        if el:
            price = extract_price_number(el.get_text())
            if price and price > 0:
                return price

        # 5. OGメタタグ
        meta = soup.find('meta', property='og:price:amount')
        if meta and meta.get('content'):
            price = extract_price_number(meta['content'])
            if price and price > 0:
                return price

        # 6. LD+JSON
        price = extract_price_from_ld_json(soup)
        if price:
            return price

        return None

    async def extract_stock(self, soup) -> str:
        # カートボタン存在チェック
        if soup.select_one('.cart-button-container') or soup.select_one('[data-ratid="cart_btn"]'):
            return "在庫あり"
        # 「売り切れ」テキスト
        text = soup.get_text().lower()
        if "売り切れ" in text or "sold out" in text:
            return "品切れ"
        if "品切れ" in text:
            return "品切れ"
        return "在庫あり"


class YahooShoppingScraper(BaseScraper):
    """Yahoo!ショッピング (store.shopping.yahoo.co.jp) スクレイパー"""

    async def fetch_html(self, url: str) -> Optional[str]:
        """Yahoo Shopping はJSレンダリング依存のためPlaywrightをまず試す"""
        html = await fetch_with_playwright(url)
        if html and len(html) > 5000:
            return html
        # PlaywrightがNGならcurl_cffiにフォールバック
        return await fetch_with_curl_cffi(url)

    async def extract_price(self, soup) -> Optional[float]:
        # 1. LD+JSON（最も信頼性が高い）
        price = extract_price_from_ld_json(soup)
        if price:
            return price

        # 2. CSSセレクタ
        selectors = [
            '.elPriceValue',      # 価格の数値部分
            '.elPriceText',       # 「1,180円」テキスト
            '.mdItemPrice',       # 旧レイアウト
            '#ItemPrice',         # 旧ID
        ]
        for sel in selectors:
            els = soup.select(sel)
            if els:
                price = extract_price_number(els[0].get_text())
                if price and price > 0:
                    return price

        # 3. class名に "price" を含む要素（ヒット率が高い順）
        for el in soup.find_all(attrs={'class': re.compile(r'price__\w+|Price__\w+', re.I)}):
            txt = el.get_text(strip=True)
            if re.search(r'\d', txt):
                price = extract_price_number(txt)
                if price and price > 0:
                    return price

        # 4. メタタグ
        meta = soup.find('meta', property='product:price:amount')
        if meta and meta.get('content'):
            price = extract_price_number(meta['content'])
            if price and price > 0:
                return price

        return None

    async def extract_stock(self, soup) -> str:
        text = soup.get_text().lower()
        if "売り切れ" in text or "sold out" in text or "品切れ" in text:
            return "品切れ"
        if "カートに入れる" in text or "今すぐ買う" in text:
            return "在庫あり"
        return "在庫あり"


class GenericScraper(BaseScraper):
    """その他のECサイト向け汎用スクレイパー"""

    async def extract_price(self, soup) -> Optional[float]:
        # 1. LD+JSON（schema.org）
        price = extract_price_from_ld_json(soup)
        if price:
            return price

        # 2. Open Graph / メタタグ
        for prop in ['product:price:amount', 'og:price:amount']:
            meta = soup.find('meta', property=prop)
            if meta and meta.get('content'):
                price = extract_price_number(meta['content'])
                if price and price > 0:
                    return price

        # 3. twitter:data1 (Twitter Card)
        meta = soup.find('meta', attrs={'name': 'twitter:data1'})
        if meta and meta.get('content'):
            price = extract_price_number(meta['content'])
            if price and price > 0:
                return price

        # 4. itemprop="price"
        el = soup.find(attrs={'itemprop': 'price'})
        if el:
            content = el.get('content') or el.get_text()
            price = extract_price_number(content)
            if price and price > 0:
                return price

        # 5. 一般的なCSSクラス名パターン
        for sel in ['.product-price', '.item-price', '.price', '#price',
                    '[class*="productPrice"]', '[class*="itemPrice"]']:
            els = soup.select(sel)
            if els:
                price = extract_price_number(els[0].get_text())
                if price and price > 0:
                    return price

        return None

    async def extract_stock(self, soup) -> str:
        text = soup.get_text().lower()
        keywords_out = ["out of stock", "sold out", "売り切れ", "品切れ", "入荷未定"]
        keywords_in = ["in stock", "在庫あり", "カートに入れる"]
        for kw in keywords_out:
            if kw in text:
                return "品切れ"
        for kw in keywords_in:
            if kw in text:
                return "在庫あり"
        return "在庫あり"


# ============================================================
# スクレイパーファクトリ
# ============================================================

def get_scraper(url: str) -> BaseScraper:
    """URLのドメインから最適なスクレイパーを自動選択"""
    domain = url.lower()
    if "amazon.co.jp" in domain or "amazon.com" in domain:
        return AmazonScraper()
    elif "rakuten.co.jp" in domain:
        return RakutenScraper()
    elif "shopping.yahoo.co.jp" in domain or "store.shopping.yahoo.co.jp" in domain:
        return YahooShoppingScraper()
    else:
        return GenericScraper()
