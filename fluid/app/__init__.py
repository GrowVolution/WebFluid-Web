from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

home_router = APIRouter(
    default_response_class=HTMLResponse
)
docs_router = APIRouter(
    default_response_class=HTMLResponse
)

from fluid.app.index import handle_request as index
home_router.get("/")(index)

from fluid.app.docs import handle_latest as latest_docs, handle_request as docs
docs_router.get("/")(lambda: RedirectResponse("/latest/", status_code=301))
docs_router.get("/latest/{path:path}")(latest_docs)
docs_router.get("/v/{version}/{path:path}")(docs)
