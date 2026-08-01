from fastapi.responses import RedirectResponse, HTMLResponse, Response
from webfluid.core.context import FluidContext
from webfluid.core.constants import FRAMEWORK_ID
from datetime import datetime

from fluid.app.http import cached, cacheable


def _docs_url(ctx) -> str:
    return ctx.fluid.config.get("DOCS_URL", "https://docs.webfluid.dev")


def _docs_root(ctx):
    return ctx.fluid.project_root / FRAMEWORK_ID / "templates" / "docs"


def _doc_url(docs_url: str, version: str, latest: str, name: str) -> str:
    prefix = "/latest/" if version == latest else f"/v/{version}/"
    return f"{docs_url}{prefix}{'' if name == 'index' else name}"


async def _not_found(ctx) -> HTMLResponse:
    return HTMLResponse(
        await ctx.fluid.render("errors/404.html"),
        status_code=404
    )


async def _render_docs(ctx, version: str, nav_version: str, path: str):
    versions = ctx.fluid.config["VERSIONS"]
    if version not in versions:
        return await _not_found(ctx)

    stripped = path.strip("/")
    if stripped.startswith("_"):
        return await _not_found(ctx)

    name = stripped or "index"
    root = _docs_root(ctx)
    if not (root / version / f"{name}.html").is_file():
        return await _not_found(ctx)

    latest = ctx.fluid.config["LATEST_VERSION"]
    docs_url = _docs_url(ctx)
    if version != latest and (root / latest / f"{name}.html").is_file():
        canonical = _doc_url(docs_url, latest, latest, name)
    else:
        canonical = _doc_url(docs_url, version, latest, name)

    info = versions[version]
    return await ctx.fluid.render(
        f"docs/{version}/{name}.html",
        version=version, stage=info["stage"], date=info["date"],
        canonical=canonical,
        nav=await ctx.fluid.render(
            f"docs/{version}/_nav.html",
            version=nav_version, path=ctx.request.url.path
        )
    )


async def handle_latest(path: str):
    ctx = FluidContext.current()
    return await _render_docs(
        ctx, ctx.fluid.config["LATEST_VERSION"], "latest", path
    )


async def handle_request(version: str, path: str):
    ctx = FluidContext.current()
    if version == ctx.fluid.config["LATEST_VERSION"]:
        return RedirectResponse(f"/latest/{path}", status_code=302)
    return await _render_docs(ctx, version, version, path)


async def handle_robots():
    ctx = FluidContext.current()
    return cached(
        await ctx.fluid.render(
            "sitemaps/robots.txt",
            disallow=[],
            sitemaps=[f"{_docs_url(ctx)}/sitemap"]
        ),
        "text/plain"
    )


async def handle_sitemap():
    ctx = FluidContext.current()
    docs_url = _docs_url(ctx)
    root = _docs_root(ctx)
    latest = ctx.fluid.config["LATEST_VERSION"]

    sitemap = {}
    for version, data in ctx.fluid.config["VERSIONS"].items():
        doc_dir = root / version
        lastmod = datetime.strptime(data["date"], "%B %d, %Y").date().isoformat()
        for file in doc_dir.rglob("*.html"):
            if file.name.startswith("_"): continue
            name = file.relative_to(doc_dir).as_posix().removesuffix(".html")
            sitemap[_doc_url(docs_url, version, latest, name)] = lastmod

    return cacheable(
        ctx,
        await ctx.fluid.render("sitemaps/map.xml", sitemap=sitemap),
        "application/xml",
        max(sitemap.values())
    )
