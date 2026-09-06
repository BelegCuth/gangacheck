import re
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import DB_PATH, IS_CLOUD_DB, SUPABASE_URL, SUPABASE_KEY

# Cliente de Supabase para cuando se configuran las credenciales en .env
supabase_client = None
if IS_CLOUD_DB:
    try:
        from supabase import create_client, Client
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[Database] Conectado exitosamente a Supabase Cloud ({SUPABASE_URL})")
    except Exception as e:
        print(f"[Database] Error al conectar con Supabase: {e}. Usando SQLite local.")
        supabase_client = None

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

DEFAULT_BENCHMARKS = [
    # Consolas y Gaming
    ("ps5_disc", "PlayStation 5 (Con Lector)", 380.0, 320.0, 430.0, "Consolas"),
    ("ps5_digital", "PlayStation 5 Digital", 330.0, 280.0, 370.0, "Consolas"),
    ("ps5_slim", "PlayStation 5 Slim 1TB", 410.0, 360.0, 460.0, "Consolas"),
    ("ps5_pro", "PlayStation 5 Pro 2TB", 680.0, 600.0, 750.0, "Consolas"),
    ("ps4_pro", "PlayStation 4 Pro 1TB", 140.0, 110.0, 170.0, "Consolas"),
    ("ps4_slim", "PlayStation 4 Slim 500GB", 100.0, 80.0, 130.0, "Consolas"),
    ("switch_oled", "Nintendo Switch OLED", 230.0, 190.0, 270.0, "Consolas"),
    ("switch_v2", "Nintendo Switch V2", 160.0, 130.0, 190.0, "Consolas"),
    ("switch_lite", "Nintendo Switch Lite", 110.0, 90.0, 135.0, "Consolas"),
    ("xbox_series_x", "Xbox Series X 1TB", 360.0, 300.0, 410.0, "Consolas"),
    ("xbox_series_s", "Xbox Series S 512GB", 175.0, 140.0, 210.0, "Consolas"),
    ("steam_deck_512", "Steam Deck 512GB", 320.0, 270.0, 380.0, "Consolas"),
    ("steam_deck_oled", "Steam Deck OLED 512GB", 440.0, 390.0, 500.0, "Consolas"),
    ("asus_rog_ally", "ASUS ROG Ally Z1 Extreme", 420.0, 360.0, 480.0, "Consolas"),
    
    # Smartphones & Tablets
    ("iphone_11_128", "Apple iPhone 11 128GB", 220.0, 180.0, 260.0, "Móviles"),
    ("iphone_12_128", "Apple iPhone 12 128GB", 280.0, 230.0, 330.0, "Móviles"),
    ("iphone_13_128", "Apple iPhone 13 128GB", 360.0, 300.0, 420.0, "Móviles"),
    ("iphone_13_pro", "Apple iPhone 13 Pro 128GB", 460.0, 400.0, 520.0, "Móviles"),
    ("iphone_14_128", "Apple iPhone 14 128GB", 460.0, 400.0, 520.0, "Móviles"),
    ("iphone_14_pro", "Apple iPhone 14 Pro 128GB", 590.0, 520.0, 670.0, "Móviles"),
    ("iphone_15_128", "Apple iPhone 15 128GB", 580.0, 510.0, 650.0, "Móviles"),
    ("iphone_15_pro", "Apple iPhone 15 Pro 128GB", 740.0, 670.0, 820.0, "Móviles"),
    ("iphone_15_promax", "Apple iPhone 15 Pro Max 256GB", 860.0, 780.0, 950.0, "Móviles"),
    ("iphone_16_128", "Apple iPhone 16 128GB", 790.0, 720.0, 860.0, "Móviles"),
    ("iphone_16_pro", "Apple iPhone 16 Pro 128GB", 990.0, 910.0, 1080.0, "Móviles"),
    ("iphone_16_promax", "Apple iPhone 16 Pro Max 256GB", 1190.0, 1090.0, 1290.0, "Móviles"),
    ("iphone_se_3", "Apple iPhone SE (2022 / 3ª Gen)", 220.0, 180.0, 260.0, "Móviles"),
    ("samsung_s23", "Samsung Galaxy S23 128GB", 390.0, 330.0, 450.0, "Móviles"),
    ("samsung_s24", "Samsung Galaxy S24 256GB", 520.0, 450.0, 590.0, "Móviles"),
    ("samsung_s24_ultra", "Samsung Galaxy S24 Ultra 256GB", 790.0, 700.0, 890.0, "Móviles"),
    ("samsung_s25", "Samsung Galaxy S25 256GB", 690.0, 610.0, 780.0, "Móviles"),
    ("samsung_s25_plus", "Samsung Galaxy S25+ 256GB", 820.0, 730.0, 920.0, "Móviles"),
    ("samsung_s25_ultra", "Samsung Galaxy S25 Ultra 256GB", 1050.0, 950.0, 1200.0, "Móviles"),
    ("ipad_air_m1", "Apple iPad Air M1 (5ª Gen)", 420.0, 360.0, 480.0, "Tablets"),
    ("ipad_pro_11_m2", "Apple iPad Pro 11 M2", 640.0, 560.0, 720.0, "Tablets"),

    # Informática y Portátiles
    ("macbook_air_m1", "Apple MacBook Air M1 256GB", 490.0, 430.0, 560.0, "Portátiles"),
    ("macbook_air_m2", "Apple MacBook Air M2 256GB", 680.0, 600.0, 760.0, "Portátiles"),
    ("macbook_pro_m1", "Apple MacBook Pro 14 M1 Pro", 950.0, 850.0, 1100.0, "Portátiles"),
    ("rtx_4060", "Tarjeta Gráfica RTX 4060 8GB", 250.0, 220.0, 290.0, "Informática"),
    ("rtx_4070", "Tarjeta Gráfica RTX 4070 12GB", 480.0, 420.0, 550.0, "Informática"),
    ("rtx_4080", "Tarjeta Gráfica RTX 4080 16GB", 830.0, 740.0, 930.0, "Informática"),
    ("rtx_3060", "Tarjeta Gráfica RTX 3060 12GB", 190.0, 160.0, 225.0, "Informática"),

    # Audio y Fotografía
    ("airpods_pro_2", "Apple AirPods Pro 2", 150.0, 120.0, 180.0, "Audio"),
    ("airpods_max", "Apple AirPods Max", 340.0, 290.0, 395.0, "Audio"),
    ("sony_wh1000xm5", "Auriculares Sony WH-1000XM5", 220.0, 180.0, 260.0, "Audio"),
    ("sony_wh1000xm4", "Auriculares Sony WH-1000XM4", 145.0, 120.0, 175.0, "Audio"),
    ("sony_a7_iii", "Cámara Sony Alpha A7 III Cuerpo", 890.0, 790.0, 1000.0, "Fotografía"),

    # Moda y Sneakers (Vinted)
    ("nike_dunk_panda", "Nike Dunk Low Retro Panda", 85.0, 65.0, 110.0, "Moda"),
    ("air_jordan_1", "Air Jordan 1 Retro High OG", 130.0, 100.0, 170.0, "Moda"),
    ("tnf_nuptse_1996", "The North Face Nuptse 1996", 160.0, 130.0, 210.0, "Moda"),

    # Herramientas y Bricolaje (Milanuncios)
    ("dewalt_xr_18v", "Taladro Percutor DeWalt XR 18V", 95.0, 75.0, 125.0, "Herramientas"),
    ("dewalt_amoladora_18v", "Amoladora DeWalt 18V Brushless", 105.0, 85.0, 135.0, "Herramientas"),
    ("cortacesped_john_deere", "Tractor Cortacésped John Deere", 1350.0, 1100.0, 1700.0, "Maquinaria")
]

