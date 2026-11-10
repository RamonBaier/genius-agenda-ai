"""Configuracao lida das variaveis de ambiente (nunca coloque segredos aqui)."""
import os


class Settings:
    timezone: str = os.getenv("TZ", "America/Recife")
    calendar_id: str = os.getenv("GOOGLE_CALENDAR_ID", "")
    google_credentials_file: str = os.getenv(
        "GOOGLE_CREDENTIALS_FILE", "/secrets/credentials.json"
    )


settings = Settings()
