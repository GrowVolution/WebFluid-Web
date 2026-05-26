from fastapi.responses import RedirectResponse
from webfluid.core.context import FluidContext


async def handle_latest(path: str):
    ctx = FluidContext.current()
    latest = ctx.fluid.config["LATEST_VERSION"]

    path = path if path.strip("/") else "index"
    versions = ctx.fluid.config["VERSIONS"]
    info = versions[latest]
    return await ctx.fluid.render(
        f"docs/{latest}/{path}.html",
        version=latest, stage=info["stage"], date=info["date"]
    )


async def handle_request(version: str, path: str):
    ctx = FluidContext.current()
    latest = ctx.fluid.config["LATEST_VERSION"]
    if version == latest:
        return RedirectResponse(f"/latest/{path}", status_code=302)

    path = path if path.strip("/") else "index"
    versions = ctx.fluid.config["VERSIONS"]
    info = versions[version]
    return await ctx.fluid.render(
        f"docs/{version}/{path}.html",
        version=version, stage=info["stage"], date=info["date"]
    )