def init_db():
    """Inicializa la base de datos local (SQLite) con tablas e índices optimizados."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de análisis guardados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            item_id TEXT,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            normalized_product TEXT,
            score REAL NOT NULL,
            verdict TEXT NOT NULL,
            market_price REAL,
            savings REAL,
            savings_pct REAL,
            risk_level TEXT,
            seller_rating REAL,
            seller_reviews INTEGER,
            has_shipping BOOLEAN,
            details_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Índices para acelerar búsquedas de caché, historial y ordenaciones
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_url ON scans(url)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_score ON scans(score DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_platform ON scans(platform)")
    
    # Tabla de productos recolectados para histórico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_listings (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            keyword TEXT,
            seller_name TEXT,
            seller_reviews INTEGER,
            has_shipping BOOLEAN,
            url TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE raw_listings ADD COLUMN image_url TEXT")
    except Exception:
        pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_keyword ON raw_listings(keyword)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_created_at ON raw_listings(created_at DESC)")
    
    # Tabla de benchmarks de referencia
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_benchmarks (
            product_key TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            median_price REAL NOT NULL,
            min_normal_price REAL NOT NULL,
            max_normal_price REAL NOT NULL,
            category TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_benchmarks_cat ON market_benchmarks(category)")
    
    # Insertar o actualizar benchmarks iniciales en SQLite
    cursor.executemany("""
        INSERT OR REPLACE INTO market_benchmarks 
        (product_key, display_name, median_price, min_normal_price, max_normal_price, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, DEFAULT_BENCHMARKS)
    
    conn.commit()
    conn.close()

    # Si Supabase está conectado, asegurar que todos los benchmarks estén actualizados
    if supabase_client:
        try:
            for bm in DEFAULT_BENCHMARKS:
                supabase_client.table("market_benchmarks").upsert({
                    "product_key": bm[0],
                    "display_name": bm[1],
                    "median_price": bm[2],
                    "min_normal_price": bm[3],
                    "max_normal_price": bm[4],
                    "category": bm[5]
                }).execute()
            print("[Database] Benchmarks sincronizados con Supabase Cloud.")
        except Exception as e:
            print(f"[Supabase Sync] Aviso: {e}")



