# WebFluid-Web

The shared website foundation for the WebFluid platform.

WebFluid-Web is the codebase behind the public WebFluid web presence. It is a
single WebFluid project that is deployed several times, each time as a different
application:

- **Landing Page** — <https://webfluid.dev>
- **Documentation** — <https://docs.webfluid.dev>
- **Ocean** — <https://ocean.webfluid.dev>

All three share this one codebase. That shared foundation — the base layout, the
styling, the footer, the localisation, and the common assets — is what
WebFluid-Web provides.

---

## Why it exists

WebFluid exists so that applications are assembled from maintained building blocks instead of
being regenerated from scratch every time — by people or by coding agents. WebFluid-Web is that
idea applied to the platform itself: three products, one codebase, and almost none of their
features written here. Accounts, payments, admin screens, tokens, integrity checks and the
marketplace come from Additives that every other WebFluid project can install the same way; this
repository adds only what is genuinely specific to the website.

The landing page, the documentation, and the Ocean marketplace are separate
products with very different needs, but they are all part of the same platform
and should look and feel like it. Maintaining three independent sites would mean
duplicating the header, the footer, the theme, the fonts, and the translation
setup three times over.

Instead, WebFluid-Web keeps them together. A single project defines a common
website base, and each public site is expressed as an **app configuration** on
top of it. The sites stay visually and structurally consistent because they
literally share the same templates and stylesheet, while still being able to run,
scale, and deploy independently.

It also serves as the reference application for WebFluid itself: the platform's
own website is built with the framework it promotes — and it is where the Additives of
the users ecosystem are developed, reviewed and exercised together before they are
published to Ocean.

---

## How it fits together

WebFluid lets one project run as multiple apps, selected at launch. WebFluid-Web
uses that directly. Each site is an `.ini` file under `app_configs/`, and the
entrypoint decides what to mount based on which app is running:

| App       | Config                  | What it serves                    | Enabled features                                                                        |
|-----------|-------------------------|-----------------------------------|-----------------------------------------------------------------------------------------|
| **home**  | `app_configs/home.ini`  | The marketing landing page.       | Database, Babel, theming, Tailwind, page processing.                                    |
| **docs**  | `app_configs/docs.ini`  | The versioned documentation site. | Theming, Tailwind, page processing (kept deliberately lean — no database or additives). |
| **ocean** | `app_configs/ocean.ini` | The full Ocean application.       | Every extension, plus the complete additive stack.                                      |

```bash
wf run home     # → webfluid.dev
wf run docs     # → docs.webfluid.dev
wf run ocean    # → ocean.webfluid.dev
```

### The shared base

Everything the three sites have in common lives in `fluid/`:

- `templates/base.html` and the shared partials (navigation, footer).
- `static/css/` — the Tailwind stylesheet used across all sites.
- `i18n/` — the base translations.
- The web-wide fonts and global settings applied in the entrypoint.

### The Landing Page

A single rendered page (`fluid/app/index.py`, `fluid/templates/index.html`)
introducing WebFluid, styled with the shared base.

### The Documentation

A set of **versioned**, server-rendered HTML pages under
`fluid/templates/docs/`, organised per release (for example `1.0.0a1` and
`1.0.0a2`). The docs app resolves the requested version, redirects `/` to the
latest release, and serves the matching template tree. It runs without a database
or any additives, which keeps it lightweight and easy to deploy.

### Ocean

The Ocean app is the full application. On top of the shared base it enables the
whole additive stack — authentication, user accounts, payments, and the Ocean
marketplace itself. WebFluid-Web renders Ocean's public-facing shell pages
(discovery, terms, licensing) so they inherit the site's look and feel, while the
marketplace behaviour behind them is provided by the **`ocean`** additive and its
dependencies.

---

## Project layout

