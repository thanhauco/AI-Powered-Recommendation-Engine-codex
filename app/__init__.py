from __future__ import annotations

"""
Application package initialization.

Exposes the top-level application factory for external tooling (e.g., uvicorn).
"""

from .main import get_application

__all__ = ["get_application"]
