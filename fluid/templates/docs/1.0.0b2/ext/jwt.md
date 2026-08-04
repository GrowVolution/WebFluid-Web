{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}JWTManager{% endblock %}
{% block doc_section %}Extensions{% endblock %}

{% block summary %}
`EXT_JWT` signs and verifies JSON Web Tokens with a **rotating** secret. Each secret is stored in
the cache under a generated key id, which goes into the token header as `kid`, so tokens signed with
an older secret keep verifying until that secret expires. It requires **`EXT_SCHEDULING`** (to run
the rotation) and **`EXT_CACHE`** (to store the secrets).
{% endblock %}

{% block body %}
## Enabling

```ini
[extensions]
EXT_SCHEDULING = 1
EXT_CACHE = 1
EXT_JWT = 1

[data]
REDIS_URI = redis://localhost:6379

[cache]
CACHE_TYPE = redis
```

Missing either dependency raises `FrameworkException` during `Fluid(...)`.

{{ bug("The signing keys live in whatever CACHE_TYPE points at, and the first rotation runs as a
    startup hook. With CACHE_TYPE = legacy the store is in-process, so every restart mints a new key
    and forgets the old ones — every token issued before that restart stops decoding. Run the JWT
    extension against Redis. This is not optional.") }}

## The key lifecycle

```text
startup hook          -> _rotate_secret()
scheduled every       -> _rotate_secret()   (IntervalTrigger, JWT_ROTARY_INTERVAL days)

_rotate_secret():
    kid = uuid4().hex
    cache["jwt:<kid>"]   = secrets.token_hex(JWT_SECRET_LENGTH)   ttl 365 days
    cache["jwt:current"] = kid                                    ttl (interval + 1) days
```

Encoding always uses `jwt:current`. Decoding reads the `kid` from the token header and looks up that
specific secret — so a token signed 20 days ago still verifies while its secret is alive (a year),
even though `jwt:current` has moved on.

## The API

```python
from webfluid.core.ext import jwt

token = jwt.encode(payload, audience="default", expire=None)
token = await jwt.aencode(payload, audience="default", expire=None)

claims = jwt.decode(token, audience="default")
claims = await jwt.adecode(token, audience="default")
```

`encode` copies your payload and adds the standard claims:

| Claim        | Value                                                                       |
|--------------|-----------------------------------------------------------------------------|
| `exp`        | now + `expire` days, or `JWT_EXPIRY_DAYS`                                   |
| `iat`, `nbf` | now                                                                         |
| `iss`        | `JWT_ISSUER`                                                                |
| `aud`        | `JWT_AUDIENCES.get(audience, audience)` — an unmapped name is used verbatim |

The header carries `kid`.

```python
# fluid/services/auth.py
from webfluid.core.ext import jwt


async def issue_token(user_id: int) -> str:
    return await jwt.aencode({"sub": str(user_id)})


async def read_token(token: str) -> dict:
    return await jwt.adecode(token)
```

{{ rule("Put the user's primary key in sub. The security battery's bearer gates resolve the
    principal with int(sub) — a uuid or an email raises ValueError inside the gate's fallback branch,
    where nothing catches it, and the request comes back 500 instead of 401.") }}

{{ rule("Use aencode / adecode inside async code. The sync pair reaches the cache through a blocking
    redis client on the event loop.") }}

## Error handling

{{ bug("A token whose kid is not in the cache surfaces as a raw TypeError from the signing library,
    not as jwt.InvalidTokenError. Catch broadly when you decode by hand:") }}

```python
from fastapi import HTTPException


async def whoami(request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="MISSING_TOKEN")
    try:
        claims = await read_token(auth.removeprefix("Bearer "))
    except Exception:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")
    return {"user_id": claims["sub"]}
```

`decode` raises `jwt.InvalidTokenError` for an unknown key id it *can* detect, for a revoked token,
and the usual PyJWT exceptions (`ExpiredSignatureError`, `InvalidAudienceError`,
`InvalidIssuerError`) otherwise.

## Revocation

Opt-in, and free when you do not use it. Put a `jti` claim in the payload and `decode` checks
`jwt:revoked:<jti>` in the cache before returning:

```python
from webfluid.core.ext import cache, jwt
from uuid import uuid4


async def issue_short_lived(user_id: int) -> tuple[str, str]:
    jti = uuid4().hex
    token = await jwt.aencode({"sub": str(user_id), "jti": jti}, expire=1)
    return token, jti


async def revoke(jti: str):
    # Any value works; decode only checks for existence.
    await cache.aset(f"jwt:revoked:{jti}", "1", timeout=60 * 60 * 24)
```

A token without a `jti` costs no cache lookup at all — which is the whole point of a stateless
token. Add one where you need a kill switch, leave it off everywhere else. Give the revocation entry
a TTL at least as long as the token's remaining lifetime.

## Audiences

```python
@register_config(10)
class Config:
    JWT_AUDIENCES = {
        "default": "Application",
        "api": "PublicAPI",
        "internal": "InternalServices"
    }
```

```python
token = await jwt.aencode({"sub": "1"}, audience="api")
claims = await jwt.adecode(token, audience="api")     # must match, or InvalidAudienceError
```

Audiences separate token populations minted by the same app. A token for `"api"` cannot be replayed
against a route that decodes with `"internal"`.

## Combining with the security battery

Writing header parsing by hand is worth doing once to see the shape. In practice, put a
`permissions` list into the payload and let the security gates do the work:

```python
token = await jwt.aencode({"sub": str(user.id), "permissions": ["posts:write"]})
```

```python
svc = security.user_service

async def publish(user = svc.requirement_or_grant(
    {"requirement": "has_any_role", "roles": ["editor", "admin"]},
    "posts:write"
)): ...
```

That single route now serves a browser session **and** a bearer token, and your handler receives a
real `User` either way. See [`ext/security.md`]({{ base }}ext/security.md).

## Config reference

| Key                   | Default                      | Notes                                                         |
|-----------------------|------------------------------|---------------------------------------------------------------|
| `JWT_ROTARY_INTERVAL` | `15`                         | Days between rotations                                        |
| `JWT_SECRET_LENGTH`   | `128`                        | Bytes passed to `secrets.token_hex`                           |
| `JWT_EXPIRY_DAYS`     | `30`                         | Default lifetime; `expire=` overrides per token               |
| `JWT_ALGORITHM`       | `"HS256"`                    | Symmetric — the secret is shared, so only this app can verify |
| `JWT_ISSUER`          | `"WebFluid"`                 | Set it to your app's name                                     |
| `JWT_AUDIENCES`       | `{"default": "Application"}` |                                                               |

{{ warning("Never call cache.clear() / aclear() in an app that uses JWT. flushdb drops jwt:current
    and every jwt:<kid>, invalidating every token in circulation.") }}

## Next

- [`ext/security.md`]({{ base }}ext/security.md) — the gates that consume these tokens.
- [`ext/cache.md`]({{ base }}ext/cache.md) — where the keys live.
- [`surface/tooling.md`]({{ base }}surface/tooling.md) — the next layer.
{% endblock %}
