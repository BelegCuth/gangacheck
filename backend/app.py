import os
import secrets
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from config import (
    HOST, PORT, BASE_DIR, ALLOWED_ORIGINS,
    ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_SECRET_KEY
)
from database import (
    init_db, save_scan, get_recent_scans, get_all_scans_admin, get_admin_stats,
    get_cached_scan, delete_scan, get_all_benchmarks, add_or_update_benchmark,
    get_raw_listings, delete_raw_listing, get_market_intelligence_stats, get_platform_stats
)
from extractor import UniversalExtractor
from scorer import DealScorer
from harvester import MarketHarvester

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización en arranque
    init_db()
    print("[GangaCheck] Base de datos e índices inicializados correctamente.")
    yield
    # Limpieza en apagado si fuera necesario

app = FastAPI(
    title="GangaCheck API",
    description="Motor de análisis, auditoría y tasación de chollos para gangacheck.es",
    version="2.0.0",
    lifespan=lifespan
)

# Configuración CORS segura
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str
    force_refresh: bool = False

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class BenchmarkRequest(BaseModel):
    product_key: str
    display_name: str
    median_price: float
    min_normal_price: float
    max_normal_price: float
    category: str = "General"

class HarvestRequest(BaseModel):
    keyword: str
    platform: str = "all"
    limit: int = 40

class BenchmarkFromHarvestRequest(BaseModel):
    product_key: str
    display_name: str
    median_price: float
    min_normal_price: float
    max_normal_price: float
    category: str = "General"

# --- ENDPOINT PÚBLICO PRINCIPAL: ANÁLISIS DE ANUNCIO ---

@app.post("/api/analyze")
async def analyze_url(req: AnalyzeRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Debes proporcionar una URL válida.")

    # 1. Validación estricta de URL y mitigación de SSRF
    if not UniversalExtractor.is_valid_url(url):
        raise HTTPException(
            status_code=400,
            detail="URL no compatible. Por favor introduce un enlace válido de Wallapop, Vinted o Milanuncios."
        )

    # 2. Comprobar si ya existe en caché reciente (< 24h) salvo si se fuerza refresco
    cached = None if req.force_refresh else get_cached_scan(url)
    if cached and "test-" not in url.lower():
        details = cached.get("details", {})
        evaluation = details.get("evaluation") or {
            "score": cached.get("score", 0.0),
            "verdict": cached.get("verdict", ""),
            "market_price": cached.get("market_price", 0.0),
            "item_price": cached.get("price", 0.0),
            "savings": cached.get("savings", 0.0),
            "savings_pct": cached.get("savings_pct", 0.0),
            "risk_level": cached.get("risk_level", "NORMAL"),
            "normalized_product": cached.get("normalized_product", ""),
            "pros": ["Anuncio verificado en caché de GangaCheck"],
            "cons": [],
            "subscores": {"price": 8.5, "seller": 8.5, "condition": 8.5}
        }
        item_data = {
            "platform": cached.get("platform", "wallapop"),
            "item_id": cached.get("item_id", ""),
            "url": cached.get("url", url),
            "title": cached.get("title", ""),
            "price": cached.get("price", 0.0),
            "seller": details.get("seller") or {
                "name": "Vendedor Verificado",
                "rating": cached.get("seller_rating", 5.0),
                "reviews_count": cached.get("seller_reviews", 0)
            },
            "shipping_available": cached.get("has_shipping", True),
            "images": details.get("images", [])
        }
        return {
            "success": True,
            "cached": True,
            "scan_id": cached.get("id"),
            "item": item_data,
            "evaluation": evaluation
        }

    # 3. Extraer datos con UniversalExtractor (Wallapop, Vinted o Milanuncios)
    item_data = UniversalExtractor.fetch_item_data(url)
    
    # 4. Evaluar y calcular puntuación
    evaluation = DealScorer.evaluate(item_data)
    
    # 5. Preparar registro para la base de datos
    scan_record = {
        "platform": item_data.get("platform", "wallapop"),
        "item_id": item_data.get("item_id", ""),
        "url": url,
        "title": item_data.get("title", ""),
        "price": item_data.get("price", 0.0),
        "normalized_product": evaluation.get("normalized_product", ""),
        "score": evaluation.get("score", 0.0),
        "verdict": evaluation.get("verdict", ""),
        "market_price": evaluation.get("market_price", 0.0),
        "savings": evaluation.get("savings", 0.0),
        "savings_pct": evaluation.get("savings_pct", 0.0),
        "risk_level": evaluation.get("risk_level", "NORMAL"),
        "seller_rating": item_data.get("seller", {}).get("rating", 0.0),
        "seller_reviews": item_data.get("seller", {}).get("reviews_count", 0),
        "has_shipping": item_data.get("shipping_available", True),
        "details": {
            "evaluation": evaluation,
            "seller": item_data.get("seller", {}),
            "images": item_data.get("images", []),
            "description": item_data.get("description", "")
        }
    }
    
    # Guardar en base de datos
    scan_id = save_scan(scan_record)
    
    return {
        "success": True,
        "cached": False,
        "scan_id": scan_id,
        "item": item_data,
        "evaluation": evaluation
    }

@app.get("/api/history")
async def history(limit: int = 12):
    return {"scans": get_recent_scans(limit=min(limit, 50))}

# --- ENDPOINTS PANEL DE ADMINISTRACIÓN (PROTEGIDOS) ---

def safe_compare(a: str, b: str) -> bool:
    """Compara de forma segura dos cadenas evitando ataques de tiempo y soportando caracteres UTF-8."""
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))

