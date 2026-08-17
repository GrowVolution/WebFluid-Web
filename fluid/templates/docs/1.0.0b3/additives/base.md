{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Base Additives{% endblock %}
{% block doc_section %}Additives{% endblock %}

{% block summary %}
A base Additive is a foundation meant to be **extended**, not run. It is declared with
`"type": "base"`, may not carry a frontend, is never listed in `[additives]`, and is folded into
exactly one default Additive at enable time.
{% endblock %}

{% block body %}
## Declaring one

```json
// additives/core/manifest.json
{
  "id": "core",
  "version": "1.0.0",
  "type": "base",
  "frontend": { "type": "none" },
  "name": "Core"
}
```

`Manifest.validated_data` raises `ManifestError("Base additives cannot have a frontend.")` if
`frontend.type` is anything but `"none"`.

Otherwise a base looks like any other Additive — routers, templates, hooks, models, services:

```python
# additives/core/__init__.py
from webfluid import Additive

additive = Additive(__name__, required_extensions=["sqlalchemy"])


@additive.before_enable
def before_enable(fluid):
    from .app import about
    additive.app.get("/about")(about)
```

Note the router prefixes differ: a base's `api`, `app` and `ws` routers are created **without**
prefixes, because the child's routers supply them.

## Extending one

```python
# additives/portal/__init__.py
from webfluid import Additive
from webfluid.utils.additives import import_base

additive = Additive(
    __name__,
    import_base("core"),
    required_extensions=["events"]
)


@additive.before_enable
def before_enable(fluid):
    from .app import index
    additive.app.get("/")(index)
```

{{ rule("Resolve the base with import_base(\"<id>\"), never with a direct Python import. import_base
    walks the installed bases in additives/, matches the manifest id, imports the package and
    verifies that its additive is actually a base. A direct import hardcodes the directory name and
    breaks the moment the base is installed under a different one.") }}

`import_base` returns `None` when the base is not installed, and `Additive(__name__, None)` is a
plain Additive with no base — so declare the dependency in the manifest so enabling fails loudly:

```json
"requires": { "additives": { "core": ">=1.0.0" } }
```

## What extension does

When the child is enabled, `_enable` folds the base into it, in this order:

1. Both manifests' requirements are checked (the child's first, then the base's).
2. The base's `api`, `app` and `ws` routers are **included into the child's**, so every base route
   answers under the child's prefix — `/about` becomes `/portal/about`.
3. `base.parent = child`; `base.prefix = child.prefix`; `base.jinja_context["id"] = child.id`.
4. The base's `required_extensions` were already merged into the child's list in the constructor.
5. The base's templates join the child's loader as a `ChoiceLoader` — child first, base second, both
   under the **child's** id namespace.
6. The base's `before_enable` hooks run after the child's; its `after_enable` hooks after the
   child's.

Consequences for the code you write:

- The base's `additive.render("x.html")` forwards to the parent, so a template the child overrides
  wins. That makes a base's templates genuinely overridable per project.
- `unique_name()` on the base delegates to the parent, so contracts a base registers are scoped to
  the **child's** id. Two projects extending the same base do not collide.
- Reverse URLs line up: `url_for` inside base templates resolves through the child's id.

## Constraints

| Rule                                                         | Enforced by                                                                    |
|--------------------------------------------------------------|--------------------------------------------------------------------------------|
| A base may not have a frontend                               | `ManifestError` at manifest validation                                         |
| A base may not extend another base                           | `AdditiveException("Base additives cannot extend other additives.")`           |
| A default Additive may only extend a **base**                | `AdditiveException("Default additives can only extend base additives.")`       |
| A base may not be enabled directly                           | `AdditiveException("Base additives are not allowed be enabled.")`              |
| A base may be extended by **exactly one** Additive at a time | `AdditiveException("Base additive '<x>' has already been extended by '<y>'.")` |

{{ warning("The one-parent rule is the constraint that surprises people. If two enabled Additives
    both extend the same base, enabling the second one fails. A base is a foundation for a single
    feature, not a shared service — if you need a shared service, write an extension.") }}

{{ info("Only the child is switched on in [additives]. The base rides along. Putting a base id into
    the config section does nothing useful and will fail at check_enable.") }}

## When to reach for one

| Situation                                                                                                         | Use                                                                        |
|-------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| A polished foundation others extend with their own routes and frontend (admin shell, auth flow, billing skeleton) | Base Additive                                                              |
| Shared models several Additives read                                                                              | Base Additive, if exactly one of them owns it — otherwise a query contract |
| A service several Additives call                                                                                  | **Extension** (`webfluid.core.ext`)                                        |
| Common helper functions                                                                                           | A plain Python package, or an extension                                    |
| A feature that stands on its own                                                                                  | Plain default Additive                                                     |

The distribution story is the real motivation: publish a base to the Ocean, and each project extends
it with project-specific routes and a project-specific frontend without forking it.

## Discovery helpers

```python
from webfluid.utils.additives import installed_additives, installed_bases, import_base

installed_additives(additive_root)     # [(id, Version, dirname), ...] for type "default"
installed_bases(additive_root)         # [(id, Version, dirname), ...] for type "base"
import_base("core")                    # the Additive instance, or None
```

Results are cached per package path; pass `cache=False` for a fresh scan.

## Next

- [`additives/contract.md`]({{ base }}additives/contract.md) — talking without imports, requirements
  and packaging.
- [`cli/ocean.md`]({{ base }}cli/ocean.md) — publishing a base.
{% endblock %}
