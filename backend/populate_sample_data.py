import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(str(Path(__file__).resolve().parent))

from database import save_scan, save_raw_listing
from scorer import DealScorer

# Lote de anuncios representativos para nutrir la base de datos en la nube
SAMPLE_ITEMS = [
    {
        "platform": "wallapop",
        "item_id": "ps5_disc_ganga",
        "url": "https://es.wallapop.com/item/playstation-5-con-lector-y-mando-1029381",
        "title": "PlayStation 5 Chasis C Con Lector + DualSense Extra",
        "description": "Vendo PS5 en perfecto estado con ticket de garantía y caja original. Funciona impecable.",
        "price": 285.0,
        "seller": {"name": "Marcos R.", "rating": 4.9, "reviews_count": 31},
        "shipping_available": True
    },
    {
        "platform": "wallapop",
        "item_id": "iphone13_azul",
        "url": "https://es.wallapop.com/item/iphone-13-128gb-azul-impecable-1029382",
        "title": "Apple iPhone 13 128GB Azul Medianoche",
        "description": "Batería al 89%, sin ningún rasguño, siempre con funda y cristal templado. Se entrega con cable original.",
        "price": 310.0,
        "seller": {"name": "Lucía P.", "rating": 5.0, "reviews_count": 18},
        "shipping_available": True
    },
    {
        "platform": "wallapop",
        "item_id": "switch_oled_blanca",
        "url": "https://es.wallapop.com/item/nintendo-switch-oled-blanca-1029383",
        "title": "Nintendo Switch OLED Blanca Completa",
        "description": "Consola Nintendo Switch versión OLED con muy pocas horas de juego. Incluye dock, cables y caja.",
        "price": 195.0,
        "seller": {"name": "Alejandro V.", "rating": 4.8, "reviews_count": 42},
        "shipping_available": True
    },
    {
        "platform": "wallapop",
        "item_id": "iphone15_sospecha",
        "url": "https://es.wallapop.com/item/iphone-15-pro-max-precintado-1029384",
        "title": "iPhone 15 Pro Max 256GB Precintado Sin Abrir",
        "description": "Regalo que no voy a usar. No acepto wallapay por problemas de cuenta, solo pago por Bizum o transferencia antes del envío.",
        "price": 260.0,
        "seller": {"name": "Usuario_3910", "rating": 0.0, "reviews_count": 0},
        "shipping_available": False
    },
    {
        "platform": "wallapop",
        "item_id": "rtx_4070_chollo",
        "url": "https://es.wallapop.com/item/tarjeta-grafica-rtx-4070-12gb-1029385",
        "title": "Gigabyte GeForce RTX 4070 Windforce OC 12GB",
        "description": "Comprada en PcComponentes en 2024, factura incluida y garantía vigente. Impecable para 1440p.",
        "price": 410.0,
        "seller": {"name": "Sergio M.", "rating": 5.0, "reviews_count": 67},
        "shipping_available": True
    },
    {
        "platform": "wallapop",
        "item_id": "airpods_pro2_caro",
        "url": "https://es.wallapop.com/item/airpods-pro-2-generacion-1029386",
        "title": "Apple AirPods Pro 2 Con Estuche MagSafe",
        "description": "Auriculares con uso habitual, estuche con algunas marcas visibles, almohadillas tamaño M.",
        "price": 175.0,
        "seller": {"name": "Javier D.", "rating": 3.9, "reviews_count": 5},
        "shipping_available": True
    }
]

def populate():
    print(f"📦 Procesando {len(SAMPLE_ITEMS)} productos y enviando a Supabase Cloud...")
    for item in SAMPLE_ITEMS:
        ev = DealScorer.evaluate(item)
        scan_id = save_scan({
            "platform": item["platform"],
            "item_id": item["item_id"],
            "url": item["url"],
            "title": item["title"],
            "price": item["price"],
            "normalized_product": ev.get("normalized_product", ""),
            "score": ev.get("score", 0.0),
            "verdict": ev.get("verdict", ""),
            "market_price": ev.get("market_price", 0.0),
            "savings": ev.get("savings", 0.0),
            "savings_pct": ev.get("savings_pct", 0.0),
            "risk_level": ev.get("risk_level", "NORMAL"),
            "seller_rating": item["seller"]["rating"],
            "seller_reviews": item["seller"]["reviews_count"],
            "has_shipping": item["shipping_available"],
            "details": {
                "evaluation": ev,
                "seller": item["seller"],
                "description": item["description"]
            }
        })
        print(f"  ✅ Guardado en Supabase: {item['title'][:35]}... -> Nota: {ev['score']}/10 ({ev['verdict']})")

    print("\n🎉 ¡Todos los productos han sido volcados exitosamente a tu base de datos en la nube!")

if __name__ == "__main__":
    populate()
