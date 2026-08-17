{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Cache{% endblock %}
{% block doc_section %}Extensions{% endblock %}

{% block summary %}
`EXT_CACHE` is a small key-value API with two interchangeable backends: `redis` (the default,
production) and `legacy` (an in-process dict with an expiry heap). Every method has an async twin.
{% endblock %}

{% block body %}
## Enabling

```ini
[extensions]
EXT_CACHE = 1

[data]
REDIS_URI = redis://localhost:6379

[cache]
CACHE_TYPE = redis
```

| Key                     | Default                                        | Notes                                                         |
|-------------------------|------------------------------------------------|---------------------------------------------------------------|
| `CACHE_TYPE`            | `"redis"`                                      | `"redis"` or `"legacy"`. An unknown value raises `ValueError` |
| `CACHE_REDIS_URI`       | `f"{REDIS_URI or 'redis://localhost:6379'}/2"` | Database **2** by default; rate limiting uses **1**           |
| `CACHE_DEFAULT_TIMEOUT` | `300`                                          | Seconds, used when `timeout` is omitted                       |

## The API

```python
from webfluid.core.ext import cache

cache.set(key, value, timeout=None)
cache.get(key)
cache.delete(key)
cache.clear()

await cache.aset(key, value, timeout=None)
await cache.aget(key)
await cache.adelete(key)
await cache.aclear()

cache.backend        # the concrete RedisCache / LegacyCache instance
```

`get` returns `None` for a miss **and** for an expired entry. `clear` / `aclear` is `flushdb` on
redis — it wipes the whole database, including the JWT keys if they share it.

## Backend differences that change your code

|                         | `redis`                            | `legacy`                        |
|-------------------------|------------------------------------|---------------------------------|
| Storage                 | Redis, `decode_responses=True`     | In-process `dict` + expiry heap |
| Value types             | **Everything comes back as `str`** | Whatever you put in, unchanged  |
| Shared across processes | Yes                                | **No**                          |
| Survives a restart      | Yes                                | No                              |
| Needs a server          | Yes                                | No                              |
| Lazy connection         | Client created on first use        | —                               |

{{ rule("Decode on the way out when you might run against redis. cache.aget returns a string there
    and the original object on legacy, so int(cached), json.loads(cached) or an explicit
    str() round-trip is the only shape that works on both. Do not store objects that do not
    round-trip through a string.") }}

{{ warning("CACHE_TYPE = legacy is wrong the moment you run more than one worker: two processes are
    two caches with two answers. It is also wrong for EXT_JWT — the signing keys live in the cache,
    so an in-process cache means every restart invalidates every issued token. Use redis for
    anything you deploy.") }}

## Typical use: memoising a query

```python
# fluid/events/models.py
from webfluid.core.ext import db, cache, events
from sqlalchemy import select, func
from fluid.models import MyModel


def register():
    events.create_signal("model:created", internal=False)

    @events.query("model:count")
    async def count_models(_):
        cached = await cache.aget("model:count")
        if cached is not None:
            return int(cached)

        async with db.async_executor(model=MyModel) as e:
            result = await e.exec(select(func.count(MyModel.id)), scalars=False)
            total = result.scalar()

        await cache.aset("model:count", total, timeout=60)
        return total

    @events.event("model:created", internal=False)
    async def bust_count(_):
        await cache.adelete("model:count")
```

The pattern: read-through on the query, invalidate on the event that changes the underlying data.
Note `int(cached)` — redis hands back a string.

## Key naming

There is no automatic namespacing. Everything shares one keyspace, including the framework:

| Prefix                                          | Owner     |
|-------------------------------------------------|-----------|
| `jwt:current`, `jwt:<kid>`, `jwt:revoked:<jti>` | `EXT_JWT` |
| anything else                                   | you       |

{{ rule("Prefix your keys with a namespace of your own — myapp:… for the main app, <additive_id>:…
    for an Additive. Never write under jwt:. And never call clear()/aclear() in an app that also
    uses JWT: flushdb drops the signing keys and invalidates every issued token.") }}

## Rules

{{ rule("Never cache anything you cannot reconstruct. A cache entry can vanish at any moment —
    eviction, a restart, a flush. Treat every read as a possible miss and always have the slow path
    available.") }}

{{ rule("Always pass an explicit timeout for values that can go stale. CACHE_DEFAULT_TIMEOUT is 300
    seconds; relying on it makes the lifetime invisible at the call site.") }}

{{ warning("Both backends resolve the timeout as `timeout or self._default_timeout`, so timeout=0
    silently becomes CACHE_DEFAULT_TIMEOUT rather than 'no expiry' or 'expire immediately'. There is
    no way to store an entry without a TTL.") }}

{{ rule("Use the async methods inside async code. The redis backend's sync client is a blocking
    socket call on the event loop.") }}

## Who else uses it

- **`EXT_JWT`** requires this switch. It stores its rotating signing secrets under `jwt:<kid>`,
  the current key id under `jwt:current`, and checks `jwt:revoked:<jti>` on decode.
- **Rate limiting** uses redis directly through `RATELIMIT_STORAGE_URI` (database 1), not through
  this extension.

## Next

- [`ext/jwt.md`]({{ base }}ext/jwt.md) — the battery that depends on this one.
- [`ext/events.md`]({{ base }}ext/events.md) — where the invalidation event comes from.
{% endblock %}
