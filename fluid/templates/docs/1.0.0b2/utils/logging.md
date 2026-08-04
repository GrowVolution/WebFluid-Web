{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Logging{% endblock %}
{% block doc_section %}Framework utility{% endblock %}

{% block summary %}
`webfluid.utils.logging.factory` is the shared log factory. It writes coloured lines to stdout and
plain ones to stderr, only while an app is actually being run by the CLI, and it attributes anything
logged from inside an Additive to a dedicated logger.
{% endblock %}

{% block body %}
## The API

```python
from webfluid.utils.logging import factory as log

log.log("info line")            # INFO
log.debug("...")
log.warning("...")
log.error("...")
log.critical("...")
log.exception(exc, "optional message")
log.log(msg, category=logging.WARNING)   # explicit level
```

`exception(exc, message=None)` formats the full traceback and emits it at **error** level:

```text
[WF]    [2026-08-03 18:04:29 +0200] [ERROR]     Failed to queue welcome mail.
ValueError: bad address
Traceback (most recent call last):
  ...
```

Line format: `[WF]\t[%Y-%m-%d %H:%M:%S %z] [LEVEL]\tmessage`, coloured by level (debug cyan, info
green, warning yellow, error red, critical red on white).

```python
# fluid/services/notify.py
from webfluid.utils.logging import factory as log


async def welcome(address: str):
    try:
        ...
        log.log(f"Welcome mail queued for {address}.")
    except Exception as e:
        log.exception(e, "Failed to queue welcome mail.")
```

## It only speaks during execution

```python
def log(self, message, category=INFO):
    if not EXECUTION: return
    self.logger.log(category, message)
```

`EXECUTION` is `enabled("IN_EXECUTION")`, which **`wf run` sets** and nothing else does. So importing
your modules, scaffolding, and running migration commands produce no framework log lines — there is
no live session to log into.

{{ warning("A consequence worth planning around: a log call from a script you run directly
    (python -c ..., a pytest run, a management command) is silently dropped. Set IN_EXECUTION=1 in
    the environment if you want output from such a context, or use the stdlib logger directly.") }}

Verbosity follows `LOG_LEVEL`, which `wf run -l debug` sets (and `-d` forces to `debug`). The default
is `info`. Handlers and level are installed by `start_session()`, called from `mix()` — you do not
configure them yourself.

## Where the lines go

Every line is written twice:

- **coloured to stdout** — through the active progress bar when one is open, so a log line during
  the startup phase does not scribble over the bar,
- **plain to stderr** — which `wf run` redirects into a timestamped file.

```text
logs/
└── app/
    ├── 2026-07-28_18-04-29.log
    └── 2026-07-28_19-11-02.log
```

One file per run, named for the start time, readable without a terminal that understands escape
codes. The interactive runner's "clear log folder" prunes that directory but always keeps the file
the current run is writing to.

## Additive attribution

Two logger names:

| Logger               | Used by                             |
|----------------------|-------------------------------------|
| `webfluid`           | The framework and your main app     |
| `webfluid.additives` | Anything running inside an Additive |

The `Router` used by Additives wraps every endpoint in `factory.additive_context(fn)`, which enters
a `_LogContext` naming the Additive logger. So calling the same `factory` from inside an Additive
route routes the line through the Additive logger automatically — no extra work.

```python
from webfluid.utils.logging import factory as log


def wrap(fn):
    return log.additive_context(fn)     # route any callable's logs through the Additive logger
```

Both loggers are configured identically in `start_session()`: level from `LOG_LEVEL`,
`propagate = False`, handlers cleared and replaced. Configuring them yourself in your app is
therefore pointless — `start_session()` will overwrite it.

## Progress bars

```python
from webfluid.utils.cli import progress_bar

with progress_bar("Importing", len(items)) as bar:
    for item in items:
        ...
        bar.update()
```

The bar is sized to the terminal (`COLUMNS`, which `wf run` passes to the child process), and while
one is open every log line is written **through** it instead of over it. That is what makes the
startup-phase bars readable.

## Rules

{{ rule("Log messages, not data dumps. A log line ends up in a file per run and on someone's console;
    a full request body or a query result belongs in a debug line at most.") }}

{{ rule("Use log.exception(e, context) in an except block, never log.error(str(e)). The former keeps
    the traceback, which is the only part that tells you where it happened.") }}

{{ rule("Never log secrets, tokens, passwords or full session contents. The log file is plain text
    and is written for every run.") }}

{{ rule("Prefer the framework factory over a module-level logging.getLogger(__name__) in a WebFluid
    app. The factory's lines share the format, the level, the colouring and the file — a stdlib
    logger's do not, and its handlers are not configured by start_session().") }}

## Next

- [`cli/run.md`]({{ base }}cli/run.md) — the process that owns the log files.
- [`ref/utils.md`]({{ base }}ref/utils.md) — the rest of `webfluid.utils`.
{% endblock %}
