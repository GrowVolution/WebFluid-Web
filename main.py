from webfluid import Fluid
from webfluid.core.ext import babel
from webfluid.core.config import DefaultConfig


def prepare_fluid() -> Fluid:
    app = Fluid(__name__)
    base_url = app.config["BASE_URL"]

    app.add_source('<link rel="preconnect" href="https://fonts.googleapis.com">', 10)
    app.add_source('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', 10)
    app.add_source(
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&'
        'family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">',
        10
    )

    if app.name == "home":
        base_url = app.config.get("HOME_URL", "https://webfluid.dev")

        from fluid.app import home_router, setup_home
        setup_home()
        app.include_router(home_router)

        from fluid.i18n import translations
        babel.update_translations("messages", translations)

    elif app.name == "docs":
        base_url = app.config.get("DOCS_URL", "https://docs.webfluid.dev")

        from fluid.app import docs_router, setup_docs
        setup_docs()
        app.include_router(docs_router)
        app.jinja_env.globals["versions"] = app.config["VERSIONS"].keys()

    elif app.name == "ocean":
        base_url = app.config.get("OCEAN_URL", "https://ocean.webfluid.dev")

        from fluid.app import ocean_router, setup_ocean
        setup_ocean()
        app.include_router(ocean_router)

    app.jinja_env.globals["latest"] = app.config["LATEST_VERSION"]
    app.jinja_env.globals["home"] = base_url
    app.jinja_env.globals["docs"] = base_url
    app.jinja_env.globals["ocean"] = base_url

    if base_url == DefaultConfig.BASE_URL:
        app.config["BASE_URL"] = base_url

    return app


if __name__ == "__main__":
    fluid = prepare_fluid()
    fluid.mix()
