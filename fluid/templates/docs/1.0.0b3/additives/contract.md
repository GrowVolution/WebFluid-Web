{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Additive Interaction{% endblock %}
{% block doc_section %}Additives{% endblock %}

{% block summary %}
Additives share one runtime but must not share Python symbols. This page is the contract layer:
id-scoped events and queries instead of imports, manifest requirements, the local request lifecycle,
composed frontends, and the `install()` / `configure()` pair that makes an Additive shippable.
{% endblock %}

{% block body %}
## One shared runtime

An Additive reaches the same batteries the main app does. `webfluid.core.ext` holds one instance of
each, process-wide:

```python
# additives/portal/app/index.py
from webfluid.core.ext import db, events, cache
from sqlalchemy import select, func

from .models.entry import Entry


async def handle_request():
    from .. import additive

    async with db.async_executor(model=Entry) as e:
        result = await e.exec(select(func.count(Entry.id)), scalars=False)
        total = result.scalar()

    return await additive.render("index.html", total=total)
```

Same database, same cache, same event manager, same scheduler — no wiring.

## The import rule

{{ rule("Never import another Additive's Python modules. The moment additives/dashboard imports
    additives.portal they are welded together: you cannot ship one without the other, disabling one
    breaks the other, and the enable order becomes load-bearing. The only thing allowed to cross an
    Additive boundary is a string.") }}

The main app's own modules (`fluid.models`, `fluid.services`) are a different case — an Additive
that imports them is coupled to *this* project, which is fine for a project-local Additive and fatal
for a distributed one. If you intend to publish it, do not import `fluid.*` either.

## Contracts: events and queries

`additive.unique_name(name)` prefixes with the Additive's id, giving every contract a stable,
predictable address. The producer serves under its own namespace:

```python
# additives/portal/events/contracts.py
from webfluid.core.ext import db, events
from sqlalchemy import select, func

from .. import additive
from ..models.entry import Entry


# Served as "portal_entry_count"
@events.query(additive.unique_name("entry_count"))
async def entry_count(_):
    async with db.async_executor(model=Entry) as e:
        result = await e.exec(select(func.count(Entry.id)), scalars=False)
        return result.scalar()


# Broadcast as "portal_entry:created"
events.create_signal(additive.unique_name("entry:created"), internal=False)
```

Registered from `before_enable`, which already runs inside the running loop:

```python
# additives/portal/__init__.py
@additive.before_enable
def before_enable(fluid):
    from .app import index
    additive.app.get("/")(index)

    from .events import contracts  # noqa: importing registers the contracts
```

The consumer knows the producer **only by id** — the same id it declares as a dependency:

```python
# additives/dashboard/events/listeners.py
from webfluid.core.ext import events

PORTAL = "portal"          # declared under requires.additives in our manifest


async def overview():
    return await events.request(f"{PORTAL}_entry_count")


@events.event(f"{PORTAL}_entry:created", internal=False)
async def on_created(data):
    from webfluid.utils.logging import factory as log
    log.log(f"[dashboard] portal created an entry: {data}")
```

{{ info("Because the consumer depends on portal by id and version in its manifest, the framework
    guarantees portal is present before either is enabled — so the string address is safe and no
    Python import ever crosses the boundary. The same scoping powers url_for inside Additive
    templates: route names run through unique_name too, so reverse-URL lookups never clash.") }}

### Contract design rules

{{ rule("Version your contract names when you change their shape: portal_entry_count stays,
    portal_entry_count_v2 is added. A consumer pinned to an older version of your Additive must keep
    working, and there is no type checking across the boundary to catch a changed payload.") }}

{{ rule("Pass plain JSON-shaped data across a contract — dicts, lists, strings, numbers. Never an ORM
    instance: it is detached, its relationships raise, and the consumer would need your models to do
    anything with it.") }}

{{ rule("Use a query when the caller needs an answer and an event when it does not. A query with
    singleton=True (the default) means exactly one Additive may serve it; use singleton=False for a
    fan-out where several may contribute and the caller gets a list.") }}

{{ rule("Handle a missing producer. events.request raises ValueError for an unknown query name, so an
    optional dependency needs events.has_query(name) or a try/except — not a crash.") }}

## The local request lifecycle

An Additive hooks its **own routes** only:

```python
@additive.context_processor
def defaults():
    return {"section": "portal"}


@additive.before_request
def guard():
    from webfluid.core.context import FluidContext
    ctx = FluidContext.current()
    if not ctx.request.session.get("user"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/login")


@additive.after_request
async def shape(result):
    return result
```

{{ bug("additive.after_request receives what the handler returned, not a Response. It runs inside the
    router's endpoint wrapper, before FastAPI serialises anything — so it sees a dict, a pydantic
    model or a string, and must return something FastAPI can still serialise. fluid.after_request,
    which sits in the ASGI middleware, receives a real Response. Same name, different altitude.") }}

`http_middleware` wraps a whole router; the chain is built once, on first request, not per call:

```python
@additive.api.http_middleware
def instrument(call_next):
    async def wrapper(*args, **kwargs):
        return await call_next(*args, **kwargs)
    return wrapper
```

## Declaring requirements

```json
{
  "id": "portal",
  "version": "1.0.0",
  "type": "default",
  "frontend": { "type": "vite", "framework": "vue", "typescript": false },
  "name": "Portal",
  "requires": {
    "wf": ">=1.0.0b3",
    "additives": { "core": ">=1.0.0" },
    "packages": ["httpx"]
  }
}
```

| Key | Checked | Meaning |
|---|---|---|
| `wf` | at enable | A PEP 440 specifier against the running framework version, prereleases included. A missing key logs a warning |
| `additives` | at enable | Map of `id` → specifier, or a list of `"id@specifier"` (a bare `"id"` means `"*"`). Enabled defaults are matched first, then installed bases |
| `packages` | at `install()` | pip requirements |

`>=1.0.0b3`, `~=1.2`, `*` all mean what pip means. A missing or mismatching Additive raises
`AdditiveException("[<name>] Missing or mismatching additive requirements: [...]")`.

`required_extensions` on the constructor is the other half — it guards on `EXT_*` switches and fails
loudly at enable time rather than at first use. A base's list is merged into the child's.

## Composed frontends

Each Additive can carry its own Vite app in `additives/<id>/frontend`, and the root workspace glob
picks all of them up:

```json
{
  "name": "myapp",
  "private": true,
  "workspaces": [
    "additives/*/frontend",
    "fluid/frontend"
  ],
  "devDependencies": { "vite": "^8.0.0" }
}
```

| | Path |
|---|---|
| Build output | `/<id>/frontend` |
| Development | proxied through `/vite-dev`, one shared dev server, HMR across all of them |
| Static | `/<id>/static` |

The per-Additive `vite.config.js` differs from the main app's only in its `base`
(`'/portal/frontend/'` instead of `'/frontend/'`).

{{ warning("HMR rides on a websocket proxied in front of the shared dev server. That connection can
    drop on its own — a Vite restart is the usual trigger — and the affected frontend then silently
    stops picking up changes. A browser refresh re-establishes it immediately; there is no need to
    restart wf run.") }}

## `install()`

The settling-in routine, run by `wf ocean install` and (in debug, with `DEV_AUTO_INSTALL=1`) on every
registration:

1. Resolve the Additives this manifest requires; pull missing ones from the Ocean, recursively.
2. Copy everything in the Additive's `extract/` folder into the main app — templates and static the
   **host** should own. **Existing files are never overwritten.**
3. Install the manifest's `packages` with pip.

Nothing is visited twice, and a dependency with dependencies of its own is followed through.

{{ rule("Use extract/ for files the host app is meant to own and edit — a page template it should
    customise, a stylesheet it should extend. Everything the Additive owns stays in its own
    templates/ and static/, where an upgrade can replace it. Anything in extract/ is written once and
    then belongs to the project.") }}

{{ info("Export DEV_AUTO_INSTALL=1 while developing an Additive: a debug run then calls install() on
    every Additive it registers, so a freshly added requirement or extract file lands without a
    manual step. It deliberately does nothing outside debug mode.") }}

## `configure()`

Lets an Additive contribute questions to `wf create app`, so its settings land in the generated app
config interactively.

```python
# additives/portal/config.py
setup = {
    "PORTAL_API_KEY": {
        "type": "password",
        "message": "Portal API key:"
    },
    "PORTAL_REGION": {
        "type": "select",
        "message": "Portal region:",
        "kwargs": { "choices": ["eu", "us"], "default": "eu" }
    },
    "PORTAL_ENABLED": {
        "type": "auto",
        "value": "1"
    }
}
```

| Key | Required | Notes |
|---|---|---|
| `type` | yes | `text`, `password`, `select`, `checkbox`, `confirm`, `auto` |
| `message` | yes, except `auto` | The prompt |
| `value` | required for `auto` | Written without asking |
| `kwargs` | no | Passed to the prompt |

Answers land in a config section named after the Additive's id. A malformed entry is skipped with a
yellow warning rather than aborting. A base Additive is configured **before** its child, so its
questions come first.

The same `config.py` is where `@register_config` lives — see
[`config/config-class.md`]({{ base }}config/config-class.md).

## Packaging checklist

Before `wf ocean publish`:

- [ ] `manifest.json` — correct `id`, real `version`, `requires.wf` set, dependencies declared.
- [ ] No import of another Additive or of `fluid.*`.
- [ ] Every contract name goes through `unique_name()`.
- [ ] Every config key prefixed with the id.
- [ ] `required_extensions` lists what the code actually uses.
- [ ] `.gitignore` present — the archive honours it, nested ones and negations included, and skips
      `.git`, `__pycache__`, `node_modules`, editor folders and compiled files.
- [ ] `extract/` holds only what the host should own.
- [ ] A license (`wf ocean publish` walks you through applying one if there is none).

## Next

- [`cli/ocean.md`]({{ base }}cli/ocean.md) — publishing and installing.
- [`utils/lifecycle.md`]({{ base }}utils/lifecycle.md) — where enabling sits in the boot sequence.
- [`ref/additives.md`]({{ base }}ref/additives.md) — the terse API list.
{% endblock %}
