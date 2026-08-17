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

| Setting             | Meaning                        | Port | Default   | Client used                            |
|---------------------|--------------------------------|------|-----------|----------------------------------------|
| `MAIL_USE_TLS`      | Implicit TLS                   | 465  | **False** | `smtplib.SMTP_SSL` / `aiosmtplib` TLS  |
| `MAIL_USE_STARTTLS` | Plain connect, then `STARTTLS` | 587  | **True**  | `smtplib.SMTP` + `starttls()`          |

Both clients honour both flags since `1.0.0b3`. The shipped pair — `MAIL_PORT = 587` with STARTTLS —
is the one to keep unless your provider says otherwise.

{{ rule("For an implicit-TLS server set MAIL_PORT = 465 AND MAIL_USE_TLS = True AND
    MAIL_USE_STARTTLS = False. Setting both flags raises FrameworkException at startup — it is a
    contradiction, not a fallback chain.") }}

{{ warning("Upgrading from 1.0.0b2 or earlier: the defaults were swapped (587 + implicit TLS, which
    no server offers) and the sync client ignored MAIL_USE_TLS entirely, opening a plain connection
    and sending credentials in the clear. If you set the flags by hand to work around either, re-read
    them against the table above.") }}

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
| Many messages in a row                                   | `async with mail.async_client():`     |

{{ rule("Prefer asend everywhere you can. It does not spawn a thread per message, and delivery
    failures surface as exceptions you can handle rather than as a log line from a thread nobody is
    watching.") }}

## Errors

Both clients narrow SMTP failures into `FrameworkException`:

| Cause                                                                       | Message                            |
|-----------------------------------------------------------------------------|------------------------------------|
| `SMTPConnectError`, `SMTPAuthenticationError` (+ the async timeout variant) | `SMTP Connection/Auth failed: …`   |
| Any other `SMTPException`                                                   | `Unexpected SMTP error: <Type>: …` |

Connect, STARTTLS and login all happen **inside** the `try` that produces those, so a refused
greeting or a rejected password raises `FrameworkException` rather than a raw `smtplib` /
`aiosmtplib` error. (Before `1.0.0b3` they happened outside it, so those two handlers could only ever
see an exception raised by the caller's own body.)

A `fake_async=True` send still runs in a detached daemon thread, so its exception reaches no caller —
but it is logged through the framework logger now instead of vanishing. Prefer `asend` for anything
whose failure you need to act on.

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

{{ info("Rendering a mail template off-request — from a scheduled job, a startup hook or an event
    handler — works since 1.0.0b3. url_for falls back to the application's route table when there is
    no request, and url_for(name, external=True) prefixes BASE_URL, which is what a link in an email
    needs. Set BASE_URL: its default is http://localhost:8000 and nothing warns you about it.") }}

{{ rule("A mail template with a .html suffix is autoescaped like any other. A .txt or .md template
    is not, so the plain part renders as written.") }}

## Next

- [`ext/babel.md`]({{ base }}ext/babel.md) — translating subjects and bodies.
- [`ext/security.md`]({{ base }}ext/security.md) — the single-use tokens that go into mail links.
- [`surface/jinja.md`]({{ base }}surface/jinja.md) — where `base_email.html` comes from.
{% endblock %}