def save_scan(data: Dict[str, Any]) -> int:
    """Guarda un análisis en Supabase (si está configurado) o en SQLite."""
    # 1. Si Supabase está activo
    if supabase_client:
        try:
            record = {
                "platform": data.get("platform", "wallapop"),
                "item_id": data.get("item_id", ""),
                "url": data.get("url", ""),
                "title": data.get("title", ""),
                "price": float(data.get("price", 0.0)),
                "normalized_product": data.get("normalized_product", ""),
                "score": float(data.get("score", 0.0)),
                "verdict": data.get("verdict", ""),
                "market_price": float(data.get("market_price", 0.0)),
                "savings": float(data.get("savings", 0.0)),
                "savings_pct": float(data.get("savings_pct", 0.0)),
                "risk_level": data.get("risk_level", "NORMAL"),
                "seller_rating": float(data.get("seller_rating", 0.0)),
                "seller_reviews": int(data.get("seller_reviews", 0)),
                "has_shipping": bool(data.get("has_shipping", True)),
                "details_json": json.dumps(data.get("details", {}), ensure_ascii=False)
            }
            res = supabase_client.table("scans").insert(record).execute()
            if res.data and len(res.data) > 0:
                return res.data[0].get("id", 1)
        except Exception as e:
            print(f"[Supabase] Error al guardar escaneo: {e}. Guardando en SQLite local.")

    # 2. Fallback o modo local: SQLite
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scans (
            platform, item_id, url, title, price, normalized_product, 
            score, verdict, market_price, savings, savings_pct, 
            risk_level, seller_rating, seller_reviews, has_shipping, details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("platform", "wallapop"),
        data.get("item_id", ""),
        data.get("url", ""),
        data.get("title", ""),
        float(data.get("price", 0.0)),
        data.get("normalized_product", ""),
        float(data.get("score", 0.0)),
        data.get("verdict", ""),
        float(data.get("market_price", 0.0)),
        float(data.get("savings", 0.0)),
        float(data.get("savings_pct", 0.0)),
        data.get("risk_level", "NORMAL"),
        float(data.get("seller_rating", 0.0)),
        int(data.get("seller_reviews", 0)),
        bool(data.get("has_shipping", True)),
        json.dumps(data.get("details", {}), ensure_ascii=False)
    ))
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scan_id

