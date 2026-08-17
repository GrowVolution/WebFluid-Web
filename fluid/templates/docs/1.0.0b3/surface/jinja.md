{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Template Resolution{% endblock %}
{% block doc_section %}Frontend{% endblock %}

{% block summary %}
The name you pass to `render()` is looked up against a stack of Jinja loaders assembled at startup
and then frozen. This page is the exact resolution order, the namespace prefixes, and what the
freezing buys and costs.
{% endblock %}

{% block body %}
## The environment

```python
Environment(
    enable_async=True,                                     # render_async everywhere
    auto_reload=DEBUG,                                     # stat templates only in debug mode
    autoescape=select_autoescape(
        ("html", "htm", "xml", "xhtml", "svg")
    ),
    cache_size=-1                                          # unbounded compiled-template cache
)
```

**Autoescape is on since `1.0.0b3`** for those five suffixes and — because `select_autoescape`
defaults `default_for_string` to `True` — for every `render_string` source. A template with any
other suffix (`.txt`, `.md`, `.json`) is **not** escaped, so plain-text mail bodies render as
written.

{{ rule("To emit HTML deliberately, wrap it in markupsafe.Markup at the point you build it, or use
    | safe at the point you render it. Never do either to a value that came from a request. An
    existing | e filter still works and does not double escape.") }}

Everything the framework injects is already `Markup`: page sources, `rendered_sources`, theme links,
`frontend()` and `wf_tailwind`. A `str` you build yourself is not.

{{ warning("Joining Markup fragments with a plain str separator returns a plain str, which is then
    escaped. Use Markup(sep).join(parts), not sep.join(parts). This is the exact bug the framework
    had to fix in Sources.rendered and the debug source callable when autoescaping was switched
    on.") }}

## `render` vs. `render_string`

```python
await fluid.render(template_name, **ctx)     # looked up against the loader stack
await fluid.render_string(source, **ctx)     # compiled from a string, no lookup
```

Both run every registered context processor first, then render. `render_string` is for templates
that come from a database or a user — a string has no name, so it can neither be cached nor
extended.

{{ warning("render() has no is_string parameter. Passing one is not an error: it silently becomes an
    ordinary template variable while your source string is looked up as a file name, producing a
    TemplateNotFound whose message is your entire template.") }}

## The loader stack

Assembled in this order, searched in this order:

```text
1. fluid/templates/            (your app)      + prefix "app/"
2. additives/<id>/templates/   (each Additive)   prefix "<id>/"  — always prefixed
3. <package>/fluid/templates/  (the framework) + prefix "fluid/"
```

Your app is searched **before** the framework, so an unprefixed name resolves to your file first and
falls through only when you do not have one.

```text
render("index.html")        -> fluid/templates/index.html        (your app)
render("docs/intro.html")   -> fluid/templates/docs/intro.html   (your app)
render("fluid_base.html")   -> bundled with the framework
render("errors/404.html")   -> bundled with the framework
```

Paths are always relative to `fluid/templates` and may nest arbitrarily. This documentation site
renders pages named `docs/{{ version }}/get-started.html`, which is just a file at that path.

## Namespaces

Each layer also answers to an explicit prefix:

| Prefix            | Resolves to               | Use it when                                                                                                            |
|-------------------|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| `app/…`           | `fluid/templates/…`       | You want to be unambiguous                                                                                             |
| `fluid/…`         | the framework's templates | You overrode a name locally but still want the original — `{% raw %}{% extends "fluid/fluid_base.html" %}{% endraw %}` |
| `<additive_id>/…` | that Additive's templates | Always, for Additive templates                                                                                         |

**Additive templates are only reachable through their id prefix.** That is why they can never shadow
your app's names. `additive.render("index.html")` adds the prefix for you, so inside an Additive you
keep writing plain names — but a template that `extends` another Additive's file must spell out the
prefix.

An Additive extending a base gets a `ChoiceLoader`: its own `templates/` first, then the base's,
both under the **child's** id.

## Overriding framework templates

Because your app is searched first, dropping a file with the same name into `fluid/templates`
replaces the framework's. No configuration.

{% raw %}
```html
<!-- fluid/templates/errors/404.html -->
{% extends "fluid/fluid_base.html" %}

{% block content %}
    <h1>{{ _('NOT_FOUND_TITLE') }}</h1>
{% endblock %}
```
{% endraw %}

Note the `fluid/` prefix on the `extends` — without it, an override of `fluid_base.html` itself
would extend itself and recurse.

### What the framework ships

| Template                              | Purpose                                     |
|---------------------------------------|---------------------------------------------|
| `fluid_base.html`                     | The default page layout                     |
| `base_email.html`                     | Starting point for HTML mail                |
| `base_error.html`                     | Shared error-page layout                    |
| `errors/400.html` … `errors/503.html` | 400, 401, 403, 404, 405, 429, 500, 502, 503 |
| `errors/debug/500.html`               | Detailed traceback page, debug mode only    |

{{ info("Error pages are rendered only for a client whose Accept header contains text/html.
    Everything else gets JSON — and outside debug mode that JSON carries nothing but the status
    text, so a production 500 cannot hand an API client the SQL fragment or connection string the
    exception happened to contain.") }}

## Adding a loader

```python
from jinja2 import PrefixLoader, FileSystemLoader

fluid.add_template_loader(PrefixLoader({
    "plugins": FileSystemLoader("/srv/plugins/templates")
}))
```

{{ rule("add_template_loader must be called before the server comes up — the stack is frozen in the
    _prepare startup hook. Call it during app assembly or from an extension's expand_fluid.
    Afterwards it raises RuntimeError: Loaders cannot be added after initialization.") }}

Additives call it themselves while being enabled, which is why their templates appear without any
work on your side.

## Freezing

The stack is built once and frozen. Two consequences:

- **Outside debug mode Jinja does not stat templates**, because nothing can change. Renders are
  measurably faster in production than while you are writing.
- **In debug mode `auto_reload` is on**, so edits show up on reload.

Compiled templates are cached without a size limit (`cache_size=-1`).

## Rules for generated templates

{{ rule("Extend fluid_base.html unless you have a reason not to. It already wires the theme link,
    the Tailwind link, the injected sources, the locale on <html lang> and the favicon — a
    hand-written document has to reproduce all of it.") }}

{{ rule("Guard the optional globals in templates that may render off-request or in an app with a
    different feature set: {{ frontend() if frontend else \"\" }}, {{ theme if theme else \"\" }},
    {{ url_for(...) if url_for else \"#\" }}. fluid_base.html does exactly this.") }}

{{ rule("Name templates after the route, mirroring the route path: fluid/templates/admin/users.html
    for /admin/users. Deep nesting is free and the only names you can collide with are the
    framework's handful.") }}

{{ rule("Never generate | safe or Markup(...) around a value whose origin you cannot trace to your
    own code. If a template you are porting from 1.0.0b2 now shows tags, the fix is to wrap the
    value where it is built — not to add | safe at the render site and move on.") }}

## Next

- [`additives/intro.md`]({{ base }}additives/intro.md) — the layer that owns the middle of the
  stack.
- [`surface/tooling.md`]({{ base }}surface/tooling.md) — the variables these templates use.
{% endblock %}
