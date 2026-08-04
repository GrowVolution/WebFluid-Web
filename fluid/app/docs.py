from fastapi.responses import RedirectResponse, HTMLResponse, Response
from webfluid.core.context import FluidContext
from webfluid.core.constants import FRAMEWORK_ID
from datetime import datetime

from fluid.app.http import cached, cacheable

MARKDOWN_SUFFIX = ".md"
MARKDOWN_MIME = "text/markdown"
MARKDOWN_TYPE = f"{MARKDOWN_MIME}; charset=utf-8"


def _docs_url(ctx) -> str:
    return ctx.fluid.config.get("DOCS_URL", "https://docs.webfluid.dev")


def _docs_root(ctx):
    return ctx.fluid.project_root / FRAMEWORK_ID / "templates" / "docs"


def _doc_url(docs_url: str, version: str, latest: str, name: str, markdown: bool = False) -> str:
    prefix = "/latest/" if version == latest else f"/v/{version}/"
    suffix = MARKDOWN_SUFFIX if markdown else ""
    return f"{docs_url}{prefix}{'' if name == 'index' else name}{suffix}"


def _hidden(name: str) -> bool:
    return any(part.startswith("_") for part in name.split("/"))


def _wants_markdown(ctx) -> bool:
    return MARKDOWN_MIME in ctx.request.headers.get("accept", "")


def _page_order(ctx, root, version):
    doc_dir = root / version
    available = {
        file.relative_to(doc_dir).as_posix().removesuffix(MARKDOWN_SUFFIX)
        for file in doc_dir.rglob(f"*{MARKDOWN_SUFFIX}")
    }
    available = {name for name in available if not _hidden(name)}

    ordered = [name for name in ctx.fluid.config["DOCS_ORDER"] if name in available]
    return ordered + sorted(available.difference(ordered))


async def _not_found(ctx) -> HTMLResponse:
    return HTMLResponse(
        await ctx.fluid.render("errors/404.html"),
        status_code=404
    )


async def _render_page(ctx, version: str, nav_version: str, name: str, markdown: bool, path: str):
    versions = ctx.fluid.config["VERSIONS"]
    latest = ctx.fluid.config["LATEST_VERSION"]
    docs_url = _docs_url(ctx)
    root = _docs_root(ctx)
    suffix = MARKDOWN_SUFFIX if markdown else ".html"

    def url(as_markdown):
        target = MARKDOWN_SUFFIX if as_markdown else ".html"
        if version != latest and (root / latest / f"{name}{target}").is_file():
            return _doc_url(docs_url, latest, latest, name, as_markdown)
        return _doc_url(docs_url, version, latest, name, as_markdown)

    info = versions[version]
    return await ctx.fluid.render(
        f"docs/{version}/{name}{suffix}",
        version=version, stage=info["stage"], date=info["date"],
        base="/latest/" if nav_version == "latest" else f"/v/{version}/",
        canonical=url(markdown), html_url=url(False),
        markdown_url=url(True) if (root / version / f"{name}{MARKDOWN_SUFFIX}").is_file() else None,
        nav=await ctx.fluid.render(
            f"docs/{version}/_nav{suffix}",
            version=nav_version, path=path
        )
    )


async def _render_docs(ctx, version: str, nav_version: str, path: str):
    if version not in ctx.fluid.config["VERSIONS"]:
        return await _not_found(ctx)

    stripped = path.strip("/")
    explicit = stripped.endswith(MARKDOWN_SUFFIX)
    if explicit: stripped = stripped.removesuffix(MARKDOWN_SUFFIX).strip("/")

    if stripped and _hidden(stripped):
        return await _not_found(ctx)

    name = stripped or "index"
    doc_dir = _docs_root(ctx) / version
    has_markdown = (doc_dir / f"{name}{MARKDOWN_SUFFIX}").is_file()

    if explicit:
        if not has_markdown: return await _not_found(ctx)
    elif not (doc_dir / f"{name}.html").is_file():
        return await _not_found(ctx)

    markdown = explicit or (has_markdown and _wants_markdown(ctx))
    content = await _render_page(
        ctx, version, nav_version, name, markdown, ctx.request.url.path
    )

    if markdown:
        page = _doc_url(
            _docs_url(ctx), version,
            ctx.fluid.config["LATEST_VERSION"], name
        )
        return Response(
            content=content,
            media_type=MARKDOWN_TYPE,
            headers={
                "Vary": "Accept",
                "Link": f'<{page}>; rel="canonical"'
            }
        )

    return HTMLResponse(content, headers={"Vary": "Accept"})


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
    docs_url = _docs_url(ctx)
    return cached(
        await ctx.fluid.render(
            "sitemaps/robots.txt",
            disallow=[],
            sitemaps=[f"{docs_url}/sitemap"],
            notes=[
                "Every documentation page is also published as Markdown at the",
                "same path with a .md suffix (for example /latest/ext/babel.md).",
                "That variant is written for AI agents and is the preferred source",
                f"for machine consumption. Index: {docs_url}/llms.txt",
                f"Full corpus: {docs_url}/llms-full.txt"
            ]
        ),
        "text/plain"
    )


async def handle_llms():
    ctx = FluidContext.current()
    latest = ctx.fluid.config["LATEST_VERSION"]
    info = ctx.fluid.config["VERSIONS"][latest]
    return cached(
        await ctx.fluid.render(
            f"docs/{latest}/_llms.md",
            version=latest, stage=info["stage"], date=info["date"],
            base="/latest/", docs=_docs_url(ctx)
        ),
        MARKDOWN_TYPE
    )


async def handle_llms_full():
    ctx = FluidContext.current()
    latest = ctx.fluid.config["LATEST_VERSION"]
    root = _docs_root(ctx)

    pages = []
    for name in _page_order(ctx, root, latest):
        pages.append(await _render_page(
            ctx, latest, "latest", name, True, f"/latest/{'' if name == 'index' else name}"
        ))

    return cacheable(
        ctx,
        "\n\n".join(page.strip() for page in pages) + "\n",
        MARKDOWN_TYPE,
        datetime.strptime(
            ctx.fluid.config["VERSIONS"][latest]["date"], "%B %d, %Y"
        ).date().isoformat()
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
