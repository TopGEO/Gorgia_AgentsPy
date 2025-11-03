"""API entry point - exports the FastAPI app for uvicorn/gunicorn"""
from .routes.chat import app

__all__ = ["app"]