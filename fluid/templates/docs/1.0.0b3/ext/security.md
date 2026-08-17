{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Security{% endblock %}
{% block doc_section %}Extensions{% endblock %}

{% block summary %}
`EXT_SECURITY` ships a user store with roles and permissions, argon2 hashing, a double-submit CSRF
guard, signed single-use tokens, 2FA and OAuth models, and a set of FastAPI dependencies that gate
routes. It gives you **building blocks, not flows** — registration, login, 2FA enrollment and
password reset routes are yours to write. It **requires `EXT_SQLALCHEMY`**.
{% endblock %}

{% block body %}
## Enabling

```ini
[extensions]
EXT_SQLALCHEMY = 1
EXT_SCHEDULING = 1
EXT_SECURITY = 1

[security]
SECURITY_SECRET = a-long-random-secret
```

- `SECURITY_SECRET` is **required in production**. In debug mode it falls back to a fixed
  development secret and logs a warning at startup.
- `EXT_SCHEDULING` is not enforced, but without it the `ExpiredToken` cleanup job never runs and
  that table grows forever.
- The battery adds eight models — run the migration cycle after enabling it.

## The four services

Reached through `webfluid.core.ext.security`:

| Service                  | Responsibility                                                     |
|--------------------------|--------------------------------------------------------------------|
| `security.user_service`  | Current user, route guards, predicates, bearer grants              |
| `security.hash_service`  | argon2 `hash` / `verify` and the thread-pooled `ahash` / `averify` |
| `security.token_service` | CSRF, signed single-use tokens                                     |
| `security.oauth_service` | authlib-backed social login                                        |

## The models

`webfluid.extensions.security.models`:

| Model                | Table                  | Notes                                                                                     |
|----------------------|------------------------|-------------------------------------------------------------------------------------------|
| `User`               | `users`                | `username` (unique), `email`, `pending_email`, `email_verified`, `psw_hash`, `created_at` |
| `Identity`           | `identities`           | OAuth link. Unique on `(sub, provider)`                                                   |
| `Role`               | `roles`                | `name` (unique), `is_admin`, `requires_2fa`                                               |
| `Permission`         | `permissions`          | `name` (unique)                                                                           |
| `TOTPSecret`         | `totp_secrets`         | One per user, `confirmed` flag                                                            |
| `WebAuthnCredential` | `webauthn_credentials` | Passkeys                                                                                  |
| `BackupCode`         | `backup_codes`         | `code_hash`, `used`                                                                       |
| `ExpiredToken`       | `expired_tokens`       | Burned single-use tokens                                                                  |

Association tables: `user_roles`, `role_permissions`.

`User.__init__(username, email, psw_hash=None)`, `Role.__init__(name, require_2fa=False)`,
`Permission.__init__(name)`.

### Relationship loading — the thing that bites

Every relationship is `lazy="raise_on_sql"` **except** `user.totp_secret` and
`user.webauthn_credentials`, which are `selectin` because the 2FA gate reads them on every gated
request.

```text
raise_on_sql:  user.roles, user.identities, user.backup_codes,
               role.users, role.permissions, permission.roles,
               and every reverse side
selectin:      user.totp_secret, user.webauthn_credentials
```

{{ warning("user.roles does not return an empty list when unloaded — it raises. That is deliberate:
    the gates query the association tables directly and never navigate a relationship, so eager
    loading them on every authenticated request was pure waste (role.users in particular meant
    hydrating every holder of a role). Load explicitly with selectinload when you actually need
    them.") }}

```python
from sqlalchemy.orm import selectinload


async def roles_of(user_id: int) -> list[str]:
    async with db.async_executor(model=User) as e:
        result = await e.exec(
            select(User).where(User.id == user_id).options(selectinload(User.roles))
        )
        user = result.first()
        return [role.name for role in user.roles]
```

## Registration and authentication

The validators are built to plug into Pydantic:

```python
# fluid/schemas/accounts.py
from pydantic import BaseModel, EmailStr, field_validator
from webfluid.extensions.security.utils import validate_username, validate_password


class CreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str

    _validate_username = field_validator("username")(validate_username)
    _validate_password = field_validator("password")(validate_password)
```

- `validate_username` enforces `^[a-zA-Z0-9_-]{3,30}$` and raises `ValueError("INVALID_USERNAME")`.
- `validate_password` raises a `ValueError` carrying an `.errors` list of symbolic codes:
  `MIN_LENGTH_8`, `MIN_LOWER_1`, `MIN_UPPER_1`, `MIN_DIGITS_1`, `MIN_SPECIAL_1`.

```python
# fluid/services/accounts.py
from webfluid.core.ext import db, security
from webfluid.extensions.security.models import User
from sqlalchemy import select


async def register(data) -> User:
    psw_hash = await security.hash_service.ahash(data.password)
    async with db.async_executor(model=User) as e:
        user = User(data.username, data.email, psw_hash)
        await e.insert(user, flush=True)
        return user


async def authenticate(username: str, password: str) -> User | None:
    async with db.async_executor(model=User) as e:
        result = await e.exec(select(User).where(User.username == username))
        user = result.first()
        if not user or not user.psw_hash: return None
        if not await security.hash_service.averify(user.psw_hash, password): return None
        return user
```

{{ rule("Use ahash / averify inside async code. argon2 costs roughly 40ms of pure CPU per call; the
    sync hash() blocks the event loop for every one of those milliseconds. The async pair runs on a
    dedicated ThreadPoolExecutor sized by SECURITY_HASHER_THREADS, which also caps how many logins
    can hash concurrently — that is intentional.") }}

## Login and logout

The current user is derived from `request.session["user_id"]`. Login stores it, logout drops it —
the session cookie is already signed by the framework.

```python
async def login(request: Request):
    data = await request.json()
    user = await authenticate(data["username"], data["password"])
    if not user:
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
    request.session["user_id"] = user.id
    return {"id": user.id, "username": user.username}


async def logout(request: Request):
    request.session.pop("user_id", None)
    return {"status": "ok"}
```

After a successful second-factor verification, set `request.session["2fa_verified"] = True` — that
is the flag `require_2fa` checks.

## Route guards

`security.user_service` exposes each guard twice: as a ready `Depends` object (attribute or method)
and as the bare resolver (`*_fn`).

```python
svc = security.user_service

# Attributes — fixed guards, no call:
async def me(user = svc.current_user): ...        # User | None, no enforcement
async def home(user = svc.require_user): ...      # 401 NOT_AUTHENTICATED
async def secure(user = svc.require_2fa): ...     # + 401 TWO_FA_REQUIRED
async def admin(user = svc.require_admin): ...    # + 403 NOT_AUTHORIZED

# Methods — parametrised guards, called:
async def a(user = svc.require_roles(["editor", "admin"])): ...       # all of them
async def b(user = svc.require_any_role(["editor", "moderator"])): ...# at least one
async def c(user = svc.require_permissions(["posts:write"])): ...     # all of them
async def d(user = svc.require_any_permission(["a", "b"])): ...       # at least one
```

### The gate chain

```text
current_user                  session lookup, yields User | None
  └── require_user            + CSRF check on unsafe methods, 401 NOT_AUTHENTICATED
        └── [EmailVerifiedGate]  401 EMAIL_NOT_VERIFIED if email is unset or
            │                    email_verified is False        (new in 1.0.0b3)
            └── require_2fa      401 TWO_FA_REQUIRED if the user HAS a second factor
                  │              configured and session["2fa_verified"] is not set
                  ├── require_admin
                  ├── require_roles / require_any_role
                  ├── require_permissions / require_any_permission
                  └── requirement_or_grant / requirement_and_grant
```

Three consequences:

- **Every** role or permission guard also enforces authentication, CSRF, a verified email and 2FA.
- `require_2fa` is a no-op for a user who has no second factor at all — it gates the ones who do.
- **Bare `require_user` is the only guard that lets an unverified email through.** That is what makes
  a verification flow reachable: put the "confirm your address" page behind `require_user`, and
  everything else behind anything below it in the chain.

{{ warning("The email gate is new in 1.0.0b3 and changes behaviour on upgrade. Every existing user
    with email_verified = False is refused from every gated route. Ship a verification flow, or
    backfill the flag for accounts you already trust. Predicate:
    security.user_service.email_verified(user) — note it returns the email string or the flag, not a
    strict bool, so compare truthiness.") }}

{{ info("The user handed to your route is detached — the dependency expunges it and closes the
    session before yielding, so an authenticated request does not hold a pool slot for its whole
    lifetime. Columns are present; relationships raise.") }}

### Predicates and `_fn` twins

For a user object you already hold:

```python
svc.email_verified(user)                 # sync
svc.has_2fa(user)                        # sync
await svc.is_admin(user)
await svc.has_roles(user, ["editor"])
await svc.has_any_role(user, [...])
await svc.has_permissions(user, [...])
await svc.has_any_permission(user, [...])
await svc.check_requirement(user, {"requirement": "has_any_role", "roles": ["editor"]})
```

`check_requirement` accepts the requirement dictionaries used by the grant gates, validates their
shape (raising `ValueError` on a bad one) and short-circuits to `True` for an admin.

Every guard also has a `_fn` twin — `svc.require_admin_fn`, `svc.require_roles_fn(roles)` — which
is the same resolver without the `Depends` wrapper, for use outside a route signature.

## CSRF

Double-submit: a signed token in a cookie, the same value in the `X-CSRF-Token` header, and the raw
value in the session.

```python
# GET once to receive the cookie and seed the session
async def csrf(request: Request):
    return security.token_service.csrf_response(request)

# Guard a standalone route (require_user already does this)
async def submit(request: Request, _ = security.token_service.csrf_protect): ...
```

`csrf_protect` skips `GET`, `HEAD` and `OPTIONS`. Failure modes: `403 MISSING_CSRF`,
`403 INVALID_CSRF`, `403 CSRF_MISMATCH`, `403 TOKEN_EXPIRED`, `403 INVALID_TOKEN`. The cookie name
comes from `SECURITY_CSRF_COOKIE_NAME` and is honoured by both halves since `1.0.0b2`.

Both halves are shape-checked since `1.0.0b3`: a validly signed payload that is not a `dict`, or
whose `csrf` entry is not a `str`, answers `403 INVALID_CSRF` instead of 500. `validate_token` also
catches `BadData` rather than only `BadSignature`, so a well-signed but undecodable payload comes
back as a 403 instead of a raw `itsdangerous` error.

## Single-use tokens

```python
svc = security.token_service

token = svc.generate_token({"user_id": user.id}, salt="verify-email")
data = await svc.validate_token(token, salt="verify-email")
```

- `salt="csrf"` (the default) validates the signature and age only.
- **Any other salt burns the token**: it is recorded in `expired_tokens`, so a second call raises
  `403 TOKEN_EXPIRED` even though the signature is still valid.
- A tampered token raises `403 INVALID_TOKEN`; an aged one `403 TOKEN_EXPIRED`.

Use a distinct salt per flow (`"verify-email"`, `"reset-password"`, `"invite"`) — a token minted for
one flow then cannot be replayed into another.

## Bearer grants: one route, browser and machine

With `EXT_JWT` enabled:

```python
# A logged-in editor, OR a token whose "permissions" claim carries "posts:write"
async def publish(user = svc.requirement_or_grant(
    {"requirement": "has_any_role", "roles": ["editor", "admin"]},
    "posts:write"
)): ...

# Simply authenticated, OR a valid grant
async def ingest(user = svc.requirement_or_grant(
    {"requirement": "is_authenticated"}, "data:ingest"
)): ...

# Both required
async def critical(user = svc.requirement_and_grant({"requirement": "is_admin"}, "ops:write")): ...
```

Requirement dictionaries: `{"requirement": "<name>"}` plus `"roles"` or `"permissions"` where the
name needs them. Valid names: `is_authenticated`, `is_admin`, `has_2fa`, `has_roles`,
`has_any_role`, `has_permissions`, `has_any_permission`. An admin passes the requirement side
unconditionally.

For the token side alone: `svc.resolve_bearer(request, grant)` yields `(user, token_present)`,
`svc.bearer_principal(request, grant)` yields just the user.

### How the fallback actually works

```text
try:    the full session chain  (require_user -> email -> 2fa -> requirement)
except HTTPException as session_exc:
        resolve_bearer(request, grant)
            principal is None and a token was present -> 403 NOT_AUTHORIZED
            principal is None and no token            -> re-raise session_exc
            principal                                  -> yield it
```

{{ warning("The except catches EVERY HTTPException the session chain raises — 401
    NOT_AUTHENTICATED, 403 MISSING_CSRF / CSRF_MISMATCH, 401 TWO_FA_REQUIRED and 401
    EMAIL_NOT_VERIFIED. A valid grant therefore bypasses all four. CSRF and 2FA being bypassed is by
    design for a machine client; the email gate being bypassed is not, and is a known issue. Mint
    grant tokens only for principals you have already verified.") }}

{{ rule("Put the user's primary key in sub. resolve_bearer resolves the principal with int(sub); a
    uuid or an email is rejected as an unusable token (401 since 1.0.0b3, 500 before that) and never
    authenticates.") }}

## OAuth

```python
@register_config(10)
class Config:
    SECURITY_OAUTH_CLIENTS = {
        "google": {
            "client_id": "...",
            "client_secret": "...",
            "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
            "client_kwargs": {"scope": "openid email profile"}
        }
    }
```

```python
svc = security.oauth_service

svc.client            # Depends -> the authlib client for a `provider` path param
svc.prepare_session   # Depends -> stores device ("mobile"/"desktop") + redirect in the session
svc.userinfo          # Depends -> completes the callback and returns the userinfo mapping
svc.authorize_response(request, provider, device, csrf=None)
svc.register_provider(name, client)      # runtime registration
svc.unregister_provider(name)
```

`authorize_response` returns a `RedirectResponse` for `device="mobile"` and an HTML page that
`postMessage`s the opener and closes itself for `device="desktop"`. Pass the `csrf_response` as
`csrf=` to carry its `Set-Cookie` through. Link the external account to a user via the `Identity`
model (`sub` + `provider`).

Unknown provider → `400 UNKNOWN_PROVIDER`; a mismatching state → `400 INVALID_STATE`.

{{ rule("The ?redirect= parameter is sanitised to a same-site absolute path since 1.0.0b3: an
    absolute URL, a protocol-relative //host and a /\\host all collapse to /. Before that a crafted
    login link sent the user to any origin after a successful sign-in. Do not reimplement the
    redirect yourself with the raw query parameter.") }}

## Two-factor and policy

`TOTPSecret`, `WebAuthnCredential` and `BackupCode` are storage — the enrollment and verification
routes are yours. `has_2fa(user)` is true when a confirmed TOTP secret exists or the user has at
least one WebAuthn credential.

`Role.requires_2fa` is a field the battery **never reads itself**. It exists for the app on top:
look it up and compose it with `require_user` and `has_2fa` into a gate of your own, the same way
`require_2fa` composes `require_user` internally. Deciding what "requires 2FA" means for your roles
is policy, and policy belongs to your app.

## Config reference

| Key                              | Default                                               |
|----------------------------------|-------------------------------------------------------|
| `SECURITY_SECRET`                | env `SECURITY_SECRET`; required in production         |
| `SECURITY_TOKEN_MAX_AGE`         | `3600`                                                |
| `SECURITY_CSRF_COOKIE_NAME`      | `"csrf_token"`                                        |
| `SECURITY_CSRF_COOKIE_SECURE`    | `True`                                                |
| `SECURITY_HASHER_TIME_COST`      | `3`                                                   |
| `SECURITY_HASHER_MEMORY_COST`    | `65536`                                               |
| `SECURITY_HASHER_PARALLELISM`    | `4`                                                   |
| `SECURITY_HASHER_THREADS`        | `4`                                                   |
| `SECURITY_PASSWORD_MIN_LENGTH`   | `8`                                                   |
| `SECURITY_PASSWORD_REQUIREMENTS` | `{"lower": 1, "upper": 1, "digits": 1, "special": 1}` |
| `SECURITY_OAUTH_CLIENTS`         | `{}`                                                  |
| `SECURITY_MODELS_DB_BIND`        | `None`                                                |

{{ warning("SECURITY_PASSWORD_REQUIREMENTS is read key by key with a fallback of 1, so a class you
    omit still demands one character. Set it to 0 explicitly to drop it.") }}

## Next

- [`ext/jwt.md`]({{ base }}ext/jwt.md) — the token side of the grant gates.
- [`ext/events.md`]({{ base }}ext/events.md) — the next battery.
- [`ref/extensions.md`]({{ base }}ref/extensions.md) — the terse API list.
{% endblock %}
