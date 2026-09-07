"""
Scanner automático de chollos — Rastrea Vinted + Milanuncios periódicamente,
evalúa cada resultado con el DealScorer y envía alertas por Telegram.
"""
import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Optional

from config import (
    AUTO_SCAN_ENABLED, AUTO_SCAN_INTERVAL_MINUTES,
    AUTO_SCAN_MIN_SCORE, AUTO_SCAN_MIN_SAVINGS, AUTO_SCAN_KEYWORDS,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)
from harvester import MarketHarvester
from scorer import DealScorer
from database import find_closest_benchmark, save_scan
from notifier import notify_deal, is_telegram_configured, send_scan_summary


class AutoScanner:
    """
    Scanner periódico que rastrea webs de segunda mano buscando chollos
    y envía alertas en tiempo real por Telegram.
    """

    def __init__(self):
        self.is_running = False
        self.last_scan_time: Optional[datetime] = None
        self.next_scan_time: Optional[datetime] = None
        self.total_scans_completed = 0
        self.total_deals_notified = 0
        self.total_items_scanned = 0
        self.last_scan_results: Dict[str, Any] = {}
        self.scan_history: List[Dict[str, Any]] = []

        # IDs ya notificados para no enviar duplicados
        self._notified_ids: Set[str] = set()

        # Configuración activa (puede modificarse en runtime)
        self.keywords = list(AUTO_SCAN_KEYWORDS)
        self.min_score = AUTO_SCAN_MIN_SCORE
        self.min_savings = AUTO_SCAN_MIN_SAVINGS
        self.interval_minutes = AUTO_SCAN_INTERVAL_MINUTES

        # Thread del scanner
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def get_status(self) -> Dict[str, Any]:
        """Devuelve el estado actual del scanner."""
        return {
            "is_running": self.is_running,
            "telegram_configured": is_telegram_configured(),
            "auto_scan_enabled": AUTO_SCAN_ENABLED,
            "interval_minutes": self.interval_minutes,
            "min_score": self.min_score,
            "min_savings": self.min_savings,
            "keywords": self.keywords,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "next_scan_time": self.next_scan_time.isoformat() if self.next_scan_time else None,
            "total_scans_completed": self.total_scans_completed,
            "total_deals_notified": self.total_deals_notified,
            "total_items_scanned": self.total_items_scanned,
            "last_scan_results": self.last_scan_results,
            "scan_history": self.scan_history[-10:]  # Últimos 10 ciclos
        }

    def update_config(self, keywords: Optional[List[str]] = None,
                      min_score: Optional[float] = None,
                      min_savings: Optional[float] = None,
                      interval_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Actualiza la configuración del scanner en runtime."""
        if keywords is not None:
            self.keywords = [kw.strip() for kw in keywords if kw.strip()]
        if min_score is not None:
            self.min_score = max(0.0, min(10.0, min_score))
        if min_savings is not None:
            self.min_savings = max(0.0, min_savings)
        if interval_minutes is not None:
            self.interval_minutes = max(5, min(1440, interval_minutes))

        print(f"[AutoScanner] Config actualizada: {len(self.keywords)} keywords, "
              f"min_score={self.min_score}, min_savings={self.min_savings}€, "
              f"interval={self.interval_minutes}min")

        return self.get_status()

    def _evaluate_listing(self, listing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evalúa un anuncio individual con el DealScorer.
        Retorna el resultado completo si es un chollo, None si no.
        """
        title = listing.get("title", "")
        price = float(listing.get("price", 0))
        if price <= 0:
            return None

        # Buscar benchmark de referencia
        benchmark = find_closest_benchmark(title)
        if not benchmark:
            return None

        # Construir item para el scorer
        item = {
            "title": title,
            "description": "",
            "price": price,
            "seller": {
                "name": listing.get("seller_name", ""),
                "rating": 0,
                "reviews": listing.get("seller_reviews", 0)
            },
            "shipping_available": listing.get("has_shipping", True)
        }

        try:
            result = DealScorer.evaluate(item)
            score = float(result.get("score", 0))
            savings = float(result.get("savings", 0))

            # Enriquecer con datos del listing original
            result["platform"] = listing.get("platform", "desconocida")
            result["url"] = listing.get("url", "")
            result["image_url"] = listing.get("image_url", "")
            result["seller_name"] = listing.get("seller_name", "")
            result["keyword"] = listing.get("keyword", "")

            if score >= self.min_score and savings >= self.min_savings:
                return result
        except Exception as e:
            print(f"[AutoScanner] Error al evaluar '{title[:40]}': {e}")

        return None

    def _run_single_scan(self) -> Dict[str, Any]:
        """Ejecuta un ciclo completo de escaneo para todos los keywords."""
        cycle_start = datetime.now()
        cycle_results = {
            "timestamp": cycle_start.isoformat(),
            "keywords_scanned": 0,
            "total_listings": 0,
            "deals_found": 0,
            "alerts_sent": 0,
            "deals": []
        }

        print(f"\n[AutoScanner] {'='*50}")
        print(f"[AutoScanner] 🔍 Iniciando ciclo de escaneo — {cycle_start.strftime('%H:%M:%S')}")
        print(f"[AutoScanner] Keywords: {', '.join(self.keywords)}")
        print(f"[AutoScanner] Umbral: nota ≥ {self.min_score}, ahorro ≥ {self.min_savings}€")

        for keyword in self.keywords:
            try:
                print(f"[AutoScanner] Rastreando '{keyword}'...")

                # Rastrear en Vinted + Milanuncios (Wallapop bloqueado por WAF)
                result = MarketHarvester.harvest_and_save(keyword, platform="all", limit=30)
                listings = result.get("listings", [])
                cycle_results["total_listings"] += len(listings)
                cycle_results["keywords_scanned"] += 1

                keyword_deals = []

                for listing in listings:
                    listing_id = str(listing.get("id", ""))
                    if listing_id in self._notified_ids:
                        continue  # Ya notificado, skip

                    deal = self._evaluate_listing(listing)
                    if deal:
                        keyword_deals.append(deal)
                        cycle_results["deals_found"] += 1

                        # Enviar alerta por Telegram
                        if is_telegram_configured():
                            success = notify_deal(deal)
                            if success:
                                cycle_results["alerts_sent"] += 1
                                self.total_deals_notified += 1
                                self._notified_ids.add(listing_id)

                        # Guardar el escaneo en la BBDD
                        try:
                            save_scan(deal)
                        except Exception as e:
                            print(f"[AutoScanner] Error al guardar scan: {e}")

                        cycle_results["deals"].append({
                            "title": deal.get("title", ""),
                            "price": deal.get("price", 0),
                            "score": deal.get("score", 0),
                            "savings": deal.get("savings", 0),
                            "platform": deal.get("platform", ""),
                            "url": deal.get("url", "")
                        })

                if keyword_deals:
                    best = max(keyword_deals, key=lambda x: float(x.get("score", 0)))
                    print(f"[AutoScanner] ✅ '{keyword}': {len(keyword_deals)} chollo(s) — "
                          f"Mejor: {best.get('title', '')[:40]} ({best.get('score')}/10, "
                          f"ahorro {best.get('savings', 0)}€)")
                else:
                    print(f"[AutoScanner] — '{keyword}': {len(listings)} anuncios, 0 chollos en umbral.")

                # Pausa entre keywords para no sobrecargar APIs
                time.sleep(2)

            except Exception as e:
                print(f"[AutoScanner] ❌ Error al rastrear '{keyword}': {e}")

        # Mantener los IDs notificados en un tamaño razonable
        if len(self._notified_ids) > 5000:
            self._notified_ids = set(list(self._notified_ids)[-2000:])

        elapsed = (datetime.now() - cycle_start).total_seconds()
        print(f"[AutoScanner] Ciclo completado en {elapsed:.1f}s — "
              f"{cycle_results['deals_found']} chollos, {cycle_results['alerts_sent']} alertas enviadas.")
        print(f"[AutoScanner] {'='*50}\n")

        self.total_scans_completed += 1
        self.total_items_scanned += cycle_results["total_listings"]
        self.last_scan_time = datetime.now()
        self.last_scan_results = cycle_results

        # Historial (mantener últimos 50 ciclos)
        self.scan_history.append({
            "timestamp": cycle_start.isoformat(),
            "duration_s": round(elapsed, 1),
            "listings": cycle_results["total_listings"],
            "deals": cycle_results["deals_found"],
            "alerts": cycle_results["alerts_sent"]
        })
        if len(self.scan_history) > 50:
            self.scan_history = self.scan_history[-50:]

        return cycle_results

    def _scanner_loop(self):
        """Bucle principal del scanner en un thread separado."""
        print(f"[AutoScanner] 🚀 Scanner automático iniciado (cada {self.interval_minutes} min).")

        while not self._stop_event.is_set():
            try:
                self.next_scan_time = datetime.now() + timedelta(minutes=self.interval_minutes)
                self._run_single_scan()
            except Exception as e:
                print(f"[AutoScanner] ❌ Error en ciclo de escaneo: {e}")

            # Esperar hasta el siguiente ciclo (comprobando cada 5 seg si hay que parar)
            wait_seconds = self.interval_minutes * 60
            for _ in range(wait_seconds // 5):
                if self._stop_event.is_set():
                    break
                time.sleep(5)

        self.is_running = False
        print("[AutoScanner] ⏹️ Scanner automático detenido.")

    def start(self):
        """Inicia el scanner en un thread de fondo."""
        if self.is_running:
            print("[AutoScanner] Ya está en ejecución.")
            return

        if not self.keywords:
            print("[AutoScanner] No hay keywords configurados. No se inicia el scanner.")
            return

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scanner_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Detiene el scanner."""
        if not self.is_running:
            return
        print("[AutoScanner] Solicitando parada del scanner...")
        self._stop_event.set()
        self.is_running = False

    def run_once(self) -> Dict[str, Any]:
        """Ejecuta un solo ciclo de escaneo (sin bucle)."""
        return self._run_single_scan()


# Singleton global del scanner
scanner_instance = AutoScanner()
