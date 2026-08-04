{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}wf create{% endblock %}
{% block doc_section %}CLI{% endblock %}

{% block summary %}
Three scaffolders: `project` writes a whole opinionated project, `app` writes an app config
interactively, `additive` writes a feature module. Everything the other pages describe by hand is
what these produce.
{% endblock %}

{% block body %}
## `wf create project <name>`

```bash
wf create project myapp
wf create project myapp --skip-frontend        # -sf: no Node, no htmx/Alpine download, no package.json
wf create project myapp --skip-defaults        # -sd: no fluid/ structure, no .gitignore
wf create project myapp --babel-fallback       # -bf: also extract + compile .po catalogs
```

Refuses to run if the target exists and is non-empty.

### What it writes

```text
myapp/
├── main.py                  # prepare_fluid(), includes the routers
├── package.json             # npm workspace           (unless -sf)
├── vite.config.js           # the orchestrator         (unless -sf)
├── .gitignore
├── additives/
└── fluid/
    ├── config.py            # @register_config Config(MyConfig)
    ├── api/
    │   ├── __init__.py      # api_router, prefix /api
    │   ├── health.py        # a ready handler
    │   └── v1/__init__.py   # v1 router, prefix /v1
    ├── app/                 # HTML routes — only for htmx / none
    │   ├── __init__.py      # app_router (HTMLResponse)
    │   └── index.py
    ├── frontend/            # Vite workspace — only for type vite
    ├── models/  schemas/  services/  events/  utils/
    ├── static/
    │   ├── css/tailwind_raw.css
    │   ├── img/
    │   └── js/
    └── templates/
        └── index.html       # extends fluid_base.html
```

The frontend answer changes two things:

| Answer          | Effect                                                                                                                                                                                          |
|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `vite`          | Creates `fluid/frontend` from a create-vite template, **removes `fluid/app`** (the Vite index owns `/`, unless you answered no to `register_index`), and `main.py` includes only the API router |
| `htmx` / `none` | Keeps `fluid/app` with a ready `index.html`, and `main.py` includes both routers                                                                                                                |

### The generated config

```python
# fluid/config.py
from webfluid.core.config import register_config

# The MyConfig class is our convention for developing public git repos.
try: from fluid._my_config import MyConfig
except ImportError:
    class MyConfig: pass


@register_config(10)
class Config(MyConfig):
    APP_CONFIG = {
        "title": "myapp",
        "version": "1.0.0"
    }
    APP_FRONTEND = { "type": "htmx", "alpine": True }
```

`fluid/_my_config.py` is in the generated `.gitignore`. Shared settings live in `config.py` and go
into git; anything local or private lives in `_my_config.py` and never does. The config builder walks
the MRO, so a key only `MyConfig` defines is picked up as if written in `Config`, and a key in both
belongs to `Config`. A clone without the file still starts.

{{ rule("Adopt this pattern in every project. It is the only mechanism the framework offers for
    keeping non-secret local overrides out of a public repository, and it costs three lines.") }}

### The generated `.gitignore`

Uses a custom `[folders]` / `[files]` section header format:

```text
[folders]
.vscode/  .idea/  .venv/  __pycache__/  node_modules/
app_configs/  app_services/  additives/  migrate/
translations/  dist/  logs/

[files]
messages.pot  tailwind.css  _my_config.py  package-lock.json  *.db
```

{{ warning("additives/ and app_configs/ are gitignored by default. That is deliberate — Additives are
    installed artefacts and app configs carry secrets — but it means git status shows nothing after
    you edit an Additive in place. Verify those changes by reading files or compiling them, not by
    git status. If an Additive is genuinely part of this repository, remove that line or track it as
    a submodule.") }}

## `wf create app <name>`

```bash
wf create app prod
wf create app prod --secret-length 64        # -sl, default 32 (bytes of token_hex)
```

Interactive. It:

1. generates `SECRET_KEY = token_hex(32)`,
2. asks which `EXT_*` extensions to enable, and writes **all eight** with `1`/`0`,
3. asks which `WF_*` features to enable, and writes **all six**,
4. discovers Additives in `additives/`, asks which to enable, and runs each selected one's
   `configure()` so its own `setup` questions land in the file,
5. writes `SECURITY_SECRET = token_hex(32)` if `EXT_SECURITY` was selected,
6. asks for `DATABASE_URI` and `REDIS_URI`,
7. asks for `MAIL_USERNAME` / `MAIL_PASSWORD` if `EXT_MAIL` was selected.

Refuses to overwrite an existing config file.

{{ bug("Everything else the scaffolders write is explicitly UTF-8; app_configs/<name>.ini is the one
    file still written — and read back by wf run — in the interpreter's locale encoding. That is
    symmetric on one machine and breaks the moment a config carrying a non-ASCII value (a mail
    username, a password with an umlaut) is generated on a Windows console and read elsewhere. Keep
    those values ASCII, or point at them through a *_FILE key, which is resolved from disk.") }}

## `wf create additive <id>`

```bash
wf create additive portal
```

Interactive. It asks for version, name, description, author, whether it is a base or extends one,
the frontend type, and the required extensions — then writes:

```text
additives/portal/
├── __init__.py        # Additive(...), before_enable registering api v1 (+ index)
├── manifest.json      # everything you answered
├── .gitignore
├── api/{__init__,health}.py, api/v1/__init__.py
├── app/{__init__,index}.py      # dropped for a vite frontend
├── models/ schemas/ services/ events/ utils/
├── static/css/tailwind_raw.css, static/img, static/js
├── templates/index.html         # unless a vite frontend
└── frontend/                    # for a vite frontend
```

Notes on what it decides for you:

- The **id is sanitised** through `safe_string()`; if that changes it, you are asked to confirm.
  `fluid` is rejected outright.
- `requires.wf` is pinned to `>={{ version }}` — the framework version you are running.
- Extending a base adds `import_base("<id>")` to `__init__.py` **and** the dependency to
  `requires.additives`.
- A Vite frontend runs `npm install -w additives/<id>/frontend` for you.

The generated `.gitignore` also decides what ships: `wf ocean publish` builds the archive from the
working directory minus `.git`, `__pycache__`, `node_modules`, editor folders, compiled files **and**
everything the `.gitignore` excludes (nested ones included, negations honoured).

## Rules for agents

{{ rule("Prefer wf create project over hand-building the tree. The generated layout is what
    wf migrate, the Alembic env.py, the npm workspace glob and every example in these docs assume —
    a hand-rolled variation costs you those.") }}

{{ rule("The scaffolders are interactive and have no non-interactive mode. Without a TTY, run
    wf create project <name> --skip-frontend (which asks nothing) and write app_configs/<name>.ini
    yourself. The .ini format is in config/app-config.md.") }}

{{ rule("Never regenerate over an existing project. All three scaffolders refuse a non-empty target,
    which is the correct behaviour — to add something, write the file by hand following the shapes on
    these pages.") }}

## Next

- [`cli/run.md`]({{ base }}cli/run.md) — running what you just generated.
- [`config/app-config.md`]({{ base }}config/app-config.md) — the file `wf create app` writes.
- [`additives/intro.md`]({{ base }}additives/intro.md) — what `wf create additive` produces.
{% endblock %}
