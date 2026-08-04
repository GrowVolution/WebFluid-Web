{% extends "docs/base.md" %}
{% from "docs/partials/_callout.md" import rule, warning, info, bug %}

{% block doc_title %}Mail{% endblock %}
{% block doc_section %}Extensions{% endblock %}

{% block summary %}
`EXT_MAIL` gives you `mail`, an SMTP client with a synchronous and an asynchronous half. Both build
a `MIMEMultipart("alternative")` message from a body mapping, both accept attachments, cc and bcc,
and both reuse an open connection when one is in scope.
{% endblock %}

{% block body %}
## Enabling

```ini
[extensions]
EXT_MAIL = 1

[mail]
MAIL_SERVER = localhost
MAIL_PORT = 1025
MAIL_USE_TLS = 0
MAIL_USE_STARTTLS = 0
MAIL_DEFAULT_SENDER = noreply@example.org
```

`expand_fluid` validates three things and raises `FrameworkException` on any of them:

- `MAIL_USERNAME` without `MAIL_PASSWORD`,
- `MAIL_PASSWORD` without `MAIL_USERNAME`,
- `MAIL_USE_TLS` **and** `MAIL_USE_STARTTLS` both true (mutually exclusive).

For local development you do not need a real server:

```bash
python -m aiosmtpd -n -l localhost:1025
```

## TLS — read this before configuring

| Setting             | Meaning                        | Port | Honoured by           |
|---------------------|--------------------------------|------|-----------------------|
| `MAIL_USE_TLS`      | Implicit TLS (`SMTP_SSL`)      | 465  | **async client only** |
| `MAIL_USE_STARTTLS` | Plain connect, then `STARTTLS` | 587  | both clients          |

