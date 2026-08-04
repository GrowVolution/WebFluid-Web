{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Frontend Tooling{% endblock %}
{% block doc_section %}Frontend{% endblock %}

{% block summary %}
The *surface* is the framework's frontend layer: a bundled Node runtime and Tailwind CLI, the shared
template context, the base layout, the injected script sources and the theme system. It is gated by
the `WF_*` feature switches, and `WF_PROCESSING` in particular is what makes templates work at all.
{% endblock %}

{% block body %}
## The feature switches

```ini
[features]
WF_PROCESSING = 1
WF_TAILWIND = 1
WF_THEMES = 1
WF_CHECK_FRONTEND = 0
WF_BUILD_FRONTEND = 1
WF_ADDITIVES = 1
```

### `WF_PROCESSING`

The one you almost always want. `setup_processing(fluid)` installs:

| Component                   | Effect                                                                                                                                                                   |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Context processor           | Adds `LANG`, `YEAR`, `id`, `theme`, `src`, `url_for` to **every** render                                                                                                 |
| `before_request` logger     | `[Request] GET /path from 1.2.3.4 (user-agent)`                                                                                                                          |
| `after_request` error pages | Renders `errors/<status>.html` for 400, 401, 403, 404, 405, 429, 500, 502, 503 — **only** when the client's `Accept` contains `text/html`                                |
| Exception handler           | Unhandled exceptions → `errors/debug/500.html` in debug, `errors/500.html` otherwise; JSON clients get the status text only (message, type and traceback are debug-only) |
| `GET /wf-identity`          | `{"id", "version", "timestamp"}`                                                                                                                                         |
| `POST /url-for`             | `{endpoint, path_params, external}` → `{"url": ...}`; unknown endpoint → `404 UNKNOWN_ENDPOINT`                                                                          |

{{ rule("Without WF_PROCESSING there is no url_for, no theme, no src and no _() fallback in your
    templates, so fluid_base.html renders a broken document and every error is a bare JSON body.
    Turn it on for anything that serves HTML.") }}

### The shared context variables

These come from the processing context processor, which is why you never pass them:

| Variable        | Type      | Value                                                                                                      |
|-----------------|-----------|------------------------------------------------------------------------------------------------------------|
| `url_for`       | callable  | `url_for(name, **path_params)` → path; `external=True` → absolute URL. **`None` when there is no request** |
| `src`           | callable  | `src()` → the injected `<script>`/`<link>` sources, timestamped in debug                                   |
| `theme`         | string    | The active theme's stylesheet link (empty without `WF_THEMES`)                                             |
| `LANG`          | string    | The active locale (from Babel, or `BABEL_DEFAULT_LOCALE`)                                                  |
| `YEAR`          | int       | Current UTC year                                                                                           |
| `id`            | string    | `"fluid"` — the framework id                                                                               |
| `_`, `ngettext` | callables | Babel's, or a no-op fallback when `EXT_BABEL` is off                                                       |

{{ bug("url_for is built from the request in the current context and is None when there is none.
    Rendering a template from a startup hook, a scheduled job or a mail routine therefore fails with
    'NoneType is not callable'. Use fluid.url_path_for(name, **params) or an absolute BASE_URL in
    off-request templates, and guard in shared ones: {{ url_for('static', path='x') if url_for else
    '' }}") }}

### `WF_TAILWIND`

On startup, `generate_tailwind_css(fluid)` compiles every `tailwind_raw.css` it finds in the app's
(and the framework's) `static/css` directories into a minified `tailwind.css` next to it. It also
publishes the `wf_tailwind` Jinja global — a ready `<link>` tag that `fluid_base.html` includes.

```css
/* fluid/static/css/tailwind_raw.css */
@import "tailwindcss" source("../../");

@theme {
    /* your design tokens */
}
```

The `source(...)` argument tells Tailwind where to scan for class names. `../../` from
`fluid/static/css` is `fluid/` — templates included, which is what you want.

{{ rule("Edit tailwind_raw.css, never tailwind.css. The compiled file is overwritten on every boot
    and is gitignored by the generated .gitignore.") }}

### `WF_THEMES`

Enables the theme API and decides **which raw stylesheet name is compiled**:

| `WF_THEMES` | Raw file the surface looks for |
|-------------|--------------------------------|
| on          | `tailwind_raw.css`             |
| off         | `tailwind_no_themes.css`       |

```python
fluid.add_theme(name, link)         # link is HTML: a <link rel="stylesheet"> tag
fluid.get_theme()                   # the active theme's markup
fluid.set_theme(request, name)      # store the choice in the session
```

Resolution order: `request.session["theme"]` → `GLOBAL_THEME` → the framework theme.

`add_theme` raises if the name exists; `set_theme` raises if it does not — so a typo is an error,
not a page that silently keeps the old style. Both raise `FrameworkException` when `WF_THEMES` is
off.

The shipped theme derives its whole surface from five CSS custom properties on `:root`:
`--wf-blend` (structural hue), `--wf-deep`, `--wf-veil`, `--wf-sunk` and `--wf-page` (the page
gradient). Page and error backgrounds, nav, footer, dropdowns, cards and traceback frames all read
from those with a neutral fallback — so a theme that only redefines the colour scale already renders
coherently.

On the client, the injected `base.js` provides `window.wf.switchTheme()` for the light/dark
preference. That is independent of the server-side theme registry.

### `WF_CHECK_FRONTEND` / `WF_BUILD_FRONTEND`

Production only — in debug the Vite dev server takes over and neither is read.

| Switch              | Runs                         | On failure                                                     |
|---------------------|------------------------------|----------------------------------------------------------------|
| `WF_CHECK_FRONTEND` | `npm run check --workspaces` | Aborts the boot (unless the message is "No workspaces found!") |
| `WF_BUILD_FRONTEND` | `npm run build --workspaces` | Raises `FrontendException` with the compiler output            |

{{ rule("Turn both off in a container image that already built its assets at image-build time. There
    is no reason to compile the same bundle on every restart, and an image without a Node toolchain
    cannot anyway. The dist folders are mounted either way.") }}

## `fluid_base.html`

The framework's base layout. It expects the processing context and provides these blocks:

| Block     | Purpose                                                     |
|-----------|-------------------------------------------------------------|
| `title`   | Document title. Default `WebFluid App`                      |
| `head`    | Extra `<head>` content — this is where `frontend()` goes    |
| `nav`     | The whole `<nav>` body. Override to replace the demo navbar |
| `content` | The page. Almost always the one you fill                    |
| `footer`  | The whole footer body                                       |
| `scripts` | The trailing script block                                   |

{% raw %}
```html
{% extends "fluid_base.html" %}

{% block title %}{{ _('HOME_TITLE') }}{% endblock %}

{% block head %}
    {{ frontend() if frontend else "" }}
{% endblock %}

{% block content %}
    <section>
        <h1>{{ _('GREETING', name=name) }}</h1>
    </section>
{% endblock %}
```
{% endraw %}

The head it renders for you: charset, viewport, favicon, `<title>`, the theme link, the Tailwind
link, and `src()`.

{{ rule("Override the nav and footer blocks in your own layout rather than editing fluid_base.html
    conceptually — it is inside the installed package. If you want to replace it wholesale, create
    fluid/templates/fluid_base.html; your app's templates are searched first. See
    surface/jinja.md.") }}

## Page sources

`fluid.add_source(html, priority=1)` queues a `<script>` or `<link>` for injection into every
rendered head through `src()`.

```python
app.add_source('<link rel="preconnect" href="https://fonts.googleapis.com">', 10)
app.add_source('<script src="/static/js/analytics.js" type="module"></script>', 5)
```

- **Priority 1–10**, higher first. The framework's own scripts (`base.js`, `i18n.js`, `events.js`)
  use priority 5.
- Sources are **deduplicated** by exact string; a repeat logs a warning and is skipped.
- The HTML is parsed and rejected with `ValueError("Invalid HTML source.")` if it is not a node.
- The list is **frozen** in the `_prepare` startup hook — add sources during app assembly or from
  an Additive's `before_enable`, never later.
- In debug mode every source gets a `?t=<timestamp>` on its `src`/`href`.

## Static files

| Mount                   | Serves                                        | Route name                                |
|-------------------------|-----------------------------------------------|-------------------------------------------|
| `/static`               | `fluid/static` (only if the directory exists) | `static`                                  |
| `/fluid/static`         | the framework's own static                    | `fluid_static` (Jinja global `wf_static`) |
| `/<additive_id>/static` | that Additive's `static/`                     | `<id>_static`                             |
| `/<prefix>/frontend`    | a Vite `dist`                                 | `<name>_frontend`                         |

{% raw %}
```html
<script src="{{ url_for('static', path='js/models.js') }}"></script>
<img src="{{ url_for(wf_static, path='img/logo.png') }}" alt="Logo">
```
{% endraw %}

Everything under a static mount is served with `Cache-Control: public, max-age=STATIC_MAX_AGE`
(a year in production, 0 in debug).

{{ rule("Keep page behaviour in fluid/static/js, one small file per page, and load it with url_for.
    Inline <script> blocks in templates cannot be cached, cannot be linted and cannot be reused —
    and the browser only downloads the behaviour a page actually uses when it is a separate file.") }}

## The bundled toolchain

Node and the Tailwind CLI are **not** shipped inside the package — they are downloaded on first use
and cached under `webfluid/surface/dist`. A system Node is used when present. Both are reachable
through the CLI:

```bash
wf node node --version
wf node npm --version
wf node npm install
wf tailwind -- --help
```

Output is forwarded verbatim. `node_cmd` raises `NodeError` on a non-zero exit.

## Next

- [`surface/frontend.md`]({{ base }}surface/frontend.md) — `APP_FRONTEND`, htmx and Vite.
- [`surface/jinja.md`]({{ base }}surface/jinja.md) — which file a template name resolves to.
- [`utils/runtime.md`]({{ base }}utils/runtime.md) — themes at request time.
{% endblock %}
