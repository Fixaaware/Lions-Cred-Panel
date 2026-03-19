# ============================================================
#  Lions Cred  |  Configurações da Aplicação
# ============================================================

import os

class Config:
    # --- Banco de Dados (SQLite) ---
    DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "database", "lions_cred.db"))
    JSON_PATH = os.getenv("JSON_PATH", os.path.join(os.path.dirname(__file__), "database", "data.json"))
    # Postgres (Neon ou outro) – obrigatório em produção.
    # Formato: postgres://usuario:senha@host:port/banco  (ou postgresql://)
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # --- Flask ---
    SECRET_KEY  = os.getenv("SECRET_KEY",  "lions-cred-secret-2026")
    DEBUG       = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    HOST        = os.getenv("FLASK_HOST",  "0.0.0.0")
    PORT        = int(os.getenv("FLASK_PORT", 5000))
