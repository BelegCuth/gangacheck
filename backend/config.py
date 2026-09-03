import os
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
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Gemini API (Opcional para extracción avanzada con IA)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Determinar modo de ejecución
IS_CLOUD_DB = bool(SUPABASE_URL and SUPABASE_KEY)

# Credenciales para el Panel de Administración privado (/admin)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ganga2026!")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "gangacheck-super-secret-admin-session-token-2026")

