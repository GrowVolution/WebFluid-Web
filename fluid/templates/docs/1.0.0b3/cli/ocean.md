{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}wf ocean{% endblock %}
{% block doc_section %}CLI{% endblock %}

{% block summary %}
The Ocean is WebFluid's package hub. `wf ocean` searches it, installs Additives and extensions into a
project, and publishes your own. Browsing and installing open-source packages works anonymously;
anything account-bound needs a token.
{% endblock %}

{% block body %}
## Authentication

```bash
wf ocean login      # paste your Ocean token when prompted
wf ocean logout     # forget the stored token
```

The token is validated and stored at `~/.wf-ocean`. Needed for publishing and for paid packages you
own; not needed for searching or installing open-source ones.

## Search

```bash
wf ocean search auth                            # additives, extensions and bundles
wf ocean search dashboard --additives --oss-only
wf ocean search -e stripe                       # extensions only
```

| Flag           | Short | Effect           |
|----------------|-------|------------------|
| `--additives`  | `-a`  | Additives only   |
| `--extensions` | `-e`  | Extensions only  |
| `--bundles`    | `-b`  | Bundles only     |
| `--oss-only`   |       | Open-source only |
| `--paid-only`  |       | Paid only        |

Packages print as a table with id, name, description, version, release date and price. Bundles get
their own table whose **first column is the bundle id**, zero-padded to six digits — that is the
value `install --bundle` takes. A bundle is a priced set of packages rather than a package.

## Install

```bash
wf ocean install -a portal -e stripe        # one additive and one extension
wf ocean install -a portal==1.2.0           # pinned
wf ocean install -b 000123                  # everything in a bundle
wf ocean install -b 123 -a portal           # a bundle plus an extra package
wf ocean install -a portal --alpha          # the latest alpha
wf ocean install -a portal -p               # the latest prerelease, whatever the channel
wf ocean install -a portal -ps              # stable if there is one, else the latest prerelease
```

| Flag                          | Short | Repeatable | Target                                                                 |
|-------------------------------|-------|------------|------------------------------------------------------------------------|
| `--additive`                  | `-a`  | yes        | `additives/<id>`                                                       |
| `--extension`                 | `-e`  | yes        | `extensions/<id>`, then `pip install -e`                               |
| `--bundle`                    | `-b`  | yes        | Expands to every package the bundle contains                           |
| `--alpha` / `--beta` / `--rc` |       |            | Switch the release channel; naming more than one picks the most mature |
| `--pre`                       | `-p`  |            | The highest prerelease of **any** channel                              |
| `--prefer-stable`             | `-ps` |            | The latest stable, falling back to a prerelease when there is none     |

`-a` and `-e` accept `id==version` for a pin. By default `install` resolves the latest **stable**
release.

### Bundles

`-b <id>` is exactly equivalent to naming every package the bundle contains, so bundles and single
packages mix freely:

- leading zeros are optional — `-b 123` and `-b 000123` are the same bundle;
- a package that appears twice (in two bundles, or in a bundle and behind an explicit `-a`) is
  installed **once** and reported as a duplicate in yellow;
- an explicit `id==version` pin **wins** over the bundle's unpinned entry;
- an unresolvable bundle id is reported and skipped; the rest of the install continues.

`Ocean.bundle(bundle_id)` is the client call behind it.

### Channel resolution

```text
--alpha/--beta/--rc   the latest release in that exact channel
--pre / -p            the latest release with ANY stage marker
--prefer-stable / -ps the latest stable; if none exists, fall back
```

`-ps` composes with an explicit channel: `-ps --beta` means "stable, else the latest beta". It also
makes `--pre` redundant, and the command says so in yellow rather than guessing. `--pre` next to an
explicit channel is likewise ignored with a warning.

**Anything already present is skipped rather than overwritten**, so re-running the command is safe.

After unpacking, each installed Additive runs its `install()` routine
([`additives/contract.md`]({{ base }}additives/contract.md)):

1. required Additives are resolved and pulled from the Ocean, recursively,
2. its `extract/` files land in your app — existing files are never overwritten,
3. its manifest `packages` are pip-installed.

Nothing is visited twice. One `wf ocean install -a portal` can therefore quietly bring in the base
it extends and the two Additives it talks to.

{{ info("Paid packages require you to be logged in and to own them (you purchase them on the Ocean).
    Because installing paid digital content starts its delivery, the CLI asks you to waive your right
    of withdrawal before downloading. Open-source packages skip that entirely.") }}

{{ rule("Run wf ocean install from the project root. It writes into additives/ and extensions/
    relative to the working directory.") }}

{{ rule("After installing an Additive, switch it on: add its id to the [additives] section of every
    app config that should load it, and make sure WF_ADDITIVES = 1. Installing does not enable.
    Then re-run the migration cycle if it brings models.") }}

## Publish

```bash
cd additives/portal
wf ocean publish
```

The package type is inferred from the working directory:

| File present     | Published as                       |
|------------------|------------------------------------|
| `manifest.json`  | Additive — id from the manifest    |
| `pyproject.toml` | Extension — id from `project.name` |

You must be logged in. Publish then walks you through:

1. **Maintainer** — your personal account or one of your organisations.
2. **Price** — extensions must carry one; Additives may be free.
3. **License** — if the package has none, it searches the hub's license catalog with you, asks for
   whatever placeholders the license needs (name, year) and applies it.

It builds an archive, uploads it with a SHA-256 checksum the hub verifies, and reports the published
id back.

### What ends up in the archive

Everything in the working directory **minus**:

- the obvious junk: `.git`, `__pycache__`, `node_modules`, editor folders, compiled files,
- everything your `.gitignore` excludes — **nested `.gitignore` files included, negations honoured**.

{{ rule("The .gitignore that wf create additive writes does double duty: it keeps the repository
    clean and it decides what ships. Check it before publishing. A secret that is gitignored is also
    not shipped; a build artefact that is not gitignored is.") }}

## Pointing at a different hub

```bash
export OCEAN_API=https://ocean.example.org/hub/api/v1
export OCEAN_AUTH=https://ocean.example.org/auth/api/v1
```

Defaults are the public Ocean at `ocean.webfluid.dev`. (`AUTH_API` was the alpha spelling of the
second variable and is no longer read.)

## Publishing checklist

Before you run it, verify the points in
[`additives/contract.md`]({{ base }}additives/contract.md): no cross-Additive imports, no `fluid.*`
imports, every contract through `unique_name()`, every config key prefixed, `requires.wf` set,
dependencies declared, `extract/` limited to what the host should own.

{{ warning("Publishing is public and versioned. Bump the manifest version for every publish — the hub
    stores releases, and a version you already published cannot be quietly replaced.") }}

## Next

- [`ref.md`]({{ base }}ref.md) — the reference section.
- [`additives/contract.md`]({{ base }}additives/contract.md) — what makes an Additive shippable.
{% endblock %}
