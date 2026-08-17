{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}App Configs{% endblock %}
{% block doc_section %}Configuration{% endblock %}

{% block summary %}
`app_configs/<name>.ini` is the CLI's entry point into a project. It replaces `.env`, selects which
app to run, and carries the switches that decide which parts of the framework boot at all. It is
read by `wf run` and by the `wf migrate` environment; it is **never** read by the running app
directly — the CLI turns it into environment variables before launching `main.py`.
{% endblock %}

{% block body %}
## Mechanics

`wf run <name>` looks for `app_configs/<name>.ini`, parses it with `utils.core.read_config`
(a `configparser` with `optionxform = str`, so keys keep their case; read as UTF-8 with a
locale-encoding fallback for files written before `1.0.0b3`), flattens **every section** into one environment
mapping and spawns `python main.py` with it. Section names are pure organisation — the framework
never looks at them, with exactly one exception (`[dev]`, below).

Because of the flattening, two sections declaring the same key silently collide. Keep keys unique
across the file.

```ini
; app_configs/app.ini
[general]
SECRET_KEY = supersecret

[extensions]
EXT_SCHEDULING = 0
EXT_SQLALCHEMY = 1
EXT_BABEL = 1
EXT_SECURITY = 0
EXT_EVENTS = 1
EXT_CACHE = 0
EXT_MAIL = 1
EXT_JWT = 0

[features]
WF_THEMES = 1
WF_TAILWIND = 1
WF_CHECK_FRONTEND = 0
WF_BUILD_FRONTEND = 1
WF_PROCESSING = 1
WF_ADDITIVES = 1

[data]
DATABASE_URI = sqlite:///app.db
REDIS_URI = redis://localhost:6379

[security]
SECURITY_SECRET = another-secret

[mail]
MAIL_USERNAME = noreply@example.org
MAIL_PASSWORD = supersecret

[additives]
my_additive = 1
```

## What belongs here vs. in a config class

This is the single most common mistake when generating WebFluid projects.

| Put it in the `.ini`                                      | Put it in `fluid/config.py`                                            |
|-----------------------------------------------------------|------------------------------------------------------------------------|
| Secrets (`SECRET_KEY`, `SECURITY_SECRET`, mail passwords) | Non-secret runtime settings (`APP_CONFIG`, `APP_FRONTEND`, `BASE_URL`) |
| Connection URIs (`DATABASE_URI`, `REDIS_URI`)             | Structured values: dicts, lists, tuples                                |
| `EXT_*` and `WF_*` switches                               | Anything a reader of the repository should see                         |
| `[additives]` toggles                                     | Defaults that every deployment shares                                  |
| Per-deployment overrides                                  |                                                                        |

The `.ini` is a flat string-to-string map. It cannot express a dict, a list or a boolean — a value
is a string, and the framework only interprets it as truthy for the switch keys. `APP_FRONTEND`,
`JWT_AUDIENCES`, `SQLALCHEMY_BINDS` and friends **must** live in a config class.

