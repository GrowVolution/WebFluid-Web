from webfluid import Fluid
from webfluid.core.ext import babel


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
        from fluid.app import home_router
        app.include_router(home_router)

        from fluid.i18n.home import translations
        babel.update_translations("messages", translations)

    elif app.name == "docs":
        from fluid.app import docs_router
        app.include_router(docs_router)
        app.jinja_env.globals["versions"] = app.config["VERSIONS"].keys()

    elif app.name == "ocean":
        from fluid.app import ocean_router, setup_ocean
        setup_ocean()
        app.include_router(ocean_router)

        from fluid.i18n.ocean import translations
        babel.update_translations("messages", translations)

    app.jinja_env.globals["latest"] = app.config["LATEST_VERSION"]
    app.jinja_env.globals["home"] = app.config.get("HOME_URL", "https://webfluid.dev")
    app.jinja_env.globals["docs"] = app.config.get("DOCS_URL", "https://docs.webfluid.dev")
    app.jinja_env.globals["ocean"] = app.config.get("OCEAN_URL", "https://ocean.webfluid.dev")
                
    return app


if __name__ == "__main__":
    fluid = create_app()
    fluid.mix()
