from webfluid import Fluid
from webfluid.core.ext import babel
from webfluid.core.context import FluidContext
from webfluid.extensions.babel.utils import load_locale, parse_best_match
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


def create_app() -> Fluid:
    app = Fluid(__name__)

    app.add_source('<link rel="preconnect" href="https://fonts.googleapis.com">', 10)
    app.add_source('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', 10)
    app.add_source(
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&'
        'family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">',
        10
    )

    if app.name == "home":
        from fluid.app import home_router, setup_home
        setup_home()
        app.include_router(home_router)

        from fluid.i18n import translations
        babel.update_translations("messages", translations)

    elif app.name == "docs":
        from fluid.app import docs_router, setup_docs
        setup_docs()
        app.include_router(docs_router)
        app.jinja_env.globals["versions"] = app.config["VERSIONS"].keys()

    elif app.name == "ocean":
        from fluid.app import ocean_router, setup_ocean
        setup_ocean()
        app.include_router(ocean_router)

        # Ocean i18n is provided by the 'ocean' Additive

    app.jinja_env.globals["latest"] = app.config["LATEST_VERSION"]
    app.jinja_env.globals["home"] = app.config.get("HOME_URL", "https://webfluid.dev")
    app.jinja_env.globals["docs"] = app.config.get("DOCS_URL", "https://docs.webfluid.dev")
    app.jinja_env.globals["ocean"] = app.config.get("OCEAN_URL", "https://ocean.webfluid.dev")

    # Alpha 2 workaround
    app.add_middleware(
        ProxyHeadersMiddleware,
        trusted_hosts=["*"]
    )
    @babel.locale_selector
    def get_locale():
        try: ctx = FluidContext.current()
        except RuntimeError:
            return load_locale(babel.default_locale)

        request = ctx.request
        if request is None:
            return load_locale(babel.default_locale)

        locale = (
            request.query_params.get("lang")    # <- Missing in 1.0.0a2 / required for SEO
            or request.cookies.get("lang")
            or parse_best_match(
                request.headers.get("Accept-Language"),
                babel.supported_locales
            )
            or babel.default_locale
        )
        return load_locale(locale)

    return app


if __name__ == "__main__":
    fluid = create_app()
    fluid.mix()