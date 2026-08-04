{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Frontend Integration{% endblock %}
{% block doc_section %}Frontend{% endblock %}

{% block summary %}
`APP_FRONTEND` declares what kind of client an app serves: nothing, htmx, or a full Vite build. The
same shape appears as the `frontend` block of an Additive manifest, so every Additive can carry its
own client and they all share one dev server and one build.
{% endblock %}

{% block body %}
## The config

```python
# fluid/config.py
@register_config(10)
class Config:
    APP_FRONTEND = { "type": "htmx", "alpine": True }
```

Validated on boot by `webfluid.utils.surface.validate_config`; an invalid block raises
`ValueError: Invalid frontend configuration: <reason>`.

| `type`   | Extra keys                                              | Meaning                                                                 |
|----------|---------------------------------------------------------|-------------------------------------------------------------------------|
| `"none"` | —                                                       | Pure SSR, no client tooling. `frontend()` still emits the Tailwind link |
| `"htmx"` | `alpine: bool` (default `False`)                        | SSR plus injected htmx (and optionally Alpine)                          |
| `"vite"` | `framework`, `typescript: bool`, `register_index: bool` | A real Vite app served and hot-reloaded by the framework                |

`framework` must be one of `lit`, `none`, `preact`, `qwik`, `react`, `solid`, `svelte`, `vue`.
`APP_FRONTEND = None` disables the frontend object entirely — no `frontend()` global at all.

## `frontend()` in templates

The `Frontend.include()` method is published as the `frontend` Jinja global. It returns:

- the htmx `<script>` (and Alpine's, deferred) for `type: "htmx"`,
- a `<link>` to the compiled `tailwind.css` when `WF_TAILWIND` is on **and** the surface has a raw
  stylesheet.

{% raw %}
```html
{% extends "fluid_base.html" %}

{% block head %}
    {{ frontend() if frontend else "" }}
{% endblock %}

{% block content %}
    <button hx-get="/health" hx-target="#out">{{ _('PING') }}</button>
    <pre id="out"></pre>
{% endblock %}
```
{% endraw %}

{{ rule("Always guard with `if frontend else \"\"`. The global does not exist when APP_FRONTEND is
    None, and a template shared between an app and an Additive may render in either case.") }}

{{ info("The helper looks for tailwind_raw.css (themes on) or tailwind_no_themes.css (themes off) in
    that surface's static/css. If neither exists it emits no stylesheet link at all — the htmx and
    Alpine tags are unaffected. A surface that styles nothing costs nothing.") }}

## htmx: the whole story

```python
APP_FRONTEND = { "type": "htmx", "alpine": True }
```

That is it. htmx and Alpine are served from the framework's own static mount
(`/fluid/static/js/htmx.min.js`, `alpine.min.js`), downloaded once at project creation. No Node, no
build step, no workspace.

Use it when the pages are server-rendered and you want partial updates without a client build.

## Vite

```python
APP_FRONTEND = {
    "type": "vite",
    "framework": "react",
    "typescript": False,
    "register_index": True
}
```

Three pieces have to line up:

**1. A root `package.json` declaring the workspaces**

```json
{
  "name": "myapp",
  "private": true,
  "workspaces": [
    "additives/*/frontend",
    "fluid/frontend"
  ],
  "devDependencies": {
    "vite": "^8.0.0"
  }
}
```

The `additives/*/frontend` glob is what lets every Additive contribute a client to the same build.

**2. A root `vite.config.js`** — the framework writes this. It discovers every workspace, merges
their configs and adds the dev plugin that resolves assets. Do not hand-write it.

**3. The per-surface Vite project** in `fluid/frontend`, whose only framework-specific requirement
is the `base`:

```js
// fluid/frontend/vite.config.js
import { defineConfig } from 'vite'

export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/frontend/' : '/vite-dev/',
}))
```

For an Additive, the build base is the Additive's prefix: `'/portal/frontend/'`.

### `register_index`

Default `true`: the framework registers `GET /` itself and serves the Vite index. Set it to `false`
to own `/` yourself — which is what you want as soon as the SPA is not the front page.

```python
# register_index: False — wire it where you want it
additive.app.get("/console")(additive.frontend.vite)
```

### Development vs. production

|            | `wf run app -d`                                                                                                                                                      | `wf run app`                                                                                      |
|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| Vite       | Dev server started by the bundled Node on port 5173                                                                                                                  | Not started                                                                                       |
| Serving    | Proxied under `/vite-dev`, HMR live                                                                                                                                  | `dist/` mounted as static under `/frontend`                                                       |
| index.html | Read from `frontend/index.html`, script/link `src`s rewritten to `/vite-dev/...`, `@vite/client` injected (plus the React refresh preamble for `framework: "react"`) | Read from `frontend/dist/index.html`                                                              |
| Build      | —                                                                                                                                                                    | `npm run check/build --workspaces` on startup, gated by `WF_CHECK_FRONTEND` / `WF_BUILD_FRONTEND` |

Debug mode **refuses port 5173** for the app itself — that port belongs to Vite.

The served index is post-processed either way: the theme link and every registered source are
injected into its `<head>`, so a Vite app gets the same framework context an SSR page does. A
`vite_ns` cookie records which surface served the page, so the asset-catch route can resolve
relative asset requests to the right workspace.

{{ warning("HMR across the main app and several Additive frontends rides on a websocket proxied in
    front of the shared dev server. That connection can drop on its own — a Vite restart is the
    usual trigger — and the affected frontend then silently stops picking up changes. A browser
    refresh re-establishes it; there is no need to restart wf run.") }}

## Several frontends

Each Additive declares its own `frontend` block in its manifest and gets:

|           | Path                                                |
|-----------|-----------------------------------------------------|
| Build     | `/<additive-id>/frontend`                           |
| Dev       | proxied through `/vite-dev`                         |
| Static    | `/<additive-id>/static`                             |
| Workspace | `additives/<id>/frontend`, matched by the root glob |

They all share one dev server and one `npm run build --workspaces`. The per-Additive
`vite.config.js` differs from the main app's only in its `base`.

## Rules

{{ rule("Do not scaffold a Vite workspace by hand. wf create project and wf create additive copy the
    right create-vite template, rewrite package.json (name it @fluid/<app>-frontend or
    @additive/<id>-frontend, drop the dev script, split tsc into a check script) and inject the
    base into the config. Doing it manually is error-prone and buys nothing.") }}

{{ rule("Pick the smallest type that does the job. type: none for pure SSR, htmx when you want
    partial updates without a build, vite only when you genuinely need a client framework. Each step
    up adds a Node toolchain requirement to your build and your image.") }}

{{ rule("Never run npm/vite through Bash in a WebFluid project. Use wf node npm ... so the bundled
    runtime and the workspace layout are the ones the framework will use at boot.") }}

## Next

- [`surface/jinja.md`]({{ base }}surface/jinja.md) — how template names resolve.
- [`additives/contract.md`]({{ base }}additives/contract.md) — composing several frontends.
- [`cli/create.md`]({{ base }}cli/create.md) — the scaffolder that writes all of this.
{% endblock %}
