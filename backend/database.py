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

def init_db():
    """Inicializa la base de datos local (SQLite) si se usa en local."""
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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
    
    # Insertar benchmarks iniciales si está vacía
    cursor.execute("SELECT COUNT(*) FROM market_benchmarks")
    if cursor.fetchone()[0] == 0:
        initial_benchmarks = [
            ("ps5_disc", "PlayStation 5 (Con Lector)", 380.0, 320.0, 430.0, "Consolas"),
            ("ps5_digital", "PlayStation 5 Digital", 330.0, 280.0, 370.0, "Consolas"),
            ("ps5_slim", "PlayStation 5 Slim", 410.0, 360.0, 460.0, "Consolas"),
            ("switch_oled", "Nintendo Switch OLED", 230.0, 190.0, 270.0, "Consolas"),
            ("switch_v2", "Nintendo Switch V2", 160.0, 130.0, 190.0, "Consolas"),
            ("xbox_series_x", "Xbox Series X 1TB", 360.0, 300.0, 410.0, "Consolas"),
            ("steam_deck_512", "Steam Deck 512GB", 320.0, 270.0, 380.0, "Consolas"),
            ("iphone_13_128", "Apple iPhone 13 128GB", 360.0, 300.0, 420.0, "Móviles"),
            ("iphone_14_128", "Apple iPhone 14 128GB", 460.0, 400.0, 520.0, "Móviles"),
            ("iphone_15_128", "Apple iPhone 15 128GB", 580.0, 510.0, 650.0, "Móviles"),
            ("airpods_pro_2", "Apple AirPods Pro 2", 150.0, 120.0, 180.0, "Audio"),
            ("rtx_4070", "Tarjeta Gráfica RTX 4070 12GB", 480.0, 420.0, 550.0, "Informática")
        ]
        cursor.executemany("""
            INSERT INTO market_benchmarks 
            (product_key, display_name, median_price, min_normal_price, max_normal_price, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, initial_benchmarks)
    
    conn.commit()
    conn.close()

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
    if supabase_client:
        try:
            supabase_client.table("raw_listings").upsert({
                "id": str(item.get("id")),
                "platform": item.get("platform", "wallapop"),
                "title": item.get("title", ""),
                "price": float(item.get("price", 0.0)),
                "keyword": item.get("keyword", ""),
                "seller_name": item.get("seller_name", ""),
                "seller_reviews": int(item.get("seller_reviews", 0)),
                "has_shipping": bool(item.get("has_shipping", True)),
                "url": item.get("url", "")
            }).execute()
            return
        except Exception as e:
            print(f"[Supabase] Error en upsert raw_listing: {e}")

    conn = get_connection()
    cursor = conn.cursor()
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
    
    best_match = None
    best_score = 0
    
    for row in rows:
        key = row["product_key"]
        name = row["display_name"].lower()
        words = name.replace("(", "").replace(")", "").split()
        matches = sum(1 for w in words if w in title_lower)
        
        if "ps5" in title_lower or "playstation 5" in title_lower:
            if "slim" in title_lower and "slim" in key:
                return row
            if "digital" in title_lower and "digital" in key:
                return row
            if ("disco" in title_lower or "lector" in title_lower or "chasis" in title_lower) and "disc" in key:
                return row
        
        if "iphone 13" in title_lower and "13" in key:
            return row
        if "iphone 14" in title_lower and "14" in key:
            return row
        if "iphone 15" in title_lower and "15" in key:
            return row
        if "switch" in title_lower:
            if "oled" in title_lower and "oled" in key:
                return row
            if "v2" in title_lower and "v2" in key:
                return row
                
        if matches > best_score and matches >= 2:
            best_score = matches
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
    """Calcula métricas clave para el panel de administración."""
    scans = get_all_scans_admin(limit=500)
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

