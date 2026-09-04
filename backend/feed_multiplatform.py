import sys
import random
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(str(Path(__file__).resolve().parent))

from database import save_scan
from scorer import DealScorer

MULTIPLATFORM_ITEMS = [
    # --- VINTED (Moda, Calzado, Sneakers y Abrigos) ---
    {
        "platform": "vinted",
        "title": "Nike Dunk Low Retro Panda Talla 43 Nuevas",
        "price": 68.0,
        "description": "Zapatillas completamente nuevas a estrenar, con etiquetas puestas y caja original. Compradas en SNKRS. Factura demostrable.",
        "seller": {"name": "sofia_sneakers", "rating": 5.0, "reviews_count": 76},
        "shipping_available": True
    },
    {
        "platform": "vinted",
        "title": "Air Jordan 1 Retro High OG Chicago Lost and Found Talla 42",
        "price": 115.0,
        "description": "Edición especial Chicago con caja vintage y cordones extras. Puestas dos veces, como nuevas sin marcas.",
        "seller": {"name": "carlos_vntg", "rating": 4.9, "reviews_count": 41},
        "shipping_available": True
    },
    {
        "platform": "vinted",
        "title": "Chaqueta The North Face Nuptse 1996 Negra Talla M",
        "price": 140.0,
        "description": "Plumífero original con relleno de plumón 700 cuins. Capucha plegable en el cuello. Impecable estado sin roturas.",
        "seller": {"name": "laura_closet", "rating": 4.8, "reviews_count": 29},
        "shipping_available": True
    },
    {
        "platform": "vinted",
        "title": "Zapatillas Nike Dunk Low Grey Fog Talla 44",
        "price": 135.0,
        "description": "Zapatillas con marcas normales de uso en suela y empeine. Sin caja original.",
        "seller": {"name": "pablo_m", "rating": 4.1, "reviews_count": 5},
        "shipping_available": True
    },
    {
        "platform": "vinted",
        "title": "Plumífero The North Face Nuptse Azul Marino Talla L",
        "price": 220.0,
        "description": "Chaqueta North Face muy abrigada. Precio poco negociable.",
        "seller": {"name": "user_closet_21", "rating": 4.3, "reviews_count": 8},
        "shipping_available": True
    },

    # --- MILANUNCIOS (Herramientas, Maquinaria, Tecnología y Ocasión) ---
    {
        "platform": "milanuncios",
        "title": "Taladro Percutor DeWalt XR 18V Brushless con 2 baterías de 4Ah",
        "price": 85.0,
        "description": "Taladro profesional sin escobillas en perfecto estado de funcionamiento. Incluye maletín TSTAK, cargador rápido y dos baterías.",
        "seller": {"name": "Reformas y Construcción Norte", "rating": 4.9, "reviews_count": 35},
        "shipping_available": True
    },
    {
        "platform": "milanuncios",
        "title": "Amoladora DeWalt 18V XR con disco de corte y maletín",
        "price": 95.0,
        "description": "Radial inalámbrica profesional con poco uso. Se entrega revisada y lista para trabajar. Envío por Milanuncios Express.",
        "seller": {"name": "Herramientas Ocasión", "rating": 4.8, "reviews_count": 24},
        "shipping_available": True
    },
    {
        "platform": "milanuncios",
        "title": "Tractor Cortacésped John Deere Hidrostático",
        "price": 1250.0,
        "description": "Motor Briggs & Stratton bicilíndrico de 18CV, doble cuchilla de corte, cesto de recogida de 300L. Mantenimiento recién hecho en taller oficial.",
        "seller": {"name": "AgroMaquinaria Gal", "rating": 5.0, "reviews_count": 18},
        "shipping_available": True
    },
    {
        "platform": "milanuncios",
        "title": "Taladro percutor DeWalt con cable 750W",
        "price": 145.0,
        "description": "Taladro con marcas de cemento y obra. Funciona bien pero tiene desgaste estético evidente.",
        "seller": {"name": "Manuel T.", "rating": 3.9, "reviews_count": 4},
        "shipping_available": True
    },
    {
        "platform": "milanuncios",
        "title": "Tractor Cortacésped John Deere X350 NUEVO",
        "price": 380.0,
        "description": "Por no usar vendo urgente. No se aceptan llamadas. Contactar solo por correo electrónico para pago anticipado por transferencia bancaria y envío urgente.",
        "seller": {"name": "Ocasión_Urgente", "rating": 0.0, "reviews_count": 0},
        "shipping_available": False
    }
]

def feed_multi():
    print(f"🚀 Iniciando volcado multicanal (Vinted & Milanuncios) a Supabase Cloud...")
    saved = 0
    
    for item in MULTIPLATFORM_ITEMS:
        slug = item["title"].lower().replace(" ", "-").replace("+", "con").replace("/", "-")[:45]
        if item["platform"] == "vinted":
            item["url"] = f"https://www.vinted.es/items/{random.randint(10000000, 99999999)}-{slug}"
            item["item_id"] = f"vin_{random.randint(1000000, 9999999)}"
        else:
            item["url"] = f"https://www.milanuncios.com/{slug}-r{random.randint(100000000, 999999999)}.htm"
            item["item_id"] = f"mila_{random.randint(1000000, 9999999)}"
            
        ev = DealScorer.evaluate(item)
        
        scan_record = {
            "platform": item["platform"],
            "item_id": item["item_id"],
            "url": item["url"],
            "title": item["title"],
            "price": item["price"],
            "normalized_product": ev.get("normalized_product", item["title"]),
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
        }
        
        save_scan(scan_record)
        saved += 1
        print(f"  [{item['platform'].upper()}] [{ev['score']}/10] {item['title'][:40]}... -> {item['price']} € ({ev['verdict']})")

    print(f"\n🎉 ¡Volcado multicanal finalizado! Se han añadido {saved} anuncios de Vinted y Milanuncios a Supabase.")

if __name__ == "__main__":
    feed_multi()
