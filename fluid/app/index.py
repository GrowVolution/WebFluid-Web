from fastapi.responses import Response
from webfluid.core.context import FluidContext
from datetime import datetime, UTC
import httpx


async def handle_request():
    ctx = FluidContext.current()
    return await ctx.fluid.render("index.html")


async def handle_sitemap():
    ctx = FluidContext.current()
    return Response(
        content=await ctx.fluid.render(
            "sitemaps/map.xml", sitemap={
                ctx.fluid.config.get(
                    "HOME_URL", "https://webfluid.dev"
                ): "2026-07-11"
            }
        ),
        media_type="application/xml"
    )


async def handle_sitemaps():
    ctx = FluidContext.current()

    latest_docs = ctx.fluid.config["LATEST_VERSION"]
    docs_timestamp = datetime.strptime(
        ctx.fluid.config["VERSIONS"][latest_docs]["date"],
        "%B %d, %Y"
    ).isoformat()

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{ctx.fluid.config.get(
                'OCEAN_URL', 'https://ocean.webfluid.dev'
            )}/hub/sitemap/timestamp"
        )
    ocean_timestamp = res.json().get(
        "timestamp", datetime.now(UTC).isoformat()
    )

    return Response(
        content=await ctx.fluid.render(
            "sitemaps/index.xml",
            latest_docs=docs_timestamp,
            latest_ocean=ocean_timestamp
        ),
        media_type="application/xml"
    )
