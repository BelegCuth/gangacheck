import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Configuración del Servidor
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Base de datos local por defecto
DB_PATH = BASE_DIR / "gangacheck.db"

# Supabase (Opcional para fase nube)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# Gemini API (Opcional para tasación inteligente con IA)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Determinar modo de base de datos
IS_CLOUD_DB = bool(SUPABASE_URL and SUPABASE_KEY)

# Configuración CORS permitida
ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000,https://gangacheck.es,https://www.gangacheck.es,https://gangacheck.onrender.com"
    ).split(",") if origin.strip()
]

# Credenciales para el Panel de Administración privado (/admin)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "belegcuth@gmail.com").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "01Coruña.").strip()
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "").strip() or "01CorunaAdminGangaCheckSecretKey2026."

# Telegram Bot para Alertas de Chollos
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Scanner automático de chollos
AUTO_SCAN_ENABLED = os.getenv("AUTO_SCAN_ENABLED", "false").lower() == "true"
AUTO_SCAN_INTERVAL_MINUTES = int(os.getenv("AUTO_SCAN_INTERVAL_MINUTES", "20"))
AUTO_SCAN_MIN_SCORE = float(os.getenv("AUTO_SCAN_MIN_SCORE", "8.0"))
AUTO_SCAN_MIN_SAVINGS = float(os.getenv("AUTO_SCAN_MIN_SAVINGS", "40"))
AUTO_SCAN_KEYWORDS = [
    kw.strip() for kw in os.getenv(
        "AUTO_SCAN_KEYWORDS",
        "PlayStation 5,iPhone 13 128GB,iPhone 14 128GB,Samsung Galaxy S25,Samsung Galaxy S24,Nintendo Switch OLED,RTX 4070,MacBook Air M1,Steam Deck"
    ).split(",") if kw.strip()
]
