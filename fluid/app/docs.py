from fastapi.responses import RedirectResponse, HTMLResponse, Response
from webfluid.core.context import FluidContext
from webfluid.core.constants import FRAMEWORK_ID
from datetime import datetime


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


async def handle_sitemap():
    ctx = FluidContext.current()
    docs_url = ctx.fluid.config.get(
        "DOCS_URL", "https://docs.webfluid.dev"
    )
    docs = ctx.fluid.app_root / FRAMEWORK_ID / "templates" / "docs"
    latest = ctx.fluid.config["LATEST_VERSION"]
    sitemap = {}
    for version, data in ctx.fluid.config["VERSIONS"].items():
        if version == latest: prefix = "/latest/"
        else: prefix = f"/v/{version}/"
        doc_dir = docs / version
        for file in doc_dir.rglob("*.html"):
            if file.name.startswith("_"): continue
            elif file.name == "index.html": path = ""
            else: path = (
                file.relative_to(doc_dir)
                .as_posix().replace(".html", "")
            )
            sitemap[f"{docs_url}{prefix}{path}"] = datetime.strptime(
                data["date"], "%B %d, %Y"
            ).date().isoformat()
    return Response(
        content=await ctx.fluid.render("sitemaps/map.xml", sitemap=sitemap),
        media_type="application/xml"
    )