def save_raw_listing(item: Dict[str, Any]):
    """Guarda un anuncio en crudo para engordar el histórico de datos."""
    img_url = item.get("image_url") or item.get("image") or ""
    payload = {
        "id": str(item.get("id")),
        "platform": item.get("platform", "wallapop"),
        "title": item.get("title", ""),
        "price": float(item.get("price", 0.0)),
        "keyword": item.get("keyword", ""),
        "seller_name": item.get("seller_name", ""),
        "seller_reviews": int(item.get("seller_reviews", 0)),
        "has_shipping": bool(item.get("has_shipping", True)),
        "url": item.get("url", "")
    }
    if supabase_client:
        try:
            supabase_client.table("raw_listings").upsert(payload).execute()
            return
        except Exception as e:
            print(f"[Supabase] Error en upsert raw_listing: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE raw_listings ADD COLUMN image_url TEXT")
    except Exception:
        pass

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO raw_listings 
            (id, platform, title, price, keyword, seller_name, seller_reviews, has_shipping, url, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(item.get("id")),
            item.get("platform", "wallapop"),
            item.get("title", ""),
            float(item.get("price", 0.0)),
            item.get("keyword", ""),
            item.get("seller_name", ""),
            int(item.get("seller_reviews", 0)),
            bool(item.get("has_shipping", True)),
            item.get("url", ""),
            img_url
        ))
    except Exception:
        cursor.execute("""
            INSERT OR REPLACE INTO raw_listings 
            (id, platform, title, price, keyword, seller_name, seller_reviews, has_shipping, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(item.get("id")),
            item.get("platform", "wallapop"),
            item.get("title", ""),
            float(item.get("price", 0.0)),
            item.get("keyword", ""),
            item.get("seller_name", ""),
            int(item.get("seller_reviews", 0)),
            bool(item.get("has_shipping", True)),
            item.get("url", "")
        ))
    conn.commit()
    conn.close()

def get_raw_listings(keyword: Optional[str] = None, platform: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Obtiene anuncios en bruto recolectados del mercado con filtros opcionales."""
    if supabase_client:
        try:
            query = supabase_client.table("raw_listings").select("*").order("created_at", desc=True).limit(limit)
            if keyword and keyword.strip():
                query = query.ilike("title", f"%{keyword.strip()}%")
            if platform and platform != "all":
                query = query.eq("platform", platform)
            res = query.execute()
            return res.data or []
        except Exception as e:
            print(f"[Supabase] Error al consultar raw_listings: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT id, platform, title, price, keyword, seller_name, seller_reviews, has_shipping, url, image_url, created_at FROM raw_listings WHERE 1=1"
    params = []
    if keyword and keyword.strip():
        query += " AND (title LIKE ? OR keyword LIKE ?)"
        params.extend([f"%{keyword.strip()}%", f"%{keyword.strip()}%"])
    if platform and platform != "all":
        query += " AND platform = ?"
        params.append(platform)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "platform": r["platform"],
            "title": r["title"],
            "price": r["price"],
            "keyword": r["keyword"],
            "seller_name": r["seller_name"],
            "seller_reviews": r["seller_reviews"],
            "has_shipping": bool(r["has_shipping"]),
            "url": r["url"],
            "image_url": r["image_url"] if "image_url" in r.keys() else "",
            "created_at": r["created_at"]
        })
    return result

