import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from config import HOST, PORT, BASE_DIR
from database import init_db, save_scan, get_recent_scans
from extractor import WallapopExtractor, UniversalExtractor
from scorer import DealScorer

app = FastAPI(
    title="GangaCheck API",
    description="Motor de análisis y tasación de chollos para gangacheck.es",
    version="1.0.0"
)

# Permitir CORS para despliegues en Vercel/Cloudflare
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str

@app.on_event("startup")
def startup_event():
    init_db()
    print("[GangaCheck] Base de datos inicializada correctamente.")

from fastapi import FastAPI, HTTPException, Header
from typing import Optional

from config import HOST, PORT, BASE_DIR, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_SECRET_KEY
from database import (
    init_db, save_scan, get_recent_scans, get_all_scans_admin, get_admin_stats,
    get_cached_scan, delete_scan, get_all_benchmarks, add_or_update_benchmark
)
from extractor import WallapopExtractor, UniversalExtractor
from scorer import DealScorer

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

@app.post("/api/analyze")
async def analyze_url(req: AnalyzeRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Debes proporcionar una URL válida.")

    # 1. Comprobar si ya existe en caché reciente (< 24h)
    cached = get_cached_scan(url)
    if cached and not "test-" in url.lower():
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

    # 2. Extraer datos con UniversalExtractor (Wallapop, Vinted o Milanuncios)
    item_data = UniversalExtractor.fetch_item_data(url)
    
    # 3. Evaluar y calcular puntuación
    evaluation = DealScorer.evaluate(item_data)
    
    # 4. Preparar registro para la base de datos
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
async def history(limit: int = 8):
    return {"scans": get_recent_scans(limit=limit)}

# --- ENDPOINTS PANEL DE ADMINISTRACIÓN (PROTEGIDOS) ---

def verify_token(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Acceso no autorizado: Token requerido")
    token = authorization.split(" ")[1]
    if token != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Sesión expirada o token no válido")

@app.post("/api/admin/login")
async def admin_login(req: AdminLoginRequest):
    if req.username == ADMIN_USERNAME and req.password == ADMIN_PASSWORD:
        return {
            "success": True,
            "token": ADMIN_SECRET_KEY,
            "username": ADMIN_USERNAME
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
    raise HTTPException(status_code=404, detail=f"admin.html no encontrado en el servidor")

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 GangaCheck.es corriendo en http://localhost:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)


