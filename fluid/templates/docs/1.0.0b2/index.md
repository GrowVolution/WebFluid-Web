{% extends "docs/base_overview.md" %}
{% from "docs/partials/_callout.md" import rule, warning %}

{% block lead %}
This is the **Markdown edition** of the WebFluid documentation. It mirrors the HTML docs page for
page — same paths, `.md` suffix — but it is written for you, an AI agent, not for a human
reading a curriculum. It trades narrative for density: exact signatures, exact defaults, the rules
that keep generated code correct, and the traps that make it silently wrong.

Every page here is also available as HTML by dropping the `.md`. Prefer the `.md`.
{% endblock %}

{% block what %}
## What WebFluid is

WebFluid is a **fullstack Python application runtime**. The `webfluid` package ships an application
class (`Fluid`, a subclass of `fastapi.FastAPI`), a set of opt-in batteries ("extensions"), a
module system ("Additives"), a managed frontend layer ("surface") and a CLI (`wf`).

Mental model, in one line: **FastAPI for the routes, Flask-shaped ergonomics for the app object, and
a runtime that owns the process** — configuration, logging, the event loop, the frontend build, the
migration environment and the module registry.

|                 |                                                                         |
|-----------------|-------------------------------------------------------------------------|
| Python          | 3.14+ required                                                          |
| Install         | `pip install webfluid=={{ version }}` (pin it; this is a beta)          |
| Import root     | `webfluid`                                                              |
| App class       | `webfluid.Fluid` — a `FastAPI` subclass, so every FastAPI idiom applies |
| Run             | `wf run <app>` — **not** `uvicorn main:app` (see the hook caveat below) |
| Template engine | Jinja2, **async**, autoescape **off**                                   |
| ORM             | SQLAlchemy 2.x declarative, sync **and** async sessions                 |
| License         | MIT                                                                     |
| Repository      | <https://github.com/GrowVolution/WebFluid>                              |

### What it is good for

- Server-rendered applications that also need a real client build (Vite/React/Vue/Svelte) without
  running two projects.
- Applications assembled from **shippable feature modules** (Additives) rather than one package —
  each with its own routes, templates, static files, frontend and manifest.
- Multi-tenant-ish deployments where one repository serves several apps that differ only by config.
- Anything that would otherwise be "FastAPI + a pile of glue": auth, i18n, mail, cache, events,
  JWT, migrations and a scheduler are all present and switched on per app.

### What it is not

- Not a microframework. It boots a lot; almost all of it is behind switches you must turn on.
- Not usable under an external ASGI server today — lifecycle hooks live in `mix()`, not in the ASGI
  lifespan protocol. See the known issues.
- Not a stable API yet. Everything in a package's `__all__` follows semver from this beta onwards;
  everything else is internal.

### The 30-second app

