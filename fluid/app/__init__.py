from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse, Response

home_router = APIRouter(
    default_response_class=HTMLResponse
)
docs_router = APIRouter(
    default_response_class=HTMLResponse
)
ocean_router = APIRouter(
    default_response_class=HTMLResponse
)


def setup_home():
    from fluid.app.index import (
        handle_request as index,
        handle_sitemap as sitemap,
        handle_sitemaps as sitemaps
    )
    home_router.get("/")(index)
    home_router.get("/sitemap", response_class=Response)(sitemap)
    home_router.get("/sitemaps", response_class=Response)(sitemaps)


def setup_docs():
    from fluid.app.docs import (
        handle_latest as latest_docs,
        handle_request as docs,
        handle_sitemap as sitemap
    )
    docs_router.get("/")(lambda: RedirectResponse("/latest/", status_code=301))
    docs_router.get("/latest/{path:path}")(latest_docs)
    docs_router.get("/v/{version}/{path:path}")(docs)
    docs_router.get("/sitemap", response_class=Response)(sitemap)


def setup_ocean():
    from fluid.app.ocean import (
        handle_discovery as discovery,
        handle_terms as terms,
        handle_licensing as licensing
    )
    ocean_router.get("/")(discovery)
    ocean_router.get("/terms")(terms)
    ocean_router.get("/licensing")(licensing)
