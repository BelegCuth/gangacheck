import sys
import re
import json
import time
from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import quote_plus

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests as cffi_requests
    HAS_CURL_CFFI = False

from database import save_raw_listing, get_raw_listings, get_market_intelligence_stats

# Palabras clave sospechosas de productos rotos, incompletos o señuelo
NOISE_KEYWORDS = [
    "para piezas", "despiece", "caja vacia", "caja vacía", "solo caja",
    "roto", "rota", "averiado", "averiada", "no funciona", "no enciende",
    "bloqueado", "bloqueada", "icloud", "para reparar", "defectuoso",
    "defectuosa", "pantalla rota", "se busca", "compro", "cambio por"
]

class MarketHarvester:
    """
    Motor de inteligencia y recolección masiva de anuncios reales en mercados de segunda mano.
    Rastrea Vinted y Wallapop, limpia precios trampa y calcula la mediana real.
    """

    VINTED_BASE = "https://www.vinted.es"
    VINTED_API = "https://www.vinted.es/api/v2/catalog/items"

    WALLAPOP_SEARCH_API = "https://api.wallapop.com/api/v3/search"
    WALLAPOP_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9",
        "Origin": "https://es.wallapop.com",
        "Referer": "https://es.wallapop.com/"
    }

    @classmethod
    def fetch_vinted(cls, keyword: str, limit: int = 40) -> List[Dict[str, Any]]:
        """
        Consulta la API pública de Vinted para obtener anuncios reales con fotos y precio.
        """
        listings = []
        try:
            session = cffi_requests.Session(impersonate="chrome120") if HAS_CURL_CFFI else cffi_requests.Session()
            # 1. Obtener cookies de sesión de Vinted
            session.get(
                cls.VINTED_BASE,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0"},
                timeout=8
            )

            # 2. Consultar catálogo
            params = {
                "search_text": keyword,
                "per_page": min(limit, 60),
                "order": "newest_first"
            }
            resp = session.get(cls.VINTED_API, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                for it in items:
                    price_val = 0.0
                    p_obj = it.get("price")
                    if isinstance(p_obj, dict):
                        price_val = float(p_obj.get("amount", 0.0))
                    elif isinstance(p_obj, (int, float, str)):
                        try:
                            price_val = float(p_obj)
                        except ValueError:
                            price_val = 0.0

                    photo_obj = it.get("photo") or {}
                    image_url = photo_obj.get("url") or photo_obj.get("full_size_url") or ""

                    user_obj = it.get("user") or {}
                    seller_name = user_obj.get("login") or "Vendedor Vinted"
                    seller_reviews = int(user_obj.get("feedback_count", 0) or user_obj.get("feedback_reputation", 0) or 0)

                    item_url = it.get("url")
                    if not item_url:
                        item_url = f"https://www.vinted.es/items/{it.get('id')}"

                    listings.append({
                        "id": f"vinted_{it.get('id')}",
                        "platform": "vinted",
                        "title": it.get("title", keyword).strip(),
                        "price": price_val,
                        "keyword": keyword,
                        "seller_name": seller_name,
                        "seller_reviews": seller_reviews,
                        "has_shipping": True,
                        "url": item_url,
                        "image_url": image_url
                    })
                print(f"[Harvester] Vinted: {len(listings)} anuncios obtenidos para '{keyword}'.")
        except Exception as e:
            print(f"[Harvester] Error al consultar Vinted para '{keyword}': {e}")

        return listings

    @classmethod
    def fetch_wallapop(cls, keyword: str, limit: int = 40) -> List[Dict[str, Any]]:
        """
        Consulta Wallapop para obtener anuncios más recientes.
        """
        listings = []
        try:
            session = cffi_requests.Session(impersonate="chrome120") if HAS_CURL_CFFI else cffi_requests.Session()
            params = {
                "keywords": keyword,
                "order_by": "date_newest",
                "latitude": "40.416775",
                "longitude": "-3.703790"
            }
            resp = session.get(cls.WALLAPOP_SEARCH_API, headers=cls.WALLAPOP_HEADERS, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for obj in data.get("search_objects", [])[:limit]:
                    slug = obj.get("web_slug") or obj.get("id")
                    img = obj.get("images", [])
                    img_url = img[0].get("original", "") if (img and isinstance(img[0], dict)) else ""

                    listings.append({
                        "id": f"wallapop_{obj.get('id')}",
                        "platform": "wallapop",
                        "title": obj.get("title", keyword).strip(),
                        "price": float(obj.get("price", 0.0)),
                        "keyword": keyword,
                        "seller_name": obj.get("user", {}).get("micro_name", "Vendedor Wallapop"),
                        "seller_reviews": int(obj.get("user", {}).get("reviews", 0) or 0),
                        "has_shipping": bool(obj.get("shipping", {}).get("user_allows_shipping", True)),
                        "url": f"https://es.wallapop.com/item/{slug}",
                        "image_url": img_url
                    })
                print(f"[Harvester] Wallapop: {len(listings)} anuncios obtenidos para '{keyword}'.")
        except Exception as e:
            print(f"[Harvester] Error al consultar Wallapop para '{keyword}': {e}")

        return listings

    @classmethod
    def filter_noise_and_outliers(cls, listings: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Elimina anuncios trampa (0€, 1€, precios simbólicos), descarta piezas rotas y filtra valores extremos.
        """
        valid = []
        noise_count = 0

        for item in listings:
            price = float(item.get("price", 0.0))
            title_lower = item.get("title", "").lower()

            # 1. Filtro de precio absurdo o gratuito
            if price < 5.0 or price > 20000.0:
                noise_count += 1
                continue

            # 2. Filtro de palabras clave trampa o rotos
            is_noise = False
            for noise_kw in NOISE_KEYWORDS:
                if noise_kw in title_lower:
                    is_noise = True
                    break

            if is_noise:
                noise_count += 1
                continue

            valid.append(item)

        # 3. Filtro IQR (rango intercuartílico) si hay suficientes muestras
        if len(valid) >= 6:
            sorted_by_price = sorted(valid, key=lambda x: x["price"])
            n = len(sorted_by_price)
            q1 = sorted_by_price[int(n * 0.25)]["price"]
            q3 = sorted_by_price[int(n * 0.75)]["price"]
            iqr = q3 - q1
            
            # Límites razonables para evitar precios troll
            lower_bound = max(5.0, q1 - 1.5 * iqr)
            upper_bound = q3 + 2.0 * iqr

            filtered_iqr = []
            for it in valid:
                if lower_bound <= it["price"] <= upper_bound:
                    filtered_iqr.append(it)
                else:
                    noise_count += 1
            valid = filtered_iqr

        return valid, noise_count

    @classmethod
    def calculate_market_metrics(cls, valid_listings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula la mediana real, precio mínimo y máximo razonable de mercado.
        """
        if not valid_listings:
            return {
                "total_valid": 0,
                "median_price": 0.0,
                "min_normal_price": 0.0,
                "max_normal_price": 0.0,
                "average_price": 0.0,
                "best_deal_price": 0.0,
                "best_deal_title": "",
                "best_deal_url": ""
            }

        prices = sorted([it["price"] for it in valid_listings])
        n = len(prices)
        median = prices[n // 2] if n % 2 != 0 else (prices[n // 2 - 1] + prices[n // 2]) / 2.0

        p15 = prices[int(n * 0.15)]
        p85 = prices[int(n * 0.85)]
        avg = sum(prices) / n

        # Mejor oferta real
        best = min(valid_listings, key=lambda x: x["price"])

        return {
            "total_valid": n,
            "median_price": round(float(median), 2),
            "min_normal_price": round(float(p15), 2),
            "max_normal_price": round(float(p85), 2),
            "average_price": round(float(avg), 2),
            "best_deal_price": round(float(best["price"]), 2),
            "best_deal_title": best.get("title", ""),
            "best_deal_url": best.get("url", "")
        }

    @classmethod
    def harvest_and_save(cls, keyword: str, platform: str = "all", limit: int = 40) -> Dict[str, Any]:
        """
        Flujo completo: rastreo en vivo, limpieza de ruido, cálculo estadístico y guardado en BBDD.
        """
        raw_results = []
        kw_clean = keyword.strip()

        if platform in ("vinted", "all"):
            raw_results.extend(cls.fetch_vinted(kw_clean, limit=limit))

        if platform in ("wallapop", "all"):
            raw_results.extend(cls.fetch_wallapop(kw_clean, limit=limit))

        # Filtrar ruido
        valid_listings, noise_count = cls.filter_noise_and_outliers(raw_results)

        # Guardar en Base de Datos (SQLite / Supabase)
        saved_count = 0
        for item in valid_listings:
            try:
                save_raw_listing(item)
                saved_count += 1
            except Exception as e:
                print(f"[Harvester] Error guardando listing: {e}")

        # Métricas calculadas
        metrics = cls.calculate_market_metrics(valid_listings)

        return {
            "success": True,
            "keyword": kw_clean,
            "platform": platform,
            "total_extracted": len(raw_results),
            "noise_discarded": noise_count,
            "saved_count": saved_count,
            "metrics": metrics,
            "listings": valid_listings
        }
