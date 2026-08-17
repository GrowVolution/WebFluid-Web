{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Reference: Extensions{% endblock %}
{% block doc_section %}Reference{% endblock %}

{% block summary %}
`webfluid.extensions` — the base class and the eight batteries. All follow the same shape: a class
with an `expand_fluid` method, instantiated once, reachable through `webfluid.core.ext`.
{% endblock %}

{% block body %}
## `FluidExtension`

```python
from webfluid.extensions import FluidExtension
```

| Member                                  | Notes                                                              |
|-----------------------------------------|--------------------------------------------------------------------|
| `__init__(fluid=None, *args, **kwargs)` | Calls `expand_fluid` immediately when `fluid` is given             |
| `expand_fluid(fluid, *args, **kwargs)`  | Override. Raises `NotImplementedError` by default                  |
| `cli_entry(app, name)`                  | Classmethod. Mounts the class's `_cli` Typer app under `wf <name>` |

`webfluid.extensions.base.Delegated(path, optional=False)` is the descriptor the batteries use to
expose sub-object attributes with a clear error before `expand_fluid` has run.

## `SQLAlchemy` — [`ext/sqlalchemy.md`]({{ base }}ext/sqlalchemy.md)

```python
from webfluid.core.ext import db
from webfluid.extensions.sqlalchemy import Model, Bind, Executor, AsyncExecutor, database_uris
```

| Member                                                        | Notes                                                                                                                           |
|---------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `db.Model`                                                    | The declarative base. `__tablename__` from `camel_to_snake(cls.__name__)`, `__bind_key__`, `set_bind(key)`, `metadata_for(key)` |
| `db.executor(bind_key=None, model=None)`                      | Context manager → `Executor`                                                                                                    |
| `db.async_executor(...)`                                      | Async context manager → `AsyncExecutor`                                                                                         |
| `db.ensured_executor(...)` / `db.ensured_async_executor(...)` | Reuse an open one, else open a new one                                                                                          |
| `db.current_executor` / `db.current_async_executor`           | The active one, or `RuntimeError`                                                                                               |
| `db.get_bind(key)` / `db.get_bind_for_model(model)`           | → `Bind`                                                                                                                        |
| `db.bind_keys`                                                | `list[str]`                                                                                                                     |
| `SQLAlchemy.get_instance()`                                   | The process-wide instance, or `FrameworkException`                                                                              |
| `await db.dispose()`                                          | Dispose every bind's engines. Registered as a **shutdown hook** by `expand_fluid`                                               |

`Executor` / `AsyncExecutor`: `exec(statement, scalars=True)`, `insert(obj, flush=False)`,
`delete(obj, flush=False)`, `flush()`, `.session`. Both subclass `BaseContext`.

`Bind`: `.sync_uri`, `.async_uri`, `.metadata`, `.sync_engine`, `.async_engine`, `session()`,
`async_session()`, `await dispose()`. Engines are created lazily; sessions use
`expire_on_commit=False` and commit/rollback/close automatically. `dispose()` is idempotent and
clears the cached engine, so a disposed bind rebuilds itself on next use.

`database_uris(uri)` → `(sync_uri, async_uri)`. Raises on a driver in the URI or an unsupported
scheme. Only the **leading** scheme prefix is rewritten since `1.0.0b3`, so a path, database name,
user or password containing the scheme word survives.

Config: `SQLALCHEMY_DATABASE_URI`, `SQLALCHEMY_BINDS`, `SQLALCHEMY_ENGINE_OPTIONS`.

## `Babel` — [`ext/babel.md`]({{ base }}ext/babel.md)

```python
from webfluid.core.ext import babel
from webfluid.extensions.babel import (
    Domain, Translations, I18nMessage, LazyString,
    translation_resolver, get_locale, get_timezone, parse_best_match,
    to_user_timezone, to_utc, format_date, format_datetime, format_time,
    format_timedelta, format_number, format_decimal, format_currency,
    format_percent, format_scientific, load_locale, format_message,
    fake_t, fake_tn
)
```

| Group     | Members                                                                                                                                |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------|
| Lookup    | `gettext`, `ngettext`, `pgettext`, `npgettext` + `a*` awaitables + `lazy_*`                                                            |
| Domains   | `register_domain(name, package=None)`, `domain_context(name)`, `current_domain`, `update_translations(domain, resolver)`               |
| Selection | `locale_selector(fn)`, `timezone_selector(fn)`, `locale_selector_fn`, `timezone_selector_fn`, `force(locale, timezone)`, `aforce(...)` |
| Settings  | `default_locale`, `default_timezone`, `supported_locales`, `date_formats`                                                              |
| CLI       | `wf babel extract`, `wf babel compile`                                                                                                 |

Jinja filters: `datetimeformat`, `dateformat`, `timeformat`, `timedeltaformat`, `numberformat`,
`decimalformat`, `currencyformat`, `percentformat`, `scientificformat`.

Models: `I18nKey`, `I18nMessage` — the latter with `uncache` / `recache` helpers.

`MergedTranslations` gained a `findtext` family in `1.0.0b3` — `findtext`, `nfindtext`, `pfindtext`,
`npfindtext` and their four `a`-prefixed pendants — which answer `None` when neither the database nor
the compiled catalog carries the message. The domain escalation tests those instead of comparing an
answer to its source, so a translation equal to its source is a hit. The eight `gettext` methods are
unchanged and still answer with the source string on a miss.

{{ warning("Formatter keywords settled in 1.0.0b2 and have not moved: every formatter takes fmt
    (format_date used to spell it ftm), to_utc converts to UTC rather than only dropping the offset,
    and parse_best_match answers a missing header with None instead of the first supported
    locale.") }}

{{ bug("The /ws/i18n translate handler runs without a FluidContext, so it always answers in
    BABEL_DEFAULT_LOCALE. Its sibling cache handler resolves the connection's locale correctly. The
    client's live._p / live._np also send their context argument in the wrong position.") }}

Requires `EXT_SQLALCHEMY`.

## `Security` — [`ext/security.md`]({{ base }}ext/security.md)

```python
from webfluid.core.ext import security
from webfluid.extensions.security.models import (
    User, Identity, Role, Permission,
    TOTPSecret, WebAuthnCredential, BackupCode, ExpiredToken
)
from webfluid.extensions.security.utils import (
    validate_username, validate_password, PasswordPolicy
)
```

**`user_service`**

| Member                                                                                                           | Kind                               |
|------------------------------------------------------------------------------------------------------------------|------------------------------------|
| `current_user`                                                                                                   | `Depends` → `User \| None`         |
| `require_user`, `require_2fa`, `require_admin`                                                                   | `Depends` attributes               |
| `require_roles(roles)`, `require_any_role(roles)`, `require_permissions(perms)`, `require_any_permission(perms)` | Methods returning `Depends`        |
| `*_fn` twin of each                                                                                              | The bare resolver                  |
| `has_2fa(user)`                                                                                                  | sync predicate                     |
| `is_admin`, `has_roles`, `has_any_role`, `has_permissions`, `has_any_permission`                                 | awaitable predicates               |
| `check_requirement(user, requirement_dict)`                                                                      | awaitable                          |
| `requirement_or_grant(req, grant)`, `requirement_and_grant(req, grant)`                                          | Session **or** / **and** JWT grant |
| `resolve_bearer(request, grant)`, `bearer_principal(request, grant)`                                             | Token side alone                   |

**`hash_service`** — `hash`, `verify`, `ahash`, `averify` (argon2, thread-pooled).

**`token_service`** — `csrf_protect` (Depends), `csrf_protect_fn`, `csrf_response(request)`,
`generate_token(data, salt="csrf")`, `await validate_token(token, salt="csrf")`.

**`oauth_service`** — `client`, `prepare_session`, `userinfo` (all Depends),
`authorize_response(request, provider, device, csrf=None)`, `register_provider`,
`unregister_provider`.

{{ bug("Every relationship on the models is lazy=\"raise_on_sql\" except user.totp_secret and
    user.webauthn_credentials. user.roles raises rather than returning an empty list — load it with
    selectinload.") }}

Requires `EXT_SQLALCHEMY`; `SECURITY_SECRET` is mandatory in production.

## `EventManager` — [`ext/events.md`]({{ base }}ext/events.md)

```python
from webfluid.core.ext import events
```

| Member                                                 | Notes                                                  |
|--------------------------------------------------------|--------------------------------------------------------|
| `create_signal(name, singleton=False, internal=False)` | Declare a channel. Register from a hook — see below    |
| `event(name, singleton=False, internal=True)`          | Decorator. Handler takes exactly 1 arg                 |
| `query(name, singleton=True, internal=True)`           | Decorator. Handler takes exactly 1 arg                 |
| `trigger(event, data=None)`                            | Sync, fire-and-forget. `ValueError` on an unknown name |
| `await request(query, data=None)`                      | Singleton → one result, otherwise a list               |
| `async for x in listen(event)`                         | Server-side stream                                     |

`internal=False` exposes a channel to the browser at `/ws/events`; the client is
`window.wf.ext.events.EventManager`. Since `1.0.0b3` the socket handler runs inside a `FluidContext`
whose `request` is the `WebSocket`, so a query resolves the caller from the connection.

Registration: before the loop exists the channel is queued and wired by the
`events.create_pending_loops` startup hook; off-loop **after** startup raises `FrameworkException`;
from inside a request the consumer task inherits that request permanently. Register from a startup
hook or `before_enable`.

`SocketManager` takes the application as its first argument since `1.0.0b3`:
`SocketManager(fluid, events, queries)`.

Config: `EVENTS_EVENT_QUEUE_SIZE`, `EVENTS_CONFIGURE_SOCKET`.

## `Mail` — [`ext/mailman.md`]({{ base }}ext/mailman.md)

```python
from webfluid.core.ext import mail
```

| Member                                                                                           | Notes                                                                            |
|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| `send(to, subject, body, attachments=None, from_email=None, cc=None, bcc=None, fake_async=True)` | `body` is a MIME-subtype map. Threads delivery by default                        |
| `await asend(...)`                                                                               | Same without `fake_async`                                                        |
| `client()` / `async_client()`                                                                    | Bare logged-in SMTP connections as context managers. A send inside one reuses it |

Both clients honour both TLS flags since `1.0.0b3`, and setting both raises at startup. Connect,
STARTTLS and login happen inside the `try`, so failures surface as `FrameworkException`. A
`fake_async=True` send logs its failure through the framework logger from a daemon thread.

## `Cache` — [`ext/cache.md`]({{ base }}ext/cache.md)

```python
from webfluid.core.ext import cache
from webfluid.extensions.cache import BaseCache
```

`set`, `get`, `delete`, `clear` + `aset`, `aget`, `adelete`, `aclear`; `cache.backend` is the
concrete implementation. Backend from `CACHE_TYPE`: `redis` (values come back as `str`) or `legacy`
(in-process, self-expiring).

## `JWTManager` — [`ext/jwt.md`]({{ base }}ext/jwt.md)

```python
from webfluid.core.ext import jwt
```

`encode(payload, audience="default", expire=None)`, `decode(token, audience="default")` and the
`aencode` / `adecode` twins. Requires `EXT_SCHEDULING` and `EXT_CACHE`; rotates its signing secret
on a schedule and keeps recent ones in the cache under their key id — which is why it needs the
Redis backend to outlive a restart. A payload carrying a `jti` is checked against
`jwt:revoked:<jti>` on decode.

## `Migrate` — [`ext/migrate.md`]({{ base }}ext/migrate.md)

CLI only. `wf migrate init <app>`, `revision <app> [-a] [-m]`, `upgrade <app>`,
`downgrade <app> [-r]`. Builds the app through `prepare_fluid()` in `main.py`.

## Next

- [`ref/surface.md`]({{ base }}ref/surface.md) — the frontend layer.
{% endblock %}
