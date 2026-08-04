{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Babel{% endblock %}
{% block doc_section %}Extensions{% endblock %}

{% block summary %}
`EXT_BABEL` wraps the `babel` library into gettext callables, locale-aware formatters, a
database-backed runtime translation store, a domain system for namespacing catalogs, and a
websocket that mirrors the catalog to the browser. It **requires `EXT_SQLALCHEMY`**.
{% endblock %}

{% block body %}
## Enabling

```ini
[extensions]
EXT_SQLALCHEMY = 1
EXT_BABEL = 1
```

`expand_fluid` raises `FrameworkException("EXT_SQLALCHEMY is required for Babel to work.")` without
it. Enabling Babel adds two models — `I18nKey` and `I18nMessage` — so run the migration cycle
afterwards ([`ext/migrate.md`]({{ base }}ext/migrate.md)).

What it wires up:

| Gated by | Effect |
|---|---|
| `BABEL_CONFIGURE_JINJA` (default `True`) | Installs `jinja2.ext.i18n` with new-style gettext callables and the nine format filters |
| `BABEL_CONFIGURE_SOCKET` (default `True`) | Mounts `/ws/i18n` and injects `i18n.js` as a page source |
| `BABEL_DATABASE_BIND` (default `None`) | `I18nKey.set_bind(...)` / `I18nMessage.set_bind(...)` |
| always | A startup hook that flushes queued `update_translations` calls into the database and the cache |

## In templates

The callables are installed new-style, so `_()` works in any template without a special base
layout:

{% raw %}
```html
<title>{{ _('HOME_TITLE') }}</title>
<h1>{{ _('GREETING', name=name) }}</h1>
<p>{{ ngettext('MODEL_COUNT_ONE', 'MODEL_COUNT_OTHER', count) }}</p>
```
{% endraw %}

Four callables, plus awaitable and lazy variants:

| Sync        | Await        | Lazy             | Signature                                       |
|-------------|--------------|------------------|-------------------------------------------------|
| `gettext`   | `agettext`   | `lazy_gettext`   | `(string, **variables)`                         |
| `ngettext`  | `angettext`  | `lazy_ngettext`  | `(singular, plural, num, **variables)`          |
| `pgettext`  | `apgettext`  | `lazy_pgettext`  | `(context, string, **variables)`                |
| `npgettext` | `anpgettext` | `lazy_npgettext` | `(context, singular, plural, num, **variables)` |

Interpolation is `%`-style: `format_message(msg, **variables)` does `msg % variables`. `ngettext`
sets `num` for you, so `'%(num)d models'` works without passing it.

{{ rule("Use SCREAMING_SNAKE keys, not English sentences, for any catalog you control. The domain
    escalation only accepts a catalog's answer when it differs from the string it was given, so a
    translation that legitimately equals its source is read as a miss and the next domain answers
    instead. Symbolic keys make that collision impossible. The framework's own catalog does exactly
    this.") }}

{{ rule("There is no alazy_gettext. A lazy string resolves through __str__, which cannot await. For
    module-level constants use lazy_gettext; inside async code use agettext.") }}

## Providing translations

Two mechanisms, and they compose: a **runtime store** (database-backed, the primary one) and
**`.po` catalogs** (static fallback).

### The runtime store

`babel.update_translations(domain, resolver)` takes a callable returning:

```text
{ locale: { key: { message_data: translation } } }
```

`message_data` is a JSON string describing plural form and context: `"{}"` for the plain form,
`'{"pf": "other"}'` for a plural, `'{"ctx": "menu"}'` for a context.

You rarely build that by hand. `translation_resolver(path, locale_map)` builds it from JSON files:

```json
// fluid/i18n/default.json
{
  "HOME_TITLE": ["Home", "Startseite"],
  "GREETING": ["Hello %(name)s!", "Hallo %(name)s!"]
}
```

```json
// fluid/i18n/pf-other.json
{
  "MODEL_COUNT_OTHER": ["%(num)d models", "%(num)d Modelle"]
}
```

- **`default.json`** holds the singular / non-plural messages.
- **The file *stem* encodes the message data.** `pf-other.json` → `{"pf": "other"}`;
  `ctx-menu.json` → `{"ctx": "menu"}`; combine with `_`: `pf-other_ctx-menu.json`.
- Every value is a **list**, indexed by the locale map.

```python
# fluid/i18n/__init__.py
from pathlib import Path
from webfluid.extensions.babel.utils import translation_resolver

translations = translation_resolver(
    Path(__file__).parent, { "en": 0, "de": 1 }
)
```

```python
# main.py or fluid/config.py
from webfluid.core.ext import babel
from fluid.i18n import translations

babel.update_translations("messages", translations)
```

{{ rule("update_translations must run before fluid.mix(). The calls are queued and flushed by a
    startup hook; the store rejects updates once the server is up. Call it from the factory, from
    an Additive's before_enable, or at import time of a module the factory imports.") }}

`"messages"` is the default domain. `BABEL_DISABLE_AUTOUPDATE = True` makes every
`update_translations` call a no-op and reads whatever the database already holds — useful once a
catalog is stable.

### `.po` fallback catalogs

```bash
wf babel extract    # writes messages.pot, inits/updates translations/<locale>/…
wf babel compile    # .po -> .mo
```

Extraction scans your project **and** the framework templates. `wf create project --babel-fallback`
runs both for you.

## Domains

A domain is a named catalog. The default is `Domain()` reading `<project_root>/translations`.

```python
babel.register_domain("shop")                       # translations/ of the project
babel.register_domain("portal", package_path)       # <package_path>/translations
babel.current_domain                                # the active Domain object

@babel.domain_context("shop")
async def handler(...): ...                         # everything inside resolves in "shop"
```

`register_domain` raises `FrameworkException` on a duplicate name.

### The escalation chain

A lookup walks, in order, until a domain answers with something **different from the input**:

1. the current domain (from `domain_context`, else the default domain),
2. the default domain,
3. a domain literally named `__fallback__`, if registered,
4. the framework's own domain (`fluid`).

If none answers, the source string is returned unchanged.

{{ bug("Step 'answers with something different from the input' is literal: a deliberate translation
    equal to its source is read as a miss and the next domain answers instead. This is the reason
    for the symbolic-key rule above.") }}

`I18nKey` carries a `(key, domain)` unique constraint as of this release, so two domains can
translate the same source string differently. Beta 1 had a global unique index on `key` — upgrading
needs a migration.

## Locale and timezone selection

Default resolution order, each step skipped when it does not parse:

**Locale:** `?lang=` query parameter → `lang` cookie → `Accept-Language` (best match against
`BABEL_SUPPORTED_LOCALES`) → `BABEL_DEFAULT_LOCALE`.

**Timezone:** `tz` cookie → `X-Timezone` header → `BABEL_DEFAULT_TIMEZONE`.

Both are resolved once per request and cached on the `FluidContext` (`cached_or`), so a page with
two hundred translated strings parses `Accept-Language` once.

```python
@register_config(10)
class Config:
    BABEL_DEFAULT_LOCALE = "en"
    BABEL_DEFAULT_TIMEZONE = "UTC"
    BABEL_SUPPORTED_LOCALES = ["en", "de"]
```

{{ info("Every step is treated as untrusted input. ?lang=xx, an unknown cookie or a malformed header
    is skipped, not raised — the chain always terminates at your configured default. Beta 2 also
    changed parse_best_match: a request with no Accept-Language header now falls through to
    BABEL_DEFAULT_LOCALE instead of picking the first entry of BABEL_SUPPORTED_LOCALES.") }}

### Custom selectors and forcing

```python
from webfluid.core.ext import babel
from webfluid.core.context import FluidContext


@babel.locale_selector
def select_locale():
    ctx = FluidContext.try_current()
    user = ctx.request.session.get("user") if ctx and ctx.request else None
    return user["locale"] if user else babel.default_locale
```

A registered selector **always wins** over the request chain and is called on **every** lookup —
there is no caching around it. Keep it cheap.

```python
with babel.force(locale="de", timezone="Europe/Berlin"):
    subject = babel.gettext("WELCOME_SUBJECT")

async with babel.aforce(locale="de"):
    subject = await babel.agettext("WELCOME_SUBJECT")
```

`force`/`aforce` push a `SelectorContext`, which outranks a registered selector for the duration of
the block. This is the correct way to render mail or a PDF in a recipient's language.

## Formatting

Nine Jinja filters, all locale-aware (and timezone-aware where relevant):

{% raw %}
```html
<p>{{ model.created_at|datetimeformat }}</p>
<p>{{ model.created_at|dateformat('full') }}</p>
<p>{{ model.created_at|timeformat }}</p>
<p>{{ model.created_at|timedeltaformat }}</p>
<p>{{ 1234.5|numberformat }}</p>
<p>{{ 1234.5|decimalformat }}</p>
<p>{{ 19.99|currencyformat('EUR') }}</p>
<p>{{ 0.75|percentformat }}</p>
<p>{{ 1234.5|scientificformat }}</p>
```
{% endraw %}

The same functions live in `webfluid.extensions.babel.utils` for Python code:

```python
from webfluid.extensions.babel.utils import (
    format_date, format_datetime, format_currency,
    to_user_timezone, to_utc
)

local = to_user_timezone(model.created_at)   # naive/aware in -> active zone out
label = format_date(local, fmt="full")       # keyword is fmt
stored = to_utc(user_input)                  # naive local in -> naive UTC out
```

{{ warning("Two breaking changes in this release. format_date's keyword used to be misspelled ftm
    and is now fmt, like every other formatter. And to_utc used to return
    dt.replace(tzinfo=None) — keeping the wall clock and throwing the instant away, so a Berlin
    12:00+02:00 came back as a naive 12:00 that every consumer read as UTC, two hours off. It
    converts to UTC first now, and reads a naive input as user-local, which makes it the true
    inverse of to_user_timezone. If you relied on the old behaviour to strip a tzinfo, call
    dt.replace(tzinfo=None) yourself.") }}

{{ rule("Store UTC, render local. to_user_timezone on the way out, to_utc on the way in. Use
    server_default=func.now() on timestamp columns and let the database write UTC.") }}

## In Python code

```python
from webfluid.core.ext import babel

subject = babel.gettext("WELCOME_SUBJECT")                 # sync
subject = await babel.agettext("WELCOME_SUBJECT")          # async — prefer this in async code
label = babel.lazy_gettext("MENU_HOME")                    # module-level constant
```

{{ bug("A key explicitly opted out of the cache is read through a synchronous session on the gettext
    path, which blocks the event loop. agettext is the non-blocking alternative; the callables
    installed into Jinja stay synchronous on purpose. Keep uncached keys off hot paths.") }}

`I18nMessage` exposes `uncache` / `recache` helpers for large or rarely used strings — the runtime
cache is not optimised for very large catalogs yet.

## On the client

With `BABEL_CONFIGURE_SOCKET` on, `/ws/i18n` serves the same catalog and `i18n.js` is injected as a
page source. The client mirrors the server API (`_`, `_n`, `_p`, `_np`) and caches the active
locale in `localStorage`.

## In an Additive

An Additive ships its catalog exactly like the main app, from `before_enable`:

```python
@additive.before_enable
async def before_enable(fluid):
    from webfluid.core.constants import EXT_BABEL
    if EXT_BABEL:
        from webfluid.core.ext import babel
        from .i18n import translations
        babel.update_translations("messages", translations)
```

Guard on `EXT_BABEL` so the Additive still loads in an app without it. Register your own domain
instead of writing into `"messages"` when the vocabulary is genuinely yours and should not leak into
the host app's catalog.

## Config reference

| Key                        | Default                                                         |
|----------------------------|-----------------------------------------------------------------|
| `BABEL_DEFAULT_LOCALE`     | `"en"`                                                          |
| `BABEL_DEFAULT_TIMEZONE`   | `"UTC"`                                                         |
| `BABEL_SUPPORTED_LOCALES`  | `["en"]`                                                        |
| `BABEL_DATE_FORMATS`       | `{"time": "medium", "date": "medium", "datetime": "medium", …}` |
| `BABEL_CONFIGURE_JINJA`    | `True`                                                          |
| `BABEL_CONFIGURE_SOCKET`   | `True`                                                          |
| `BABEL_DATABASE_BIND`      | `None`                                                          |
| `BABEL_DISABLE_AUTOUPDATE` | `False`                                                         |

## Next

- [`ext/security.md`]({{ base }}ext/security.md) — the next battery.
- [`utils/runtime.md`]({{ base }}utils/runtime.md) — `FluidContext.cached_or`, which the locale
  cache is built on.
{% endblock %}
