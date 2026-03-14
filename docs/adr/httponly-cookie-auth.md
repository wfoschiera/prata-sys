# ADR: Migrate JWT storage from localStorage to httpOnly cookies

**Status:** Deferred
**Date:** 2026-03-14

## Context

The current authentication flow stores the JWT access token in `localStorage`:

```ts
// frontend/src/main.tsx
OpenAPI.TOKEN = async () => {
  return localStorage.getItem("access_token") || ""
}
```

Tokens stored in `localStorage` are readable by any JavaScript running on the page. This means a successful XSS attack — injected script via a user-supplied value, a compromised dependency, or a CDN hijack — can silently exfiltrate the token and impersonate the user until it expires.

As a temporary mitigation (PR #24), the protected layout's `beforeLoad` now validates the token against the backend on every navigation, so stale tokens no longer leave the user on a blank page. However, the XSS risk remains.

## Decision

Migrate to **httpOnly, SameSite=Strict cookies** for token storage. httpOnly cookies are set and cleared by the server and are never accessible to JavaScript — XSS cannot read them.

## Implementation Plan

### Backend changes (`backend/app/api/routes/login.py`)

1. Change `POST /login/access-token` to set the token as a cookie instead of returning it in the JSON body:

```python
from fastapi import Response

@router.post("/login/access-token")
def login_access_token(response: Response, ...) -> None:
    token = create_access_token(subject=user.id)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="strict",
        secure=True,       # require HTTPS in production
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
```

2. Add `POST /logout` endpoint that clears the cookie:

```python
@router.post("/logout")
def logout(response: Response) -> None:
    response.delete_cookie("access_token")
```

3. Update `get_current_user` dependency to read the token from the cookie instead of the `Authorization` header:

```python
from fastapi import Cookie

async def get_current_user(access_token: str | None = Cookie(default=None)) -> User:
    ...
```

4. Update CORS settings to allow credentials:

```python
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,   # required for cookies
    allow_origins=[settings.FRONTEND_HOST],
)
```

### Frontend changes

1. Remove `localStorage` token handling from `main.tsx` — `OpenAPI.TOKEN` is no longer needed since the browser sends the cookie automatically.

2. Update `useAuth` login/logout mutations to call the new endpoints (no token to store/remove):

```ts
const login = async (data: AccessToken) => {
  await LoginService.loginAccessToken({ formData: data })
  // cookie is set by the server — nothing to store
}

const logout = async () => {
  await LoginService.logout()
  // cookie is cleared by the server
}
```

3. The `isLoggedIn()` helper in `useAuth.ts` becomes unreliable (we can no longer read the cookie from JS). Remove it and rely solely on the `beforeLoad` backend validation introduced in PR #24.

4. All `fetch`/OpenAPI client calls must include `credentials: "include"` to send the cookie cross-origin. Configure the generated client:

```ts
OpenAPI.WITH_CREDENTIALS = true
```

## Trade-offs

| | localStorage (current) | httpOnly cookie |
|---|---|---|
| XSS resistant | No | **Yes** |
| CSRF resistant | Yes (no auto-send) | Requires `SameSite=Strict` or CSRF token |
| Works cross-origin | Yes | Requires `credentials: include` + CORS |
| Readable by JS | Yes | **No** |
| Revocable server-side | No (stateless JWT) | No (stateless JWT) |

`SameSite=Strict` mitigates CSRF for same-site navigation. For cross-origin API clients (e.g., mobile apps or third-party integrations), the `Authorization` header approach should be kept as an alternative.

## Why deferred

1. Requires coordinated changes across backend auth, CORS config, the generated OpenAPI client, and all frontend auth flows — a non-trivial surface area.
2. The OpenAPI-generated client (`frontend/src/client/`) does not natively support `credentials: include` without custom configuration; needs verification after client regeneration.
3. The E2E Playwright tests use `storageState` to manage auth cookies — test setup needs updating to work with server-set cookies instead of `localStorage` tokens.

## References

- [OWASP: HTML5 Security — localStorage](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#local-storage)
- [OWASP: Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [FastAPI docs: OAuth2 with cookies](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- PR #24 — immediate mitigation (backend token validation in `beforeLoad`)