```python
# main.py
from webfluid import Fluid

def prepare_fluid() -> Fluid:
    app = Fluid(__name__)

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

`SECRET_KEY` is the only mandatory config value. Everything else has a framework default.
{% endblock %}

{% block map %}
## How to navigate these docs

Each entry below is a full page. Fetch the ones you need; do not fetch all of them by default.
If you want the entire corpus in one request: `/llms-full.txt`. The machine-readable index is
`/llms.txt`.

### By layer

| Page                                                                                                                                                                                                                                                                | Read it when you need to                                                          |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| [`get-started.md`]({{ base }}get-started.md)                                                                                                                                                                                                                        | Bootstrap a project, know the directory layout the framework expects              |
| [`config/app-config.md`]({{ base }}config/app-config.md)                                                                                                                                                                                                            | Write or read `app_configs/<app>.ini`; enable extensions/features; handle secrets |
| [`config/config-class.md`]({{ base }}config/config-class.md)                                                                                                                                                                                                        | Set runtime settings; the complete `DefaultConfig` key table                      |
| [`ext/base.md`]({{ base }}ext/base.md)                                                                                                                                                                                                                              | Write a `FluidExtension` or a `wf` sub-CLI                                        |
| [`ext/scheduling.md`]({{ base }}ext/scheduling.md)                                                                                                                                                                                                                  | Schedule background jobs                                                          |
| [`ext/sqlalchemy.md`]({{ base }}ext/sqlalchemy.md)                                                                                                                                                                                                                  | Define models, run queries, manage binds and sessions                             |
| [`ext/migrate.md`]({{ base }}ext/migrate.md)                                                                                                                                                                                                                        | Create and apply Alembic migrations                                               |
| [`ext/mailman.md`]({{ base }}ext/mailman.md)                                                                                                                                                                                                                        | Send mail                                                                         |
| [`ext/babel.md`]({{ base }}ext/babel.md)                                                                                                                                                                                                                            | Translate, format dates/numbers, select locale                                    |
| [`ext/security.md`]({{ base }}ext/security.md)                                                                                                                                                                                                                      | Users, passwords, route guards, CSRF, tokens, OAuth                               |
| [`ext/events.md`]({{ base }}ext/events.md)                                                                                                                                                                                                                          | In-process pub/sub, request/response queries, browser push                        |
| [`ext/cache.md`]({{ base }}ext/cache.md)                                                                                                                                                                                                                            | Cache values (redis or in-process)                                                |
| [`ext/jwt.md`]({{ base }}ext/jwt.md)                                                                                                                                                                                                                                | Mint and verify JWTs                                                              |
| [`surface/tooling.md`]({{ base }}surface/tooling.md)                                                                                                                                                                                                                | Understand `WF_*` feature switches, `fluid_base.html`, Tailwind, themes           |
| [`surface/frontend.md`]({{ base }}surface/frontend.md)                                                                                                                                                                                                              | Configure `APP_FRONTEND`; wire htmx or a Vite SPA                                 |
| [`surface/jinja.md`]({{ base }}surface/jinja.md)                                                                                                                                                                                                                    | Know which template file a name resolves to                                       |
| [`additives/intro.md`]({{ base }}additives/intro.md)                                                                                                                                                                                                                | Build a feature module                                                            |
| [`additives/base.md`]({{ base }}additives/base.md)                                                                                                                                                                                                                  | Build or extend a base Additive                                                   |
| [`additives/contract.md`]({{ base }}additives/contract.md)                                                                                                                                                                                                          | Make two Additives talk without importing each other                              |
| [`utils/lifecycle.md`]({{ base }}utils/lifecycle.md)                                                                                                                                                                                                                | Run code at startup/shutdown                                                      |
| [`utils/runtime.md`]({{ base }}utils/runtime.md)                                                                                                                                                                                                                    | Reach the request from anywhere; hook the request flow                            |
| [`utils/logging.md`]({{ base }}utils/logging.md)                                                                                                                                                                                                                    | Log correctly                                                                     |
| [`cli/wf.md`]({{ base }}cli/wf.md)                                                                                                                                                                                                                                  | Know what commands exist                                                          |
| [`cli/create.md`]({{ base }}cli/create.md)                                                                                                                                                                                                                          | Scaffold a project, app or Additive                                               |
| [`cli/run.md`]({{ base }}cli/run.md)                                                                                                                                                                                                                                | Run an app, pick flags, understand debug mode                                     |
| [`cli/ocean.md`]({{ base }}cli/ocean.md)                                                                                                                                                                                                                            | Install or publish packages                                                       |
| [`ref.md`]({{ base }}ref.md) → [`ref/core.md`]({{ base }}ref/core.md), [`ref/extensions.md`]({{ base }}ref/extensions.md), [`ref/surface.md`]({{ base }}ref/surface.md), [`ref/additives.md`]({{ base }}ref/additives.md), [`ref/utils.md`]({{ base }}ref/utils.md) | Look up a symbol without prose                                                    |

### By task

| Task                                  | Pages, in order                                                                                                                                    |
|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| "Create a new WebFluid project"       | [`cli/create.md`]({{ base }}cli/create.md), [`get-started.md`]({{ base }}get-started.md), [`config/app-config.md`]({{ base }}config/app-config.md) |
| "Add a database model + endpoint"     | [`ext/sqlalchemy.md`]({{ base }}ext/sqlalchemy.md), [`ext/migrate.md`]({{ base }}ext/migrate.md)                                                   |
| "Add login / protect a route"         | [`ext/security.md`]({{ base }}ext/security.md), then [`ext/jwt.md`]({{ base }}ext/jwt.md) for machine clients                                      |
| "Add a page"                          | [`surface/jinja.md`]({{ base }}surface/jinja.md), [`surface/tooling.md`]({{ base }}surface/tooling.md)                                             |
| "Make it multilingual"                | [`ext/babel.md`]({{ base }}ext/babel.md)                                                                                                           |
| "Split a feature into its own module" | [`additives/intro.md`]({{ base }}additives/intro.md), [`additives/contract.md`]({{ base }}additives/contract.md)                                   |
| "Push live updates to the browser"    | [`ext/events.md`]({{ base }}ext/events.md)                                                                                                         |
| "Something runs at startup"           | [`utils/lifecycle.md`]({{ base }}utils/lifecycle.md)                                                                                               |
| "Why is my config value ignored"      | [`config/app-config.md`]({{ base }}config/app-config.md), [`config/config-class.md`]({{ base }}config/config-class.md)                             |
{% endblock %}

{% block rules %}
## Rules that apply everywhere

These recur on almost every page. Internalise them once.

1. **Nothing is on by default.** Extensions are enabled by `EXT_*` switches in the app config,
   surface features by `WF_*` switches, Additives by id in `[additives]`. Code that uses
   `webfluid.core.ext.db` without `EXT_SQLALCHEMY = 1` fails at runtime, not at import.
2. **Reach batteries through the shared registry**, never by constructing them:
   `from webfluid.core.ext import db, babel, security, events, cache, mail, jwt, scheduler`.
   These are process-wide singletons created lazily on first attribute access.
3. **Use the app factory.** Name it `prepare_fluid()` in `main.py`. `wf migrate` looks for exactly
   that name, and module-level `Fluid(__name__)` breaks as soon as anything imports your modules
   without a config in the environment.
4. **Do not import `fluid` at module level inside handlers.** In a factory there is no module-level
   app. Use `FluidContext.current().fluid`, or for Additives the module-local `additive`.
5. **`fluid.config` always contains every framework key.** Index it (`fluid.config["X"]`), do not
   `.get("X", <repeat of the default>)`. Only keys *you* invent need a `get` with a fallback.
6. **Register hooks while building the app, never from a request.** Startup/shutdown hooks,
   template loaders, sources and static prefixes are frozen once the server is up.
7. **Every hook has an arity contract.** Startup/shutdown hooks and `before_request` take **no**
   required arguments; `after_request` takes exactly one; event and query handlers take exactly one.
   A mismatch raises `TypeError` at registration time.
8. **Async first.** Every I/O API has an `a*` twin (`asend`, `agettext`, `aget`, `aencode`,
   `async_executor`). Inside `async def`, use the async one.
9. **Write no comments or docstrings if you are editing an existing WebFluid codebase** unless the
   project already has them — the generated code style is deliberately bare.
10. **Pin the version.** This is a beta; `__all__` is semver-stable, everything else is not.

{{ rule("When you generate code for this framework, prefer the shape the scaffolder produces —
    fluid/api for JSON routers, fluid/app for HTML routes, fluid/models, fluid/schemas,
    fluid/services, fluid/events, fluid/utils. Every page in these docs assumes that layout, and
    wf create project produces it.") }}
{% endblock %}

{% block release %}
## Release state: {{ version }} ({{ stage }}, {{ date }})

Beta 2 is a stabilisation release over beta 1. No new batteries, almost no renames; the surface of
the framework is unchanged. What it fixed, condensed:

- `FluidContext.__len__` made a data-less request context falsy, so `if ctx` was false on every
  plain request. Consequence: `get_locale` dropped `?lang=`, the `lang` cookie and
  `Accept-Language` and every page fell back to `BABEL_DEFAULT_LOCALE`; `Themes.get` lost the
  session theme; `country_from_request` lost its headers. **Contexts are always truthy now — test
  `try_current()` against `None`, never for truthiness.**
- Locale and timezone selectors treat request input as untrusted: an unparseable `?lang=`, `lang`
  cookie, `Accept-Language`, `tz` cookie or `X-Timezone` is skipped instead of raising.
- The 500 handler no longer leaks `str(exc)` outside debug mode.
- `slowapi`'s limiter is seated on `app.state`, so a hit limit answers 429 instead of 500.
- `I18nKey` is unique per `(key, domain)` instead of globally. **Existing databases need a
  migration.**
- `SECURITY_CSRF_COOKIE_NAME` is actually used by both `csrf_response` and `csrf_protect`.
- The HTTP proxy drops the upstream's hop-by-hop/encoding headers and recomputes `Content-Length`;
  the websocket proxy no longer mangles paths containing the word `http`.
- `wf migrate init` runs (it raised `NameError` on every call in beta 1).
- Arrow/function keys no longer kill `wf run --interactive` on Windows.
- Shutdown always completes, including when the server task dies (e.g. a bound port).
- Every generated file is written as explicit UTF-8 — **except `app_configs/<name>.ini`**, see
  known issues.
{% endblock %}

{% block bugs %}
## Known issues in {{ version }}

Read this section before generating code. Each of these is a live defect in the shipped package,
not a documentation gap. They are repeated in context on the relevant pages.

### Runtime and lifecycle

- **Hooks do not run under an external ASGI server.** Startup and shutdown hooks run from
  `fluid.mix()`, not through the ASGI lifespan protocol. `uvicorn main:fluid` or `gunicorn` skips
  table creation, the scheduler, Additive registration and the frontend build. **Run apps through
  `wf run`.**
- **`url_for` is `None` outside a request.** The context processors build it from the request in
  the current context. Rendering a template from a startup hook, a scheduled job or a mail routine
  fails with `NoneType is not callable`. Use `fluid.url_path_for()` or `BASE_URL` in off-request
  templates.
- **Streaming responses skip `after_request` processors.** The request middleware buffers so
  processors can rewrite the body and gives that up the moment the app announces `more_body`.
  A buffered response also keeps the app's `Content-Length` — return a *new* response when you
  change the body.
- **`additive.after_request` does not receive a `Response`.** It runs inside the router's endpoint
  wrapper, before FastAPI serialises anything, so it receives whatever the handler returned (a
  dict, a model, a string). `fluid.after_request` *does* receive a real `Response`.
- **`RATELIMIT_DEFAULT` never applies.** slowapi evaluates application-wide defaults only from its
  own middleware, which the framework does not install. An undecorated route is never checked, and
  `@fluid.limit(...)` replaces the defaults rather than adding to them. Put the limit on the route.

### Data

- **`database_uris` rewrites the scheme word everywhere in the URI**, not only the leading one.
  `sqlite:///data/sqlite/app.db` becomes `sqlite+aiosqlite:///data/sqlite+aiosqlite/app.db`. Keep
  the scheme word out of paths, database names, users and passwords.
