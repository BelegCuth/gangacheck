import re
from typing import Dict, Any, List, Tuple
from database import find_closest_benchmark

class DealScorer:
    """
    Motor analítico para calcular la puntuación de 0 a 10 (Chollo Score),
    detectar banderas rojas de fraude y generar pros/contras claros.
    """

    SCAM_KEYWORDS = [
        "bizum", "transferencia", "whatsapp", "fuera de la aplicacion",
        "no acepto wallapay", "no acepto envios wallapop", "pago por adelantado",
        "escribeme al", "contacto solo por correo", "mensajeria urgente pago yo"
    ]

    CONDITION_POSITIVE = [
        "factura", "garantia", "precintado", "a estrenar", "sin abrir",
        "impecable", "como nuevo", "perfecto estado", "caja original",
        "dos mandos", "mando extra", "funda"
    ]

    CONDITION_NEGATIVE = [
        "para piezas", "pantalla rota", "marcas de uso", "arañazos",
        "drift", "bateria al", "sin cargador", "sin cables", "no funciona",
        "desperfectos", "golpe", "reparar"
    ]

    @classmethod
    def evaluate(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        title = item.get("title", "")
        description = item.get("description", "")
        price = float(item.get("price", 0.0))
        seller = item.get("seller", {})
        shipping_available = item.get("shipping_available", True)

        full_text = f"{title} {description}".lower()

        # 1. Obtener precio de mercado de referencia
        benchmark = find_closest_benchmark(title)
        if benchmark:
            market_price = float(benchmark["median_price"])
            product_name = benchmark["display_name"]
            category = benchmark.get("category", "General")
        else:
            # Estimación contextual por defecto si no está en catálogo específico
            market_price = max(price * 1.25, price + 40)
            product_name = title
            category = "General"

        # 2. Análisis del Descuento
        savings = market_price - price
        savings_pct = (savings / market_price) * 100 if market_price > 0 else 0

        # Subnota de precio (0 a 10)
        # Si precio == market_price -> 5.0
        # Si ahorras 30% -> 9.0
        # Si ahorras 40%+ -> 10.0
        # Si pagas 25% de más -> 2.5
        if savings_pct >= 40:
            price_score = 10.0
        elif savings_pct >= 25:
            price_score = 8.5 + (savings_pct - 25) * 0.1
        elif savings_pct >= 10:
            price_score = 6.8 + (savings_pct - 10) * 0.11
        elif savings_pct >= 0:
            price_score = 5.0 + (savings_pct) * 0.18
        elif savings_pct >= -25:
            price_score = max(1.5, 5.0 + (savings_pct) * 0.14)
        else:
            price_score = 1.0

        # 3. Análisis de Seguridad / Banderas Rojas de Estafa
        risk_flags = []
        is_high_risk = False

        # Detectar palabras prohibidas/sospechosas
        for kw in cls.SCAM_KEYWORDS:
            if kw in full_text:
                risk_flags.append(f"Mención sospechosa detectada: '{kw}'")
                is_high_risk = True

        seller_rating = float(seller.get("rating", 0.0))
        seller_reviews = int(seller.get("reviews_count", 0))

        if seller_reviews == 0:
            risk_flags.append("Vendedor nuevo sin valoraciones previas")
            if savings_pct > 35:
                # Superchollo de cuenta recién creada = señal típica de estafa
                is_high_risk = True
                risk_flags.append("Descuento anormalmente alto para un perfil sin historial")

        if not shipping_available and savings_pct > 30:
            risk_flags.append("No permite envío oficial por la plataforma")

        # 4. Análisis de Estado y Accesorios
        pros = []
        cons = []

        for kw in cls.CONDITION_POSITIVE:
            if kw in full_text:
                pros.append(f"Incluye o destaca: {kw.title()}")

        for kw in cls.CONDITION_NEGATIVE:
            if kw in full_text:
                cons.append(f"Detalle a tener en cuenta: {kw.title()}")

        # Pros basados en el precio y vendedor
        if savings_pct > 15:
            pros.append(f"Ahorras {round(savings, 2)} € (-{round(savings_pct)}%) frente al precio medio habitual")
        if seller_reviews >= 15 and seller_rating >= 4.5:
            pros.append(f"Vendedor fiable con {seller_reviews} valoraciones ({seller_rating} ⭐)")
        if shipping_available:
            pros.append("Protección al comprador y envíos seguros disponibles")

        # Contras
        if savings_pct < -5:
            cons.append(f"Precio un {abs(round(savings_pct))}% por encima de la media de mercado")
        if seller_reviews < 3:
            cons.append("Vendedor con poco o ningún historial de transacciones")

        # 5. Cálculo de la Puntuación Final Ponderada
        # Ponderación: 65% Precio, 20% Vendedor/Seguridad, 15% Estado/Extras
        trust_score = 5.0
        if seller_reviews >= 20 and seller_rating >= 4.7:
            trust_score = 9.5
        elif seller_reviews >= 5 and seller_rating >= 4.0:
            trust_score = 7.5
        elif seller_reviews == 0:
            trust_score = 3.0

        condition_modifier = len(pros) * 0.3 - len(cons) * 0.5
        
        final_score = (price_score * 0.65) + (trust_score * 0.20) + 1.0 + condition_modifier

        # ANULACIÓN POR ESTAFA (Kill-switch):
        # Si se detecta un patrón de fraude claro, la nota se hunde a 1.0 o 0.5
        if is_high_risk and len(risk_flags) >= 2:
            final_score = min(final_score, 1.2)
            verdict = "⚠️ Posible Estafa / Alto Riesgo"
            risk_level = "ALTO"
        elif final_score >= 8.8:
            verdict = "🔥 ¡Chollo Épico! (Compra Recomendada)"
            risk_level = "BAJO"
        elif final_score >= 7.2:
            verdict = "🟢 Muy Buen Precio"
            risk_level = "BAJO"
        elif final_score >= 5.0:
            verdict = "🟡 Precio Justo de Mercado"
            risk_level = "MODERADO"
        elif final_score >= 3.5:
            verdict = "🟠 Algo Caro"
            risk_level = "MODERADO"
        else:
            verdict = "🔴 Sobreprecio Descarado"
            risk_level = "ALTO"

        final_score = round(max(0.1, min(10.0, final_score)), 1)

        # Sugerencia de afiliación inteligente si está caro o con riesgo
        affiliate_suggestion = None
        if final_score < 6.5 or is_high_risk:
            affiliate_suggestion = {
                "title": f"¿Prefieres comprar {product_name} con garantía y factura?",
                "description": "Compara precios en Amazon Renewed / Reacondicionados con 30 días de devolución y 1 año de garantía directa.",
                "button_text": "Ver alternativas garantizadas en Amazon",
                "tag": "Garantía Oficial"
            }

        return {
            "score": final_score,
            "verdict": verdict,
            "risk_level": risk_level,
            "market_price": round(market_price, 2),
            "item_price": round(price, 2),
            "savings": round(savings, 2),
            "savings_pct": round(savings_pct, 1),
            "normalized_product": product_name,
            "category": category,
            "pros": pros[:4],
            "cons": cons[:4],
            "risk_flags": risk_flags,
            "affiliate": affiliate_suggestion
        }
