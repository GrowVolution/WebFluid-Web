{% set base = "/latest/" if version == "latest" else "/v/" ~ version ~ "/" %}
- [Overview]({{ base }}.md) — what WebFluid is, how to navigate these docs, release state and known bugs
- [Getting Started]({{ base }}get-started.md) — install, minimal app, the layout the framework expects

**Configuration**
- [App configs]({{ base }}config/app-config.md) — `app_configs/<app>.ini`, switches, `*_FILE` secrets, `[dev]`
- [Config classes]({{ base }}config/config-class.md) — `register_config`, `DefaultConfig`, every framework key

**Extensions**
- [Introduction]({{ base }}ext/base.md) — `FluidExtension`, entry points, `expand_fluid`
- [Scheduling]({{ base }}ext/scheduling.md) — APScheduler `AsyncIOScheduler`
- [SQLAlchemy]({{ base }}ext/sqlalchemy.md) — `Model`, executors, binds, sessions
- [Migrate]({{ base }}ext/migrate.md) — Alembic wrapper, `prepare_fluid`, single/multi-db
- [Mail]({{ base }}ext/mailman.md) — SMTP, sync/async, batching, attachments
- [Babel]({{ base }}ext/babel.md) — gettext, domains, locale selection, formatters
- [Security]({{ base }}ext/security.md) — users, gates, CSRF, tokens, OAuth, bearer grants
- [Events]({{ base }}ext/events.md) — signals, events, queries, browser socket
- [Cache]({{ base }}ext/cache.md) — redis / legacy backends
- [JWTManager]({{ base }}ext/jwt.md) — encode/decode, rotation, revocation

**Frontend (surface)**
- [Introduction]({{ base }}surface/tooling.md) — feature switches, `fluid_base.html`, Tailwind, themes
- [Integration]({{ base }}surface/frontend.md) — `APP_FRONTEND`, htmx, Vite workspaces
- [Template resolution]({{ base }}surface/jinja.md) — loader order, namespaces, overriding

**Additives**
- [Introduction]({{ base }}additives/intro.md) — manifest, routers, enabling
- [Base Additives]({{ base }}additives/base.md) — `type: base`, `import_base`, extension semantics
- [Interaction between]({{ base }}additives/contract.md) — events/queries as contracts, requirements, packaging

**Framework utility**
- [Lifecycle]({{ base }}utils/lifecycle.md) — `mix()`, startup/shutdown hooks, graceful stop
- [Runtime]({{ base }}utils/runtime.md) — `FluidContext`, request hooks, themes, proxy, rate limits
- [Logging]({{ base }}utils/logging.md) — the log factory, levels, files, additive attribution

**CLI**
- [Introduction]({{ base }}cli/wf.md) — command tree, extension CLIs
- [Create]({{ base }}cli/create.md) — `wf create project/app/additive`
- [Run]({{ base }}cli/run.md) — `wf run`, flags, debug and interactive mode
- [Ocean]({{ base }}cli/ocean.md) — search, install, publish

**Reference**
- [Overview]({{ base }}ref.md) — package layout, stability contract
- [Core]({{ base }}ref/core.md) — `Fluid`, config, context, `core.ext`, constants
- [Extensions]({{ base }}ref/extensions.md) — the battery API surface
- [Surface]({{ base }}ref/surface.md) — `Frontend`, Node and Tailwind tooling
- [Additives]({{ base }}ref/additives.md) — `Additive`, `Router`, `Manifest`, registry helpers
- [Utils]({{ base }}ref/utils.md) — helpers, logging, exceptions