def delete_raw_listing(listing_id: str) -> bool:
    """Elimina un anuncio en bruto por ID."""
    if supabase_client:
        try:
            supabase_client.table("raw_listings").delete().eq("id", listing_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase] Error al eliminar raw_listing: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM raw_listings WHERE id = ?", (listing_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_market_intelligence_stats(keyword: Optional[str] = None) -> Dict[str, Any]:
    """Calcula estadísticas agregadas sobre los anuncios recolectados."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT price FROM raw_listings WHERE price > 5"
    params = []
    if keyword and keyword.strip():
        query += " AND (title LIKE ? OR keyword LIKE ?)"
        params.extend([f"%{keyword.strip()}%", f"%{keyword.strip()}%"])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {
            "total_items": 0,
            "median_price": 0.0,
            "min_price": 0.0,
            "max_price": 0.0,
            "avg_price": 0.0
        }
    
    prices = sorted([float(r["price"]) for r in rows])
    n = len(prices)
    median = prices[n // 2] if n % 2 != 0 else (prices[n // 2 - 1] + prices[n // 2]) / 2.0
    
    p15 = prices[int(n * 0.15)]
    p85 = prices[int(n * 0.85)]
    
    return {
        "total_items": n,
        "median_price": round(float(median), 2),
        "min_price": round(float(p15), 2),
        "max_price": round(float(p85), 2),
        "avg_price": round(sum(prices) / n, 2)
    }

def get_benchmark(product_key: str) -> Optional[Dict[str, Any]]:
    if supabase_client:
        try:
            res = supabase_client.table("market_benchmarks").select("*").eq("product_key", product_key).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            print(f"[Supabase] Error al leer benchmark: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM market_benchmarks WHERE product_key = ?", (product_key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def find_closest_benchmark(title: str) -> Optional[Dict[str, Any]]:
    title_lower = title.lower()
    
    rows = []
    if supabase_client:
        try:
            res = supabase_client.table("market_benchmarks").select("*").execute()
            if res.data:
                rows = res.data
        except Exception as e:
            print(f"[Supabase] Error al consultar benchmarks: {e}")

    if not rows:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM market_benchmarks")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
    
    # 1. Reglas directas de alta precisión
    # Consolas PlayStation
    if "ps5" in title_lower or "playstation 5" in title_lower:
        if "pro" in title_lower:
            match = next((r for r in rows if r["product_key"] == "ps5_pro"), None)
            if match: return match
        if "slim" in title_lower:
            match = next((r for r in rows if r["product_key"] == "ps5_slim"), None)
            if match: return match
        if "digital" in title_lower:
            match = next((r for r in rows if r["product_key"] == "ps5_digital"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "ps5_disc"), None)
        if match: return match

    if "ps4" in title_lower or "playstation 4" in title_lower:
        if "pro" in title_lower:
            match = next((r for r in rows if r["product_key"] == "ps4_pro"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "ps4_slim"), None)
        if match: return match

    # Nintendo Switch
    if "switch" in title_lower:
        if "oled" in title_lower:
            match = next((r for r in rows if r["product_key"] == "switch_oled"), None)
            if match: return match
        if "lite" in title_lower:
            match = next((r for r in rows if r["product_key"] == "switch_lite"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "switch_v2"), None)
        if match: return match

    # Steam Deck & ROG Ally
    if "steam deck" in title_lower:
        if "oled" in title_lower:
            match = next((r for r in rows if r["product_key"] == "steam_deck_oled"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "steam_deck_512"), None)
        if match: return match
    if "rog ally" in title_lower or "asus rog" in title_lower:
        match = next((r for r in rows if r["product_key"] == "asus_rog_ally"), None)
        if match: return match

    # Xbox
    if "xbox" in title_lower:
        if "series x" in title_lower or "series_x" in title_lower:
            match = next((r for r in rows if r["product_key"] == "xbox_series_x"), None)
            if match: return match
        if "series s" in title_lower or "series_s" in title_lower:
            match = next((r for r in rows if r["product_key"] == "xbox_series_s"), None)
            if match: return match

    # iPhones
    if "iphone" in title_lower:
        if " se" in title_lower or "iphone se" in title_lower:
            match = next((r for r in rows if r["product_key"] == "iphone_se_3"), None)
            if match: return match
        for gen in ["16", "15", "14", "13", "12", "11"]:
            if gen in title_lower:
                if "pro max" in title_lower or "promax" in title_lower:
                    match = next((r for r in rows if f"{gen}_promax" in r["product_key"] or f"{gen}_pro_max" in r["product_key"]), None)
                    if not match:
                        match = next((r for r in rows if f"{gen}_pro" in r["product_key"] or f"{gen}_128" in r["product_key"]), None)
                    if match: return match
                elif "pro" in title_lower:
                    match = next((r for r in rows if f"{gen}_pro" in r["product_key"]), None)
                    if not match:
                        match = next((r for r in rows if f"{gen}_128" in r["product_key"]), None)
                    if match: return match
                else:
                    match = next((r for r in rows if f"{gen}_128" in r["product_key"]), None)
                    if match: return match

    # Samsung
    if "s25" in title_lower or "galaxy s25" in title_lower:
        if "ultra" in title_lower:
            match = next((r for r in rows if r["product_key"] == "samsung_s25_ultra"), None)
            if match: return match
        if "plus" in title_lower or "s25+" in title_lower or "s25 +" in title_lower:
            match = next((r for r in rows if r["product_key"] == "samsung_s25_plus"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "samsung_s25"), None)
        if match: return match
    if "s24" in title_lower or "galaxy s24" in title_lower:
        if "ultra" in title_lower:
            match = next((r for r in rows if r["product_key"] == "samsung_s24_ultra"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "samsung_s24"), None)
        if match: return match
    if "s23" in title_lower or "galaxy s23" in title_lower:
        match = next((r for r in rows if r["product_key"] == "samsung_s23"), None)
        if match: return match

    # iPads y MacBooks
    if "macbook" in title_lower:
        if "pro" in title_lower:
            match = next((r for r in rows if r["product_key"] == "macbook_pro_m1"), None)
            if match: return match
        if "m2" in title_lower:
            match = next((r for r in rows if r["product_key"] == "macbook_air_m2"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "macbook_air_m1"), None)
        if match: return match
    if "ipad" in title_lower:
        if "pro" in title_lower:
            match = next((r for r in rows if r["product_key"] == "ipad_pro_11_m2"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "ipad_air_m1"), None)
        if match: return match

    # Tarjetas Gráficas RTX
    if "rtx" in title_lower:
        for rtx in ["4080", "4070", "4060", "3060"]:
            if rtx in title_lower:
                match = next((r for r in rows if rtx in r["product_key"]), None)
                if match: return match

    # Audio
    if "airpods" in title_lower:
        if "max" in title_lower:
            match = next((r for r in rows if r["product_key"] == "airpods_max"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "airpods_pro_2"), None)
        if match: return match
    if "wh-1000xm5" in title_lower or "1000xm5" in title_lower or "wh1000xm5" in title_lower:
        match = next((r for r in rows if r["product_key"] == "sony_wh1000xm5"), None)
        if match: return match
    if "wh-1000xm4" in title_lower or "1000xm4" in title_lower or "wh1000xm4" in title_lower:
        match = next((r for r in rows if r["product_key"] == "sony_wh1000xm4"), None)
        if match: return match

    # Moda & Sneakers (Vinted)
    if "dunk" in title_lower:
        match = next((r for r in rows if "dunk" in r["product_key"]), None)
        if match: return match
    if "jordan" in title_lower:
        match = next((r for r in rows if "jordan" in r["product_key"]), None)
        if match: return match
    if "nuptse" in title_lower or ("north face" in title_lower and ("chaqueta" in title_lower or "plumifero" in title_lower or "plumífero" in title_lower)):
        match = next((r for r in rows if "nuptse" in r["product_key"]), None)
        if match: return match

    # Herramientas (Milanuncios)
    if "dewalt" in title_lower:
        if "amoladora" in title_lower or "radial" in title_lower:
            match = next((r for r in rows if r["product_key"] == "dewalt_amoladora_18v"), None)
            if match: return match
        match = next((r for r in rows if r["product_key"] == "dewalt_xr_18v"), None)
        if match: return match
    if "cortacesped" in title_lower or "cortacésped" in title_lower or "tractor" in title_lower:
        match = next((r for r in rows if "cortacesped" in r["product_key"]), None)
        if match: return match

    # 2. Matching difuso por tokens como fallback
    best_match = None
    best_score = 0
    clean_words = set(re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ ]', ' ', title_lower).split())

    for row in rows:
        name_words = set(re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ ]', ' ', row["display_name"].lower()).split())
        common = clean_words.intersection(name_words)
        # Quitar stop-words comunes
        common = [w for w in common if len(w) > 2 and w not in ["con", "para", "del", "por", "las", "los", "una", "uno"]]
        if len(common) > best_score and len(common) >= 2:
            best_score = len(common)
            best_match = row

    return best_match

def get_recent_scans(limit: int = 10) -> List[Dict[str, Any]]:
    if supabase_client:
        try:
            res = supabase_client.table("scans").select(
                "id, platform, title, price, score, verdict, market_price, savings, savings_pct, created_at"
            ).order("id", desc=True).limit(limit).execute()
            if res.data:
                return res.data
        except Exception as e:
            print(f"[Supabase] Error al leer historial: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, platform, title, price, score, verdict, market_price, savings, savings_pct, created_at
        FROM scans 
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_scans_admin(limit: int = 100) -> List[Dict[str, Any]]:
    """Devuelve todos los análisis con campos completos para la tabla del panel de administración."""
    if supabase_client:
        try:
            res = supabase_client.table("scans").select("*").order("id", desc=True).limit(limit).execute()
            if res.data:
                return res.data
        except Exception as e:
            print(f"[Supabase] Error al leer scans admin: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_admin_stats() -> Dict[str, Any]:
    """Calcula métricas clave para el panel de administración usando consultas SQL agregadas ultra-rápidas."""
    if supabase_client:
        try:
            # En Supabase obtenemos el total y calculamos
            scans = get_all_scans_admin(limit=1000)
            total_items = len(scans)
            bargains_count = sum(1 for s in scans if float(s.get("score", 0)) >= 7.5)
            scams_count = sum(1 for s in scans if s.get("risk_level") == "ALTO" or "Estafa" in str(s.get("verdict", "")))
            total_savings = sum(max(0.0, float(s.get("savings", 0))) for s in scans)
            avg_score = round(sum(float(s.get("score", 0)) for s in scans) / total_items, 1) if total_items > 0 else 0.0
            return {
                "total_scans": total_items,
                "bargains_count": bargains_count,
                "scams_flagged": scams_count,
                "total_savings": round(total_savings, 2),
                "average_score": avg_score
            }
        except Exception as e:
            print(f"[Supabase Stats] Error: {e}")

    # En SQLite usamos agregación SQL pura (O(1) en memoria)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_scans,
            COALESCE(SUM(CASE WHEN score >= 7.5 THEN 1 ELSE 0 END), 0) as bargains_count,
            COALESCE(SUM(CASE WHEN risk_level = 'ALTO' OR verdict LIKE '%Estafa%' THEN 1 ELSE 0 END), 0) as scams_flagged,
            COALESCE(SUM(CASE WHEN savings > 0 THEN savings ELSE 0 END), 0) as total_savings,
            COALESCE(AVG(score), 0.0) as average_score
        FROM scans
    """)
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "total_scans": row["total_scans"] or 0,
            "bargains_count": row["bargains_count"] or 0,
            "scams_flagged": row["scams_flagged"] or 0,
            "total_savings": round(float(row["total_savings"] or 0.0), 2),
            "average_score": round(float(row["average_score"] or 0.0), 1)
        }
    return {
        "total_scans": 0,
        "bargains_count": 0,
        "scams_flagged": 0,
        "total_savings": 0.0,
        "average_score": 0.0
    }

