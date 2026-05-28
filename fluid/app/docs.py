from fastapi.responses import RedirectResponse, HTMLResponse
from webfluid.core.context import FluidContext


async def handle_latest(path: str):
    ctx = FluidContext.current()
    latest = ctx.fluid.config["LATEST_VERSION"]

    stripped = path.strip("/")
    if stripped and stripped.startswith("_"):
        return HTMLResponse(
            await ctx.fluid.render("errors/404.html"),
            status_code=404
        )

    path = path if stripped else "index"
    versions = ctx.fluid.config["VERSIONS"]
    info = versions[latest]
    return await ctx.fluid.render(
        f"docs/{latest}/{path}.html",
        version=latest, stage=info["stage"], date=info["date"],
        nav=await ctx.fluid.render(
            f"docs/{latest}/_nav.html",
            version="latest", path=ctx.request.url.path
        )
    )


async def handle_request(version: str, path: str):
    ctx = FluidContext.current()
    latest = ctx.fluid.config["LATEST_VERSION"]
    if version == latest:
        return RedirectResponse(f"/latest/{path}", status_code=302)

    stripped = path.strip("/")
    if stripped and stripped.startswith("_"):
        return HTMLResponse(
            await ctx.fluid.render("errors/404.html"),
            status_code=404
        )

    path = path if stripped else "index"
    versions = ctx.fluid.config["VERSIONS"]
    info = versions[version]
    return await ctx.fluid.render(
        f"docs/{version}/{path}.html",
        version=version, stage=info["stage"], date=info["date"],
        nav=await ctx.fluid.render(
            f"docs/{version}/_nav.html",
            version=version, path=path
        )
    )
