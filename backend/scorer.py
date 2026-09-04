import re
import json
import urllib.parse
from typing import Dict, Any, List, Optional
from config import GEMINI_API_KEY
from database import find_closest_benchmark

# Intento de importar requests para llamar a la API de Gemini si está configurada
try:
    import requests
except ImportError:
    requests = None

class DealScorer:
    """
    Motor analítico para calcular la puntuación de 0 a 10 (Chollo Score),
    detectar banderas rojas de fraude y generar pros/contras claros.
    Incluye integración opcional con Google Gemini para tasación por IA.
    """

    SCAM_KEYWORDS = [
        "bizum", "transferencia", "whatsapp", "fuera de la aplicacion",
        "no acepto wallapay", "no acepto envios wallapop", "pago por adelantado",
        "escribeme al", "contacto solo por correo", "mensajeria urgente pago yo",
        "pago previo", "transferencia bancaria", "no utilizo envios integrados",
        "escribir a", "contacto al 6", "contacto al +34"
    ]

    CONDITION_POSITIVE = [
        "factura", "garantia", "garantía", "precintado", "a estrenar", "sin abrir",
        "impecable", "como nuevo", "perfecto estado", "caja original",
        "dos mandos", "mando extra", "funda", "ticket", "cargador original",
        "batería 100", "bateria 100", "batería al 9", "bateria al 9", "sin usar"
    ]

    CONDITION_NEGATIVE = [
        "para piezas", "pantalla rota", "marcas de uso", "arañazos",
        "drift", "bateria al 7", "batería al 7", "bateria al 8", "sin cargador", "sin cables",
        "no funciona", "desperfectos", "golpe", "reparar", "bloqueado",
        "para reparar", "le cuesta encender", "desgaste"
    ]

    @classmethod
    def evaluate(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        title = item.get("title", "")
        description = item.get("description", "")
        price = float(item.get("price", 0.0))
        seller = item.get("seller", {})
        shipping_available = item.get("shipping_available", True)

        full_text = f"{title} {description}".lower()

        # 1. Intentar obtener precio de referencia del catálogo oficial
        benchmark = find_closest_benchmark(title)
        ai_used = False

        if benchmark:
            market_price = float(benchmark["median_price"])
            product_name = benchmark["display_name"]
            category = benchmark.get("category", "General")
            confidence = "ALTA (Catálogo oficial de mercado)"
        elif GEMINI_API_KEY and requests:
            # 2. Si no está en catálogo y hay API Key de Gemini, consultar a la IA
            ai_data = cls._ask_gemini_estimator(title, description, price)
            if ai_data and ai_data.get("market_price"):
                market_price = float(ai_data["market_price"])
                product_name = ai_data.get("clean_name", title)
                category = ai_data.get("category", "Segunda Mano")
                confidence = "INTELIGENCIA ARTIFICIAL (Gemini AI)"
                ai_used = True
            else:
                market_price, product_name, category, confidence = cls._contextual_estimate(title, price, full_text)
        else:
            # 3. Estimación heurística contextual neutral
            market_price, product_name, category, confidence = cls._contextual_estimate(title, price, full_text)

        # 2. Análisis del Descuento
        savings = market_price - price
        savings_pct = (savings / market_price) * 100 if market_price > 0 else 0

        # Subnota de precio (0 a 10)
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

        for kw in cls.SCAM_KEYWORDS:
            if kw in full_text:
                risk_flags.append(f"Mención sospechosa detectada: '{kw}'")
                is_high_risk = True

        seller_rating = float(seller.get("rating", 0.0) or 0.0)
        seller_reviews = int(seller.get("reviews_count", 0) or 0)

        if seller_reviews == 0:
            risk_flags.append("Vendedor nuevo sin valoraciones previas")
            if savings_pct > 35:
                is_high_risk = True
                risk_flags.append("Descuento anormalmente alto para un perfil sin historial")

        if not shipping_available and savings_pct > 30:
            risk_flags.append("No permite envío oficial con protección al comprador")

        # 4. Análisis de Estado y Accesorios
        pros = []
        cons = []

        for kw in cls.CONDITION_POSITIVE:
            if kw in full_text and len(pros) < 3:
                pros.append(f"Incluye o destaca: {kw.title()}")

        for kw in cls.CONDITION_NEGATIVE:
            if kw in full_text and len(cons) < 3:
                cons.append(f"Detalle a tener en cuenta: {kw.title()}")

        # Pros basados en el precio y vendedor
        if savings_pct > 15:
            pros.append(f"Ahorras {round(savings, 2)} € (-{round(savings_pct)}%) frente al precio medio habitual")
        if seller_reviews >= 15 and seller_rating >= 4.5:
            pros.append(f"Vendedor fiable con {seller_reviews} valoraciones ({seller_rating} ⭐)")
        if shipping_available:
            pros.append("Protección al comprador y envíos con seguimiento disponibles")

        # Contras
        if savings_pct < -5:
            cons.append(f"Precio un {abs(round(savings_pct))}% por encima de la media de mercado")
        if seller_reviews < 3 and not is_high_risk:
            cons.append("Vendedor con poco o ningún historial de transacciones")

        # 5. Cálculo de la Puntuación Final Ponderada (60% Precio, 25% Vendedor, 15% Estado)
        trust_score = 5.0
        if seller_reviews >= 20 and seller_rating >= 4.7:
            trust_score = 9.5
        elif seller_reviews >= 5 and seller_rating >= 4.0:
            trust_score = 7.5
        elif seller_reviews == 0:
            trust_score = 3.0

        condition_modifier = len(pros) * 0.25 - len(cons) * 0.45
        final_score = (price_score * 0.60) + (trust_score * 0.25) + 0.8 + condition_modifier

        # ANULACIÓN POR ESTAFA (Kill-switch)
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

        # Enlace dinámico a alternativa en Amazon Renewed / Reacondicionados
        clean_search_query = urllib.parse.quote_plus(product_name)
        affiliate_url = f"https://www.amazon.es/s?k={clean_search_query}&tag=gangacheck-21"
        
        affiliate_suggestion = {
            "title": f"¿Prefieres comprar {product_name} con garantía y factura?",
            "description": "Compara precios en productos reacondicionados con 30 días de devolución y garantía directa.",
            "button_text": "Ver alternativas garantizadas en Amazon",
            "url": affiliate_url,
            "tag": "Garantía Oficial"
        }

        # Sub-puntuaciones normalizadas (0 al 10)
        subscores = {
            "price": round(max(0.5, min(10.0, price_score)), 1),
            "seller": round(max(0.5, min(10.0, trust_score)), 1),
            "condition": round(max(1.0, min(10.0, 7.0 + (len(pros) * 0.8) - (len(cons) * 1.2))), 1)
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
            "confidence": confidence,
            "ai_used": ai_used,
            "subscores": subscores,
            "pros": pros[:4],
            "cons": cons[:4],
            "risk_flags": risk_flags,
            "affiliate": affiliate_suggestion
        }

    @classmethod
    def _contextual_estimate(cls, title: str, price: float, full_text: str) -> tuple:
        """Estimación contextual cuando el producto no está en el catálogo oficial."""
        # Limpieza básica del título
        clean_title = title.replace("-", " ").strip()
        if len(clean_title) > 40:
            clean_title = clean_title[:40].strip() + "..."

        # Si el precio es muy bajo (< 30 €), asumimos que el mercado está cerca
        if price < 30:
            market_price = price * 1.15
        elif price < 100:
            market_price = price * 1.20
        else:
            market_price = price * 1.18

        return market_price, clean_title, "Segunda Mano", "ESTIMACIÓN CONTEXTUAL"

    @classmethod
    def _ask_gemini_estimator(cls, title: str, description: str, price: float) -> Optional[Dict[str, Any]]:
        """Consulta a Google Gemini API para estimar producto y precio de mercado si la clave está configurada."""
        if not GEMINI_API_KEY or not requests:
            return None

        prompt = f"""Eres un tasador experto en mercados de segunda mano en España (Wallapop, Vinted, Milanuncios).
Analiza este anuncio:
- Título: {title}
- Descripción: {description[:300]}
- Precio ofertado: {price} EUR

Devuelve EXCLUSIVAMENTE un JSON válido (sin markdown ni bloques de código extra) con este formato:
{{
  "clean_name": "Nombre estándar del producto (ej: Sony WH-1000XM4)",
  "category": "Consolas|Móviles|Informática|Audio|Fotografía|Moda|Herramientas|Hogar|General",
  "market_price": 0.0 (mediana aproximada habitual en segunda mano en buen estado en euros)
}}"""

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}
            }
            resp = requests.post(url, json=payload, timeout=4)
            if resp.status_code == 200:
                res_data = resp.json()
                text_out = res_data["candidates"][0]["content"]["parts"][0]["text"]
                # Extraer JSON del texto
                text_out = text_out.strip()
                if "```json" in text_out:
                    text_out = text_out.split("```json")[1].split("```")[0].strip()
                elif "```" in text_out:
                    text_out = text_out.split("```")[1].split("```")[0].strip()
                return json.loads(text_out)
        except Exception as e:
            print(f"[DealScorer Gemini] Error al consultar IA: {e}")

        return None


