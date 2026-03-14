"""Shared rate limiter instance.

Defined here to break the circular import that would occur if login.py
imported the limiter from main.py (main.py → api_router → login.py → main.py).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Keyed by client IP. The login endpoint applies a 5/minute limit;
# all other endpoints use the default (none) unless explicitly decorated.
# Rate limiting is disabled in local/test environments to avoid test interference.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    enabled=settings.ENVIRONMENT == "production",
)
