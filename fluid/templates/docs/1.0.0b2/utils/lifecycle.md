{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Lifecycle{% endblock %}
{% block doc_section %}Framework utility{% endblock %}

{% block summary %}
`fluid.mix()` owns the process: it opens the logging session, runs your startup hooks, serves, and
on a stop signal runs your shutdown hooks and exits. This page is the exact sequence, the arity and
ordering rules for hooks, and the one thing about it that will bite you in production.
{% endblock %}

{% block body %}
## What `mix()` does

```python
def run(self): asyncio.run(self._start())

async def _start(self):
    log_factory.start_session()
    await self._lifecycle.run_startup()

    serve = asyncio.create_task(self._run_server())
    stop = asyncio.create_task(self._shutdown_flag.wait())
    try:
        await asyncio.wait((serve, stop), return_when=FIRST_COMPLETED)
        stop.cancel()
        if not serve.done() and self._server:
            self._server.should_exit = True
        await serve
    finally:
        await self._lifecycle.run_shutdown()
        log_factory.log("Server stopped.")
```

In order:

1. **Logging session** — handlers and level are installed from `LOG_LEVEL`.
2. **Startup phase** — every registered hook, in registration order, each wrapped in `safe_execute`
   (exceptions are logged, not raised) with a progress bar.
3. **Serve** — uvicorn on `SERVER_HOST:SERVER_PORT`, with its own signal handlers disabled.
4. **Wait** — on the shutdown flag **or** the server task, whichever finishes first.
5. **Shutdown phase** — in a `finally`, so it runs on every path, in **reverse** registration order.

Because the wait covers the server task too, a server that dies on its own — a bound port, uvicorn
calling `sys.exit(1)` — is re-raised where you can read it and the shutdown hooks still run. In beta
1 that case hung forever.

{{ bug("This whole sequence lives in mix(), not in the ASGI lifespan protocol. An external ASGI
    server that imports your app and serves it directly — uvicorn main:fluid, gunicorn — never runs
    your startup or shutdown hooks: no tables, no scheduler, no Additives, no frozen loader stack, no
    static mounts. Run WebFluid apps through wf run.") }}

## Hooks

```python
app.startup_hook(fn)         # or @app.startup_hook
app.shutdown_hook(fn)        # or @app.shutdown_hook
```

| Property            | Startup                     | Shutdown                       |
|---------------------|-----------------------------|--------------------------------|
| Required arguments  | **0**                       | **0**                          |
| Sync or async       | both                        | both                           |
| Order               | registration order          | **reverse** registration order |
| Exceptions          | logged, execution continues | logged, execution continues    |
| Registration window | before the server starts    | before the server stops        |

`Phase.add` calls `required_arg_count(fn)` and raises
`TypeError("Startup hooks must not receive non optional arguments.")` on a mismatch — at
registration time, so the error points at the right line.

After the phase has run it is **sealed**: adding a hook raises
`RuntimeError("Startup hooks cannot be added after the server was started.")`

```python
from webfluid import Fluid
from webfluid.core.ext import db


def prepare_fluid() -> Fluid:
    app = Fluid(__name__)

    from fluid.app import app_router
    from fluid.api import api_router
    app.include_router(app_router)
    app.include_router(api_router)

    from fluid.events.models import register as register_events
    app.startup_hook(register_events)

    @app.startup_hook
    async def create_tables():
        bind = db.get_bind_for_model(db.Model)
        db.Model.metadata.create_all(bind.sync_engine)

    @app.shutdown_hook
    def goodbye():
        from webfluid.utils.logging import factory as log
        log.log("The app is cooling down.")

    return app


if __name__ == "__main__":
    prepare_fluid().mix()
```

{{ rule("Register hooks while building the app, in the factory. Never from inside a request handler
    — the phase is sealed by then and it raises.") }}

{{ rule("Hooks run sequentially, and a slow hook holds up every hook after it and delays the first
    request. Keep them focused: register things, warm one cache, create tables. Put long-running work
    behind the scheduler or an event.") }}

## What the framework itself registers

Your hooks join the same queue these use, which is why `wf run` shows a progress bar sized to the
total:

| Phase    | Hook                                                                                                                                 | Condition                     |
|----------|--------------------------------------------------------------------------------------------------------------------------------------|-------------------------------|
| startup  | `register_additives(fluid)`                                                                                                          | `WF_ADDITIVES`                |
| startup  | `scheduler.start`                                                                                                                    | `EXT_SCHEDULING`              |
| startup  | Babel translation flush                                                                                                              | `EXT_BABEL`                   |
| startup  | JWT secret rotation                                                                                                                  | `EXT_JWT`                     |
| startup  | `fluid._prepare` — freeze static prefixes, mount static, freeze sources, add proxy-headers middleware, freeze the Jinja loader stack | always                        |
| startup  | `frontend.cover_fluid`                                                                                                               | `APP_FRONTEND` is not `None`  |
| startup  | Tailwind compile                                                                                                                     | `WF_TAILWIND`                 |
| startup  | Vite dev server / production build + mount                                                                                           | `APP_FRONTEND.type == "vite"` |
| shutdown | `close_proxy_client`                                                                                                                 | always                        |
| shutdown | Vite dev server stop                                                                                                                 | debug + vite                  |

{{ warning("Order within the startup phase matters and is not fully under your control: _prepare
    freezes the sources, the static prefixes and the loader stack, and it is registered during
    Fluid.__init__ — so a hook you add in the factory runs after it. Do not call add_source,
    add_template_loader or static_prefixes.add from a hook; call them directly during app
    assembly.") }}

## Graceful shutdown

The runtime installs handlers for `SIGINT` and `SIGTERM` (plus `SIGBREAK` on Windows) from a startup
hook. A `Ctrl+C` or a container stop sets the shutdown flag rather than killing the process:

```text
signal -> flag set -> uvicorn should_exit -> in-flight request finishes
       -> shutdown hooks (reverse order) -> "Server stopped."
```

Under `wf run` there is a second layer: the CLI process forwards `SIGINT`/`SIGTERM` to the child and
gives it 10 seconds before killing it.

{{ rule("Put anything that must survive a restart into a shutdown hook: flushing a buffer, closing a
    third-party client, deregistering from a service discovery. But keep it short — the 10 second
    grace period is the budget for the whole phase.") }}

## Startup work that is not a hook

| Do this at                             | For                                                                          |
|----------------------------------------|------------------------------------------------------------------------------|
| Module import time (`fluid/config.py`) | Config classes                                                               |
| Factory body, before `return app`      | Routers, sources, template loaders, extensions, `scheduler.add_job`          |
| `startup_hook`                         | Events and queries, table creation, cache warming, anything needing the loop |
| `additive.before_enable`               | An Additive's routes, contracts and jobs                                     |
| `shutdown_hook`                        | Flushing and closing                                                         |

## Next

- [`utils/runtime.md`]({{ base }}utils/runtime.md) — what happens between boot and shutdown.
- [`cli/run.md`]({{ base }}cli/run.md) — the process that drives all of this.
- [`ext/events.md`]({{ base }}ext/events.md) — the battery whose registration must be a hook.
{% endblock %}
