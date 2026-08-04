{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}wf run{% endblock %}
{% block doc_section %}CLI{% endblock %}

{% block summary %}
`wf run <app>` reads `app_configs/<app>.ini` into an environment, launches `main.py` as a child
process with it, streams the child's stdout to your console and its stderr into a timestamped log
file. It is the only supported way to run a WebFluid app.
{% endblock %}

{% block body %}
## Signature

```bash
wf run <app> [-h HOST] [-p PORT] [-l LEVEL] [-d] [-i]
```

| Flag | Long            | Default     | Effect                                                   |
|------|-----------------|-------------|----------------------------------------------------------|
| `-h` | `--host`        | `127.0.0.1` | Bind host → `SERVER_HOST`                                |
| `-p` | `--port`        | `8000`      | Bind port → `SERVER_PORT`                                |
| `-l` | `--loglevel`    | `info`      | → `LOG_LEVEL` (ignored under `-d`, which forces `debug`) |
| `-d` | `--debug`       | off         | Debug mode                                               |
| `-i` | `--interactive` | off         | Control menu instead of a plain stream                   |

Preconditions, each exiting 1 with a red message:

- `app_configs/<app>.ini` must exist (it suggests `wf create app <app>`),
- `main.py` must exist in the current directory,
- `-d` with `-p 5173` is refused — that port belongs to the Vite dev server.

## What it arranges

```text
read app_configs/<app>.ini
  ├─ flatten every section into env      (skip [dev] unless -d)
  ├─ resolve every *_FILE key from disk
  └─ count truthy [additives] -> ENABLED_ADDITIVES

inject APP_NAME, SERVER_HOST, SERVER_PORT, IN_EXECUTION=1,
       PYTHONUNBUFFERED=1, PYTHONIOENCODING=<console>:backslashreplace,
       COLUMNS, LINES, LOG_LEVEL (+ DEBUG_MODE=1 under -d)

Popen([sys.executable, "main.py"], stdout=PIPE, stderr=<log file>, env=env)
```

Two details that matter:

- **`COLUMNS` / `LINES` are passed through**, which is why a progress bar inside the app renders at
  the right width and redraws in place instead of scrolling a line per frame.
- **`PYTHONIOENCODING` carries `backslashreplace`**, so redirecting output to a file degrades bars
  to ASCII rather than failing to encode.

The child's stderr goes straight to `logs/<app>/<timestamp>.log`; its stdout is read continuously
whether or not you are watching, so muting the stream never blocks the app on a full pipe.

## Debug mode

`-d` sets `DEBUG_MODE=1`, which the framework reads once at import of
`webfluid.core.constants`. It changes:

|                                           | Normal                                          | `-d`                                                                   |
|-------------------------------------------|-------------------------------------------------|------------------------------------------------------------------------|
| `SESSION_COOKIE_SECURE`                   | `True`                                          | `False` — sessions survive plain http                                  |
| `STATIC_MAX_AGE`                          | `31536000`                                      | `0`, plus a `?t=` cache-buster on rendered asset URLs                  |
| Jinja `auto_reload`                       | off                                             | on                                                                     |
| 500 page                                  | `errors/500.html`, JSON body = status text only | `errors/debug/500.html`, JSON body carries message, type and traceback |
| Vite                                      | `dist/` mounted as static                       | Dev server started and proxied under `/vite-dev`, HMR live             |
| `WF_CHECK_FRONTEND` / `WF_BUILD_FRONTEND` | Read                                            | **Not read**                                                           |
| `[dev]` config section                    | Skipped                                         | Applied                                                                |
| `LOG_LEVEL`                               | `--loglevel`                                    | forced `debug`                                                         |
| `DEV_AUTO_INSTALL`                        | Ignored                                         | Runs `Additive.install()` on every registration when set               |

{{ rule("Never run a production deployment with -d. It disables the secure session cookie, disables
    static caching, and puts exception messages and tracebacks into API responses.") }}

## Interactive mode

`-i` asks for host, port and debug up front if you did not pass them, then drops into a menu:

| Option        | Effect                                                                   |
|---------------|--------------------------------------------------------------------------|
| Restart       | Stop then start                                                          |
| Stop          | `CTRL_BREAK_EVENT` on Windows, `SIGTERM` otherwise; 10s grace, then kill |
| Start         | Start if not running                                                     |
| Join log      | Live stream; leave with `ESC`                                            |
| Clear logs    | Prune `logs/<app>/`, always keeping the current run's file               |
| Clear console |                                                                          |
| Exit          |                                                                          |

Arrow and function keys are consumed rather than decoded — Windows reports those as a two-byte
sequence starting with a null or `0xE0` byte, and decoding the first byte as UTF-8 used to kill the
CLI with `UnicodeDecodeError`. Fixed in this release.

When you stop the app the reader is drained before the closing message, so shutdown-hook output
prints where it happened rather than after the goodbye.

## Signals

A plain (non-interactive) run installs handlers for `SIGINT` and `SIGTERM` and forwards them, so a
clean `Ctrl+C` triggers the graceful sequence from
[`utils/lifecycle.md`]({{ base }}utils/lifecycle.md): in-flight request finishes, shutdown hooks run,
process exits. A signal is no longer the only way out either — if the server itself dies (usually a
bound port), the failure is raised where you can read it and the hooks still run.

## Deployment

{{ bug("Startup and shutdown hooks run from fluid.mix(), not through the ASGI lifespan protocol. An
    external ASGI server that imports your app — uvicorn main:fluid, gunicorn -k uvicorn.workers... —
    never runs them: no tables, no scheduler, no Additives, no frozen loader stack, no static mounts.
    Your container entrypoint must be wf run <app>.") }}

A workable container shape:

```dockerfile
# build assets at image build time
RUN wf node npm install && wf node npm run build --workspaces

# and turn the boot-time build off
ENV WF_CHECK_FRONTEND=0 WF_BUILD_FRONTEND=0

CMD ["wf", "run", "prod", "-h", "0.0.0.0", "-p", "8000"]
```

Bind to `0.0.0.0` inside a container — the default `127.0.0.1` is unreachable from outside it. Put
secrets behind `*_FILE` keys pointing at mounted secret files.

{{ rule("One process per app. wf run has no worker model and the framework's event bus, legacy cache
    and scheduler are all in-process. Scale by running several containers behind a proxy, and
    remember: separate event buses, separate legacy caches, and the scheduler firing once per
    process. Use Redis for the cache, and give the scheduler its own single-instance app config.") }}

## Next

- [`cli/ocean.md`]({{ base }}cli/ocean.md) — packages.
- [`utils/lifecycle.md`]({{ base }}utils/lifecycle.md) — what happens after the process starts.
- [`config/app-config.md`]({{ base }}config/app-config.md) — the file this command reads.
{% endblock %}
