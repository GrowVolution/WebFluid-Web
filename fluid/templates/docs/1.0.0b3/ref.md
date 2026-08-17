{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Reference{% endblock %}
{% block doc_section %}Reference{% endblock %}

{% block summary %}
A terse map of every name WebFluid exports, grouped by where it lives. Use it to look a symbol up
without reading prose. The five sub-pages are
[Core]({{ base }}ref/core.md), [Extensions]({{ base }}ref/extensions.md),
[Surface]({{ base }}ref/surface.md), [Additives]({{ base }}ref/additives.md) and
[Utils]({{ base }}ref/utils.md).
{% endblock %}

{% block body %}
## Stability contract

{{ rule("From this beta onwards, everything listed in a package's __all__ follows semantic
    versioning. Anything else — module layout, private attributes, helpers that are not exported —
    is internal and may move in any release. Import from the documented paths, and keep your version
    pinned while the beta runs.") }}

## Lazy exports

Every package in the tree resolves its exports through a module-level `__getattr__`:

```python
def __getattr__(name):
    if name == "Fluid":
        from .fluid import Fluid
        return Fluid
    ...
    raise AttributeError(name)

def __dir__(): return sorted(__all__)
```

Three consequences:

1. `import webfluid` does not drag the whole framework into memory.
2. An extension you never enable is never instantiated.
3. `dir(package)` is the honest list of what it offers — use it to discover the surface.

## The import tree

```text
webfluid
├── Fluid, Additive, Manifest, version
├── core
│   ├── Fluid, Additive, Manifest
│   ├── config      register_config, Config, DefaultConfig
│   ├── context     BaseContext, FluidContext
│   ├── ext         scheduler, db, babel, security, events, cache, mail, jwt
│   └── constants   DEBUG, EXECUTION, the EXT_*/WF_* flags, static prefixes, hub urls
├── extensions
│   ├── FluidExtension
│   ├── SQLAlchemy, Babel, Security, EventManager, Mail, Cache, JWTManager
│   ├── babel       Domain, Translations, I18nMessage, LazyString, the formatters
│   ├── cache       BaseCache, Cache
│   ├── sqlalchemy  Model, Bind, Executor, AsyncExecutor, database_uris
│   └── security    services, models, utils
├── surface
│   ├── dist, Frontend
│   ├── load_node, node_cli, node_cmd, node_proc
│   └── load_tailwind, generate_tailwind_css, generate_tailwind_asset, tailwind_cmd, tailwind_cli
├── utils
│   ├── enabled, safe_string, camel_to_snake, random_code, get_root_path, parse_config
│   ├── required_arg_count, async_result, safe_execute, run_in_executor
│   ├── check_priority, build_sorted_tuple, try_import, read_config, in_running_loop
│   ├── Version, check_required_version
│   ├── get_proxy, get_websocket_proxy, add_proxy, close_proxy_client
│   ├── additives, ocean, countries, logging, cli, surface
├── fluid           the framework's own templates, static and i18n
└── exceptions      FrameworkException and its children
```

## Top-level exports

```python
from webfluid import Fluid, Additive, Manifest, version
from webfluid import utils, fluid, extensions, exceptions
```

| Name       | What it is                                                                 |
|------------|----------------------------------------------------------------------------|
| `Fluid`    | The application class, a `FastAPI` subclass. [Core]({{ base }}ref/core.md) |
| `Additive` | A self-contained sub-app. [Additives]({{ base }}ref/additives.md)          |
| `Manifest` | A parsed `manifest.json`. [Additives]({{ base }}ref/additives.md)          |
| `version`  | A callable returning the running framework version as a `Version`          |

## Where to import what

| You need                            | Import from                                      |
|-------------------------------------|--------------------------------------------------|
| The app class                       | `webfluid`                                       |
| A battery instance                  | `webfluid.core.ext`                              |
| The request context                 | `webfluid.core.context`                          |
| Config registration                 | `webfluid.core.config`                           |
| Runtime flags                       | `webfluid.core.constants`                        |
| `Model`, executors, `database_uris` | `webfluid.extensions.sqlalchemy`                 |
| Security models and validators      | `webfluid.extensions.security.models` / `.utils` |
| Babel helpers and formatters        | `webfluid.extensions.babel.utils`                |
| The log factory                     | `webfluid.utils.logging`                         |
| Additive registry helpers           | `webfluid.utils.additives`                       |
| Exceptions                          | `webfluid.exceptions`                            |

{{ warning("Do not import from a module path that is not in the tree above — for example
    webfluid.core.fluid.main or webfluid.extensions.security.services.user.gating. Those are internal
    and are free to move between releases.") }}

## The agent skill in the package

`webfluid/.agents/skills/webfluid` ships inside the distribution: a `SKILL.md` plus
`references/project-setup.md`, `runtime.md`, `batteries.md`, `additives.md`, `frontend.md` and
`pitfalls.md`. If you are working in a repository where `webfluid` is installed, that is the local
copy of this material, cut for editing a codebase rather than reading one.

{{ rule("These docs are the authority on exhaustive detail (full config tables, complete API
    surfaces, the release-accurate defect list); the packaged skill is the authority on what the
    installed version does. When the installed version is newer than the published latest, the
    package's own CHANGELOG.md is the authority on the delta.") }}

## Next

- [`ref/core.md`]({{ base }}ref/core.md) — `Fluid`, config, context, `core.ext`, constants.
{% endblock %}
