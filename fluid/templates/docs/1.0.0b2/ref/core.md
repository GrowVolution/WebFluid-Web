{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Reference: Core{% endblock %}
{% block doc_section %}Reference{% endblock %}

{% block summary %}
`webfluid` and `webfluid.core.*` — the application class, configuration, the request context, the
shared battery registry and the runtime constants.
{% endblock %}

{% block body %}
## `Fluid`

```python
from webfluid import Fluid

app = Fluid(import_name)
```

A `fastapi.FastAPI` subclass, so every FastAPI idiom applies. Construction parses config, sets up
static mounts, Jinja, middleware and the enabled batteries.

### Methods

| Signature                              | Notes                                                                  |
|----------------------------------------|------------------------------------------------------------------------|
| `await render(template, **ctx)`        | Runs context processors, then renders through the async Jinja env      |
| `await render_string(source, **ctx)`   | Same, for a template held as a string                                  |
| `mix()`                                | Blocking. Owns the loop, the lifecycle phases and the shutdown signals |
| `url_path_for(name, /, **path_params)` | Reverse a route through a rebuilt name index. Raises `NoMatchFound`    |

### Registration properties

Each returns the `add` method of a phase or registry, so it works as a decorator or a call.

| Property              | Required args of `fn` | Window                                  |
|-----------------------|-----------------------|-----------------------------------------|
| `startup_hook`        | 0                     | Before the server starts                |
| `shutdown_hook`       | 0                     | Before the server stops                 |
| `before_request`      | 0                     | Any time                                |
| `after_request`       | 1 (`response`)        | Any time                                |
| `context_processor`   | 0                     | Any time                                |
| `add_template_loader` | — (a loader)          | Before startup — then `RuntimeError`    |
| `add_source`          | `(src, priority=1)`   | Before startup — then `RuntimeError`    |
| `add_theme`           | `(name, link)`        | Needs `WF_THEMES`                       |
| `get_theme`           | `()`                  | Needs `WF_THEMES`                       |
| `set_theme`           | `(request, name)`     | Needs `WF_THEMES`                       |
| `limit`               | slowapi's `limit`     | No-op when `RATELIMIT_ENABLED` is false |

### Attributes

| Attribute                          | Type                                                     |
|------------------------------------|----------------------------------------------------------|
| `config`                           | `Config` (a `dict`) — every framework key is present     |
| `name`                             | The app name, from `APP_NAME`, sanitised and lowercased  |
| `project_root`                     | `Path` — the directory of `import_name`                  |
| `additive_root`                    | `Path` — `project_root / "additives"`                    |
| `jinja_env`                        | The async `jinja2.Environment`                           |
| `sources` / `rendered_sources`     | The frozen head sources (tuple / joined string)          |
| `static_files` / `static_prefixes` | The static registry and the middleware-exempt prefixes   |
| `frontend`                         | The `Frontend` object, when `APP_FRONTEND` is not `None` |

`app_root` is a **deprecated** alias of `project_root` and emits a `DeprecationWarning`.

## `webfluid.core.config`

```python
from webfluid.core.config import register_config, Config, DefaultConfig
```

| Name                          | Notes                                                                               |
|-------------------------------|-------------------------------------------------------------------------------------|
| `register_config(priority=1)` | Class decorator. Priority 1–10; higher wins. Raises `ValueError` outside that range |
| `Config`                      | A `dict` subclass. `from_object(obj_or_module_path)` pulls in upper-case attributes |
| `DefaultConfig`               | The single source of truth for every framework default                              |
| `init_configs(fluid)`         | Imports `fluid.config` and every enabled Additive's `config` module                 |
| `build_config()`              | Merges `DefaultConfig` + registered classes into a plain dict                       |

The merge collects **upper-case attributes across the whole MRO**, in reverse, so inheritance works
and the subclass wins. Full key table: [`config/config-class.md`]({{ base }}config/config-class.md).

## `webfluid.core.identity`

The seam a fork edits. Everything else derives from it.

| Group    | Names                                                                                                                       |
|----------|-----------------------------------------------------------------------------------------------------------------------------|
| Identity | `FRAMEWORK_ID` (`"fluid"`), `FRAMEWORK_NAME`, `FRAMEWORK_ABBR` (`"wf"`), `FRAMEWORK_PACKAGE`, `FRAMEWORK_ROOT`              |
| URLs     | `FRAMEWORK_SITE`, `FRAMEWORK_DOCS`                                                                                          |
| Hub      | `HUB_NAME`, `HUB_API_URL`, `HUB_AUTH_URL`, `HUB_TOKEN_FILE`                                                                 |
| Derived  | `CLI_NAME`, `ENV_PREFIX`, `EXTENSION_GROUP`, `MAIN_LOGGER`, `ADDITIVE_LOGGER`, `REQUIRES_KEY`, `IDENTITY_ROUTE`             |
| Assets   | `BASE_TEMPLATE` (`"fluid_base.html"`), `STATIC_MOUNT`, `STATIC_GLOBAL` (`"wf_static"`), `TAILWIND_GLOBAL` (`"wf_tailwind"`) |

## `webfluid.core.context`

```python
from webfluid.core.context import FluidContext, BaseContext
```

### `FluidContext`

| Member                                                                                           | Notes                                                                         |
|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `.fluid`, `.request`                                                                             | The app and the `Request` (or `None`)                                         |
| `current()`                                                                                      | The context, or `RuntimeError`                                                |
| `try_current()`                                                                                  | The context, or `None`                                                        |
| `cached_or(key, factory)`                                                                        | Classmethod. Memoises per request; calls the factory directly with no context |
| `cached(key, factory)`                                                                           | Instance method version                                                       |
| `__getitem__`, `__setitem__`, `get`, `pop`, `keys`, `values`, `items`, `__contains__`, `__len__` | Dict-like storage                                                             |
| `__bool__`                                                                                       | **Always `True`**                                                             |

{{ rule("A context is always truthy, even when empty. Test try_current() against None. len() still
    reports the size of the storage — that is exactly the trap beta 1 shipped.") }}

Construction: `FluidContext(fluid, request=None, *args, **kwargs)`. Positional args are callables
stored under their `__name__`; keyword args go into the storage.

### `BaseContext`

The contextvar-backed base for `Executor`, `AsyncExecutor`, `DomainContext`, `SelectorContext`,
`ClientContext` and the log context. Provides `current()`, `try_current()`, re-entrant
`__enter__`/`__exit__` (and async variants), and:

```python
with SomeContext.outer(depth=1) as parent: ...
```

which temporarily re-enters an enclosing context, yielding `None` when there is none.

## `webfluid.core.ext`

The shared, ready-to-use battery instances. Created lazily on first attribute access and cached in
module globals.

```python
from webfluid.core.ext import (
    scheduler,   # APScheduler AsyncIOScheduler
    db,          # SQLAlchemy
    babel,       # Babel
    security,    # Security
    events,      # EventManager
    cache,       # Cache
    mail,        # Mail
    jwt          # JWTManager
)
```

{{ warning("Importing one of these does not enable it. Using a battery whose EXT_ switch is off
    raises at first use — SQLAlchemy with FrameworkException('expand_fluid() has not been called'),
    the Delegated-based ones likewise.") }}

## `webfluid.core.constants`

Resolved once, at import time, from the environment.

| Name                                                                                                              | Value                                                             |
|-------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| `APP_STATIC`, `FRAMEWORK_STATIC`                                                                                  | `"/static"`, `"/fluid/static"`                                    |
| `HUB_API`, `HUB_AUTH`                                                                                             | Ocean base URLs, overridable with `OCEAN_API` / `OCEAN_AUTH`      |
| `DEBUG`, `EXECUTION`                                                                                              | `enabled("DEBUG_MODE")`, `enabled("IN_EXECUTION")`                |
| `THEMES`, `TAILWIND`, `CHECK_FRONTEND`, `BUILD_FRONTEND`, `PROCESSING`, `ADDITIVES`                               | Resolved `WF_*` switches                                          |
| `FEATURE_FLAGS`                                                                                                   | The tuple of their environment names                              |
| `EXT_SCHEDULING`, `EXT_SQLALCHEMY`, `EXT_BABEL`, `EXT_SECURITY`, `EXT_EVENTS`, `EXT_CACHE`, `EXT_MAIL`, `EXT_JWT` | Resolved `EXT_*` switches                                         |
| `EXTENSION_FLAGS`                                                                                                 | Their environment names                                           |
| `DEV_AUTO_INSTALL`                                                                                                | Run `Additive.install()` on every registration during a debug run |

{{ rule("These are module-level constants read at import time, not live values. A test that changes
    os.environ after the module is imported changes nothing. Use webfluid.utils.enabled(key) for a
    dynamic read.") }}

## `webfluid.version`

```python
from webfluid import version

version()          # -> Version, e.g. Version("{{ version }}")
```

`Version` (in `webfluid.utils`) is a `packaging.version.Version` subclass built from
`Version(*parts)`, with `stage` (`"a"`, `"b"`, `"rc"` or `""`) and `build` (int) on top of the usual
comparison behaviour.

## Next

- [`ref/extensions.md`]({{ base }}ref/extensions.md) — the battery API surface.
{% endblock %}
