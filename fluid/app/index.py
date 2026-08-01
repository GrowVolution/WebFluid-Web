from fastapi.responses import Response
from webfluid.core.context import FluidContext
from datetime import datetime, UTC
import httpx

from fluid.app.http import cached, cacheable, seo_context


def _home_url(ctx) -> str:
    return ctx.fluid.config.get("HOME_URL", "https://webfluid.dev")


def _home_lastmod(ctx) -> str:
    return ctx.fluid.config.get("HOME_LASTMOD", "2026-08-01")


async def handle_request():
    ctx = FluidContext.current()
    return await ctx.fluid.render(
        "index.html", **seo_context(ctx, _home_url(ctx))
    )


async def handle_robots():
    ctx = FluidContext.current()
    home = _home_url(ctx)
    return cached(
        await ctx.fluid.render(
            "sitemaps/robots.txt",
            disallow=[],
            sitemaps=[f"{home}/sitemaps", f"{home}/sitemap"]
        ),
        "text/plain"
    )


async def handle_sitemap():
    ctx = FluidContext.current()
    lastmod = _home_lastmod(ctx)
    return cacheable(
        ctx,
        await ctx.fluid.render(
            "sitemaps/map.xml", sitemap={f"{_home_url(ctx)}/": lastmod}
        ),
        "application/xml",
        lastmod
    )


async def handle_sitemaps():
    ctx = FluidContext.current()

    latest_docs = ctx.fluid.config["LATEST_VERSION"]
    docs_timestamp = datetime.strptime(
        ctx.fluid.config["VERSIONS"][latest_docs]["date"],
        "%B %d, %Y"
    ).date().isoformat()

    ocean_url = ctx.fluid.config.get("OCEAN_URL", "https://ocean.webfluid.dev")
    ocean_timestamp = datetime.now(UTC).date().isoformat()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{ocean_url}/hub/sitemap/timestamp")
        res.raise_for_status()
        ocean_timestamp = res.json().get("timestamp") or ocean_timestamp
    except (httpx.HTTPError, ValueError):
        pass

    home_timestamp = _home_lastmod(ctx)
    return cacheable(
        ctx,
        await ctx.fluid.render(
            "sitemaps/index.xml",
            latest_home=home_timestamp,
            latest_docs=docs_timestamp,
            latest_ocean=ocean_timestamp
        ),
        "application/xml",
        max(home_timestamp, docs_timestamp, ocean_timestamp)
    )
