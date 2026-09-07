"""
Módulo de notificaciones — Envía alertas de chollos detectados por Telegram.
Usa la API de Telegram Bot (HTTP POST puro, sin dependencias adicionales).
"""
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, Optional

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def is_telegram_configured() -> bool:
    """Comprueba si las credenciales de Telegram están configuradas."""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def _safe_log(text: str):
    """Imprime mensajes de forma segura evitando errores de codificación en consolas Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(text.encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass


def send_telegram(message: str, parse_mode: str = "HTML") -> bool:
    """
    Envía un mensaje al chat de Telegram configurado.
    Usa la API HTTP directa — sin librerías externas.
    """
    if not is_telegram_configured():
        _safe_log("[Notifier] Telegram no configurado (falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID).")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=10)
        if res.status == 200:
            _safe_log(f"[Notifier] ✅ Mensaje enviado a Telegram (chat {TELEGRAM_CHAT_ID}).")
            return True
        else:
            _safe_log(f"[Notifier] ⚠️ Telegram respondió con código {res.status}.")
            return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        _safe_log(f"[Notifier] ❌ Error HTTP {e.code} al enviar a Telegram: {body}")
        return False
    except Exception as e:
        _safe_log(f"[Notifier] ❌ Error al enviar a Telegram: {e}")
        return False


def format_deal_alert(deal: Dict[str, Any]) -> str:
    """
    Genera un mensaje HTML formateado con toda la información del chollo.
    Optimizado para Telegram con emojis, negritas y enlace directo.
    """
    score = float(deal.get("score", 0))
    title = deal.get("title", "Producto desconocido")
    price = float(deal.get("price", 0))
    market_price = float(deal.get("market_price", 0))
    savings = float(deal.get("savings", 0))
    savings_pct = float(deal.get("savings_pct", 0))
    platform = deal.get("platform", "desconocida")
    risk_level = deal.get("risk_level", "NORMAL")
    url = deal.get("url", "")
    verdict = deal.get("verdict", "")
    seller_name = deal.get("seller_name", "")
    keyword = deal.get("keyword", "")

    # Emoji según la nota
    if score >= 9.5:
        fire = "🔥🔥🔥"
        label = "CHOLLO INCREÍBLE"
    elif score >= 9.0:
        fire = "🔥🔥"
        label = "CHOLLO EXCELENTE"
    elif score >= 8.0:
        fire = "🔥"
        label = "BUEN CHOLLO"
    else:
        fire = "📢"
        label = "OPORTUNIDAD"

    # Emoji de riesgo
    risk_emoji = "🟢 BAJO" if risk_level == "BAJO" else ("🟡 MEDIO" if risk_level == "MEDIO" else "🔴 ALTO")

    # Emoji de plataforma
    plat_emoji = {"wallapop": "🟢", "vinted": "🔵", "milanuncios": "🟠"}.get(platform.lower(), "⚪")

    now = datetime.now().strftime("%H:%M")

    msg = f"""{fire} <b>{label} — Nota {score}/10</b>

📦 <b>{title}</b>
💰 Precio: <b>{price:.0f}€</b> (Mercado: {market_price:.0f}€)
📉 Ahorro: <b>{savings:.0f}€</b> ({savings_pct:.0f}% bajo mercado)
{plat_emoji} Plataforma: <b>{platform.capitalize()}</b>
⚠️ Riesgo: {risk_emoji}"""

    if seller_name:
        msg += f"\n👤 Vendedor: {seller_name}"

    if keyword:
        msg += f"\n🔍 Búsqueda: {keyword}"

    if url:
        msg += f"\n\n🔗 <a href=\"{url}\">Ver anuncio original →</a>"

    msg += f"\n\n⏱️ Detectado: {now} — <b>¡Actúa rápido!</b>"

    return msg


def notify_deal(deal: Dict[str, Any]) -> bool:
    """Formatea y envía una alerta de chollo a Telegram."""
    message = format_deal_alert(deal)
    return send_telegram(message)


def send_test_message() -> bool:
    """Envía un mensaje de prueba para verificar la conexión con Telegram."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = f"""✅ <b>GangaCheck — Conexión Verificada</b>

🔔 Las alertas de chollos están configuradas correctamente.
📡 Servidor: Render Cloud
🗓️ Fecha: {now}

Recibirás notificaciones automáticas cuando se detecten chollos con:
• Nota ≥ 8.0/10
• Ahorro ≥ 40€

<i>— GangaCheck.es 🔥</i>"""
    return send_telegram(msg)


def send_scan_summary(keyword: str, total_found: int, deals_count: int, best_deal: Optional[Dict] = None) -> bool:
    """Envía un resumen del ciclo de escaneo (solo si hay chollos)."""
    if deals_count == 0:
        return False

    msg = f"""📊 <b>Resumen de Escaneo Automático</b>

🔍 Producto: <b>{keyword}</b>
📦 Anuncios encontrados: {total_found}
🔥 Chollos detectados: <b>{deals_count}</b>"""

    if best_deal:
        msg += f"""

🏆 <b>Mejor chollo:</b>
{best_deal.get('title', 'N/A')} — {float(best_deal.get('price', 0)):.0f}€ (Ahorro: {float(best_deal.get('savings', 0)):.0f}€)"""

    return send_telegram(msg)
