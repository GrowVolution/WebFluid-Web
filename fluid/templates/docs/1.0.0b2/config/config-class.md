{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Config Classes{% endblock %}
{% block doc_section %}Configuration{% endblock %}

{% block summary %}
Config classes carry every non-secret runtime setting. They are plain Python classes decorated with
`@register_config(priority)`; the framework merges them on top of `DefaultConfig` during
`Fluid.__init__` and exposes the result as the `fluid.config` dict. This page is also the complete
reference table of every framework config key and its default.
{% endblock %}

{% block body %}
## How the merge works

```python
# webfluid/core/config/build.py, in effect
config = _values(DefaultConfig)                     # framework defaults
for group in priority_desc_to_asc:                  # 10 applied last
    for cls in group:
        config.update(_values(cls))                 # your classes on top
```

`_values(cls)` walks `cls.__mro__` in reverse and collects every **upper-case** attribute. Three
consequences:

1. **Only `UPPER_CASE` names are config.** `my_setting = 1` on a config class is invisible.
2. **Inheritance works.** A key defined on a base class is picked up as if written on the subclass;
   the subclass wins on conflicts. This is what the `MyConfig` convention below relies on.
3. **Higher priority overrides lower.** `register_config(priority)` accepts 1–10, default 1.
   Same-priority classes are applied in registration order, later ones winning.

The result is a `Config` (a `dict` subclass) reachable as `fluid.config`.

## Registering

### The normal way: `fluid/config.py`

`init_configs()` runs at the very top of `Fluid.__init__` and imports `fluid.config` for you.
Putting the class there is all the registration you need.

```python
# fluid/config.py
from webfluid.core.config import register_config

try: from fluid._my_config import MyConfig
except ImportError:
    class MyConfig: pass


@register_config(10)
class Config(MyConfig):
    APP_CONFIG = {
        "title": "myapp",
        "version": "1.0.0"
    }
    APP_FRONTEND = {
        "type": "htmx",
        "alpine": True
    }
```

The `MyConfig` pattern is the framework's convention for public repositories: shared settings live
in `config.py` and are committed; local or private ones live in `fluid/_my_config.py`, which the
generated `.gitignore` excludes. Because the builder walks the MRO, a key only `MyConfig` defines
is picked up exactly as if it had been written in `Config`; a key in both belongs to `Config`.
A clone without `_my_config.py` still starts.

### The manual way

Anywhere, as long as the decorator has executed **before** `Fluid(...)`:

```python
from webfluid.core.config import register_config

@register_config(10)
class MyConfig:
    SESSION_COOKIE_SECURE = True

fluid = Fluid(__name__)     # registration must come first
```

{{ rule("Prefer fluid/config.py. Manual registration only works if the module is imported before
    the constructor runs, which is fragile in a factory and impossible from an Additive.") }}

### From an Additive

`init_configs()` also imports `additives.<pkg>.config` for every **enabled** Additive, so an
Additive ships its own defaults the same way. The established shape:

```python
# additives/portal/config.py
from webfluid.core.config import register_config

try: from ._my_config import MyConfig
except ImportError:
    class MyConfig: pass


class DefaultConfig:
    PORTAL_REGION = "eu"
    PORTAL_PAGE_SIZE = 25


@register_config()
class Config(MyConfig, DefaultConfig): pass
```

Priority 1 (the default) is correct here: the host application should be able to override an
Additive's defaults with its own priority-10 class.

## Reading config

```python
fluid.config["SESSION_COOKIE_SECURE"]          # framework key: always present
fluid.config.get("PORTAL_REGION", "eu")        # your own key: may be absent
```

{{ rule("Never re-state a framework default at the call site. fluid.config carries every key
    DefaultConfig declares, so config.get('SESSION_COOKIE_SECURE', not debug) is both redundant and
    a second source of truth — exactly how two defaults drifted apart during the alpha. Index
    framework keys; use get() only for keys you invented.") }}

Outside a request, reach the config through the context or the app object you already hold:

```python
from webfluid.core.context import FluidContext

ctx = FluidContext.try_current()
region = ctx.fluid.config["PORTAL_REGION"] if ctx else "eu"
```

## Complete default reference

Everything below is a `DefaultConfig` attribute, so every key is present in `fluid.config`.
`DEBUG` is `enabled("DEBUG_MODE")`, i.e. true under `wf run -d`.

### Application

| Key            | Default                                                 | Notes                                                                                                                       |
|----------------|---------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `APP_CONFIG`   | `{"title": "WebFluid Application", "version": "1.0.0"}` | Passed verbatim as `**kwargs` to `FastAPI.__init__`. Set `docs_url`/`redoc_url` to `None` here to disable the OpenAPI UIs   |
| `APP_FRONTEND` | `{"type": "htmx", "alpine": True}`                      | Validated on boot; `None` disables the frontend object entirely. See [`surface/frontend.md`]({{ base }}surface/frontend.md) |
| `BASE_URL`     | `"http://localhost:8000"`                               | Used for external URLs when there is no request                                                                             |
| `SECRET_KEY`   | `os.getenv("SECRET_KEY")`                               | **Required.** Signs the session cookie                                                                                      |

### Session and proxy

| Key                       | Default       | Notes                                                                                               |
|---------------------------|---------------|-----------------------------------------------------------------------------------------------------|
| `SESSION_COOKIE_NAME`     | `"session"`   |                                                                                                     |
| `SESSION_COOKIE_SAMESITE` | `"lax"`       |                                                                                                     |
| `SESSION_COOKIE_SECURE`   | `not DEBUG`   | Maps to Starlette's `https_only`. A non-secure cookie outside debug logs a warning                  |
| `PROXY_FIX`               | `False`       | Adds uvicorn's `ProxyHeadersMiddleware`                                                             |
| `PROXY_TRUSTED_HOSTS`     | `"127.0.0.1"` | Whose `X-Forwarded-*` headers are believed. `"*"` trusts everyone — only behind a proxy you control |

### Static and theming

| Key              | Default                        | Notes                                                          |
|------------------|--------------------------------|----------------------------------------------------------------|
| `STATIC_MAX_AGE` | `0` if `DEBUG` else `31536000` | `Cache-Control: public, max-age=…` on every static mount       |
| `GLOBAL_THEME`   | `"fluid"`                      | The theme used when the session has none. Requires `WF_THEMES` |

### Rate limiting

| Key                     | Default                                        | Notes                                               |
|-------------------------|------------------------------------------------|-----------------------------------------------------|
| `RATELIMIT_ENABLED`     | `True`                                         | When false, `fluid.limit` becomes a no-op decorator |
| `RATELIMIT_STORAGE_URI` | `f"{REDIS_URI or 'redis://localhost:6379'}/1"` |                                                     |
| `RATELIMIT_DEFAULT`     | `["500/day", "100/hour"]`                      | See the bug below                                   |

{{ bug("RATELIMIT_DEFAULT never applies. slowapi evaluates application-wide defaults only from its
    own middleware, which the framework does not install — so an undecorated route is never
    checked, and a @fluid.limit(...) decorator replaces the defaults instead of adding to them.
    Treat the value as documentation of intent and put the limit you want on the route.") }}

### SQLAlchemy — [`ext/sqlalchemy.md`]({{ base }}ext/sqlalchemy.md)

| Key                         | Default                                         | Notes                                                              |
|-----------------------------|-------------------------------------------------|--------------------------------------------------------------------|
| `SQLALCHEMY_DATABASE_URI`   | `os.getenv("DATABASE_URI", "sqlite:///app.db")` | **Without a driver.** The extension derives sync and async drivers |
| `SQLALCHEMY_BINDS`          | `{}`                                            | `{"key": "uri"}`. Also decides the Alembic template                |
| `SQLALCHEMY_ENGINE_OPTIONS` | `{"pool_pre_ping": True, "pool_recycle": 3600}` | Passed to both `create_engine` and `create_async_engine`           |

### Babel — [`ext/babel.md`]({{ base }}ext/babel.md)

| Key                        | Default                                                         | Notes                                                                            |
|----------------------------|-----------------------------------------------------------------|----------------------------------------------------------------------------------|
| `BABEL_DEFAULT_LOCALE`     | `"en"`                                                          | Final fallback of the selection chain                                            |
| `BABEL_DEFAULT_TIMEZONE`   | `"UTC"`                                                         |                                                                                  |
| `BABEL_SUPPORTED_LOCALES`  | `["en"]`                                                        | What `Accept-Language` is matched against                                        |
| `BABEL_DATE_FORMATS`       | `{"time": "medium", "date": "medium", "datetime": "medium", …}` | Per-kind format map                                                              |
| `BABEL_CONFIGURE_JINJA`    | `True`                                                          | Installs the gettext callables and the format filters                            |
| `BABEL_CONFIGURE_SOCKET`   | `True`                                                          | Mounts `/ws/i18n` and injects `i18n.js`                                          |
| `BABEL_DATABASE_BIND`      | `None`                                                          | Put `I18nKey`/`I18nMessage` on a non-default bind                                |
| `BABEL_DISABLE_AUTOUPDATE` | `False`                                                         | Ignore every `update_translations` call and read what the database already holds |

### Events — [`ext/events.md`]({{ base }}ext/events.md)

| Key                       | Default | Notes                                                        |
|---------------------------|---------|--------------------------------------------------------------|
| `EVENTS_EVENT_QUEUE_SIZE` | `5`     | Per-listener buffer. A slow consumer drops its oldest events |
| `EVENTS_CONFIGURE_SOCKET` | `True`  | Mounts `/ws/events` and injects `events.js`                  |

### Security — [`ext/security.md`]({{ base }}ext/security.md)

| Key                              | Default                                               | Notes                                                                                                        |
|----------------------------------|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `SECURITY_SECRET`                | `os.getenv("SECURITY_SECRET")`                        | Signs CSRF and one-time tokens. **Required in production**; debug falls back to a fixed dev secret and warns |
| `SECURITY_TOKEN_MAX_AGE`         | `3600`                                                | Seconds                                                                                                      |
| `SECURITY_CSRF_COOKIE_NAME`      | `"csrf_token"`                                        |                                                                                                              |
| `SECURITY_CSRF_COOKIE_SECURE`    | `True`                                                |                                                                                                              |
| `SECURITY_HASHER_TIME_COST`      | `3`                                                   | argon2                                                                                                       |
| `SECURITY_HASHER_MEMORY_COST`    | `65536`                                               | argon2, KiB                                                                                                  |
| `SECURITY_HASHER_PARALLELISM`    | `4`                                                   | argon2                                                                                                       |
| `SECURITY_HASHER_THREADS`        | `4`                                                   | Size of the pool `ahash`/`averify` run on — also the cap on concurrent logins                                |
| `SECURITY_PASSWORD_MIN_LENGTH`   | `8`                                                   |                                                                                                              |
| `SECURITY_PASSWORD_REQUIREMENTS` | `{"lower": 1, "upper": 1, "digits": 1, "special": 1}` | Merged, not replaced — see below                                                                             |
| `SECURITY_OAUTH_CLIENTS`         | `{}`                                                  | `{name: authlib client kwargs}`                                                                              |
| `SECURITY_MODELS_DB_BIND`        | `None`                                                | Put the security tables on a non-default bind                                                                |

{{ warning("SECURITY_PASSWORD_REQUIREMENTS is read key by key with a fallback of 1, so a class you
    omit from your dictionary still demands one character. To drop a requirement, set it to 0
    explicitly: {\"special\": 0} keeps demanding a lower case, an upper case and a digit.") }}

### JWT — [`ext/jwt.md`]({{ base }}ext/jwt.md)

| Key                   | Default                      | Notes                                                               |
|-----------------------|------------------------------|---------------------------------------------------------------------|
| `JWT_ROTARY_INTERVAL` | `15`                         | Days between secret rotations                                       |
| `JWT_SECRET_LENGTH`   | `128`                        | Bytes of randomness per secret                                      |
| `JWT_EXPIRY_DAYS`     | `30`                         | Default token lifetime; `encode(..., expire=n)` overrides per token |
| `JWT_ALGORITHM`       | `"HS256"`                    |                                                                     |
| `JWT_ISSUER`          | `"WebFluid"`                 | `iss` claim                                                         |
| `JWT_AUDIENCES`       | `{"default": "Application"}` | Short name → `aud` value. An unknown name is used verbatim          |

### Mail — [`ext/mailman.md`]({{ base }}ext/mailman.md)

| Key                               | Default                                    | Notes                                                               |
|-----------------------------------|--------------------------------------------|---------------------------------------------------------------------|
| `MAIL_SERVER`                     | `"localhost"`                              |                                                                     |
| `MAIL_PORT`                       | `587`                                      |                                                                     |
| `MAIL_USE_TLS`                    | `False`                                    | Implicit TLS (port 465). **Async client only** — see the bug below  |
| `MAIL_USE_STARTTLS`               | `True`                                     | STARTTLS upgrade (port 587). Mutually exclusive with `MAIL_USE_TLS` |
| `MAIL_TIMEOUT`                    | `10`                                       | Seconds                                                             |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | `os.getenv(...)`                           | All or nothing — one without the other raises                       |
| `MAIL_DEFAULT_SENDER`             | `MAIL_USERNAME` or `"noreply@example.com"` |                                                                     |

{{ bug("The synchronous SyncManager stores MAIL_USE_TLS and then opens a plain smtplib.SMTP
    connection, so mail.send() against an implicit-TLS server talks plaintext with your credentials
    in it. Use port 587 with MAIL_USE_STARTTLS, or send with mail.asend().") }}

### Cache — [`ext/cache.md`]({{ base }}ext/cache.md)

| Key                     | Default                                        | Notes                                |
|-------------------------|------------------------------------------------|--------------------------------------|
| `CACHE_TYPE`            | `"redis"`                                      | `"redis"` or `"legacy"` (in-process) |
| `CACHE_REDIS_URI`       | `f"{REDIS_URI or 'redis://localhost:6379'}/2"` |                                      |
| `CACHE_DEFAULT_TIMEOUT` | `300`                                          | Seconds                              |

## Adding your own keys

Prefix them so they cannot collide with a framework key or another Additive's, and read them with
`get`:

```python
@register_config(10)
class Config:
    MYAPP_FEATURE_X = True
    MYAPP_UPSTREAM = "https://api.example.org"
```

```python
value = fluid.config.get("MYAPP_UPSTREAM", "https://api.example.org")
```

An extension reads its own keys in `expand_fluid`; see [`ext/base.md`]({{ base }}ext/base.md).

## Next

- [`ext/base.md`]({{ base }}ext/base.md) — how an extension consumes config.
- [`utils/lifecycle.md`]({{ base }}utils/lifecycle.md) — when config is available.
- [`ref/core.md`]({{ base }}ref/core.md) — the config API surface.
{% endblock %}
