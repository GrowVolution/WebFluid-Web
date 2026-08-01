from fastapi.responses import Response
from datetime import datetime, timezone, time
from email.utils import format_datetime, parsedate_to_datetime
from typing import Optional

_CACHE_MAX_AGE = 3600


def cached(content: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": f"public, max-age={_CACHE_MAX_AGE}"}
    )


def cacheable(ctx, content: str, media_type: str, lastmod: str) -> Response:
    modified = datetime.combine(
        datetime.strptime(lastmod, "%Y-%m-%d").date(),
        time(0, 0), timezone.utc
    )
    headers = {
        "Cache-Control": f"public, max-age={_CACHE_MAX_AGE}",
        "Last-Modified": format_datetime(modified, usegmt=True)
    }

    since = ctx.request.headers.get("if-modified-since")
    if since:
        try: known = parsedate_to_datetime(since)
        except (TypeError, ValueError): known = None
        if known is not None:
            if known.tzinfo is None: known = known.replace(tzinfo=timezone.utc)
            if known >= modified:
                return Response(status_code=304, headers=headers)

    return Response(content=content, media_type=media_type, headers=headers)


def seo_context(ctx, base: str, path: Optional[str] = None) -> dict:
    if path is None: path = ctx.request.url.path

    locales = list(ctx.fluid.config.get("BABEL_SUPPORTED_LOCALES") or [])
    lang = ctx.request.query_params.get("lang")
    canonical = f"{base.rstrip('/')}{path}"

    return {
        "canonical": f"{canonical}?lang={lang}" if lang in locales else canonical,
        "alternates": [(code, f"{canonical}?lang={code}") for code in locales],
        "x_default": canonical
    }
