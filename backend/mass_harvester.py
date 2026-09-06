"""
Script de Recolección Masiva de Mercado Real en Supabase Cloud.
Extrae cientos de anuncios reales de Vinted y Milanuncios,
calcula medianas, guarda raw_listings y evalúa chollos para la tabla de scans.
"""
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harvester import MarketHarvester
from scorer import DealScorer
from database import save_scan, find_closest_benchmark, get_platform_stats

SEARCH_TARGETS = [
    # Móviles de alta rotación
    ("iPhone 13 128GB", 30),
    ("iPhone 14 128GB", 30),
    ("iPhone 15 Pro", 25),
    ("Samsung Galaxy S25", 25),
    ("Samsung Galaxy S24", 30),
    ("Samsung Galaxy S23", 25),

    # Consolas y Gaming
    ("PlayStation 5", 35),
    ("Nintendo Switch OLED", 30),
    ("Steam Deck", 25),

    # Portátiles e Informática
    ("MacBook Air M1", 25),
    ("Tarjeta Gráfica RTX 4070", 25),
    ("Tarjeta Gráfica RTX 4060", 25),

    # Moda / Flipping Vinted
    ("The North Face Nuptse", 30),
    ("Air Jordan 1", 30),
]

def run_mass_harvest():
    print("\n" + "="*70)
    print("🚀 INICIANDO RECOLECCIÓN MASIVA DE DATOS REALES EN SUPABASE CLOUD")
    print("="*70)

    total_extracted_global = 0
    total_raw_saved_global = 0
    total_scans_generated = 0
    total_chollos_found = 0

    for idx, (keyword, limit) in enumerate(SEARCH_TARGETS, 1):
        print(f"\n[{idx}/{len(SEARCH_TARGETS)}] 🔍 Rastreando '{keyword}' (Límite: {limit})...")
        try:
            res = MarketHarvester.harvest_and_save(keyword, platform="all", limit=limit)
            listings = res.get("listings", [])
            extracted = res.get("total_extracted", 0)
            saved = res.get("saved_count", 0)
            metrics = res.get("metrics", {})

            total_extracted_global += extracted
            total_raw_saved_global += saved

            print(f"    Extraídos: {extracted} | Válidos guardados en raw: {saved}")
            if metrics:
                print(f"    Mediana mercado: {metrics.get('median_price')}€ | Media: {metrics.get('average_price')}€")

            # Ahora evaluamos chollos con DealScorer y generamos scans reales
            keyword_chollos = 0
            for item in listings:
                price = float(item.get("price", 0))
                title = item.get("title", "")
                
                # Ignorar accesorios de 1-15 euros cuando buscamos un teléfono o consola
                if price < 25.0 and any(w in keyword.lower() for w in ["iphone", "samsung", "playstation", "macbook", "rtx"]):
                    continue

                benchmark = find_closest_benchmark(title)
                if not benchmark:
                    benchmark = find_closest_benchmark(keyword)

                if benchmark:
                    try:
                        eval_item = {
                            "title": title,
                            "description": "",
                            "price": price,
                            "seller": {
                                "name": item.get("seller_name", "Vendedor"),
                                "rating": 4.8,
                                "reviews": item.get("seller_reviews", 10)
                            },
                            "shipping_available": item.get("has_shipping", True)
                        }
                        scored = DealScorer.evaluate(eval_item)
                        scored["platform"] = item.get("platform", "vinted")
                        scored["url"] = item.get("url", "")
                        scored["image_url"] = item.get("image_url", "")
                        scored["keyword"] = keyword

                        # Guardar scan en BBDD
                        save_scan(scored)
                        total_scans_generated += 1

                        score = float(scored.get("score", 0))
                        if score >= 7.5:
                            keyword_chollos += 1
                            total_chollos_found += 1
                    except Exception as e:
                        pass

            print(f"    Scans generados: {len(listings)} | Chollos (≥7.5): {keyword_chollos}")
            time.sleep(1.5)  # Pausa respetuosa entre llamadas

        except Exception as e:
            print(f"    ❌ Error procesando '{keyword}': {e}")

    print("\n" + "="*70)
    print("✅ RECOLECCIÓN MASIVA COMPLETADA")
    print("="*70)
    print(f"📦 Total anuncios extraídos de webs: {total_extracted_global}")
    print(f"🗄️ Total guardados en base de mercado (raw): {total_raw_saved_global}")
    print(f"📊 Total escaneos con tasación añadidos: {total_scans_generated}")
    print(f"🔥 Total chollos detectados: {total_chollos_found}")

    # Mostrar nuevas estadísticas de Supabase
    try:
        stats = get_platform_stats()
        print("\n📈 ESTADO ACTUALIZADO DE SUPABASE CLOUD:")
        print(f"   Total registros combinados: {stats.get('total_database_items')}")
        print(f"   Escaneos analizados: {stats.get('total_scans')}")
        print(f"   Catálogo raw: {stats.get('total_raw')}")
        for p, d in stats.get("platforms", {}).items():
            print(f"   - {d.get('display_name')}: {d.get('total_items')} anuncios | Mediana: {d.get('median_price')}€ | Cuota: {d.get('share_pct')}%")
    except Exception as e:
        print(f"Error consultando stats finales: {e}")

if __name__ == "__main__":
    run_mass_harvest()