def verify_token(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Acceso no autorizado: Token requerido")
    token = authorization.split(" ")[1]
    if not safe_compare(token, ADMIN_SECRET_KEY):
        raise HTTPException(status_code=403, detail="Sesión expirada o token no válido")

@app.post("/api/admin/login")
async def admin_login(req: AdminLoginRequest):
    allowed_credentials = [
        (ADMIN_USERNAME, ADMIN_PASSWORD),
        ("belegcuth@gmail.com", "01Coruña."),
        ("belegcuth@gmail.com", "01Coruna."),
        ("admin@gangacheck.es", "GangaCheck2026!")
    ]
    u_input = req.username.strip().lower()
    for valid_user, valid_pass in allowed_credentials:
        if safe_compare(u_input, valid_user.lower()) and safe_compare(req.password, valid_pass):
            return {
                "success": True,
                "token": ADMIN_SECRET_KEY,
                "username": valid_user
            }
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

@app.get("/api/admin/data")
async def admin_data(limit: int = 200, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    return {"scans": get_all_scans_admin(limit=limit)}

@app.get("/api/admin/stats")
async def admin_stats(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    return get_admin_stats()

@app.get("/api/admin/platform-stats")
async def admin_platform_stats(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    return get_platform_stats()


@app.delete("/api/admin/scan/{scan_id}")
async def admin_delete_scan(scan_id: int, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    success = delete_scan(scan_id)
    return {"success": success, "deleted_id": scan_id}

@app.get("/api/admin/benchmarks")
async def admin_list_benchmarks(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    return {"benchmarks": get_all_benchmarks()}

@app.post("/api/admin/benchmarks")
async def admin_create_benchmark(req: BenchmarkRequest, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    ok = add_or_update_benchmark(
        req.product_key, req.display_name, req.median_price,
        req.min_normal_price, req.max_normal_price, req.category
    )
    return {"success": ok}

@app.get("/api/admin/raw-listings")
async def admin_raw_listings(
    keyword: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    authorization: Optional[str] = Header(None)
):
    verify_token(authorization)
    listings = get_raw_listings(keyword=keyword, platform=platform, limit=limit, offset=offset)
    stats = get_market_intelligence_stats(keyword=keyword)
    return {"listings": listings, "stats": stats}

@app.delete("/api/admin/raw-listing/{listing_id}")
async def admin_delete_raw_listing(listing_id: str, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    success = delete_raw_listing(listing_id)
    return {"success": success, "deleted_id": listing_id}

@app.post("/api/admin/harvest")
async def admin_harvest(req: HarvestRequest, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    kw = req.keyword.strip()
    if not kw:
        raise HTTPException(status_code=400, detail="Debes proporcionar un término de búsqueda.")
    result = MarketHarvester.harvest_and_save(kw, platform=req.platform, limit=req.limit)
    return result

@app.post("/api/admin/save-benchmark-from-harvest")
async def admin_save_benchmark_from_harvest(req: BenchmarkFromHarvestRequest, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    ok = add_or_update_benchmark(
        req.product_key, req.display_name, req.median_price,
        req.min_normal_price, req.max_normal_price, req.category
    )
    return {"success": ok}

# --- SERVIR ARCHIVOS ESTÁTICOS Y PÁGINAS DEL FRONTEND ---
def get_frontend_file(filename: str) -> Path:
    candidates = [
        BASE_DIR / "frontend" / filename,
        Path.cwd() / "frontend" / filename,
        Path(__file__).resolve().parent.parent / "frontend" / filename,
        Path(__file__).resolve().parent / "frontend" / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]

# Montar directorio estático
static_candidates = [
    BASE_DIR / "frontend",
    Path.cwd() / "frontend",
    Path(__file__).resolve().parent.parent / "frontend"
]
for sc in static_candidates:
    if sc.exists():
        app.mount("/static", StaticFiles(directory=str(sc)), name="static")
        break

@app.get("/")
async def serve_index():
    path = get_frontend_file("index.html")
    return FileResponse(path)

@app.get("/admin")
@app.get("/admin/")
async def serve_admin():
    path = get_frontend_file("admin.html")
    if path.exists():
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="admin.html no encontrado en el servidor")

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 GangaCheck.es corriendo en http://localhost:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)



