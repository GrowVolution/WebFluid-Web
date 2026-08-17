{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Reference: Utils{% endblock %}
{% block doc_section %}Reference{% endblock %}

{% block summary %}
`webfluid.utils` — the helpers the framework leans on internally and exposes for your own use, plus
the log factory and the exception hierarchy.
{% endblock %}

{% block body %}
## `webfluid.utils`

```python
from webfluid.utils import (
    enabled, safe_string, camel_to_snake, random_code, get_root_path,
    parse_config, required_arg_count, async_result, safe_execute,
    run_in_executor, check_priority, build_sorted_tuple, try_import,
    Version, check_required_version,
    get_proxy, get_websocket_proxy, add_proxy, close_proxy_client
)
```

### Strings and environment

| Function                     | Notes                                                                                                           |
|------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `enabled(key)`               | `os.getenv(key, "").lower() in ("true", "1", "yes")`. A **dynamic** read, unlike the `core.constants` snapshots |
| `safe_string(text)`          | Replaces everything outside `[a-zA-Z0-9_-]` with `_`. The Additive id rule                                      |
| `camel_to_snake(text)`       | `MyModel` → `my_model`. The `__tablename__` rule                                                                |
| `random_code(length=6)`      | Uppercase letters + digits                                                                                      |
| `get_root_path(import_name)` | The directory of a module, without importing it when it is already loaded                                       |
| `parse_config(key, value)`   | The `*_FILE` resolution shared by `wf run` and the migration environment                                        |
| `read_config(path)`          | A `ConfigParser` with `optionxform = str`, UTF-8 with a locale fallback                                         |

### Callables

| Function                                           | Notes                                                                               |
|----------------------------------------------------|-------------------------------------------------------------------------------------|
| `required_arg_count(fn)`                           | Counts parameters without defaults. The introspection behind every hook arity check |
| `await async_result(value)`                        | Await it if it is a coroutine, otherwise return it                                  |
| `await safe_execute(fn, reraise, *args, **kwargs)` | Call sync or async; `reraise=False` logs the exception and returns `None`           |
| `await run_in_executor(fn, *args, executor=None)`  | Run a blocking call off the event loop                                              |
| `in_running_loop()`                                | Whether there is a running asyncio loop                                             |

{{ rule("run_in_executor is the correct answer whenever you must call something blocking from async
    code — a sync SDK, a CPU-bound hash, a sync database driver. Give it its own ThreadPoolExecutor
    when the work is frequent, the way HashService does.") }}

### Versions and priorities

| Function                                                                               | Notes                                                                                                                                        |
|----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `Version(*parts)`                                                                      | A `packaging.version.Version` subclass; `Version(1, 2, 0)` or `Version("1.2.0")`. Adds `.stage` (`"a"`/`"b"`/`"rc"`/`""`) and `.build` (int) |
| `check_required_version(requirement, version_type="framework", additive_version=None)` | Evaluates a PEP 440 specifier with `prereleases=True`. `"*"` is always true                                                                  |
| `check_priority(priority)`                                                             | Raises `ValueError` outside 1–10                                                                                                             |
| `build_sorted_tuple(data, defaults=None)`                                              | Values of a dict sorted by key, descending                                                                                                   |
| `try_import(name)`                                                                     | Returns `None` for a missing module — but **still raises** when the module exists and its own imports fail                                   |

### Proxies

| Function                                                               | Notes                                                  |
|------------------------------------------------------------------------|--------------------------------------------------------|
| `get_proxy(base_url, prefix="", pass_prefix=False, proxy_plugin=None)` | An async HTTP proxy handler                            |
| `get_websocket_proxy(...)`                                             | The websocket equivalent                               |
| `add_proxy(target, base_url, ...)`                                     | Register both on a `Fluid` or on an Additive's routers |
| `await close_proxy_client()`                                           | Registered as a shutdown hook by the framework         |

The HTTP proxy drops the upstream's hop-by-hop and encoding headers
(`content-encoding`, `content-length`, `transfer-encoding`, `connection`) and recomputes the length
for the body it actually forwards, while repeated headers such as `Set-Cookie` survive as separate
lines. This is what HMR rides on.

The websocket proxy awaits its cancelled pump task and retrieves the exception of the completed one,
so an upstream that drops no longer surfaces as `Task exception was never retrieved`.

## `webfluid.utils.logging`

```python
from webfluid.utils.logging import factory as log

log.log("info line")
log.debug("..."); log.warning("..."); log.error("..."); log.critical("...")
log.exception(exc, "optional message")
```

| Member                 | Notes                                                                 |
|------------------------|-----------------------------------------------------------------------|
| `factory`              | The singleton `LogFactory`. **Logs only while `IN_EXECUTION` is set** |
| `additive_context(fn)` | Route a callable's logs through the `webfluid.additives` logger       |
| `start_session()`      | Installs handlers and the level from `LOG_LEVEL`. Called by `mix()`   |

Coloured to stdout (through the active progress bar), plain to stderr (which `wf run` redirects into
`logs/<app>/<timestamp>.log`).

## `webfluid.utils.cli`

| Member                                        | Notes                                                                                   |
|-----------------------------------------------|-----------------------------------------------------------------------------------------|
| `progress_bar(description, length, **kwargs)` | A tqdm bar sized to the terminal. While one is open, log lines are written *through* it |
| `download_file(url, dest)`                    | A streamed download with a bar attached                                                 |
| `CliContext`                                  | The `BaseContext` carrying the active bar                                               |

## `webfluid.utils.additives`

`register_additives`, `installed_additives`, `installed_bases`, `import_base`,
`require_extensions`, `id_check`, `version_check`, `type_check`. See
[`ref/additives.md`]({{ base }}ref/additives.md).

## `webfluid.utils.countries`

| Member                                                         | Notes                                  |
|----------------------------------------------------------------|----------------------------------------|
| `Country`                                                      | ISO 3166-1 alpha-2 `StrEnum`           |
| `DEFAULT_COUNTRY`                                              | The fallback code                      |
| `is_valid(code)`, `coerce(code)`, `normalize(code)`            | Validate and canonicalise              |
| `localized_names(locale=None)`, `options(locale=None)`         | Babel-localized names / select options |
| `country_from_request(request=None, fallback=DEFAULT_COUNTRY)` | Resolve from geo headers               |

## `webfluid.utils.ocean`

| Member                                                      | Notes                                                                  |
|-------------------------------------------------------------|------------------------------------------------------------------------|
| `Ocean`                                                     | The HTTP client behind `wf ocean` — search, resolve, download, publish |
| `load_token` / `save_token` / `delete_token` / `token_file` | The token at `~/.wf-ocean`                                             |
| `extract_archive(data, target)`                             | Archive extraction                                                     |
| `humanize_error(detail)`                                    | Human-readable messages for hub error codes                            |

## `webfluid.exceptions`

```text
FrameworkException
├── FrontendException
│   ├── NodeError
│   └── TailwindError
├── AdditiveException
│   └── ManifestError
└── OceanError            (.status, .detail)
```

| Exception                     | Raised by                                                                                                                                                    |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `FrameworkException`          | Missing `SECRET_KEY`, a battery used before `expand_fluid`, a missing extension dependency, SMTP failures, unknown themes, event registration outside a loop |
| `FrontendException`           | Covering a frontend twice, a failed production build, a failed asset download                                                                                |
| `NodeError` / `TailwindError` | A non-zero exit from the bundled toolchain                                                                                                                   |
| `AdditiveException`           | An Additive outside `additives.`, a bad manifest, illegal base relationships, missing requirements                                                           |
| `ManifestError`               | Manifest validation                                                                                                                                          |
| `OceanError`                  | The hub client; carries `status` and `detail`                                                                                                                |

{{ rule("Catch FrameworkException when you want to handle any framework-level failure uniformly, and
    the specific subclass when you can actually recover. Never catch bare Exception around framework
    calls — the exception handler already turns an unhandled one into a proper 500.") }}

## That's the whole surface

You now have the complete map: the app class, the batteries, the surface, the module system and the
helpers. Keep [the overview]({{ base }}.md) handy for the known issues this beta ships with, pin
your version, and build.
{% endblock %}
