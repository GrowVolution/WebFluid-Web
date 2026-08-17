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

|                 |                                                                          |
|-----------------|--------------------------------------------------------------------------|
| Python          | 3.14+ required                                                           |
| Install         | `pip install webfluid=={{ version }}` (pin it; this is a beta)           |
| Import root     | `webfluid`                                                               |
| App class       | `webfluid.Fluid` — a `FastAPI` subclass, so every FastAPI idiom applies  |
| Run             | `wf run <app>` — **not** `uvicorn main:app` (see the hook caveat below)  |
| Template engine | Jinja2, **async**, autoescape **on** (html/xml suffixes + `render_string`) |
| ORM             | SQLAlchemy 2.x declarative, sync **and** async sessions                  |
| Agent skill     | `webfluid/.agents/skills/webfluid` ships inside the package              |
| License         | MIT                                                                      |
| Repository      | <https://github.com/GrowVolution/WebFluid>                               |

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
- Not a stable API yet. Everything in a package's `__all__` follows semver from beta 1 onwards;
  everything else is internal.

### Orient before you write

Almost every WebFluid mistake comes from assuming a feature is available. Nothing is on by default.
Four reads settle what your code may use:

| Read                        | Tells you                                                                          |
|-----------------------------|------------------------------------------------------------------------------------|
| `app_configs/*.ini`         | Which `EXT_*` batteries, `WF_*` surface features and `[additives]` are on, per app |
| `fluid/config.py`           | The app's config class: `APP_CONFIG`, `APP_FRONTEND`, binds, custom keys           |
| `main.py`                   | The `prepare_fluid()` factory: which routers, hooks and extensions are wired       |
| `additives/*/manifest.json` | Which feature modules exist, their ids, and what they require                      |

`app_configs/`, `additives/` and `migrate/` are **gitignored by the generated `.gitignore`**.
`git status` will not show your edits there — verify by reading files, not by diffing.

```bash
python -c "from webfluid import version; print(version())"
```

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
| [`surface/jinja.md`]({{ base }}surface/jinja.md)                                                                                                                                                                                                                    | Know which template file a name resolves to, and what autoescaping does           |
| [`additives/intro.md`]({{ base }}additives/intro.md)                                                                                                                                                                                                                | Build a feature module                                                            |
| [`additives/base.md`]({{ base }}additives/base.md)                                                                                                                                                                                                                  | Build or extend a base Additive                                                   |
| [`additives/contract.md`]({{ base }}additives/contract.md)                                                                                                                                                                                                          | Make two Additives talk without importing each other                              |
| [`utils/lifecycle.md`]({{ base }}utils/lifecycle.md)                                                                                                                                                                                                                | Run code at startup/shutdown                                                      |
| [`utils/runtime.md`]({{ base }}utils/runtime.md)                                                                                                                                                                                                                    | Reach the request from anywhere; hook the request flow                            |
| [`utils/logging.md`]({{ base }}utils/logging.md)                                                                                                                                                                                                                    | Log correctly                                                                     |
| [`cli/wf.md`]({{ base }}cli/wf.md)                                                                                                                                                                                                                                  | Know what commands exist                                                          |
| [`cli/create.md`]({{ base }}cli/create.md)                                                                                                                                                                                                                          | Scaffold a project, app or Additive                                               |
| [`cli/run.md`]({{ base }}cli/run.md)                                                                                                                                                                                                                                | Run an app, pick flags, understand debug mode                                     |
| [`cli/ocean.md`]({{ base }}cli/ocean.md)                                                                                                                                                                                                                            | Install or publish packages, expand bundles, pick a channel                       |
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
| "Why does my HTML render as text"     | [`surface/jinja.md`]({{ base }}surface/jinja.md) — autoescaping is on since {{ version }}                                                          |
{% endblock %}

{% block rules %}
## Rules that apply everywhere

These recur on almost every page. Internalise them once.

1. **Nothing is on by default.** Extensions are enabled by `EXT_*` switches in the app config,
   surface features by `WF_*` switches, Additives by id in `[additives]` **and** `WF_ADDITIVES = 1`.
   Code that uses `webfluid.core.ext.db` without `EXT_SQLALCHEMY = 1` fails at runtime, not at
   import.
2. **Reach batteries through the shared registry**, never by constructing them:
   `from webfluid.core.ext import db, babel, security, events, cache, mail, jwt, scheduler`.
   These are process-wide singletons created lazily on first attribute access.
