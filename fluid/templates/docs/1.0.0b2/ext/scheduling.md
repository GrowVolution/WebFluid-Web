{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info %}

{% block doc_title %}Scheduling{% endblock %}
{% block doc_section %}Extensions{% endblock %}

{% block summary %}
`EXT_SCHEDULING` is the thinnest battery: it is not a `FluidExtension` at all, but a bare
APScheduler `AsyncIOScheduler` that the framework starts on a startup hook. Everything you know
about APScheduler applies unchanged.
{% endblock %}

{% block body %}
## Enabling

```ini
[extensions]
EXT_SCHEDULING = 1
```

That is the whole wiring. `enable_extensions` does:

```python
if EXT_SCHEDULING: fluid.startup_hook(ext.scheduler.start)
```

The instance is created lazily on first attribute access of `webfluid.core.ext.scheduler` and
cached, so every module that imports it gets the same scheduler.

## Usage

```python
# fluid/jobs.py
from webfluid.utils.logging import factory as log


async def heartbeat():
    log.log("Beat!")
```

```python
# main.py
from webfluid import Fluid
from webfluid.core.ext import scheduler
from apscheduler.triggers.interval import IntervalTrigger

from fluid.jobs import heartbeat

scheduler.add_job(heartbeat, IntervalTrigger(seconds=5))


def prepare_fluid() -> Fluid:
    return Fluid(__name__)
```

Jobs may be added **before or after** the app is constructed — `add_job` on a non-running
`AsyncIOScheduler` queues the job and it is scheduled once `start()` runs. Both sync and async
callables work; async ones are awaited on the app's loop.

Common triggers:

```python
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

scheduler.add_job(job, IntervalTrigger(minutes=15))
scheduler.add_job(job, CronTrigger(hour=0))                  # daily at midnight
scheduler.add_job(job, CronTrigger(day_of_week="mon", hour=9))
```

## Rules

{{ rule("A scheduled job runs without a request, so FluidContext.current() raises and url_for is
    None. Use FluidContext.try_current(), fluid.url_path_for() or BASE_URL. Rendering a template
    from a job fails on url_for unless you avoid it.") }}

{{ rule("Jobs run on the application's event loop. A blocking call inside one blocks every request.
    Wrap blocking work in webfluid.utils.run_in_executor(fn, *args).") }}

{{ warning("The scheduler is in-process and has no persistent job store configured. Every process
    that boots runs its own copy of every job — with two workers, every job fires twice. If you
    scale horizontally, either run the scheduler in a single dedicated app (one app config with
    EXT_SCHEDULING = 1, the rest with 0) or configure a shared job store yourself before start().") }}

## Who else uses it

Two batteries register jobs of their own, which is why they depend on this switch:

- **`EXT_JWT`** requires `EXT_SCHEDULING`: it rotates the signing secret every
  `JWT_ROTARY_INTERVAL` days and mints the first one on a startup hook.
- **`EXT_SECURITY`** adds a cleanup job that deletes `ExpiredToken` rows older than
  `SECURITY_TOKEN_MAX_AGE`, every 15 days. Without `EXT_SCHEDULING` that table grows forever.

An Additive registers its jobs from `before_enable`, which already runs inside the loop:

```python
@additive.before_enable
async def before_enable(fluid):
    from webfluid.core.ext import scheduler
    from apscheduler.triggers.cron import CronTrigger
    from .jobs import nightly

    scheduler.add_job(nightly, CronTrigger(hour=3))
```

## Next

- [`ext/sqlalchemy.md`]({{ base }}ext/sqlalchemy.md) — the battery most jobs need.
- [`utils/lifecycle.md`]({{ base }}utils/lifecycle.md) — where startup hooks fit.
{% endblock %}
