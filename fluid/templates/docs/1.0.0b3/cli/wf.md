{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}The wf CLI{% endblock %}
{% block doc_section %}CLI{% endblock %}

{% block summary %}
`wf` is the entry point for everything: scaffolding, running, migrating, translating, packaging. It
is a Typer app with five built-in command groups plus one per installed extension.
{% endblock %}

{% block body %}
## The command tree

```text
wf
├── create      Scaffold projects, apps and additives
│   ├── project <name> [-sd] [-sf] [-bf]
│   ├── app <name> [-sl N]
│   └── additive <id>
├── ocean       Search, install and publish Ocean packages
│   ├── login / logout
│   ├── search [query] [-a|-e|-b] [--oss-only|--paid-only]
│   ├── install [-a id[==version]] [-e id] [-b bundle_id]
│   │           [--alpha|--beta|--rc] [-p|--pre] [-ps|--prefer-stable]
│   └── publish
├── run <app> [-h host] [-p port] [-l level] [-d] [-i]
├── node        Forward a command to the bundled Node runtime
├── tailwind    Forward a command to the Tailwind CLI
├── migrate     (extension) Alembic wrapper
│   ├── init <app>
│   ├── revision <app> [-a] [-m msg]
│   ├── upgrade <app>
│   └── downgrade <app> [-r rev]
└── babel       (extension) Translation catalogs
    ├── extract
    └── compile
```

The first five are core. `migrate` and `babel` are **extension CLIs**: on every invocation the CLI
walks `entry_points(group="webfluid.extensions")` and calls `cls.cli_entry(app, ep.name)`, which
mounts each extension's `_cli` Typer app under its entry-point name.

That is the same mechanism your own extension uses — see [`ext/base.md`]({{ base }}ext/base.md). An
entry point whose target is not a `FluidExtension` subclass is skipped with a yellow warning.

## Where each command runs

| Command                       | Working directory it expects | What it touches                                  |
|-------------------------------|------------------------------|--------------------------------------------------|
| `wf create project <name>`    | Anywhere                     | Creates `<name>/`                                |
| `wf create app <name>`        | Project root                 | Writes `app_configs/<name>.ini`                  |
| `wf create additive <id>`     | Project root                 | Writes `additives/<id>/`                         |
| `wf run <app>`                | Project root                 | Needs `main.py` **and** `app_configs/<app>.ini`  |
| `wf migrate …`                | Project root                 | Reads `app_configs/<app>.ini`, writes `migrate/` |
| `wf babel …`                  | Project root                 | Writes `messages.pot`, `translations/`           |
| `wf ocean install`            | Project root                 | Writes `additives/`, `extensions/`               |
| `wf ocean publish`            | The package directory        | Reads `manifest.json` or `pyproject.toml`        |
| `wf node …` / `wf tailwind …` | Anywhere                     | Forwards through                                 |

{{ rule("Every command except wf create project and wf ocean publish expects the project root — the
    directory containing main.py, fluid/ and app_configs/. cd there first.") }}

## Passthrough commands

```bash
wf node node --version
wf node npm --version
wf node npm install
wf node npm run build --workspaces

wf tailwind -- --help
```

Both forward the underlying tool's output verbatim. `wf node` uses the bundled standalone Node
(downloaded on first use, cached in `webfluid/surface/dist`) or a system Node when one is present.
`wf tailwind` needs the `--` separator so Typer stops parsing the following flags.

{{ rule("In a WebFluid project, run npm through wf node npm rather than a global npm. It guarantees
    the same runtime the framework will use at boot, and it works on machines that have no Node
    installed at all.") }}

## Exit behaviour

Commands raise `typer.Exit(1)` on a precondition failure with a red message — a missing app config,
a missing `main.py`, a non-empty target directory, debug mode on port 5173. `wf migrate` shells out
to Alembic with `check=True`, so a failed migration exits non-zero.

## Agent checklist

Reasonable defaults when driving the CLI non-interactively:

| Goal                                           | Command                                                             |
|------------------------------------------------|---------------------------------------------------------------------|
| New project, no interactive frontend questions | `wf create project myapp --skip-frontend`                           |
| New project, full scaffold                     | `wf create project myapp` (asks about the frontend)                 |
| Run for development                            | `wf run app -d`                                                     |
| Run on another port                            | `wf run app -p 9000`                                                |
| Verbose run                                    | `wf run app -d -l debug`                                            |
| Migrate after a model change                   | `wf migrate revision app -a -m "..."` then `wf migrate upgrade app` |

{{ warning("wf create app and wf create additive are interactive — they prompt for extensions,
    features, database URIs, frontend type and more. There is no non-interactive flag. When you need
    a config file without a TTY, write the .ini yourself; the format is in config/app-config.md.") }}

## Next

- [`cli/create.md`]({{ base }}cli/create.md) — the scaffolders in detail.
- [`cli/run.md`]({{ base }}cli/run.md) — what `wf run` arranges.
- [`cli/ocean.md`]({{ base }}cli/ocean.md) — the package hub.
{% endblock %}