```
wf-site/
├── main.py             # entrypoint: imports prepare_fluid() and runs it
├── app_configs/        # per-app .ini configurations (secrets, switches, [additives])
├── fluid/              # the shared website base
│   ├── __init__.py     # prepare_fluid(): builds the app for home / docs / ocean
│   ├── app/            # route handlers (index, docs, ocean)
│   ├── templates/      # base layout, landing page, docs, ocean pages
│   ├── static/         # shared CSS (Tailwind) and JS
│   └── i18n/           # base translations
├── additives/          # additive packages, enabled by the ocean app
└── docker-compose.yml  # an example stack for the three services
```

The `additives/` directory holds the installable feature modules the Ocean app
depends on. Each additive is its own repository with a human-facing `README.md` and
`CHANGELOG.md`, and an agent-facing `CONTRACT.md` and `.agents/SKILL.md`. Several also
carry a Flutter SDK in `flutter_sdk/`; `additives/example` is the app that runs all of
those SDKs together.

---

## Development notes

This is a standard WebFluid project, so the usual workflow applies:

- Run a site locally with `wf run <app>` (add `-d` for debug, `-i` for the
  interactive control menu). The project targets WebFluid `1.0.0rc1`: the app
  factory lives in `fluid/__init__.py`, so `wf migrate` builds the real application.
- After editing an Additive's `CONTRACT.md` or `.agents/` files, run
  `wf agents index` inside `additives/` to refresh their line-range indexes.
- The framework's central communication interface is `EventBus`. Python consumers
  use the shared `events` instance from `webfluid.core.ext`; browser consumers use
  `new window.wf.ext.events.EventBus()`. Rebuild frontend assets after updating the
  framework so every active consumer uses the renamed constructor. Versioned
  documentation preserves the API of its original release.
- Styling changes go into `fluid/static/css/tailwind_raw.css` and are compiled to
  `tailwind.css` with the bundled Tailwind tooling.
- `docker-compose.yml` is an example stack for a Swarm behind Traefik: the three
  services mount the checkout as `/app` and start the same image with a different
  app name; `ocean` builds the `Dockerfile`, which adds the Python packages its
  additives need. Replace the example hostnames with your own.

For the framework itself, see the [WebFluid repository](https://github.com/GrowVolution/WebFluid)
and the [documentation](https://docs.webfluid.dev).

---

## License

WebFluid-Web is released under the **GNU General Public License v3 (GPL v3)**.
This is the GPL notice referenced in the site footer, and it covers the shared
website foundation used by Ocean, the Landing Page, and the Documentation.

The additives enabled by the Ocean app are distributed separately and under their
own licenses. See the [Ocean Licensing page](https://ocean.webfluid.dev/licensing)
for the authoritative, per-component overview.

## Audit and deployment settings

The source audit and validation results are recorded in [AUDIT.md](AUDIT.md).
Fonts are served locally from `fluid/static/fonts/`, including their OFL license notices; visitors
no longer contact Google Fonts. Documentation routes reject traversal, hidden paths and Windows
path aliases before looking up a template.

`PROXY_TRUSTED_HOSTS` defaults to loopback (`127.0.0.1,::1`). For the example Traefik deployment,
set the actual ingress addresses/CIDRs in `fluid/_my_config.py`; trust only proxies allowed to
connect to the application. Do not use `*` on an application port reachable by untrusted clients.
The framework's request logger records paths only under `wf run -d` (`REQUEST_LOG_PATH`) and client
addresses or user agents only on request (`REQUEST_LOG_CLIENT`, `REQUEST_LOG_USER_AGENT`). Peer
operators must configure independent `PEERING_TRUSTED_REFERENCES` to endorse artifact provenance.
Old versioned documentation continues to describe its original release.

Install the npm workspace with `npm install` at the root; `package.json` keeps Vite on its patched
releases (`^8.3.5`). `constraints.txt` records Python security floors and is applied by the image
build; existing environments can apply it with `python -m pip install --upgrade -r constraints.txt`.

The alpha `users` package now defaults to the neutral application signature `dev.example.app`.
Set `USERS_MOBILE_SIGNATURES` explicitly to the deployed app identity before using app links.
