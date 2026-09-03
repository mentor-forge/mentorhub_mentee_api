"""E2E Bearer JWT for black-box API tests (Developer Edition ``login.html`` persona defaults).

Uses ``JWT_SECRET``, ``JWT_ISSUER``, ``JWT_AUDIENCE``, and ``JWT_ALGORITHM`` from the
environment when set (``pipenv run e2e`` exports the Developer Edition defaults). Override
those variables to match a non-default API stack (same values the container / compose uses).

Persona claims align with ``welcome-auth.js`` / ``login.html`` (``profile_id`` is required
by ``api-utils`` 1.0.1 token validation). Installed ``Token.to_dict()`` maps JWT
``display_name`` (or OIDC ``name``) to the application ``display_name`` field.
"""

from __future__ import annotations

import os
import time
from typing import Iterable

import jwt

# Defaults match login.html / compose JWT settings (HS256, iss dev-idp, aud dev-api) and Pipfile dev/e2e.
_DEFAULT_JWT_SECRET = "local-dev-jwt-secret-fixed"
_DEFAULT_JWT_ISSUER = "dev-idp"
_DEFAULT_JWT_AUDIENCE = "dev-api"
_DEFAULT_JWT_ALGORITHM = "HS256"

# Mike Storey — admin persona from Profile.0.1.0.0.json / welcome-auth.js
_E2E_SUBJECT = "mike"
_E2E_DISPLAY_NAME = "Mike Storey"
_E2E_ROLES = ("admin",)
_E2E_PROFILE_ID = "A00000000000000000000001"
_E2E_CUSTOMER_ID = "D00000000000000000000006"
_E2E_MENTOR_ID = ""


def get_auth_token(
    *,
    roles: Iterable[str] | None = None,
    sub: str | None = None,
    display_name: str | None = None,
    profile_id: str | None = None,
    customer_id: str | None = None,
    mentor_id: str | None = None,
) -> str:
    """Mint a long-lived JWT for black-box tests."""
    secret = os.environ.get("JWT_SECRET") or _DEFAULT_JWT_SECRET
    issuer = os.environ.get("JWT_ISSUER") or _DEFAULT_JWT_ISSUER
    audience = os.environ.get("JWT_AUDIENCE") or _DEFAULT_JWT_AUDIENCE
    algorithm = os.environ.get("JWT_ALGORITHM") or _DEFAULT_JWT_ALGORITHM
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": sub or _E2E_SUBJECT,
        "display_name": display_name or _E2E_DISPLAY_NAME,
        "iat": now,
        "exp": now + 10 * 365 * 24 * 60 * 60,
        "roles": list(roles) if roles is not None else list(_E2E_ROLES),
        "profile_id": profile_id or _E2E_PROFILE_ID,
        "customer_id": customer_id if customer_id is not None else _E2E_CUSTOMER_ID,
        "mentor_id": mentor_id if mentor_id is not None else _E2E_MENTOR_ID,
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token
