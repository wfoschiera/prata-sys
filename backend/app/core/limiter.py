"""Shared rate limiter instance.

Defined here to break the circular import that would occur if login.py
imported the limiter from main.py (main.py → api_router → login.py → main.py).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Keyed by client IP (get_remote_address reads request.client.host, which reflects
# the real client IP once the backend trusts Caddy's X-Forwarded-For — see the
# --forwarded-allow-ips flag on the backend's start command in compose.prod.yml).
# The login endpoint applies a 5/minute limit; sensitive auth endpoints
# (password recovery/reset) have their own explicit limits; everything else
# falls back to the conservative default below.
# Rate limiting is disabled in local/test environments to avoid test interference.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/hour"],
    enabled=settings.ENVIRONMENT in {"production", "staging"},
)
