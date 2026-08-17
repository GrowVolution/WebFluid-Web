{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Fluid Extensions{% endblock %}
{% block doc_section %}Extensions{% endblock %}

{% block summary %}
An extension teaches the framework a new capability: a shared service, a set of Jinja globals, a
lifecycle hook, a `wf` sub-command. It is a Python **distribution** that advertises itself through
the `webfluid.extensions` entry-point group. It is not the right tool for routes, templates or
static files — that is what Additives are for
([`additives/intro.md`]({{ base }}additives/intro.md)).
{% endblock %}

{% block body %}
## Decision table: extension or Additive?

| You want to ship…                                      | Use          |
|--------------------------------------------------------|--------------|
| A service other code calls (`db`, `mail`, `cache`)     | Extension    |
| Jinja globals or filters                               | Extension    |
| A `wf <name> …` command group                          | Extension    |
| Behaviour that must exist before routes are registered | Extension    |
| Routes, templates, static files, a frontend            | **Additive** |
| A feature a project can toggle per app config          | **Additive** |
| Something distributed and installed with `pip`         | Extension    |
| Something distributed and installed into `additives/`  | **Additive** |

## The base class

```python
from webfluid.extensions import FluidExtension


class FluidExtension:
    def __init__(self, fluid=None, *args, **kwargs):
        if fluid is not None:
            self.expand_fluid(fluid, *args, **kwargs)

    def expand_fluid(self, fluid, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def cli_entry(cls, app, name):
        if not hasattr(cls, "_cli"): return
        app.add_typer(cls._cli, name=name)
```

Three rules follow directly:

1. **`expand_fluid(fluid, *args, **kwargs)` is the only required override.** It receives the app
   and is where you read config, register hooks and publish globals.
2. **Constructing with a `fluid` calls `expand_fluid` immediately.** `MyExtension(app)` and
   `ext = MyExtension(); ext.expand_fluid(app)` are equivalent. Keep the parent signature so both
   work.
3. **A `_cli` class attribute (a `typer.Typer`) becomes a `wf` sub-command** named after the
   entry-point name.

### `Delegated` — attributes that fail loudly

The batteries expose their internals through a descriptor that raises a clear error when
`expand_fluid` has not run yet:

```python
from webfluid.extensions.base import Delegated


class Mail(FluidExtension):
    send = Delegated("_sync.send")            # -> self._sync.send
    asend = Delegated("_async.send")
    client = Delegated("_sync.client", True)  # optional: None is allowed at the last step
```

Accessing `mail.send` before `expand_fluid` raises
`FrameworkException("Mail.expand_fluid() has not been called.")` instead of `AttributeError: NoneType`.
Use it when you build sub-objects lazily in `expand_fluid` — it makes the failure mode obvious.

## Building one

### 1. The distribution

An extension has to be an installable distribution, because the CLI discovers it through entry
points.

```bash
mkdir -p myext/src/extension
cd myext
```

```toml
# myext/pyproject.toml
[project]
name = "extension"
version = "1.0"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[project.entry-points."webfluid.extensions"]
myext = "extension.main:MyExtension"
```

- The group name is exactly `webfluid.extensions`.
- The entry-point **name** (`myext`) becomes the CLI sub-command: `wf myext …`.
- The target must be a **class**, and a subclass of `FluidExtension`. The CLI checks and skips it
  with a warning otherwise.

### 2. The class

```python
# myext/src/extension/main.py
from webfluid.extensions import FluidExtension
from typing import TYPE_CHECKING, Optional
import typer

if TYPE_CHECKING:
    from webfluid import Fluid


class MyExtension(FluidExtension):
    _cli = typer.Typer(help="My extension.")

    def __init__(self, fluid: Optional["Fluid"] = None, *_, **__):
        self._foo = "default"
        self._bar = "default"
        super().__init__(fluid)

    def expand_fluid(self, fluid: "Fluid", *_, **__):
        self._foo = fluid.config.get("MYEXT_FOO", self._foo)
        self._bar = fluid.config.get("MYEXT_BAR", self._bar)

        fluid.jinja_env.globals["my_ext"] = self._my_util
        fluid.startup_hook(self._warm_up)

    async def _warm_up(self):
        ...

    def _my_util(self) -> str:
        return f"Foo is {self._foo} but bar is {self._bar}!"

    @staticmethod
    @_cli.command()
    def hello(name: str):
        typer.secho(f"Hello {name} :)", fg=typer.colors.GREEN, bold=True)
```

{{ rule("Set every instance attribute in __init__ before calling super().__init__(fluid). The
    parent constructor may call expand_fluid immediately, and expand_fluid usually reads those
    attributes as its own defaults.") }}

{{ rule("Your keys are not in DefaultConfig, so this is the one place fluid.config.get(key, default)
    is correct. Prefix them with your extension's name (MYEXT_*) to avoid collisions.") }}

### 3. Install and use

```bash
pip install -e .
wf myext hello "my friend"
```

```python
# main.py
from webfluid import Fluid
from extension.main import MyExtension

my_ext = MyExtension()


def prepare_fluid() -> Fluid:
    app = Fluid(__name__)
    my_ext.expand_fluid(app)
    return app
```

{% raw %}
```html
<!-- fluid/templates/index.html -->
<p>{{ my_ext() }}</p>
```
{% endraw %}

## What `expand_fluid` may do

Everything on the `Fluid` object is fair game, because extensions run inside the constructor
(built-in ones) or right after it (yours). The useful surface:

| Call                                                   | Effect                                                                       |
|--------------------------------------------------------|------------------------------------------------------------------------------|
| `fluid.config[...]` / `.get(...)`                      | Read settings. Already fully merged at this point                            |
| `fluid.jinja_env.globals[name] = fn`                   | Publish a template global                                                    |
| `fluid.jinja_env.filters[name] = fn`                   | Publish a template filter                                                    |
| `fluid.jinja_env.add_extension(...)`                   | Add a Jinja extension                                                        |
| `fluid.startup_hook(fn)` / `fluid.shutdown_hook(fn)`   | Lifecycle. Both take zero required args                                      |
| `fluid.context_processor(fn)`                          | Add template variables to every render                                       |
| `fluid.before_request(fn)` / `fluid.after_request(fn)` | Hook the request flow                                                        |
| `fluid.add_source(html, priority=1)`                   | Inject a `<script>`/`<link>` into every rendered head                        |
| `fluid.add_template_loader(loader)`                    | Contribute Jinja templates                                                   |
| `fluid.websocket(path)(handler)`                       | Mount a websocket (this is how Babel and Events do `/ws/i18n`, `/ws/events`) |
| `fluid.static_prefixes.add(prefix)`                    | Exempt a path prefix from the request middleware                             |

`add_source`, `add_template_loader` and `static_prefixes` are **frozen** in the `_prepare` startup
hook. Call them during `expand_fluid`, not later.

### How the built-in batteries do it

`enable_extensions(fluid)` runs during the constructor and is worth reading as a reference:

```python
if EXT_SCHEDULING: fluid.startup_hook(ext.scheduler.start)
if EXT_SQLALCHEMY: ext.db.expand_fluid(fluid)
if EXT_BABEL:
    ext.babel.expand_fluid(fluid)
    if EXECUTION:
        ext.babel.register_domain(FRAMEWORK_ID)
        ext.babel.update_translations(FRAMEWORK_ID, translations)
if EXT_SECURITY: ext.security.expand_fluid(fluid)
...
```

The instances come from `webfluid.core.ext`, which creates each one lazily on first attribute
access and caches it in module globals. That is why `from webfluid.core.ext import db` gives every
module the *same* object with no wiring.

{{ warning("Do not instantiate a battery yourself. SQLAlchemy raises FrameworkException on a second
    expand_fluid, and the others assume a single process-wide instance. Import from
    webfluid.core.ext.") }}

## Guarding on other extensions

An extension that needs a battery should assert it, the way `JWTManager` does:

```python
from webfluid.core.constants import EXT_SCHEDULING, EXT_CACHE
from webfluid.exceptions import FrameworkException


def expand_fluid(self, fluid, *_, **__):
    if not EXT_SCHEDULING:
        raise FrameworkException("EXT_SCHEDULING is required for MyExtension to work.")
    if not EXT_CACHE:
        raise FrameworkException("EXT_CACHE is required for MyExtension to work.")
```

The constants in `webfluid.core.constants` are resolved once at import time from the environment.
For a dynamic check, use `webfluid.utils.enabled("EXT_CACHE")`.

## The CLI half

`wf` walks `entry_points(group="webfluid.extensions")` on every invocation and calls
`cls.cli_entry(app, ep.name)`, which mounts `cls._cli` as a Typer sub-app. Commands must be
`staticmethod`s (or module-level functions added to the Typer instance) — they run without an
application, so they cannot rely on `fluid`.

`wf migrate` and `wf babel` are exactly this: extension CLIs, not core commands.

Two patterns for a command that needs the app: build it yourself the way `Migrate` does (import
`main.py`, call `prepare_fluid()`), or read the app config directly through
`webfluid.utils.read_config` and `parse_config`.

## Publishing

`wf ocean publish` from the directory containing `pyproject.toml` uploads it as an extension;
`wf ocean install -e <id>` pulls it into `extensions/<id>` and pip-installs it editable. Details in
[`cli/ocean.md`]({{ base }}cli/ocean.md).

## Next

- [`ext/scheduling.md`]({{ base }}ext/scheduling.md) — the simplest battery.
- [`ref/extensions.md`]({{ base }}ref/extensions.md) — the full battery API surface.
- [`additives/intro.md`]({{ base }}additives/intro.md) — the other half of the modularity story.
{% endblock %}
