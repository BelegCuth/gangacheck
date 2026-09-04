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
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin@gangacheck.es").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "GangaCheck2026!").strip()
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "").strip() or secrets.token_hex(32)



