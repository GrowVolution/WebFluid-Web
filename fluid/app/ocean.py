from webfluid.core.context import FluidContext
from webfluid.core.ext import events, security as s
from typing import TYPE_CHECKING

from fluid.app.http import cached, seo_context

if TYPE_CHECKING:
    from webfluid.extensions.security.models import User

_types = ("additives", "extensions", "bundles")
_licenses = ("open", "paid")
_sorts = ("newest", "oldest", "price_asc", "price_desc")

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
        q: str = "", type: str = "", license: str = "", sort: str = "",
        user: "User" = s.user_service.current_user
):
    ctx = FluidContext.current()

    types = ",".join(
        part.strip() for part in type.split(",")
        if part.strip() in _types
    )
    licensing = license if license in _licenses else ""
    ordering = sort if sort in _sorts else ""

    data = await events.request("ocean_discovery", {
        "type": types,
        "q": q,
        "license": licensing,
        "sort": ordering,
        "offset": 0,
        "uid": user.id if user else None
    })

    return await ctx.fluid.render(
        "ocean/discovery/index.html",
        user=user,
        q=q,
        slice=data["html"],
        has_more=data["has_more"],
        next_offset=data["next_offset"],
        **seo_context(ctx, _ocean_url(ctx))
    )


async def handle_terms(user: "User" = s.user_service.current_user):
    ctx = FluidContext.current()
    return await ctx.fluid.render(
        "ocean/terms.html", user=user,
        **seo_context(ctx, _ocean_url(ctx))
    )


async def handle_licensing(user: "User" = s.user_service.current_user):
    ctx = FluidContext.current()
    return await ctx.fluid.render(
        "ocean/licensing.html", user=user,
        **seo_context(ctx, _ocean_url(ctx))
    )
