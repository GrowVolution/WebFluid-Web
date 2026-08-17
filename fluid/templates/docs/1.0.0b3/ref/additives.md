{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Reference: Additives{% endblock %}
{% block doc_section %}Reference{% endblock %}

{% block summary %}
The module system: the `Additive` class, its `Router`, the `Manifest`, and the registry helpers that
discover and load Additives at startup.
{% endblock %}

{% block body %}
## `Additive`

```python
from webfluid import Additive

additive = Additive(import_name, base=None, required_extensions=None)
```

Must live inside the `additives` package and expose itself as a module attribute named `additive`.

### Routers

| Attribute | Prefix (default kind) | Response class | Mounted at |
|---|---|---|---|
| `api` | `/api` | JSON | `/<prefix>/api` |
| `app` | — | `HTMLResponse` | `/<prefix>` |
| `ws` | `/ws` | — | `/<prefix>/ws` |

A **base** Additive's routers carry no prefixes — the child's supply them.

### Methods and properties

| Member | Notes |
|---|---|
| `await render(template, **ctx)` | Runs the Additive's context processors, prefixes with the id, delegates to `fluid.render` |
| `before_enable(fn)` | `fn(fluid)` — **exactly one** argument. Where routes and contracts are registered |
| `after_enable(fn)` | `fn()` — no arguments. Reverse order |
| `before_request(fn)` | `fn()` — scoped to this Additive's routes |
| `after_request(fn)` | `fn(result)` — see the bug below |
| `context_processor(fn)` | `fn()` → dict, merged into this Additive's renders |
| `jinja_context` | The Additive's context dict; frozen after enable |
| `await enable(fluid)` | Guarded by `require_extensions(*required_extensions)` |
| `install(_seen=None)` | Resolve required Additives, extract files, pip-install packages |
| `configure(config)` | Contribute `setup` questions to `wf create app` |
| `check_enable()` | Raises for a base |
| `unique_name(name)` | `f"{id}_{name}"`, delegating to the parent when this is an extended base |
| `id`, `name`, `version`, `prefix`, `is_base`, `base`, `parent`, `manifest`, `root_path`, `import_name`, `frontend`, `required_extensions` | Identity and metadata. `version` is a `Version` |

{{ bug("after_request runs inside the router's endpoint wrapper, before FastAPI serialises anything.
    It receives — and must return — whatever the handler returned: a dict, a model, a string. This is
    NOT the same as fluid.after_request, which sits in the ASGI middleware and receives a real
    Response.") }}

### Construction errors

| Condition | Exception |
|---|---|
| `import_name` does not contain `"additives."` | `AdditiveException` |
| Missing or invalid `manifest.json` | `AdditiveException` wrapping `FileNotFoundError` / `ManifestError` |
| A base given a `base` | `AdditiveException("Base additives cannot extend other additives.")` |
| A `base` argument that is not a base | `AdditiveException("Default additives can only extend base additives.")` |

## `Router`

`webfluid.core.additive.Router`, an `APIRouter` subclass used by all three Additive routers.

| Member | Notes |
|---|---|
| `http_middleware(fn)` | Wrap every route of this router. `fn(call_next)` returns the wrapper. The chain is built **once**, on first request |
| `add_api_route` / `add_api_websocket_route` | Overridden to wrap the endpoint in `log_factory.additive_context`, so its log lines go to the `webfluid.additives` logger |

The framework installs one `http_middleware` on `api` and `app` itself — the one that runs the
Additive's `before_request` / `after_request` phases.

{{ bug("It is installed on api and app only. additive.ws routes are registered through
    add_api_websocket_route, which wraps the endpoint for logging but not in the middleware chain, so
    an Additive's before_request guard does NOT protect its websocket endpoints. Check the connection
    inside the endpoint.") }}

{{ warning("The middleware chain is built lazily, on the first call of each endpoint, and cached in
    that endpoint's closure. An http_middleware registered after a route has already served a request
    applies to routes that have not been hit yet and not to that one. Register middleware in
    before_enable, with everything else.") }}

## `Manifest`

```python
from webfluid import Manifest
```

Dict-like: `manifest["id"]`, `get`, `keys`, `values`, `items`, `__contains__`, `__len__`,
`__setitem__`.

### Fields

| Field | Type | Required | Validator |
|---|---|---|---|
| `id` | str | yes | `id_check` — must equal `safe_string(id)` |
| `version` | str | yes | `version_check` |
| `type` | str | yes | `type_check` — `"base"` or `"default"` |
| `frontend` | dict | yes | `validate_config` from `webfluid.utils.surface` |
| `name` | str | no | |
| `description` | str | no | |
| `authors` | list | no | |
| `requires` | dict | no | Checked at enable time |

`version_check` accepts 1–3 release numbers (each 0–999) and an optional pre-release stage
`a`/`b`/`rc` with a build of 1–9. Epoch, dev, post and local segments are rejected. So `1.2.0a1` is
valid, `1.0.0.dev1` is not.

A `"base"` with a `frontend.type` other than `"none"` raises `ManifestError`.

### `requires`

```json
"requires": {
  "wf": ">=1.0.0b3",
  "additives": { "core": ">=1.0.0" },
  "packages": ["httpx"]
}
```

`additives` also accepts a list: `["core@>=1.0.0", "billing"]`, where a bare id means `"*"`.

`check_requirements(additive_root)` validates the framework version and the required Additives; it
may be called repeatedly. A missing `wf` key logs a warning rather than failing.

## `webfluid.utils.additives`

```python
from webfluid.utils.additives import (
    register_additives, installed_additives, installed_bases,
    import_base, require_extensions, id_check, version_check, type_check
)
```

| Function | Notes |
|---|---|
| `await register_additives(fluid)` | The `WF_ADDITIVES` startup hook. Discovers, imports, enables and wires every switched-on Additive. Failures are logged per Additive, not fatal |
| `installed_additives(package, do_log=False, cache=True)` | `[(id, Version, dirname), ...]` for `type: "default"`. The path's basename must be `additives` |
| `installed_bases(package, do_log=False, cache=True)` | Same for `type: "base"` |
| `import_base(base_id)` | Resolve an installed base by id, or `None` |
| `require_extensions(*names)` | Decorator asserting `EXT_<NAME>` for each; raises `RuntimeError` |
| `id_check`, `version_check`, `type_check` | The manifest field validators, each returning `(ok, value_or_reason)` |

Discovery results are cached per package path — pass `cache=False` for a fresh scan.

## What enabling does, in order

```text
1. check_enable()                      base -> raise
2. manifest.check_requirements()       framework + additive versions
3. if base:
     base.check_requirements()
     child.{api,app,ws}.include_router(base.{api,app,ws})
     base.parent = child; base.prefix = child.prefix
     base.jinja_context["id"] = child.id
4. if frontend:
     frontend.cover_additive(additive)
     jinja_context["frontend"] = frontend.include
     fluid.static_prefixes.add(frontend.prefix)
5. jinja_context["id"] = id;  jinja freeze + add_template_loader
6. fluid.include_router(api / app / ws, prefix=additive.prefix)
7. if static/ exists: mount at <prefix>/static, name "<id>_static"
```

`before_enable` hooks run before step 1's body, `after_enable` after step 7 — child first, then base
in both phases.

## Next

- [`ref/utils.md`]({{ base }}ref/utils.md) — the helper layer.
{% endblock %}
