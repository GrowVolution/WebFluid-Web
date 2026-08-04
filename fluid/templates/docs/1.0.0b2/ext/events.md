{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Events{% endblock %}
{% block doc_section %}Extensions{% endblock %}

{% block summary %}
`EXT_EVENTS` is an in-process publish/subscribe layer with two shapes: **events** (fire-and-forget
broadcasts) and **queries** (request/response). Public events also reach the browser through a
managed websocket. It is the mechanism Additives use to talk to each other without importing each
other.
{% endblock %}

{% block body %}
## Enabling

```ini
[extensions]
EXT_EVENTS = 1

[events]
EVENTS_EVENT_QUEUE_SIZE = 5
EVENTS_CONFIGURE_SOCKET = 1
```

With `EVENTS_CONFIGURE_SOCKET` on (the default) the manager mounts `/ws/events` and injects
`events.js` as a page source. Turn it off for a worker or a headless API — everything server-side
still works.

## The timing rule

{{ rule("events.create_signal() and events.event() must be called from inside the running event
    loop. Declaring a channel creates a BroadCaster and starts its consumer loop, and asyncio has no
    loop while your factory is assembling the app. Register from a startup hook, an Additive's
    before_enable, or a request handler — never at import time.") }}

Calling `create_signal` outside a loop **before** startup is tolerated: the name is queued and its
loop is created by the `create_pending_loops` startup hook. Calling it outside a loop **after**
startup raises `FrameworkException` with an explicit message. Do not rely on the queue — put
registration in a hook.

```python
# fluid/events/models.py
from webfluid.core.ext import events


def register():
    events.create_signal("model:created", internal=False)

    @events.event("model:created", internal=False)
    async def on_model_created(data):
        from webfluid.utils.logging import factory as log
        log.log(f"A new model appeared: {data}")

    @events.query("model:count")
    async def count_models(_):
        from webfluid.core.ext import db
        from sqlalchemy import select, func
        from fluid.models import MyModel

        async with db.async_executor(model=MyModel) as e:
            result = await e.exec(select(func.count(MyModel.id)), scalars=False)
            return result.scalar()
```

```python
# main.py
def prepare_fluid() -> Fluid:
    app = Fluid(__name__)

    from fluid.events.models import register as register_events
    app.startup_hook(register_events)

    return app
```

Queries have no broadcast loop, so they would survive import-time registration — but keeping every
contract of a module in one `register()` means you never have to remember which kind needs the loop.

## Events

```python
events.create_signal(name, singleton=False, internal=False)
events.event(name, singleton=False, internal=True)      # decorator
events.trigger(event, data=None)                        # sync, fire-and-forget
async for data in events.listen(event): ...             # async stream
```

| Flag        | Meaning                                                                        |
|-------------|--------------------------------------------------------------------------------|
| `singleton` | The name may only be registered once. A second declaration raises `ValueError` |
| `internal`  | `True` = server-only. `False` = the browser may subscribe and trigger it       |

Note the asymmetric defaults: `create_signal` defaults to `internal=False` (public),
`event` defaults to `internal=True` (server-only). **Declaring a signal public and then registering
a handler without `internal=False` raises** `ValueError: Event '<name>' is already registered as
public`. Pass the flag consistently on every call for a given name.

Handlers must accept **exactly one required argument** (the data). A mismatch raises
`FrameworkException` at registration.

### Triggering

```python
events.trigger("model:created", {"id": model.id, "value": model.value})
```

`trigger` is **synchronous and does not block**: it drops the payload into each listener's buffer
and returns. Every registered handler runs, and every subscribed browser receives it, on the loop
behind that channel. There is nothing to await — if you need an answer, use a query.

`trigger` raises `ValueError` for an unknown event name, so declare before you publish.

### Handler context

Handlers run inside a fresh `FluidContext` carrying `event` and `event_data`, and inheriting the
**request of the triggering context** when there is one. That means a handler triggered from a
request sees `ctx.request`, and the locale resolution inside it works as it does for the request
itself. Triggered from a job, `ctx.request` is `None`.

```python
@events.event("model:created", internal=False)
async def notify(data):
    from webfluid.core.context import FluidContext
    ctx = FluidContext.current()
    ctx["event"]           # the event name
    ctx["event_data"]      # == data
    ctx.request            # the triggering request, or None
```

Exceptions inside a handler with a request are re-raised; without one they are logged and swallowed
(`safe_execute(fn, ctx.request is not None, data)`).

## Queries

```python
events.query(name, singleton=True, internal=True)       # decorator
result = await events.request(query, data=None)
```

- **`singleton=True` (default):** exactly one handler; `request` returns its result.
- **`singleton=False`:** many handlers; `request` gathers all of them and returns a **list**.
- Handlers take exactly one argument.
- Unknown query name → `ValueError`.

```python
total = await events.request("model:count")
```

Query handlers run concurrently via `asyncio.gather`, each inside its own context, and exceptions
are re-raised when a request context exists.

{{ rule("Use a query, not an event, whenever you need a value back. trigger() gives you nothing —
    not even a delivery guarantee. request() awaits and returns.") }}

## Reaching the browser

Only **public** (`internal=False`) events cross to the client. The injected client lives at
`window.wf.ext.events`:

```html
<script type="module">
  const events = new window.wf.ext.events.EventManager()
  await events.subscribe("model:created")
  events.registerHandler("model:created", (data) => {
    console.log("A model was created:", data)
  })
</script>
```

The socket protocol at `/ws/events` takes JSON messages with `id`, `type` and `data`. Types:
`subscribe`, `unsubscribe`, `listen`, `trigger`, `request`. The client handles reconnection and
keeps the listen loop alive; you should not need to speak it directly.

## Delivery semantics

```text
publish -> for each listener: append to a bounded deque, set its asyncio.Event
consume -> drain the deque, then await the Event
```

{{ bug("The buffer is bounded by EVENTS_EVENT_QUEUE_SIZE (default 5). When a listener is full, the
    oldest message is dropped and a warning naming the channel and the dropped payload is logged.
    Delivery is best-effort: fine for dashboards and live notifications, wrong for anything that
    must not be lost. Use the database plus a query for that.") }}

Other properties worth knowing:

- **In-process only.** Two workers are two independent event buses. A browser connected to worker A
  never sees an event triggered on worker B.
- **No persistence, no replay.** A listener that connects after a trigger has missed it.
- **No ordering guarantee across channels**, only within one.

## Contracts between Additives

This is the primary use of the battery. Names are strings, so two Additives can talk without a
shared Python symbol. `additive.unique_name(name)` prefixes with the Additive's id so contracts
cannot collide:

```python
# additives/portal/events/contracts.py  — the producer
from webfluid.core.ext import events
from .. import additive


@events.query(additive.unique_name("model_count"))     # served as "portal_model_count"
async def model_count(_):
    ...


events.create_signal(additive.unique_name("model:created"), internal=False)
```

```python
# additives/dashboard/events/listeners.py  — the consumer
from webfluid.core.ext import events

PORTAL = "portal"          # declared under requires.additives in our manifest


async def overview():
    return await events.request(f"{PORTAL}_model_count")


@events.event(f"{PORTAL}_model:created", internal=False)
async def on_created(data):
    ...
```

Registering from `before_enable` is correct and simple, because enabling already happens inside the
running loop:

```python
@additive.before_enable
def before_enable(_):
    from .events import contracts  # noqa: importing registers them
```

Full treatment in [`additives/contract.md`]({{ base }}additives/contract.md).

## Introspection

```python
events.has_event(name)      events.has_query(name)
events.is_singleton(name)   events.is_internal(name)
events.broadcaster(name)    events.handlers(name)
```

## Next

- [`ext/cache.md`]({{ base }}ext/cache.md) — the obvious companion for a query that is expensive.
- [`additives/contract.md`]({{ base }}additives/contract.md) — events as the module contract.
- [`utils/lifecycle.md`]({{ base }}utils/lifecycle.md) — where registration belongs.
{% endblock %}
