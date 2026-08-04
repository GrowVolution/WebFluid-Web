# WebFluid Documentation

> WebFluid is a fullstack Python application runtime built on FastAPI: an app class with opt-in
> batteries (database, i18n, auth, mail, cache, events, JWT, scheduler), a module system called
> Additives, a managed frontend layer, and the `wf` CLI. This is the documentation for
> {{ version }} ({{ stage }}, {{ date }}).

Every page below is Markdown written for AI agents: exact signatures, exact defaults, the rules that
keep generated code correct, and the known defects of this release. Each one is also available as
HTML by dropping the `.md` suffix. `Accept: text/markdown` on any documentation URL returns the
Markdown variant without the suffix.

The whole corpus in one document: {{ docs }}/llms-full.txt

## Start here

- [Overview]({{ docs }}{{ base }}.md): what WebFluid is, how to navigate these docs, the rules that apply everywhere, the release state and the complete known-issues list. Read this first.
- [Getting Started]({{ docs }}{{ base }}get-started.md): install, the minimum viable app, what `Fluid(import_name)` does in constructor order, and the project layout every other page assumes.

## Configuration

- [App configs]({{ docs }}{{ base }}config/app-config.md): the `app_configs/<name>.ini` format, the `EXT_*` and `WF_*` switches, `*_FILE` secrets, the `[dev]` section, and what belongs here versus in a config class.
- [Config classes]({{ docs }}{{ base }}config/config-class.md): `register_config`, the merge order, the `MyConfig` convention, and the complete table of every framework config key with its default.

## Extensions (the batteries)

- [Introduction]({{ docs }}{{ base }}ext/base.md): `FluidExtension`, the `webfluid.extensions` entry point, `expand_fluid`, `Delegated`, and when to write an extension instead of an Additive.
- [Scheduling]({{ docs }}{{ base }}ext/scheduling.md): the APScheduler `AsyncIOScheduler` behind `EXT_SCHEDULING`, and the multi-process caveat.
- [SQLAlchemy]({{ docs }}{{ base }}ext/sqlalchemy.md): `db.Model`, sync and async executors, binds, driver-less URIs, what survives an executor block.
- [Migrate]({{ docs }}{{ base }}ext/migrate.md): the Alembic wrapper, `prepare_fluid()`, single- versus multi-database templates, what the migration environment sees.
- [Mail]({{ docs }}{{ base }}ext/mailman.md): SMTP sync and async, the body mapping, attachments, connection reuse, and the TLS defect on the sync path.
- [Babel]({{ docs }}{{ base }}ext/babel.md): gettext callables, the JSON-backed runtime translation store, domains and escalation, locale/timezone selection, the nine format filters.
- [Security]({{ docs }}{{ base }}ext/security.md): users, roles, permissions, argon2, the route-guard chain, CSRF, single-use tokens, OAuth, bearer grants, and the `raise_on_sql` relationships.
- [Events]({{ docs }}{{ base }}ext/events.md): signals, events and queries, the running-loop rule, browser push, and the best-effort delivery semantics.
- [Cache]({{ docs }}{{ base }}ext/cache.md): the redis and legacy backends, and what changes in your code between them.
- [JWTManager]({{ docs }}{{ base }}ext/jwt.md): encode/decode, the rotating key lifecycle, revocation via `jti`, audiences.

## Frontend (the surface)

- [Introduction]({{ docs }}{{ base }}surface/tooling.md): the `WF_*` feature switches, the shared template context, `fluid_base.html`, page sources, static mounts, Tailwind and themes.
- [Integration]({{ docs }}{{ base }}surface/frontend.md): `APP_FRONTEND`, the htmx path, Vite workspaces, development versus production serving.
- [Template resolution]({{ docs }}{{ base }}surface/jinja.md): the loader stack and its order, namespace prefixes, overriding framework templates, and what freezing buys.

## Additives (the module system)

- [Introduction]({{ docs }}{{ base }}additives/intro.md): the anatomy of an Additive, the manifest, the three routers, rendering, the scoped lifecycle, enabling.
- [Base Additives]({{ docs }}{{ base }}additives/base.md): `type: base`, `import_base`, what extension actually does, and the one-parent constraint.
- [Interaction between]({{ docs }}{{ base }}additives/contract.md): id-scoped events and queries instead of imports, manifest requirements, composed frontends, `install()` and `configure()`.

## Framework utility

- [Lifecycle]({{ docs }}{{ base }}utils/lifecycle.md): what `mix()` does step by step, hook arity and ordering, graceful shutdown, and why an external ASGI server does not work.
- [Runtime]({{ docs }}{{ base }}utils/runtime.md): `FluidContext`, `cached_or`, the request hooks and the cost of `after_request`, themes, reverse URLs, proxies, rate limits.
- [Logging]({{ docs }}{{ base }}utils/logging.md): the log factory, levels, the execution gate, log files, Additive attribution.

## CLI

- [Introduction]({{ docs }}{{ base }}cli/wf.md): the full command tree, how extension CLIs attach, and which directory each command expects.
- [Create]({{ docs }}{{ base }}cli/create.md): `wf create project` / `app` / `additive` and exactly what each writes.
- [Run]({{ docs }}{{ base }}cli/run.md): flags, the environment it builds, debug mode, interactive mode, signals and deployment.
- [Ocean]({{ docs }}{{ base }}cli/ocean.md): searching, installing and publishing packages.

## Reference

- [Overview]({{ docs }}{{ base }}ref.md): the import tree, top-level exports, the stability contract, where to import what.
- [Core]({{ docs }}{{ base }}ref/core.md): `Fluid`, `core.config`, `core.identity`, `core.context`, `core.ext`, `core.constants`, `version`.
- [Extensions]({{ docs }}{{ base }}ref/extensions.md): the API surface of `FluidExtension` and all eight batteries.
- [Surface]({{ docs }}{{ base }}ref/surface.md): `Frontend`, the frontend config block, the Node and Tailwind tooling.
- [Additives]({{ docs }}{{ base }}ref/additives.md): `Additive`, `Router`, `Manifest`, the registry helpers, and the exact enable sequence.
- [Utils]({{ docs }}{{ base }}ref/utils.md): helpers, versioning, proxies, the log factory, countries, the Ocean client, the exception hierarchy.

## Optional

- [Repository](https://github.com/GrowVolution/WebFluid): source, issues and the changelog.
- [Sitemap]({{ docs }}/sitemap): every documentation URL, all versions.
