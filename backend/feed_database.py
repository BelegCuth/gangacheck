import sys
import random
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from database import save_scan, get_all_scans_admin
from scorer import DealScorer

# Catálogo diverso de productos populares de segunda mano para alimentar la BBDD
CATALOG = [
    # --- CONSOLAS Y GAMING ---
    {
        "title": "PlayStation 5 Chasis D Slim 1TB con 2 mandos",
        "price": 340.0,
        "description": "Comprada en reyes, con factura y caja original. Incluye mando blanco y mando negro DualSense. Muy cuidada.",
        "seller": {"name": "Álvaro M.", "rating": 4.9, "reviews_count": 28},
        "shipping_available": True
    },
    {
        "title": "PS5 Digital Edition 825GB + Auriculares Pulse 3D",
        "price": 275.0,
        "description": "Consola digital sin lector, funciona perfecta. La vendo por mudanza. Incluye cable HDMI 2.1 y auriculares oficiales.",
        "seller": {"name": "Daniel T.", "rating": 5.0, "reviews_count": 45},
        "shipping_available": True
    },
    {
        "title": "Nintendo Switch OLED Blanca con funda y Zelda Tears of the Kingdom",
        "price": 210.0,
        "description": "Pantalla OLED sin rayones, siempre con protector de cristal templado. Se entrega con funda rígida y juego físico Zelda.",
        "seller": {"name": "Clara G.", "rating": 4.8, "reviews_count": 19},
        "shipping_available": True
    },
    {
        "title": "Nintendo Switch V2 Gris Completa",
        "price": 135.0,
        "description": "Versión con batería mejorada. Los joycon no tienen drift. Incluye cargador original y dock.",
        "seller": {"name": "Rubén P.", "rating": 4.7, "reviews_count": 12},
        "shipping_available": True
    },
    {
        "title": "Steam Deck 512GB Anti-glare con dock oficial",
        "price": 290.0,
        "description": "Pantalla grabada antirreflejos, muy poco uso. Incluye funda original Valve y dock para conectar a la tele.",
        "seller": {"name": "Jorge H.", "rating": 5.0, "reviews_count": 33},
        "shipping_available": True
    },
    {
        "title": "Xbox Series X 1TB Negra con Forza Horizon 5",
        "price": 310.0,
        "description": "Consola muy potente, silenciosa y en estado de 10. Se puede probar antes de comprar. Envíos disponibles por Wallapop.",
        "seller": {"name": "Marcos S.", "rating": 4.9, "reviews_count": 26},
        "shipping_available": True
    },

    # --- SMARTPHONES ---
    {
        "title": "iPhone 13 128GB Medianoche - Salud Batería 91%",
        "price": 330.0,
        "description": "Libre de fábrica, sin golpes ni arañazos. Funciona FaceID y TrueTone perfectamente. Incluye caja y cable.",
        "seller": {"name": "Elena R.", "rating": 4.9, "reviews_count": 52},
        "shipping_available": True
    },
    {
        "title": "Apple iPhone 14 128GB Blanco Estrella",
        "price": 420.0,
        "description": "Comprado en Apple Store hace 1 año, garantía vigente hasta fin de año. Batería al 94%. Impecable.",
        "seller": {"name": "Mateo L.", "rating": 5.0, "reviews_count": 14},
        "shipping_available": True
    },
    {
        "title": "iPhone 15 128GB Negro Titanio NUEVO",
        "price": 540.0,
        "description": "Abierto solo para comprobar funcionamiento. Factura de compra de julio 2024. Batería al 100%.",
        "seller": {"name": "Patricia F.", "rating": 4.8, "reviews_count": 21},
        "shipping_available": True
    },
    {
        "title": "iPhone 15 Pro Max 512GB Azul Titanio PRECINTADO",
        "price": 290.0,
        "description": "No negociable. No acepto wallapay por comisiones altas, solo pago por Bizum previo y envío por MRW 24h.",
        "seller": {"name": "VentasExpress_00", "rating": 0.0, "reviews_count": 0},
        "shipping_available": False
    },
    {
        "title": "Samsung Galaxy S24 256GB Gris Ónix",
        "price": 490.0,
        "description": "Terminal tope de gama con Galaxy AI. 7 años de actualizaciones. Pantalla impoluta y accesorios originales.",
        "seller": {"name": "Carlos B.", "rating": 4.8, "reviews_count": 39},
        "shipping_available": True
    },

    # --- COMPONENTES Y PORTÁTILES ---
    {
        "title": "Tarjeta Gráfica ASUS Dual RTX 4070 12GB OC",
        "price": 435.0,
        "description": "Usada solo para jugar fines de semana a 1440p. Nunca minería, temperaturas excelentes con caja y factura.",
        "seller": {"name": "Víctor N.", "rating": 5.0, "reviews_count": 61},
        "shipping_available": True
    },
    {
        "title": "MSI GeForce RTX 4070 Ventus 3X 12GB",
        "price": 460.0,
        "description": "Muy silenciosa, 3 ventiladores. Entrego con ticket de garantía de PcComponentes.",
        "seller": {"name": "Adrián C.", "rating": 4.9, "reviews_count": 17},
        "shipping_available": True
    },
    {
        "title": "MacBook Air M1 8GB 256GB Gris Espacial",
        "price": 480.0,
        "description": "Batería con solo 84 ciclos (97% salud). Portátil finísimo, sin golpes. Cargador de 30W original.",
        "seller": {"name": "Sofía M.", "rating": 4.9, "reviews_count": 24},
        "shipping_available": True
    },

    # --- AUDIO Y FOTOGRAFÍA ---
    {
        "title": "Apple AirPods Pro 2da Generación USB-C",
        "price": 135.0,
        "description": "Estuche con carga USB-C y altavoz para buscar con Find My. Cancelación de ruido brutal. Almohadillas a estrenar.",
        "seller": {"name": "Guillermo Z.", "rating": 5.0, "reviews_count": 48},
        "shipping_available": True
    },
    {
        "title": "Auriculares Sony WH-1000XM5 Negros",
        "price": 220.0,
        "description": "Los mejores auriculares de viaje. Cancelación activa de ruido insuperable. Estuche de viaje y cables intactos.",
        "seller": {"name": "Lucía H.", "rating": 4.8, "reviews_count": 16},
        "shipping_available": True
    },
    {
        "title": "Cámara Sony Alpha A7 III Cuerpo",
        "price": 890.0,
        "description": "Sensor Full Frame de 24MP. 18.000 disparos (muy poco uso). Sensor limpio, 2 baterías y cargador doble.",
        "seller": {"name": "Raúl E.", "rating": 5.0, "reviews_count": 73},
        "shipping_available": True
    },

    # --- ANUNCIOS CAROS / SOBREPRECIO (Para calibrar filtros) ---
    {
        "title": "PlayStation 5 con lector chasis A",
        "price": 460.0,
        "description": "PS5 de las primeras, tiene marcas de uso en los plásticos negros. Sin caja.",
        "seller": {"name": "Ignacio K.", "rating": 3.7, "reviews_count": 3},
        "shipping_available": True
    },
    {
        "title": "Nintendo Switch OLED Blanca",
        "price": 280.0,
        "description": "Consola con algunos roces. Incluye cargador no oficial.",
        "seller": {"name": "Tomás V.", "rating": 4.1, "reviews_count": 6},
        "shipping_available": True
    },

    # --- ALERTA DE RIESGO / ESTAFA ---
    {
        "title": "PlayStation 5 Slim 1TB NUEVA PRECINTADA",
        "price": 180.0,
        "description": "Urge venta por traslado. No acepto wallapay, contactar directamente por whatsapp al 612345678 para pago por Bizum.",
        "seller": {"name": "User_8849", "rating": 0.0, "reviews_count": 0},
        "shipping_available": False
    }
]

def feed():
    print(f"🚀 Iniciando proceso de análisis y volcado a Supabase Cloud...")
    saved_count = 0
    
    for item in CATALOG:
        # Generar URL simulada coherente
        slug = item["title"].lower().replace(" ", "-").replace("+", "con").replace("/", "-")[:45]
        item["url"] = f"https://es.wallapop.com/item/{slug}-{random.randint(100000, 999999)}"
        item["platform"] = "wallapop"
        item["item_id"] = f"w_{random.randint(1000000, 9999999)}"
        
        # Evaluar con el motor analítico de GangaCheck
        ev = DealScorer.evaluate(item)
        
        # Guardar en Supabase
        scan_record = {
            "platform": "wallapop",
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
        saved_count += 1
        print(f"  [{ev['score']}/10] {item['title'][:40]}... -> {item['price']} € ({ev['verdict']})")

    print(f"\n🎉 ¡Proceso completado! Se han añadido {saved_count} nuevos productos analizados a tu Supabase Cloud.")

if __name__ == "__main__":
    feed()