3. **Use the app factory.** Name it `prepare_fluid()` in `main.py`. `wf migrate` looks for exactly
   that name, and module-level `Fluid(__name__)` breaks as soon as anything imports your modules
   without a config in the environment.
4. **Do not import `fluid` at module level inside handlers.** In a factory there is no module-level
   app. Use `FluidContext.current().fluid`, or for Additives a `from .. import additive` **inside**
   the handler function.
5. **`fluid.config` always contains every framework key.** Index it (`fluid.config["X"]`), do not
   `.get("X", <repeat of the default>)`. Only keys *you* invent need a `get` with a fallback.
6. **Register hooks while building the app, never from a request.** Startup/shutdown hooks,
   template loaders, sources and static prefixes are frozen once the server is up — and an event
   registered from inside a request pins that request into its consumer task forever.
7. **Every hook has an arity contract.** Startup/shutdown hooks, `before_request` and
   `context_processor` take **no** required arguments; `after_request` takes exactly one; event and
   query handlers take exactly one. A mismatch raises `TypeError` at registration time.
8. **Async first.** Every I/O API has an `a*` twin (`asend`, `agettext`, `aget`, `aencode`,
   `ahash`, `async_executor`). Inside `async def`, use the async one.
9. **Autoescaping is on** for `.html`, `.htm`, `.xml`, `.xhtml`, `.svg` and every `render_string`
   source. To emit HTML on purpose, wrap it in `markupsafe.Markup` or use `| safe`; never reach for
   either on a value that came from a request.
10. **Write no comments or docstrings if you are editing an existing WebFluid codebase** unless the
    project already has them — the generated code style is deliberately bare.
11. **Pin the version.** This is a beta; `__all__` is semver-stable, everything else is not. Do not
    import from undocumented module paths such as `webfluid.core.fluid.main`.

