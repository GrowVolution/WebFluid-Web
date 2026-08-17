{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Getting Started{% endblock %}
{% block doc_section %}Introduction{% endblock %}

{% block summary %}
Install, minimum viable app, and the directory layout every other page assumes. If you are
scaffolding a real project, skip to [`cli/create.md`]({{ base }}cli/create.md) — `wf create project`
produces this layout in one command. Read this page anyway: it explains *why* the layout is what it
is, which is what you need in order to extend it correctly.
{% endblock %}

{% block body %}
## Requirements

|                     |                                                                                                                                                                    |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Python              | **3.14 or newer** (hard requirement)                                                                                                                               |
| Package             | `webfluid` on PyPI                                                                                                                                                 |
| CLI                 | `wf`, installed with the package                                                                                                                                   |
| Optional at runtime | Redis (cache, rate limits, JWT keys), a database (SQLite works out of the box), Node (downloaded on demand by the surface, not required for `type: none` / `htmx`) |

```bash
pip install webfluid=={{ version }}
```

Pin the version. This is a beta and only the names in each package's `__all__` are semver-stable.

## The minimum

The framework needs exactly three things to start: a `main.py`, a `fluid/templates/` directory and
an `app_configs/<name>.ini` carrying `SECRET_KEY`.

```bash
mkdir -p myapp/fluid/templates myapp/app_configs
cd myapp
```

```python
# main.py
from webfluid import Fluid
from fastapi.responses import HTMLResponse


def prepare_fluid() -> Fluid:
    app = Fluid(__name__)

    @app.get("/", response_class=HTMLResponse)
    async def home():
        return await app.render("index.html", name="world")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    prepare_fluid().mix()
```

```ini
; app_configs/app.ini
[general]
SECRET_KEY = supersecret
```

```bash
wf run app
```

Output:

```text
Starting application...
[WF]    [2026-08-01 18:04:29 +0200] [INFO]      Mixing your WebFluid application.
[WF]    [2026-08-01 18:04:29 +0200] [INFO]      Running startup hooks...
[WF]    [2026-08-01 18:04:29 +0200] [INFO]      Server is listening on 127.0.0.1:8000.
```

{{ rule("Always define the app inside a factory called prepare_fluid(). wf migrate imports main.py
    and calls exactly that name (falling back to a module-level fluid). A module-level
    Fluid(__name__) is constructed at import time, which means it is constructed by every tool that
    imports your modules — including ones that have no app config in the environment, where the
    constructor raises on the missing SECRET_KEY.") }}

## What `Fluid(import_name)` actually does

In constructor order — this is the sequence that decides what is available when:

1. `project_root` is resolved from `import_name` (the directory holding `main.py`);
   `additive_root` is `project_root / "additives"`.
2. `init_configs()` imports `fluid.config` and the `config` module of every **enabled** Additive.
3. `Config()` is built: `DefaultConfig` first, then every `@register_config`-decorated class merged
   on top in priority order. **After this, `fluid.config` holds every key the framework knows.**
4. `SECRET_KEY` is asserted. Missing → `FrameworkException`.
5. `self.name` is `APP_NAME` from the environment (set by `wf run`), lowercased and sanitised.
6. `FastAPI.__init__(**config["APP_CONFIG"])`.
7. Lifecycle phases, Jinja environment, sources, themes, static mounts, limiter, server.
8. Feature wiring: Additive registration is queued as a startup hook, enabled extensions are
   expanded, the frontend is set up.
9. Middleware: request middleware, session middleware, processing (if `WF_PROCESSING`), and the
   proxy-client shutdown hook.

Consequences you will hit:

- Config classes must be **registered before the constructor runs**. Putting `@register_config`
  in `fluid/config.py` is enough — step 2 imports it for you.
- Extensions are enabled during the constructor, so `webfluid.core.ext.db` is usable from step 8
  onwards, i.e. anywhere in a request or a hook, but not before `Fluid(...)` returns.
- `ProxyHeadersMiddleware`, the static mounts and the Jinja loader stack are finalised in the
  `_prepare` startup hook, not in the constructor.

## Rendering

`fluid.render(template, **ctx)` is **async**. It runs every registered context processor and then
renders through an async Jinja environment. `fluid.render_string(source, **ctx)` does the same for a
template held as a string.

```python
return await app.render("index.html", name="world")
```

{% raw %}
```html
<!-- fluid/templates/index.html -->
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{{ title }}</title></head>
<body>
    <p>Hello <b>{{ name }}</b>!</p>
</body>
</html>
```
{% endraw %}

Two things that surprise people:

- **Autoescape is on** for `.html`, `.htm`, `.xml`, `.xhtml`, `.svg` and every `render_string`
  source. A value that is deliberately HTML has to be `markupsafe.Markup` or carry `| safe`; never
  either on a value that came from a request. Other suffixes (`.txt`, `.md`) are not escaped.
- **Templates live in `fluid/templates`**, not next to `main.py`. Full resolution order is in
  [`surface/jinja.md`]({{ base }}surface/jinja.md).

{{ warning("render() has no is_string flag. Passing one is not an error — it silently becomes a
    template variable while your source string is looked up as a file name, and you get a
    TemplateNotFound naming the whole template. Use render_string.") }}

## The project layout

This is what `wf create project` writes and what every example in these docs assumes:

```text
myapp/
├── main.py                  # prepare_fluid(), includes the routers
├── package.json             # npm workspace (only with a Vite frontend)
├── vite.config.js           # orchestrator, written by the CLI
├── app_configs/             # one .ini per app — never committed
│   └── app.ini
├── additives/               # feature modules
└── fluid/
    ├── config.py            # @register_config Config
    ├── _my_config.py        # local overrides, gitignored
    ├── api/
    │   ├── __init__.py      # api_router (prefix /api)
    │   ├── health.py
    │   └── v1/__init__.py   # v1 router (prefix /v1)
    ├── app/                 # HTML routes
    │   ├── __init__.py      # app_router (HTMLResponse default)
    │   └── index.py
    ├── frontend/            # Vite workspace (vite frontend type only)
    ├── models/              # SQLAlchemy models
    ├── schemas/             # pydantic schemas
    ├── services/            # business logic
    ├── events/              # event and query handlers
    ├── utils/
    ├── static/
    │   ├── css/tailwind_raw.css
    │   ├── img/
    │   └── js/
    └── templates/
        └── index.html
```

The split is load-bearing, not decorative:

| Directory         | Holds                    | Why it matters                                                 |
|-------------------|--------------------------|----------------------------------------------------------------|
| `fluid/api`       | JSON routers             | Mounted under `/api`; default response class is JSON           |
| `fluid/app`       | HTML routes              | Router is created with `default_response_class=HTMLResponse`   |
| `fluid/models`    | `db.Model` subclasses    | The generated Alembic `env.py` imports `fluid.models` by name  |
| `fluid/schemas`   | Pydantic models          | Where the security validators plug in                          |
| `fluid/services`  | Business logic           | Handlers stay thin; services are reusable from jobs and events |
| `fluid/events`    | Signals, events, queries | Registered from a startup hook, not at import                  |
| `fluid/static`    | Served at `/static`      | Reverse it with the route name `static`                        |
| `fluid/templates` | Jinja templates          | Searched *before* the framework's own templates                |

{{ rule("Put handlers in their own module and attach them to a router in the package __init__.py.
    The scaffolder does this, the Additive system does this, and it is the only shape that works
    cleanly with the factory pattern (no module-level app to close over).") }}

A router package, in full:

```python
# fluid/app/index.py
from webfluid.core.context import FluidContext


async def handle_request():
    ctx = FluidContext.current()
    return await ctx.fluid.render("index.html")
```

```python
# fluid/app/__init__.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

app_router = APIRouter(default_response_class=HTMLResponse)

from fluid.app.index import handle_request as index
app_router.get("/")(index)
```

```python
# main.py
def prepare_fluid() -> Fluid:
    app = Fluid(__name__)

    from fluid.app import app_router
    from fluid.api import api_router
    app.include_router(app_router)
    app.include_router(api_router)

    return app
```

`FluidContext.current()` is how a handler reaches the app without a module-level reference. Details
in [`utils/runtime.md`]({{ base }}utils/runtime.md).

## Debug mode

`wf run app -d` sets `DEBUG_MODE=1`, which changes a lot:

- `SESSION_COOKIE_SECURE` defaults to `False` (so sessions survive plain http on localhost).
- `STATIC_MAX_AGE` drops to `0`, and asset URLs get a `?t=<timestamp>` cache-buster.
- Jinja `auto_reload` is on, so template edits are picked up.
- The detailed `errors/debug/500.html` replaces the generic 500 page, and the JSON error body
  carries the message, type and traceback.
- The Vite dev server is started and proxied for HMR (Vite frontends only).
- The `[dev]` section of the app config is applied.
- `LOG_LEVEL` is forced to `debug`.

{{ info("Debug mode refuses port 5173 — that port is reserved for the Vite dev server the framework
    manages.") }}

## Checklist for a first working app

1. `pip install webfluid=={{ version }}` (Python 3.14+).
2. `wf create project myapp` — or the three directories above by hand.
3. `wf create app app` (interactive) — or an `.ini` with `SECRET_KEY`.
4. Turn on the extensions you actually need in `[extensions]`; nothing is on by default.
5. Put the app together in `prepare_fluid()`; register hooks there, not later.
6. `wf run app -d` while developing, `wf run app` otherwise.

## Next

- [`config/app-config.md`]({{ base }}config/app-config.md) — the `.ini` format and every switch.
- [`config/config-class.md`]({{ base }}config/config-class.md) — the full default-config table.
- [`cli/create.md`]({{ base }}cli/create.md) — let the scaffolder write all of this.
{% endblock %}
