{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Reference: Surface{% endblock %}
{% block doc_section %}Reference{% endblock %}

{% block summary %}
`webfluid.surface` — the frontend layer: serving the UI, plus the bundled Node and Tailwind tooling
that drives it. Most of this you reach through config and the CLI rather than directly.
{% endblock %}

{% block body %}
## `Frontend`

```python
from webfluid.surface import Frontend
```

One instance covers one *surface* — the main app or a single Additive.

| Member                                                          | Notes                                                                                         |
|-----------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `Frontend(fluid=None, additive=None)`                           | Passing either covers it immediately                                                          |
| `cover_fluid(fluid)`                                            | Configure from `APP_FRONTEND`, rooted at `project_root / "fluid"`                             |
| `cover_additive(additive)`                                      | Configure from the manifest's `frontend`, rooted at the Additive                              |
| `include()`                                                     | The markup the `frontend()` template helper emits: htmx / Alpine tags + the Tailwind link     |
| `await vite()`                                                  | The served Vite index, rewritten for HMR in debug. `HTTPException(404)` when there is no Vite |
| `generate_tailwind(frontend, static)`                           | Compile this surface's raw stylesheet into the Vite source tree and/or the static folder      |
| `Frontend.prepare(fluid)`                                       | Classmethod. Wires the dev-server proxy (debug) or the check/build/mount flow (production)    |
| `.type`, `.alpine`, `.prefix`, `.rel`, `.tailwind`, `.has_vite` | State                                                                                         |

Covering the same object twice raises `FrontendException("Frontend has already been configured.")`.

### The frontend config block

Used both as `APP_FRONTEND` and as the manifest's `frontend`:

| `type`   | Keys                                        | Defaults             |
|----------|---------------------------------------------|----------------------|
| `"none"` | —                                           |                      |
| `"htmx"` | `alpine`                                    | `False`              |
| `"vite"` | `framework`, `typescript`, `register_index` | — / `False` / `True` |

`framework` ∈ `lit`, `none`, `preact`, `qwik`, `react`, `solid`, `svelte`, `vue`.

`register_index: False` means the framework does **not** take the `/` route — wire
`additive.frontend.vite` (or `fluid.frontend.vite`) where you want it.

### Paths

| Surface           | Build served at    | Static at        |
|-------------------|--------------------|------------------|
| Main app          | `/frontend`        | `/static`        |
| Additive `portal` | `/portal/frontend` | `/portal/static` |
| Framework         | —                  | `/fluid/static`  |
| Dev server proxy  | `/vite-dev`        | —                |

## `webfluid.utils.surface`

| Function                  | Notes                                                                                                                                                       |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `setup_frontend(project)` | Downloads htmx and Alpine, clones the create-vite templates, loads Node and Tailwind, writes the root `package.json` and the orchestrating `vite.config.js` |
| `validate_config(dict)`   | Validates a frontend block; returns `(ok, value_or_reason)`                                                                                                 |

`webfluid.surface.dist` is the `Path` where Node, Tailwind and the Vite templates are cached.

## Node tooling

```python
from webfluid.surface import load_node, node_cmd, node_proc, node_cli
```

| Function                              | Notes                                                                                           |
|---------------------------------------|-------------------------------------------------------------------------------------------------|
| `load_node()`                         | Ensure a Node runtime — system Node if present, otherwise download a standalone one into `dist` |
| `node_cmd(cmd, cwd)`                  | Run a Node/npm command and wait. Raises `NodeError` on a non-zero exit                          |
| `node_proc(cmd, cwd, **popen_kwargs)` | Spawn a long-lived Node process                                                                 |
| `node_cli(app)`                       | Mounts `wf node`                                                                                |

CLI: `wf node node --version`, `wf node npm install`, `wf node npm run build --workspaces`.

## Tailwind tooling

```python
from webfluid.surface import (
    load_tailwind, generate_tailwind_css, generate_tailwind_asset, tailwind_cmd, tailwind_cli
)
```

| Function                                      | Notes                                                                                            |
|-----------------------------------------------|--------------------------------------------------------------------------------------------------|
| `load_tailwind()`                             | Ensure the standalone Tailwind CLI                                                               |
| `generate_tailwind_css(fluid)`                | Compile every `tailwind_raw.css` in the app (and the framework) — the `WF_TAILWIND` startup hook |
| `generate_tailwind_asset(input, output, cwd)` | Compile one file                                                                                 |
| `tailwind_cmd(args, cwd)`                     | Raw passthrough. Raises `TailwindError`                                                          |
| `tailwind_cli(app)`                           | Mounts `wf tailwind`                                                                             |

CLI: `wf tailwind -- --help` (the `--` is required).

The raw stylesheet name depends on `WF_THEMES`: `tailwind_raw.css` with themes on,
`tailwind_no_themes.css` with themes off.

{{ rule("Never edit a compiled tailwind.css — it is regenerated on every boot with WF_TAILWIND on,
    and it is in the generated .gitignore. Edit the raw file.") }}

## Vite internals

Not exported, but worth knowing they exist:

| Piece               | Role                                                                                                                                                                           |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Vite`              | Per-surface Vite handling: index rewriting, static mounting, Tailwind generation                                                                                               |
| `manipulate_index`  | Rewrites `src`/`href` to `/vite-dev/...` in debug, injects `@vite/client` and the React refresh preamble, and inserts the theme link and every registered source into `<head>` |
| `asset_catch`       | The catch-all `/{path:path}` route that resolves a relative asset request to the workspace named by the `vite_ns` cookie                                                       |
| `dev.startup_hook`  | Starts the dev server and adds the `/vite-dev` proxy                                                                                                                           |
| `prod.startup_hook` | `npm run check/build --workspaces`, gated by `WF_CHECK_FRONTEND` / `WF_BUILD_FRONTEND`                                                                                         |

{{ warning("asset_catch registers a route matching /{path:path} on the app. It is added as a startup
    hook, so it is registered last and only when at least one Vite surface exists — but it does mean
    an unmatched path in a Vite app reaches that handler rather than the 404 route. It rejects
    anything without a dot, anything under api/ or the framework static, and anything containing
    /frontend.") }}

## Next

- [`ref/additives.md`]({{ base }}ref/additives.md) — the module system.
{% endblock %}