- **`wf migrate init` picks its template from `SQLALCHEMY_BINDS` in the config, at init time.**
  Binds attached at runtime via `Model.set_bind` are invisible to it.

### Mail

- **The synchronous client ignores `MAIL_USE_TLS`.** `SyncManager` stores the flag and opens a
  plain connection; only `MAIL_USE_STARTTLS` is honoured on that path, so `mail.send()` against an
  implicit-TLS server talks plaintext with your credentials in it. The async client is correct.
  The shipped defaults (port 587 + `MAIL_USE_TLS` on + `MAIL_USE_STARTTLS` off) are the wrong pair
  for both clients — use 587 with `MAIL_USE_STARTTLS`, or `mail.asend()`.

### Auth and tokens

- **JWT signing keys live in the cache**, and a rotation runs as a startup hook. With
  `CACHE_TYPE = legacy` (in-process) every restart mints a new key and forgets the old ones, so
  every previously issued token stops decoding. Run JWT against Redis. A token whose `kid` is not
  in the cache raises a raw `TypeError` from the signing library, not `InvalidTokenError` — catch
  broadly when decoding by hand.
- **`resolve_bearer` assumes a numeric subject.** It does `int(sub)`; a uuid or email `sub` raises
  `ValueError` inside the gate's fallback branch and the request comes back 500 instead of 401.
  Keep `sub` the user's primary key.

