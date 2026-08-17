{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Runtime{% endblock %}
{% block doc_section %}Framework utility{% endblock %}

{% block summary %}
Every request is wrapped in a `FluidContext` — a contextvar-backed object carrying the app, the
request and a per-request scratchpad. It is what makes `render`, `url_for` and the locale resolution
"just know" about the current request without threading arguments through every call.
{% endblock %}

{% block body %}
## `FluidContext`

```python
from webfluid.core.context import FluidContext

ctx = FluidContext.current()        # the context, or RuntimeError
ctx = FluidContext.try_current()    # the context, or None

ctx.fluid                           # the Fluid app
ctx.request                         # the starlette Request, or None
```

| Accessor        | No context                                       | Use it when                                                |
|-----------------|--------------------------------------------------|------------------------------------------------------------|
| `current()`     | raises `RuntimeError("No active FluidContext.")` | A request is genuinely required                            |
| `try_current()` | returns `None`                                   | You have a sensible fallback — jobs, hooks, shared helpers |

{{ rule("A FluidContext is ALWAYS truthy, even when it carries no data. Test the result of
    try_current() against None, never for truthiness. len(ctx) still reports the size of its
    storage — in beta 1 __len__ made a plain request context falsy, which is what silently broke
    get_locale, Themes.get and country_from_request for every request.") }}

```python
ctx = FluidContext.try_current()
if ctx is not None:          # correct
    ...

if ctx:                      # also correct now, but say what you mean
    ...
```

### The scratchpad

The context behaves like a dict for the duration of the request:

```python
ctx["key"] = value
ctx["key"]                   # KeyError if absent
ctx.get("key", default)
ctx.pop("key", default)
"key" in ctx
ctx.keys() / ctx.values() / ctx.items()
```

Event and query handlers get `event` and `event_data` in that storage.

### `cached_or` — memoise per request

```python
FluidContext.cached_or(key, factory)
```

Calls `factory()` at most once per request and caches the result. With **no** context it simply
calls the factory — so the same helper works in a job:

```python
from webfluid.core.context import FluidContext


def pricing_tier():
    return FluidContext.cached_or("pricing_tier", _resolve_tier)
```

This is how the active locale and timezone are parsed once per request instead of once per
translated string.

{{ rule("Reach for cached_or whenever a value is expensive and stable within a request — the current
    user's permissions, a tenant lookup, a feature-flag snapshot. Namespace the key so two callers
    cannot collide.") }}

### `BaseContext`

`FluidContext` is one of several contextvar-backed contexts sharing a base:

| Context                      | Carries                     |
|------------------------------|-----------------------------|
| `FluidContext`               | app + request + storage     |
| `Executor` / `AsyncExecutor` | the active database session |
| `DomainContext`              | the active Babel domain     |
| `SelectorContext`            | forced locale/timezone      |
| `ClientContext`              | an open SMTP connection     |
| `_LogContext`                | which logger to write to    |

All of them get `current()`, `try_current()` and:

```python
with FluidContext.outer(depth=1) as parent:
    ...      # temporarily re-enter the enclosing context, or None if there is none
```

They are re-entrant: entering the same instance twice stacks tokens and exiting pops them.

## Request hooks

Three decorators, all running inside the context:

```python
# fluid/runtime.py
from webfluid.core.context import FluidContext


def register(app):

    @app.before_request
    def require_session():
        ctx = FluidContext.current()
        if ctx.request.url.path.startswith("/admin"):
            if not ctx.request.session.get("user"):
                from fastapi.responses import RedirectResponse
                return RedirectResponse("/login")

    @app.after_request
    async def add_header(response):
        response.headers["X-Powered-By"] = "WebFluid"
        return response

    @app.context_processor
    def globals_():
        return {"brand": "My Portal"}
```

| Hook                | Required args      | Returns                                              | Effect                          |
|---------------------|--------------------|------------------------------------------------------|---------------------------------|
| `before_request`    | **0**              | `None` to continue, or a `Response` to short-circuit | Runs before routing             |
| `after_request`     | **1** (`response`) | a `Response`                                         | Runs after the app produced one |
| `context_processor` | **0**              | a dict                                               | Merged into every `render`      |

Context processors are merged as `result | ctx` — **explicit `render(**ctx)` values win** over
processor values.

The processing layer uses exactly these: a context processor for the shared template variables, a
before-request logger, an after-request hook that swaps in the styled error pages.

### The cost of `after_request`

```text
no after_request processors -> the response streams straight through
one or more                 -> the whole body is buffered so processors can see it
```

{{ bug("Two limits of that buffering. (1) A streaming response is detected the moment the app
    announces more_body and released unbuffered — it never reaches your after_request processors at
    all. (2) A buffered response carries the headers the app produced, Content-Length among them, so
    a processor that changes the body must return a NEW response rather than mutating the one it was
    handed.") }}

{{ rule("Register an after_request processor only when you need one, and prefer one that only touches
    headers. A single registered processor turns every response in the app into a buffered one.") }}

{{ bug("WF_PROCESSING registers one unconditionally — the error-page swap — so an app that serves
    HTML never takes the streaming path at all, even though that processor reads nothing but the
    status code. Budget for buffering; there is no configuration that avoids it short of turning
    WF_PROCESSING off.") }}

{{ bug("That error-page processor builds a NEW HTMLResponse for 400, 401, 403, 404, 405, 429, 500,
    502 and 503 when the client accepts text/html, discarding the response it replaces. Headers your
    handler set on it — Set-Cookie, WWW-Authenticate, Retry-After — are lost. Session cookies survive
    because the session middleware sits outside. Return a JSONResponse, or a status outside that
    table, when the headers matter.") }}

Static paths are exempt: the request middleware passes anything matching `static_prefixes`
(`/static`, `/fluid/static`, `/frontend`, `/vite-dev`, plus every Additive's) straight through
without building a context at all.

## Themes at runtime

```python
from fastapi import Request
from webfluid.core.context import FluidContext


async def pick_theme(request: Request, name: str):
    ctx = FluidContext.current()
    ctx.fluid.set_theme(request, name)      # stored in the session
    return await ctx.fluid.render("index.html")
```

Resolution: `request.session["theme"]` → `GLOBAL_THEME` → the framework theme. `set_theme` raises
for an unregistered name, so a typo is an error rather than a page that keeps the old style. All
three calls require `WF_THEMES`.

The client-side light/dark helper `window.wf.switchTheme()` is independent of this registry.

## Reverse URLs

| Call                                     | Needs a request | Returns                                               |
|------------------------------------------|-----------------|-------------------------------------------------------|
| `url_for(name, **params)` (Jinja global) | no              | path; absolute with `external=True`                   |
| `fluid.url_path_for(name, **params)`     | no              | path                                                  |
| `POST /url-for`                          | yes             | `{"url": ...}`; unknown name → `404 UNKNOWN_ENDPOINT` |

`url_path_for` maintains a name → routes index that rebuilds itself whenever the route count
changes, and tries each candidate until one matches. It raises `NoMatchFound` when none does.

Since `1.0.0b3` the `url_for` Jinja global works off-request: with a request in context it resolves
through the request, without one it falls back to `fluid.url_path_for` and `external=True` prefixes
`BASE_URL`. That is what makes rendering a mail template from a job or a startup hook work — before,
it handed back `None` and the template failed with `NoneType is not callable`.

{{ rule("Set BASE_URL. It defaults to http://localhost:8000, and off-request that default is what
    every external URL you generate will carry.") }}

The Additive `url_for` behaves identically, after running the endpoint name through
`additive.unique_name()`.

## Proxies

```python
PROXY_FIX = True
PROXY_TRUSTED_HOSTS = "10.0.0.0/8"   # or "*", or a comma-separated list
```

With `PROXY_FIX` on, uvicorn's `ProxyHeadersMiddleware` is added in the `_prepare` startup hook, so
`request.client.host` and the scheme survive a reverse proxy. There is no wrapper object to hand
your server — it is part of the middleware stack.

{{ rule("Set PROXY_TRUSTED_HOSTS to the actual proxy, not \"*\", unless nothing but your proxy can
    reach the app. A trusted \"*\" means any client can claim any IP through X-Forwarded-For, which
    defeats the rate limiter and every IP-based decision you make.") }}

This middleware is the **only** thing that lets a forwarded header change `request.client`. Nothing
downstream — the limiter included — reads one on its own.

The framework also ships general-purpose proxy helpers (`get_proxy`, `get_websocket_proxy`,
`add_proxy`, `close_proxy_client`) — the same ones HMR rides on. The HTTP one drops the upstream's
hop-by-hop and encoding headers and recomputes `Content-Length` for the body it forwards, while
repeated headers such as `Set-Cookie` survive as separate lines. The websocket one awaits its
cancelled pump tasks and retrieves their exceptions, so an upstream that drops no longer surfaces as
`Task exception was never retrieved`.

## Rate limiting

```python
@app.get("/expensive")
@app.limit("5/minute")
async def expensive(request: Request):
    return {"ok": True}
```

The decorated function **must** take a `request: Request` parameter — slowapi reads the key from it.
A limit hit answers 429 with the usual rate-limit headers.

The key is `slowapi.util.get_remote_address`, i.e. `request.client`. It **never** reads a forwarded
header on its own, so a client cannot mint itself a fresh bucket by inventing one. Behind a reverse
proxy that means every request keys on the *proxy's* address until you turn `PROXY_FIX` on — set it,
and the per-client keys come back.

{{ warning("Before 1.0.0b3 the key was get_ipaddr, which preferred an unverified X_Forwarded_For
    request header: a client could send a different value on every request and never hit a limit,
    while behind a real proxy every client landed in one bucket because that spelling is not the one
    proxies send. If you were compensating for either, remove the workaround.") }}

{{ bug("RATELIMIT_DEFAULT never applies. slowapi evaluates application-wide defaults only from its
    own middleware, which the framework does not install — so an undecorated route is not limited at
    all, and a decorated one replaces the defaults rather than stacking on them. Put the limit you
    want on every route that needs one.") }}

With `RATELIMIT_ENABLED = False`, `fluid.limit` becomes a no-op decorator, so the same code runs
unlimited without edits.

## Next

- [`utils/logging.md`]({{ base }}utils/logging.md) — the log factory.
- [`cli/wf.md`]({{ base }}cli/wf.md) — the CLI section.
- [`ref/core.md`]({{ base }}ref/core.md) — the context API in reference form.
{% endblock %}
