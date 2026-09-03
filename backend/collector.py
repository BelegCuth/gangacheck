import time
import json
from typing import List, Dict, Any
from urllib.parse import quote_plus
from config import BASE_DIR
from database import init_db, save_raw_listing

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests as cffi_requests
    HAS_CURL_CFFI = False

DEFAULT_KEYWORDS = [
    "playstation 5",
    "iphone 13",
    "iphone 14",
    "nintendo switch oled",
    "steam deck",
    "rtx 4070"
]

class WallapopCollector:
    """
    Rastreador en segundo plano para poblar la base de datos con anuncios reales.
    Permite construir el histórico de precios para alimentar a GangaCheck.
    """
    
    SEARCH_URL = "https://api.wallapop.com/api/v3/search"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9",
        "Origin": "https://es.wallapop.com",
        "Referer": "https://es.wallapop.com/"
    }

    @classmethod
    def fetch_keyword(cls, keyword: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Busca los anuncios más recientes de una palabra clave."""
        params = {
            "keywords": keyword,
            "order_by": "date_newest",
            "latitude": "40.416775",
            "longitude": "-3.703790"
        }
        
        items = []
        try:
            if HAS_CURL_CFFI:
                session = cffi_requests.Session(impersonate="chrome120")
                resp = session.get(cls.SEARCH_URL, headers=cls.HEADERS, params=params, timeout=10)
            else:
                resp = cffi_requests.get(cls.SEARCH_URL, headers=cls.HEADERS, params=params, timeout=10)
                
            if resp.status_code == 200:
                data = resp.json()
                search_objects = data.get("search_objects", [])
                for obj in search_objects[:limit]:
                    items.append({
                        "id": str(obj.get("id")),
                        "platform": "wallapop",
                        "title": obj.get("title", ""),
                        "price": float(obj.get("price", 0.0)),
                        "keyword": keyword,
                        "seller_name": obj.get("user", {}).get("micro_name", "Vendedor"),
                        "seller_reviews": int(obj.get("user", {}).get("reviews", 0) or 0),
                        "has_shipping": bool(obj.get("shipping", {}).get("user_allows_shipping", True)),
                        "url": f"https://es.wallapop.com/item/{obj.get('web_slug', obj.get('id'))}"
                    })
                print(f"[Collector] '{keyword}': {len(items)} anuncios obtenidos con éxito.")
            else:
                print(f"[Collector] Respuesta {resp.status_code} al buscar '{keyword}'.")
        except Exception as e:
            print(f"[Collector] Aviso al consultar '{keyword}': {e}")
            
        return items

def run_collection(keywords: List[str] = DEFAULT_KEYWORDS):
    """Ejecuta una ronda de recolección y almacena los datos en la base de datos."""
    init_db()
    print(f"🚀 Iniciando recolección de datos para {len(keywords)} categorías...")
    total_saved = 0
    
    for kw in keywords:
        items = WallapopCollector.fetch_keyword(kw)
        for item in items:
            save_raw_listing(item)
            total_saved += 1
        time.sleep(2) # Pausa preventiva para ser respetuoso con la red
        
    print(f"✅ Recolección finalizada: {total_saved} anuncios guardados en la base de datos.")

if __name__ == "__main__":
    run_collection()