### i18n

- **A translation equal to its source is read as a miss** and the next domain in the escalation
  chain answers instead. Use symbolic keys (`ERROR_TITLE`) for catalogs you control.
- **Uncached translations block.** A key opted out of the cache is read through a synchronous
  session on the `gettext` path. `agettext` is the non-blocking alternative; the Jinja callables
  stay synchronous on purpose.

### Config and tooling

- **`app_configs/<name>.ini` is written and read in the interpreter's locale encoding**, not UTF-8.
  Symmetric on one machine, broken the moment a config with a non-ASCII value is written on a
  Windows console and read elsewhere. Keep app-config values ASCII or use the `*_FILE` indirection.
- **`events.create_signal` / `events.event` need a running loop.** Call them from an enable hook,
  a startup hook or a request handler — never at import time.
- **Event delivery is best-effort.** Broadcasts use a bounded per-listener buffer sized by
  `EVENTS_EVENT_QUEUE_SIZE`; a slow consumer loses its oldest events (logged as a warning).
- **HMR rides on a proxied websocket that can die.** A browser refresh re-establishes it; no need
  to restart `wf run`.

{{ warning("Treat this list as part of the API. Generating code that trips one of these produces a
    program that looks right and behaves wrong.") }}
{% endblock %}

{% block breaks %}
## Breaking changes in {{ version }}

All three are in `webfluid.extensions.babel.utils`.

| Before                                                                  | Now                                                                             | Action                                                                                 |
|-------------------------------------------------------------------------|---------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| `format_date(d, ftm=...)`                                               | `format_date(d, fmt=...)`                                                       | Rename the keyword. Positional calls and the `dateformat` Jinja filter are unaffected. |
| `to_utc(dt)` returned `dt.replace(tzinfo=None)`                         | Converts to UTC first, then drops the offset; reads a naive input as user-local | If you relied on it to strip a `tzinfo`, call `dt.replace(tzinfo=None)` yourself.      |
| `parse_best_match(None, available)` returned the first supported locale | Returns `None`                                                                  | Handle the `None` and fall back to `BABEL_DEFAULT_LOCALE`.                             |

## About this Markdown edition

- Same URL as the HTML page, plus `.md`. The overview is `{{ base }}.md`.
- The HTML page declares this file via `<link rel="alternate" type="text/markdown">`, and this
  file's response carries a `Link: …; rel="canonical"` header pointing back at the HTML.
- `Accept: text/markdown` on any documentation URL returns this variant without the suffix.
- Index of every page: `/llms.txt`. Whole corpus in one document: `/llms-full.txt`.
- Older versions (`1.0.0a1`, `1.0.0a2`, `1.0.0b1`) are HTML only. The Markdown mirror starts at
  `1.0.0b2`.
{% endblock %}