{{ rule("app_configs/ is gitignored by the generated .gitignore. Never write a value there that the
    repository needs in order to start — a fresh clone has no app_configs directory at all.") }}

## The switches

Both switch families are read from the environment at **import time** of
`webfluid.core.constants`, through `enabled(key)`, which is true for `"true"`, `"1"` or `"yes"`
(case-insensitive). Everything else, including an absent key, is false.

### `EXT_*` — extensions

| Switch           | Enables                                                   | Hard requirements                                          |
|------------------|-----------------------------------------------------------|------------------------------------------------------------|
| `EXT_SCHEDULING` | APScheduler `AsyncIOScheduler`, started on a startup hook | —                                                          |
| `EXT_SQLALCHEMY` | `db` — engines, sessions, `Model`                         | —                                                          |
| `EXT_BABEL`      | `babel` — gettext, formatters, `/ws/i18n`                 | **`EXT_SQLALCHEMY`**                                       |
| `EXT_SECURITY`   | `security` — users, gates, CSRF, OAuth                    | `EXT_SQLALCHEMY` (models); `SECURITY_SECRET` in production |
| `EXT_EVENTS`     | `events` — signals, queries, `/ws/events`                 | —                                                          |
| `EXT_CACHE`      | `cache` — redis or legacy backend                         | —                                                          |
| `EXT_MAIL`       | `mail` — sync and async SMTP                              | —                                                          |
| `EXT_JWT`        | `jwt` — encode/decode + key rotation                      | **`EXT_SCHEDULING` and `EXT_CACHE`**                       |

A missing hard requirement raises `FrameworkException` during `Fluid(...)`, not at first use.

### `WF_*` — surface features

| Switch              | Effect                                                                                                                                                                                                  |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `WF_PROCESSING`     | Installs the shared template context (`url_for`, `theme`, `src`, `LANG`, `YEAR`, `id`, the gettext fallback), the request logger, the styled error pages, and the `/wf-identity` + `/url-for` endpoints |
| `WF_TAILWIND`       | Compiles every `tailwind_raw.css` into a minified `tailwind.css` on startup; publishes the `wf_tailwind` Jinja global                                                                                   |
| `WF_THEMES`         | Enables `add_theme` / `get_theme` / `set_theme` and the client light-dark helper. Also selects the raw stylesheet name: `tailwind_raw.css` with themes on, `tailwind_no_themes.css` with themes off     |
| `WF_CHECK_FRONTEND` | Production only: `npm run check --workspaces` on startup; a type error aborts the boot                                                                                                                  |
| `WF_BUILD_FRONTEND` | Production only: `npm run build --workspaces` on startup; a failed build aborts the boot                                                                                                                |
| `WF_ADDITIVES`      | Registers and enables every Additive switched on in `[additives]`                                                                                                                                       |

`WF_CHECK_FRONTEND` and `WF_BUILD_FRONTEND` are **not read in debug mode** — the Vite dev server
takes over there.

{{ rule("Turn WF_PROCESSING on for anything that renders HTML. Without it there is no url_for, no
    theme, no src and no error pages in your templates, and fluid_base.html renders a broken
    document.") }}

{{ info("WF_PROCESSING registers an after_request processor (the error-page swap), which puts every
    response in the app on the buffered path — see utils/runtime.md. That is the price of styled
    error pages; a headless API that answers JSON only can leave the switch off.") }}

### `[additives]`

One line per Additive **id**, not per directory name (they usually match, but the manifest's `id`
wins). `WF_ADDITIVES` must also be on. Base Additives are never listed — they are pulled in by
whichever default Additive extends them.

```ini
[additives]
portal = 1
dashboard = 0
```

`wf run` counts the truthy entries into `ENABLED_ADDITIVES` so the registration progress bar knows
its length.

## Secrets from files

Any key may be suffixed with `_FILE` and point at a path instead. The CLI reads the file (UTF-8)
and exposes the contents under the key **without** the suffix. If the file does not exist, the raw
value (the path string) is kept as a fallback.

```ini
[general]
SECRET_KEY_FILE = /run/secrets/secret_key

[security]
SECURITY_SECRET_FILE = /run/secrets/security_secret
```

The app sees `SECRET_KEY` and `SECURITY_SECRET`. `wf run` and the `wf migrate` environment share
the same parser, so a migration also sees the real secret. This is the correct way to feed Docker
and Kubernetes secrets into a WebFluid app.

## The `[dev]` section

`[dev]` is the one section name with meaning: its keys are applied **only** when `-d` / `--debug`
is passed. It is skipped entirely on a normal run.

```ini
[general]
SECRET_KEY = supersecret
DATABASE_URI = postgresql://user:pw@db/prod

[dev]
DATABASE_URI = sqlite:///dev.db
```

Because the CLI iterates sections in file order and `[dev]` overwrites what came before it, keep
`[dev]` **last** in the file.

## Environment variables the CLI sets for you

`wf run` injects these on top of the parsed config. Do not set them in the `.ini`:

| Variable                      | Value                                                      |
|-------------------------------|------------------------------------------------------------|
| `APP_NAME`                    | The config name — becomes `fluid.name`                     |
| `SERVER_HOST` / `SERVER_PORT` | From `--host` / `--port`, default `127.0.0.1` / `8000`     |
| `IN_EXECUTION`                | `1` — gates the log factory and the framework i18n catalog |
| `DEBUG_MODE`                  | `1` when `-d`                                              |
| `LOG_LEVEL`                   | `--loglevel`, forced to `debug` under `-d`                 |
| `COLUMNS` / `LINES`           | Terminal size, so progress bars render correctly           |
| `PYTHONIOENCODING`            | Console encoding + `backslashreplace`                      |
| `PYTHONUNBUFFERED`            | `1`                                                        |
| `ENABLED_ADDITIVES`           | Count of truthy `[additives]` entries                      |

Two more are read but never set by `wf run`:

- `DEV_AUTO_INSTALL=1` — in debug mode, calls `Additive.install()` on every Additive as it is
  registered. Development convenience; ignored outside debug.
- `OCEAN_API` / `OCEAN_AUTH` — point the Ocean client at a different hub.

## One project, many apps

`fluid.name` comes from the config name, so a single `main.py` can assemble different applications
from the same codebase:

```python
def prepare_fluid() -> Fluid:
    app = Fluid(__name__)

    if app.name == "api":
        from fluid.api import api_router
        app.include_router(api_router)
    elif app.name == "web":
        from fluid.app import app_router
        app.include_router(app_router)

    return app
```

`wf run api` and `wf run web` then serve different route sets with different switches, different
databases and different Additives — from one repository.

{{ bug("wf create app writes app_configs/<name>.ini in the interpreter's locale encoding, and
    wf run reads it back the same way. That is symmetric on one machine and breaks as soon as a
    config carrying a non-ASCII value is written on a Windows console and read elsewhere. Keep app
    config values ASCII, or move them behind the *_FILE indirection.") }}

## Next

- [`config/config-class.md`]({{ base }}config/config-class.md) — everything that does *not* belong
  in the `.ini`.
- [`cli/run.md`]({{ base }}cli/run.md) — what `wf run` does with the file.
- [`cli/create.md`]({{ base }}cli/create.md) — `wf create app` generates one interactively.
{% endblock %}
