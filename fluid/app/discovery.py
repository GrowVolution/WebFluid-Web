from webfluid.core.context import FluidContext
from webfluid.core.ext import events, security as s
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webfluid.extensions.security.models import User

_types = ("additives", "extensions", "bundles")
_licenses = ("open", "paid")
_sorts = ("newest", "oldest", "price_asc", "price_desc")


async def handle_request(
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
        "discovery/index.html",
        user=user,
        q=q,
        slice=data["html"],
        has_more=data["has_more"],
        next_offset=data["next_offset"]
    )
