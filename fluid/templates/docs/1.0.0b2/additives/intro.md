{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Additives{% endblock %}
{% block doc_section %}Additives{% endblock %}

{% block summary %}
An Additive is a **self-contained sub-app**: its own routers, templates, static files, frontend,
request lifecycle and manifest, mounted under its own URL prefix. It is the unit you build features
in and the unit you ship. Everything on this page is generated for you by `wf create additive` —
read it so you can extend the result correctly.
{% endblock %}

{% block body %}
## Anatomy

```text
additives/
└── portal/
    ├── __init__.py        # exposes `additive: Additive`  (mandatory)
    ├── manifest.json      # id, version, type, frontend    (mandatory)
    ├── config.py          # @register_config, optional `setup` for wf create app
    ├── api/               # JSON routes  -> /portal/api
    │   ├── __init__.py
    │   ├── health.py
    │   └── v1/__init__.py
    ├── app/               # HTML routes  -> /portal
    │   ├── __init__.py
    │   └── index.py
    ├── models/            # SQLAlchemy models
    ├── schemas/
    ├── services/
    ├── events/            # contracts
    ├── utils/
    ├── static/            # served at /portal/static
    ├── templates/         # namespaced under "portal/"
    └── frontend/          # optional Vite workspace
```

Hard requirements enforced by the constructor:

1. **The package must live under `additives.`** — `Additive.__init__` raises
   `AdditiveException("Additives have to be created inside the 'additives' package.")` otherwise.
2. **`manifest.json` must exist and validate.** A missing or malformed one raises
   `AdditiveException("[<name>] Failed to load manifest: …")`.
3. **The package must expose `additive`**, an `Additive` instance. `register_additives` logs an
   error and skips the package otherwise.

## The manifest

```json
{
  "id": "portal",
  "version": "1.0.0",
  "type": "default",
  "frontend": { "type": "none" },
  "name": "Portal",
  "description": "Customer portal",
  "authors": [{ "name": "Pierre", "email": "pierre@example.org" }],
  "requires": {
    "wf": ">=1.0.0b2",
    "additives": { "core": ">=1.0.0" },
    "packages": ["httpx"]
  }
}
```

| Field                    | Required | Rules                                                                                                                  |
|--------------------------|----------|------------------------------------------------------------------------------------------------------------------------|
| `id`                     | yes      | Must survive `safe_string()` — `[a-zA-Z0-9_-]` only. Cannot be `fluid`                                                 |
| `version`                | yes      | 1–3 numbers, each 0–999, optional pre-release stage `a`/`b`/`rc` with build 1–9. No epoch, dev, post or local segments |
| `type`                   | yes      | `"default"` or `"base"`                                                                                                |
| `frontend`               | yes      | Same shape as `APP_FRONTEND`. A `base` **must** use `{"type": "none"}`                                                 |
| `name`                   | no       | Defaults to the package directory name                                                                                 |
| `description`, `authors` | no       | Metadata                                                                                                               |
| `requires`               | no       | `wf` (framework specifier), `additives` (map or list), `packages` (pip requirements)                                   |

The **`id`** is the public identity: it is the URL prefix (`_` → `-`), the template namespace, the
static mount, the config-file switch and the prefix `unique_name()` applies to contracts.

## The additive object

```python
# additives/portal/__init__.py
from webfluid import Additive

additive = Additive(
    __name__,
    required_extensions=["sqlalchemy", "events"]
)


@additive.before_enable
def before_enable(fluid):
    from .app import index
    additive.app.get("/")(index)

    from .api import v1
    additive.api.include_router(v1)
```

```python
Additive(import_name, base=None, required_extensions=None)
```

- `base` — a base Additive to extend, resolved with `import_base("core")`. See
  [`additives/base.md`]({{ base }}additives/base.md).
- `required_extensions` — lowercase names checked against `EXT_<NAME>` when the Additive is enabled.
  A missing one raises `RuntimeError: Extension '<name>' is not enabled.` A base's list is merged
  into the child's.

{{ rule("Register routes inside before_enable, not at module level. The framework includes the three
    routers into the app the moment the Additive is enabled — anything attached after that point is
    never mounted. before_enable is also already inside the running event loop, which is what event
    and query registration needs.") }}

## The three routers

| Attribute      | Prefix | Default response | Mounted at  |
|----------------|--------|------------------|-------------|
| `additive.app` | —      | `HTMLResponse`   | `/<id>`     |
| `additive.api` | `/api` | JSON             | `/<id>/api` |
| `additive.ws`  | `/ws`  | —                | `/<id>/ws`  |

(For a **base** Additive all three are created without prefixes, because the child supplies them.)

They are `webfluid.core.additive.Router` instances — `APIRouter` subclasses that wrap every endpoint
so its log lines are attributed to the Additive, and that support `http_middleware`.

```python
# additives/portal/app/index.py
async def handle_request():
    from .. import additive
    return await additive.render("index.html")
```

```python
# additives/portal/app/__init__.py
from .index import handle_request as index

__all__ = ["index"]
```

{% raw %}
```html
<!-- additives/portal/templates/index.html -->
{% extends "fluid_base.html" %}

{% block title %}{{ _('PORTAL_TITLE') }}{% endblock %}

{% block head %}
    {{ frontend() if frontend else "" }}
{% endblock %}

{% block content %}
    <h1>{{ _('PORTAL_HEADING') }}</h1>
{% endblock %}
```
{% endraw %}

{{ rule("Import the additive object lazily inside the handler (from .. import additive), not at
    module top level. The package __init__ imports the handler modules from before_enable, so a
    top-level import of the package from a handler module is a circular import.") }}

## Rendering

`additive.render(template, **ctx)`:

1. runs the Additive's own context processors,
2. prefixes the name with the Additive's id,
3. delegates to `FluidContext.current().fluid.render(...)`.

So `additive.render("index.html")` resolves `additives/portal/templates/index.html`. If the Additive
extends a base, the base's templates are in the same namespace, searched after the child's.

An Additive rendering through a **parent** (i.e. it *is* a base with a parent) forwards to the
parent's `render` instead, so the child's namespace wins.

{{ warning("additive.render needs a FluidContext with a fluid — it calls FluidContext.current(),
    which raises RuntimeError outside a request. Rendering from a scheduled job means building the
    context yourself.") }}

## Context and lifecycle hooks

```python
@additive.context_processor
def defaults():
    return {"section": "portal"}


@additive.before_request
def guard():
    ...            # return a response to short-circuit


@additive.after_request
async def shape(result):
    return result  # see the warning below


@additive.before_enable
def before_enable(fluid): ...     # exactly one argument: fluid


@additive.after_enable
def after_enable(): ...           # no arguments
```

All of these are **scoped to the Additive's own routes**, not the whole app.

The Additive's Jinja context always carries `id` (its own id) and `url_for` — a variant that runs
the endpoint name through `unique_name()` first, so an Additive's reverse-URL lookups never collide
with anyone else's.

{{ bug("additive.after_request does NOT receive a Response. It runs inside the router's endpoint
    wrapper, before FastAPI serialises anything, so what it receives — and must return — is whatever
    your handler returned: a dict, a pydantic model, a string. fluid.after_request, which sits in the
    ASGI middleware, does receive a real Response. Same name, different altitude.") }}

`http_middleware` wraps every route of one router, and the chain is built once, not per request:

```python
@additive.api.http_middleware
def timed(call_next):
    async def wrapper(*args, **kwargs):
        return await call_next(*args, **kwargs)
    return wrapper
```

## Enabling

Two switches, both required:

```ini
[features]
WF_ADDITIVES = 1

[additives]
portal = 1
```

The key is the manifest **`id`**, not the directory name. Nothing loads unless it is explicitly
switched on.

### What happens on enable

`register_additives` runs as a startup hook and, for each enabled Additive:

1. `check_enable()` — a base raises here; it may not be enabled directly.
2. `manifest.check_requirements(additive_root)` — framework version and required Additives.
3. If it extends a base: the base's routers are included into the child's, the base takes the
   child's prefix and id, and the base's requirements are checked too.
4. If it has a frontend: `cover_additive`, `frontend` goes into the Jinja context, the frontend
   prefix is registered as a static prefix.
5. `id` goes into the Jinja context; the template loader is added to the app.
6. The three routers are included into the app under `/<prefix>`.
7. If `static/` exists, it is mounted at `/<prefix>/static` under the route name `<id>_static`.

`before_enable` hooks run **before** step 1's siblings (the whole `_enable` body); `after_enable`
hooks run after. Failures are caught and logged per Additive — one broken Additive does not stop the
app.

{{ info("Enabling happens inside a startup hook, i.e. inside the running event loop. That is why
    before_enable is the right place to register events, queries and scheduler jobs.") }}

## Rules

{{ rule("One feature per Additive. If two Additives always ship together and neither works alone,
    they are one Additive — or one base plus one child.") }}

{{ rule("Never import another Additive's Python modules. Talk over events and queries; see
    additives/contract.md. An import welds the two together and makes both unshippable.") }}

{{ rule("Prefix every config key, cache key, event name and query name with the Additive's id. Use
    additive.unique_name() for contracts and a manual <ID>_ prefix for config keys.") }}

{{ rule("Reach the app's batteries through webfluid.core.ext, exactly as the main app does. An
    Additive shares the runtime — same database, same cache, same event manager, no wiring.") }}

## Next

- [`additives/base.md`]({{ base }}additives/base.md) — foundations that are meant to be extended.
- [`additives/contract.md`]({{ base }}additives/contract.md) — talking without imports, requirements,
  packaging.
- [`cli/create.md`]({{ base }}cli/create.md) — `wf create additive` writes all of the above.
{% endblock %}
