from webfluid.core.context import FluidContext
from webfluid.core.ext import security as s
from typing import TYPE_CHECKING

from fluid.app.http import cached, seo_context

if TYPE_CHECKING:
    from webfluid.extensions.security.models import User

_disallow = ["/hub/$", "/hub/api/", "/hub/invite/"]


def _ocean_url(ctx) -> str:
    return ctx.fluid.config.get("OCEAN_URL", "https://ocean.webfluid.dev")


async def handle_robots():
    ctx = FluidContext.current()
    return cached(
        await ctx.fluid.render(
            "sitemaps/robots.txt",
            disallow=_disallow,
            sitemaps=[f"{_ocean_url(ctx)}/hub/sitemap"]
        ),
        "text/plain"
    )


async def handle_discovery(
        q: str = "", user: "User" = s.user_service.current_user
):
    ctx = FluidContext.current()
    return await ctx.fluid.render(
        "ocean/discovery/index.html",
        user=user,
        q=q,
        **seo_context(ctx, _ocean_url(ctx))
    )


def terms_context() -> dict:
    ctx = FluidContext.try_current()
    request = getattr(ctx, "request", None)
    if request is None: return {}

    url = ctx.fluid.config.get("COMPLIANCE_TERMS_URL", "/terms")
    if request.url.path != url: return {}
    return seo_context(ctx, _ocean_url(ctx), url)


async def handle_licensing(user: "User" = s.user_service.current_user):
    ctx = FluidContext.current()
    return await ctx.fluid.render(
        "ocean/licensing.html", user=user,
        **seo_context(ctx, _ocean_url(ctx))
    )