def get_platform_stats() -> Dict[str, Any]:
    """Calcula métricas agregadas por cada web (Wallapop, Vinted, Milanuncios) desde Supabase o SQLite."""
    platforms = ["wallapop", "vinted", "milanuncios"]
    scans = get_all_scans_admin(limit=1000)
    raw = get_raw_listings(limit=1000)

    stats = {}
    total_all_items = 0

    for p in platforms:
        p_scans = [s for s in scans if (s.get("platform") or "").lower() == p]
        p_raw = [r for r in raw if (r.get("platform") or "").lower() == p]

        scans_count = len(p_scans)
        raw_count = len(p_raw)
        total_p = scans_count + raw_count
        total_all_items += total_p

        all_prices = (
            [float(s.get("price", 0)) for s in p_scans if float(s.get("price", 0)) > 0] +
            [float(r.get("price", 0)) for r in p_raw if float(r.get("price", 0)) > 0]
        )

        avg_price = round(sum(all_prices) / len(all_prices), 2) if all_prices else 0.0
        sorted_prices = sorted(all_prices)
        median_price = round(sorted_prices[len(sorted_prices) // 2], 2) if sorted_prices else 0.0

        chollos = sum(1 for s in p_scans if float(s.get("score", 0)) >= 7.5)
        risks = sum(1 for s in p_scans if s.get("risk_level") == "ALTO" or "Estafa" in str(s.get("verdict", "")))

        connector_status = "online"
        connector_label = "Conectado en vivo"
        if p == "wallapop":
            connector_status = "emulated"
            connector_label = "Emulación Browser / WAF"

        stats[p] = {
            "platform": p,
            "display_name": "Milanuncios" if p == "milanuncios" else p.capitalize(),
            "scans_count": scans_count,
            "raw_count": raw_count,
            "total_items": total_p,
            "median_price": median_price,
            "avg_price": avg_price,
            "chollos_count": chollos,
            "risks_count": risks,
            "connector_status": connector_status,
            "connector_label": connector_label,
            "share_pct": 0.0
        }

    if total_all_items > 0:
        for p in platforms:
            stats[p]["share_pct"] = round((stats[p]["total_items"] / total_all_items) * 100, 1)

    return {
        "platforms": stats,
        "total_database_items": total_all_items,
        "total_scans": len(scans),
        "total_raw": len(raw)
    }


def get_cached_scan(url: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
    """Busca si la URL ya fue analizada recientemente para servir el resultado desde caché."""
    if not url:
        return None
    clean_url = url.strip()

    if supabase_client:
        try:
            res = supabase_client.table("scans").select("*").eq("url", clean_url).order("id", desc=True).limit(1).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                details = row.get("details_json")
                if isinstance(details, str):
                    try:
                        row["details"] = json.loads(details)
                    except Exception:
                        row["details"] = {}
                # No servir como caché si fue un fallback por bloqueo anti-bot
                source = (row.get("details") or {}).get("source", "")
                if "smart_parser" not in source and "slug_fallback" not in source:
                    return row
        except Exception as e:
            print(f"[Supabase Cache] Error: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    # Filtrar por antigüedad máxima de max_age_hours
    cursor.execute(
        "SELECT * FROM scans WHERE url = ? AND created_at >= datetime('now', ?) ORDER BY id DESC LIMIT 1",
        (clean_url, f"-{max_age_hours} hours")
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        if isinstance(d.get("details_json"), str):
            try:
                d["details"] = json.loads(d["details_json"])
            except Exception:
                d["details"] = {}
        # Ignorar fallbacks en caché
        source = (d.get("details") or {}).get("source", "")
        if "smart_parser" not in source and "slug_fallback" not in source:
            return d
    return None

def delete_scan(scan_id: int) -> bool:
    """Elimina un análisis de Supabase o SQLite."""
    if supabase_client:
        try:
            res = supabase_client.table("scans").delete().eq("id", scan_id).execute()
            return True
        except Exception as e:
            print(f"[Supabase Delete] Error: {e}")
            return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
    conn.commit()
    conn.close()
    return True

def get_all_benchmarks() -> List[Dict[str, Any]]:
    """Lista todos los benchmarks actuales."""
    if supabase_client:
        try:
            res = supabase_client.table("market_benchmarks").select("*").order("category").execute()
            if res.data:
                return res.data
        except Exception as e:
            print(f"[Supabase Benchmarks] Error: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM market_benchmarks ORDER BY category, display_name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_or_update_benchmark(product_key: str, display_name: str, median_price: float, min_price: float, max_price: float, category: str = "General") -> bool:
    """Añade o actualiza un precio de referencia en la base de datos."""
    data = {
        "product_key": product_key.strip().lower(),
        "display_name": display_name.strip(),
        "median_price": float(median_price),
        "min_normal_price": float(min_price),
        "max_normal_price": float(max_price),
        "category": category.strip()
    }
    if supabase_client:
        try:
            supabase_client.table("market_benchmarks").upsert(data).execute()
            return True
        except Exception as e:
            print(f"[Supabase Upsert Benchmark] Error: {e}")
            return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO market_benchmarks
        (product_key, display_name, median_price, min_normal_price, max_normal_price, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data["product_key"], data["display_name"], data["median_price"], data["min_normal_price"], data["max_normal_price"], data["category"]))
    conn.commit()
    conn.close()
    return True


