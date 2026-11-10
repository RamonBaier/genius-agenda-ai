"""Porta de entrada HTTP do servico. Rotas finas: a logica fica em outros modulos."""
from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="Genius Agenda Service", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "timezone": settings.timezone}
