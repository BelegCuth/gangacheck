"""
Script de Saneamiento y Purga de Ruido en Supabase Cloud.
Elimina fundas, carcasas, cajas vacías y anuncios no españoles colados previamente.
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harvester import NOISE_KEYWORDS
from database import (
    get_raw_listings, delete_raw_listing,
    get_all_scans_admin, delete_scan,
    get_platform_stats
)

def purge_database():
    print("\n" + "="*70)
    print("🧹 INICIANDO SANEAMIENTO Y LIMPIEZA DE RUIDO EN SUPABASE CLOUD")
    print("="*70)

    # 1. Purgar RAW LISTINGS
    raw_items = get_raw_listings(limit=2000)
    print(f"Examinando {len(raw_items)} anuncios raw de mercado...")

    raw_purged = 0
    for r in raw_items:
        title = r.get("title", "").lower()
        price = float(r.get("price", 0))
        rid = r.get("id")
        kw = (r.get("keyword") or "").lower()

        is_high_tech = any(t in kw for t in ["iphone", "samsung", "galaxy", "ps5", "playstation", "switch", "macbook", "rtx"])

        # Criterio 1: Contiene palabra de funda, accesorio o caja
        has_noise_word = any(nw in title for nw in NOISE_KEYWORDS)

        # Criterio 2: Precio ridículamente bajo para ser el producto real (funda/cable)
        is_too_cheap = is_high_tech and price < 35.0

        if has_noise_word or is_too_cheap:
            try:
                delete_raw_listing(rid)
                raw_purged += 1
                reason = "Palabra prohibida" if has_noise_word else "Precio accesorio (<35€)"
                print(f"   🗑️ [RAW] Eliminado: '{r.get('title')[:45]}' ({price}€) -> {reason}")
            except Exception as e:
                print(f"   Error eliminando raw {rid}: {e}")

    print(f"\n✅ Total Raw eliminados por ruido/fundas: {raw_purged}")

    # 2. Purgar SCANS
    scans = get_all_scans_admin(limit=2000)
    print(f"\nExaminando {len(scans)} escaneos tasados...")

    scans_purged = 0
    for s in scans:
        title = s.get("title", "").lower()
        price = float(s.get("price", 0))
        sid = s.get("id")
        prod_key = (s.get("product_key") or "").lower()

        is_high_tech = any(t in prod_key for t in ["iphone", "samsung", "ps5", "switch", "macbook", "rtx"])

        has_noise_word = any(nw in title for nw in NOISE_KEYWORDS)
        is_too_cheap = is_high_tech and price < 35.0

        if has_noise_word or is_too_cheap:
            try:
                delete_scan(sid)
                scans_purged += 1
                reason = "Palabra prohibida" if has_noise_word else "Precio accesorio (<35€)"
                print(f"   🗑️ [SCAN] Eliminado: '{s.get('title')[:45]}' ({price}€) -> {reason}")
            except Exception as e:
                print(f"   Error eliminando scan {sid}: {e}")

    print(f"\n✅ Total Scans eliminados por ruido/fundas: {scans_purged}")

    # 3. Mostrar métricas actualizadas
    stats = get_platform_stats()
    print("\n" + "="*70)
    print("✨ BASE DE DATOS SANEADA Y PURGADA:")
    print(f"   Total registros limpios: {stats.get('total_database_items')}")
    print(f"   Total scans reales: {stats.get('total_scans')}")
    print(f"   Total catálogo raw limpio: {stats.get('total_raw')}")
    for p, d in stats.get("platforms", {}).items():
        print(f"   - {d.get('display_name')}: {d.get('total_items')} anuncios | Mediana real: {d.get('median_price')}€")
    print("="*70 + "\n")

if __name__ == "__main__":
    purge_database()
