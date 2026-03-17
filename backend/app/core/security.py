from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

# Use fast Argon2 params in local/staging to speed up tests (~0.3s → ~0.001s per hash).
# Production keeps the secure defaults (time_cost=3, memory_cost=65536, parallelism=4).
if settings.ENVIRONMENT == "production":
    _argon2_hasher = Argon2Hasher()
else:
    _argon2_hasher = Argon2Hasher(time_cost=1, memory_cost=1024, parallelism=1)

password_hash = PasswordHash(
    (
        _argon2_hasher,
        BcryptHasher(),
    )
)


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    return password_hash.verify_and_update(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)
