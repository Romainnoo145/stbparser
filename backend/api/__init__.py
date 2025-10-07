"""
API Module

FastAPI web server for receiving Offorte webhooks.
"""

from .server import app

__all__ = ["app"]