{{ bug("SyncManager stores MAIL_USE_TLS and then opens a plain smtplib.SMTP connection — only
    MAIL_USE_STARTTLS is honoured on that path. So mail.send() against a server configured for
    implicit TLS talks plaintext, with your credentials in it. The async client passes both flags to
    aiosmtplib correctly. Until this is fixed: pair port 587 with MAIL_USE_STARTTLS, or send with
    mail.asend().") }}

{{ warning("The shipped defaults — MAIL_PORT 587, MAIL_USE_TLS False, MAIL_USE_STARTTLS True — are
    the correct pair and work on both clients. What breaks is switching MAIL_USE_TLS on: that needs
    port 465 and only the async client honours it. Never set MAIL_USE_TLS = 1 while leaving the port
    at 587.") }}

## The API

```python
from webfluid.core.ext import mail

mail.send(to, subject, body, attachments=None,
          from_email=None, cc=None, bcc=None, fake_async=True)

await mail.asend(to, subject, body, attachments=None,
                 from_email=None, cc=None, bcc=None)

with mail.client() as smtp: ...              # bare, logged-in smtplib.SMTP
async with mail.async_client() as smtp: ...  # bare, logged-in aiosmtplib.SMTP
```

| Parameter     | Type             | Notes                                                                                            |
|---------------|------------------|--------------------------------------------------------------------------------------------------|
| `to`          | `str`            | A single address; the `To` header is set verbatim                                                |
| `subject`     | `str`            |                                                                                                  |
| `body`        | `dict[str, str]` | **MIME subtype → content.** `{"plain": ..., "html": ...}`                                        |
| `attachments` | `list[dict]`     | `{"bytes": bytes\|str, "type": str, "filename": str}` — `type` is the MIME *application* subtype |
| `from_email`  | `str`            | Overrides `MAIL_DEFAULT_SENDER`                                                                  |
| `cc` / `bcc`  | `list[str]`      | Joined into the headers                                                                          |
| `fake_async`  | `bool`           | Sync only. `True` (default) hands delivery to a `threading.Thread` and returns immediately       |

{{ rule("body is a mapping, not a string. mail.send(to, subject, \"hello\") produces a message with
    one part per character, because the code iterates body.items(). Always pass
    {\"plain\": \"hello\"}.") }}

A service, the conventional home for this:

```python
# fluid/services/notify.py
from webfluid.core.ext import mail, babel


async def welcome(address: str, value: str):
    subject = await babel.agettext("WELCOME_SUBJECT")
    await mail.asend(
        address,
        subject,
        {
            "plain": f"Saved your model: {value}.",
            "html": f"<p>Saved your model <b>{value}</b>.</p>"
        }
    )
```

Attachments:

```python
await mail.asend(
    "to@example.org",
    "Your report",
    {"plain": "See attached."},
    attachments=[{
        "bytes": pdf_bytes,
        "type": "pdf",
        "filename": "report.pdf"
    }]
)
```

A missing key in an attachment dict raises `FrameworkException("Failed to send mail: '<key>'")`.

## Batching: one connection for many messages

Every `send`/`asend` opens and closes its own SMTP session by default. That is right for
transactional mail and wrong for a loop. Opening a client puts it in a `ClientContext` (a
contextvar), and `send`/`asend` reuse it:

```python
async with mail.async_client():
    for address in recipients:
        await mail.asend(address, "Release notes", {"plain": body})
```

{{ warning("Sync and async clients do not mix. mail.send() inside an async_client() block sees a
    context whose is_async is True, treats it as no context and opens its own connection — and vice
    versa. Keep a batch on one side of the fence.") }}

The context is per task, so the reuse is scoped to the code inside the block. The yielded object is
a plain `smtplib.SMTP` / `aiosmtplib.SMTP`, so anything the framework does not wrap is still
reachable.

## Sync vs. async, decided

| Situation                                                | Use                                   |
|----------------------------------------------------------|---------------------------------------|
| Inside `async def` (routes, event handlers, async hooks) | `await mail.asend(...)`               |
| Fire-and-forget from sync code                           | `mail.send(...)` — threads delivery   |
| Sync code that must know delivery happened               | `mail.send(..., fake_async=False)`    |
| Any implicit-TLS server                                  | `mail.asend(...)` (see the bug above) |
| Many messages in a row                                   | `async with mail.async_client():`     |

{{ rule("Prefer asend everywhere you can. It is the only client that honours both TLS modes, it does
    not spawn a thread per message, and delivery failures surface as exceptions you can handle
    instead of dying in a detached thread.") }}

## Errors

Both clients narrow SMTP failures into `FrameworkException`:

| Cause                                                                       | Message                            |
|-----------------------------------------------------------------------------|------------------------------------|
| `SMTPConnectError`, `SMTPAuthenticationError` (+ the async timeout variant) | `SMTP Connection/Auth failed: …`   |
| Any other `SMTPException`                                                   | `Unexpected SMTP error: <Type>: …` |

A `fake_async=True` send raises inside its thread, where nothing catches it — another reason to
prefer `asend` for anything that matters.

## Templated mail

The framework ships `base_email.html` as a starting layout. Render it and pass the result as the
`html` body part:

```python
from webfluid.core.context import FluidContext


async def send_receipt(address: str, order):
    ctx = FluidContext.current()
    html = await ctx.fluid.render("mail/receipt.html", order=order)
    await mail.asend(address, "Your receipt", {"plain": order.summary, "html": html})
```

{{ warning("Rendering a mail template from a scheduled job or a startup hook fails: the context
    processors build url_for from the request in the current context and hand back None when there
    is none, so a template using url_for raises 'NoneType is not callable'. Use
    fluid.url_path_for() or an absolute BASE_URL in mail templates.") }}

## Next

- [`ext/babel.md`]({{ base }}ext/babel.md) — translating subjects and bodies.
- [`ext/security.md`]({{ base }}ext/security.md) — the single-use tokens that go into mail links.
- [`surface/jinja.md`]({{ base }}surface/jinja.md) — where `base_email.html` comes from.
{% endblock %}
