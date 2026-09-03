import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from config import HOST, PORT, BASE_DIR
from database import init_db, save_scan, get_recent_scans
from extractor import WallapopExtractor
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

@app.post("/api/analyze")
async def analyze_url(req: AnalyzeRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Debes proporcionar una URL válida.")

    # 1. Extraer datos del anuncio
    item_data = WallapopExtractor.fetch_item_data(url)
    
    # 2. Evaluar y calcular puntuación
    evaluation = DealScorer.evaluate(item_data)
    
    # 3. Preparar registro para la base de datos
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
        "scan_id": scan_id,
        "item": item_data,
        "evaluation": evaluation
    }

@app.get("/api/history")
async def history(limit: int = 6):
    return {"scans": get_recent_scans(limit=limit)}

# Servir archivos estáticos del frontend
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 GangaCheck.es corriendo en http://localhost:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