{{ rule("When you generate code for this framework, prefer the shape the scaffolder produces —
    fluid/api for JSON routers, fluid/app for HTML routes, fluid/models, fluid/schemas,
    fluid/services, fluid/events, fluid/utils. Every page in these docs assumes that layout, and
    wf create project produces it.") }}
{% endblock %}

{% block release %}
## Release state: {{ version }} ({{ stage }}, {{ date }})

The second stabilisation release over beta 1. It closes most of what beta 2 published as known
issues, and adds five security fixes an audit found afterwards. **One breaking change:
autoescaping.**

### Security fixes — assume the old behaviour is what an attacker still tries

| Was                                                                         | {{ version }}                                                                                     |
|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| Template values were interpolated verbatim (XSS anywhere input reached HTML) | `select_autoescape(("html", "htm", "xml", "xhtml", "svg"))` plus every `render_string` source     |
| The `vite_ns` cookie was joined onto `project_root` unchecked                | Only registered frontend namespaces are accepted; the resolved file must stay under the root      |
| A token's `kid` was interpolated into the cache key as-is                    | A `kid` that is not 32 lowercase hex characters raises `jwt.InvalidTokenError` before any lookup  |
| The rate limiter keyed on the client-supplied `X_Forwarded_For`              | Keys on `request.client`; use `PROXY_FIX` + `PROXY_TRUSTED_HOSTS` behind a proxy                  |
| `?redirect=` was replayed after OAuth as given                               | Only same-site absolute paths survive; an absolute URL, `//host` and `/\host` become `/`          |

The first one is the reachable-by-default one: with `vite_ns` empty, `GET /app_configs/<app>.ini`
returned the config including `SECRET_KEY`.

### Correctness fixes — the beta 2 docs are stale here

| The beta 2 docs say                                                      | {{ version }}                                                                                       |
|---------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `database_uris` rewrites the scheme word everywhere in a URI               | Only the leading scheme prefix is replaced                                                       |
| `mail.send()` talks plaintext against an implicit-TLS server               | The sync client opens `SMTP_SSL`; defaults are 587 + STARTTLS; setting both flags raises at boot |
| A refused SMTP greeting escapes as a raw `smtplib` error                   | Connect, STARTTLS and login happen inside the `try`, so both clients raise `FrameworkException`  |
| A detached `mail.send()` loses its exception in the worker thread          | The daemon thread logs the failure through the framework logger                                  |
| `app_configs/<name>.ini` is written in the locale encoding                 | Written as UTF-8, read through `utils.core.read_config` with a locale fallback                   |
| A non-numeric `sub` makes `resolve_bearer` answer 500                      | Rejected as an unusable token → the request falls through to 401                                 |
| An unknown `kid` raises a raw `TypeError`                                  | Raises `jwt.InvalidTokenError("Unknown key id.")`                                                |
| A CSRF token whose payload is not a dict answers 500                       | Answers `403 INVALID_CSRF`; `validate_token` catches `BadData`, not only `BadSignature`          |
| `url_for` is `None` outside a request                                      | Resolves through the application's route table; `external=True` prefixes `BASE_URL`              |
| A translation equal to its source is read as a miss                        | Hit and miss are reported separately through `findtext`; identity translations work              |
| `events.create_signal` at import time raises `RuntimeError`                | Queued and wired up from a startup hook                                                          |
| A malformed websocket frame tears the connection down                      | Answered as a named error; the socket stays usable; `WebSocketDisconnect` is contained           |
| A disconnect leaves its subscriptions in `SocketManager`                   | `leave()` drops them; `unsubscribe` checks the **caller's** subscription                         |
| Database engines are never disposed                                        | `SQLAlchemy.dispose()` runs as a shutdown hook and closes every pool                             |

Two of those rules survive their fix and are still worth following: **put the user's primary key in
`sub`** (a non-numeric subject is now a 401 rather than a 500, but still never authenticates), and
**use symbolic `SCREAMING_SNAKE` translation keys** (they were always the right shape).

### Added

- **`FluidContext` on the events socket.** `/ws/events` handlers run inside a context whose
  `request` is the `WebSocket`. `security.user_service.current_user_fn`, the Babel locale resolution
  and `url_for` all work against it, because `WebSocket` and `Request` are both Starlette
  `HTTPConnection`s. **Resolve the caller server-side; never take a principal id from the payload of
  a public query.**
- **`EmailVerifiedGate`** between the default gate and `require_2fa`. Every guard past
  `require_user` answers `401 EMAIL_NOT_VERIFIED` for an unset or unverified `email`. Bare
  `require_user` is unaffected — that is what keeps a verification flow reachable. Predicate:
  `UserService.email_verified(user)` / `requirements.email_verified`.
- **`wf ocean install --bundle/-b`, `--pre/-p`, `--prefer-stable/-ps`.** `-b` expands a bundle id to
  the packages it contains (leading zeros optional; duplicates installed once; an explicit
  `id==version` beats the bundle's unpinned entry). `-p` takes the newest prerelease of any channel;
  `-ps` takes the newest stable and falls back to a prerelease. `wf ocean search` prints the
  zero-padded bundle id as its first column.
- **`utils.core.read_config`** — reads an ini file as UTF-8, falls back to the locale encoding,
  returns an empty parser for a missing file. Also **`utils.core.in_running_loop()`**.
- **`render_as_batch` in both generated `env.py` templates** when the dialect is SQLite, so column
  renames and type changes work on the database you develop against. `env.py` is generated once —
  an existing migration environment needs the two lines copied in by hand.
- **`webfluid/.agents/skills/webfluid`** ships inside the distribution: `SKILL.md` plus six
  reference files. If you are working in a repository with `webfluid` installed, that is the local
  copy of this material; these docs are the exhaustive version.

### Changed

- **`MAIL_USE_TLS` defaults to `False` and `MAIL_USE_STARTTLS` to `True`**, matching the
  `MAIL_PORT` default of 587. Setting both raises `FrameworkException` at startup. For an
  implicit-TLS server set `MAIL_PORT = 465` **and** `MAIL_USE_TLS = True` explicitly.
- **`MergedTranslations` gained `findtext` / `nfindtext` / `pfindtext` / `npfindtext`** and their
  four `a`-prefixed pendants, answering `None` on a miss. The eight `gettext` methods are unchanged.
- **`SocketManager(fluid, events, queries)`** — the application is the first argument now.
- **`Sources.rendered` is a `Markup`**, and `Markup("")` before the freeze.
- **`Vite._instances` → `Vite._namespaces`** (a set); `asset_catch(project_root, namespaces)`.

### Performance

Template rendering costs about 12 % more with autoescaping on (123 µs → 138 µs on an
interpolation-dense page), well inside the 300 µs budget; the request benchmark is unchanged at
~43 µs. Against it: `SocketManager` no longer leaks a subscription entry per disconnect, and
database pools are closed at shutdown rather than held to process exit.
{% endblock %}

{% block bugs %}
## Known issues in {{ version }}

Read this section before generating code. Each of these is a live defect in the shipped package,
not a documentation gap. They are repeated in context on the relevant pages.

### Runtime and lifecycle

- **Hooks do not run under an external ASGI server.** Startup and shutdown hooks run from
  `fluid.mix()`, not through the ASGI lifespan protocol. `uvicorn main:fluid` or `gunicorn` skips
  table creation, the scheduler, Additive registration, the frozen loader stack and the static
  mounts. **Run apps through `wf run`;** your container entrypoint must be `wf run <app>`.
- **`WF_PROCESSING` buffers every response.** The request middleware streams straight through only
  when *no* `after_request` processor is registered, and `WF_PROCESSING` registers one
  unconditionally (the error-page swap). So any app rendering HTML buffers every response body, even
  though that processor reads nothing but the status code. Streaming responses are still detected
  and released unbuffered.
- **The styled error page discards the response it replaces.** For 400, 401, 403, 404, 405, 429,
  500, 502 and 503 with `Accept: text/html`, the processor builds a **new** `HTMLResponse`, so
  `Set-Cookie`, `WWW-Authenticate` and `Retry-After` set by your handler are lost. Session cookies
  survive (the session middleware sits outside). Return a `JSONResponse`, or a status outside that
  table, when headers matter.
- **Streaming responses skip `after_request` processors.** Detected the moment the app announces
  `more_body`. A buffered response also keeps the app's `Content-Length` — return a **new** response
  when you change the body.
- **`additive.after_request` does not receive a `Response`.** It runs inside the router's endpoint
  wrapper, before FastAPI serialises anything, so it receives whatever the handler returned.
  `fluid.after_request` *does* receive a real `Response`.
- **`additive.before_request` / `after_request` do not run for `additive.ws` routes.** The Additive
  request lifecycle is installed as HTTP middleware on `additive.api` and `additive.app` only. Check
  the connection inside the websocket endpoint.
- **`RATELIMIT_DEFAULT` never applies.** slowapi evaluates application-wide defaults only from its
  own middleware, which the framework does not install. An undecorated route is never checked, and
  `@fluid.limit(...)` replaces the defaults rather than adding to them. **Put the limit on the
  route.**

### Events

- **Registering an event from inside a request handler pins that request.** `create_loop` starts the
  consumer with `asyncio.create_task`, which copies the calling context, so every later handler on
  that channel sees a dead `Request` — and the wrapper then re-raises instead of logging, so a
  failing handler vanishes into the gather. **Register from a startup hook or `before_enable`.**
- **A half-registered event survives its own error.** Registering a *new* event off-loop *after*
  startup raises `FrameworkException`, but the broadcaster is already in the registry, so
  `has_event(name)` is `True` and `trigger()` succeeds into a channel nothing drains. Do not catch
  that exception.
- **Delivery is best-effort.** A bounded per-listener buffer sized by `EVENTS_EVENT_QUEUE_SIZE`
  (default 5); a slow consumer loses its oldest events, logged as a warning. In-process only, no
  persistence, no replay. Use the database plus a query for anything that must not be lost.

### i18n

- **`/ws/i18n`'s `translate` always answers in `BABEL_DEFAULT_LOCALE`.** That socket did not get a
  `FluidContext`, so `get_locale()` has nothing to read and never sees the connection's `?lang=`,
  `lang` cookie or `Accept-Language`. Its sibling `cache` request resolves the locale correctly, so
  the two halves disagree. **Use the cache-backed client API (`_`, `_n`, `_p`, `_np`), not
  `live.*`.**
- **`live._p` and `live._np` send their arguments in the wrong order.** The client sends
  `[string, context]` where the server reads `apgettext(context, string)`, and
  `[singular, plural, num, context]` against `anpgettext(context, singular, plural, num)`.
- **`ngettext` raises without `EXT_BABEL`.** The no-op fallback interpolates with `n`, the real
  implementation with `num`, so `'%(num)d items'` renders with the battery on and raises
  `KeyError: 'num'` — a 500 — with it off. Write the count in yourself if a template must work in
  both configurations.
- **Uncached translations block.** A key explicitly opted out of the cache is read through a
  synchronous session on the `gettext` path. `agettext` is the non-blocking alternative; the Jinja
  callables stay synchronous on purpose.
- **`?lang=` and the `lang` cookie accept any locale Babel can parse**, not only
  `BABEL_SUPPORTED_LOCALES` — only the `Accept-Language` path is restricted. An unsupported locale
  gets source strings, and `Domain` keeps one loaded catalog per locale asked for. Bounded, but a
  client can make an app hold a few hundred empty catalogs.

### Auth and tokens

- **A bearer grant walks past the email-verified gate.** `requirement_or_grant` /
  `requirement_and_grant` catch the session chain's `HTTPException` — `401 EMAIL_NOT_VERIFIED`
  included — and fall back to `resolve_bearer`, which checks only the token's grant list. Mint grant
  tokens only for principals you have already verified.
- **JWT signing keys live in the cache**, and a rotation runs as a startup hook. With
  `CACHE_TYPE = legacy` (in-process) every restart mints a new key and forgets the old ones. **Run
  JWT against Redis.**

### Data and tooling

- **`wf migrate init` picks its template from `SQLALCHEMY_BINDS` in the config, at init time.**
  Binds attached at runtime via `Model.set_bind` — which is how `SECURITY_MODELS_DB_BIND`,
  `BABEL_DATABASE_BIND` and most Additives do it — are invisible to it. Declare them in
  `SQLALCHEMY_BINDS` before running `init`, or install the `multi_db` template by hand.
- **The Vite catch-all serves the frontend workspace, not `dist`.** `asset_catch` resolves under
  `<vite_ns>/<path>` and `<vite_ns>/public/<path>`, and the framework sets the `vite_ns` cookie
  itself, so in production `GET /package.json` or `GET /src/main.ts` returns the workspace file.
  Keep nothing secret inside a frontend workspace.
- **App configs written before {{ version }} on a non-UTF-8 console** read back correctly on the
  machine that wrote them, but a non-ASCII value in one cannot be recovered elsewhere. Rewrite them
  once, or keep values ASCII and use `*_FILE`.
- **HMR rides on a proxied websocket that can die.** A Vite restart is the usual trigger; the
  affected frontend then silently stops picking up changes. A browser refresh re-establishes it — no
  need to restart `wf run`.

{{ warning("Treat this list as part of the API. Generating code that trips one of these produces a
    program that looks right and behaves wrong.") }}
{% endblock %}

{% block breaks %}
## Breaking changes in {{ version }}

| Before                                       | Now                                                          | Action                                                                                             |
|----------------------------------------------|--------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| Templates interpolated values verbatim       | Autoescape on for html/htm/xml/xhtml/svg and `render_string` | Wrap deliberate HTML in `Markup` or add `\| safe`. Never on request data. `\| e` still works        |
| `MAIL_USE_TLS = True`, `MAIL_USE_STARTTLS = False` | Swapped, matching port 587; both set raises at startup | For implicit TLS set `MAIL_PORT = 465` **and** `MAIL_USE_TLS = True`                                |
| `SocketManager(events, queries)`             | `SocketManager(fluid, events, queries)`                      | Only affects code that constructed one by hand                                                     |
| `Sources.rendered` was a `str`               | A `Markup` (`Markup("")` before the freeze)                  | Join framework source fragments with `Markup`, not `str` — a `str` separator gives back a `str`     |
| `Vite._instances` (counter)                  | `Vite._namespaces` (set); `asset_catch(root, namespaces)`    | Internal; only affects code that read the counter                                                  |

### The autoescape migration, concretely

**A template of yours that deliberately interpolates an HTML string now shows the tags.** Two
correct moves:

```python
from markupsafe import Markup

badge = Markup(f'<span class="badge">{count}</span>')   # you built it, you vouch for it
```

```html
{{ '{{' }} trusted_html | safe {{ '}}' }}
```

Never do either to a value that came from a request. Everything the framework injects — page
sources, `rendered_sources`, theme links, `frontend()`, `wf_tailwind` — is already `Markup`. A `str`
you build yourself is not, and joining `Markup` pieces with a plain `str` separator gives a plain
`str` back, which will then be escaped.

Templates with a suffix outside the escaped set — `.txt`, `.md`, `.json` — are not escaped, so
plain-text mail bodies render as written.

## About this Markdown edition

- Same URL as the HTML page, plus `.md`. The overview is `{{ base }}.md`.
- The HTML page declares this file via `<link rel="alternate" type="text/markdown">`, and this
  file's response carries a `Link: …; rel="canonical"` header pointing back at the HTML.
- `Accept: text/markdown` on any documentation URL returns this variant without the suffix.
- Index of every page: `/llms.txt`. Whole corpus in one document: `/llms-full.txt`.
- Older versions (`1.0.0a1`, `1.0.0a2`, `1.0.0b1`) are HTML only. The Markdown mirror starts at
  `1.0.0b2`; `/v/1.0.0b2/<page>.md` still resolves if you need to compare.
{% endblock %}
