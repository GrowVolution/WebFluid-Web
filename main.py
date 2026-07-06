from webfluid import Fluid
from webfluid.core.ext import babel
from webfluid.utils import try_import, enabled
from webfluid.utils.additives import installed_additives
from pathlib import Path


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

        if enabled("CONTAINERIZED"):
            cwd = Path(__file__).parent.resolve()
            for additive in installed_additives(cwd / "additives"):
                a, _, p = additive
                if not enabled(a): continue
                mod = try_import(f"additives.{p}")
                adt = getattr(mod, "additive", None)
                if not adt: continue
                adt.install()

    app.jinja_env.globals["latest"] = app.config["LATEST_VERSION"]
    app.jinja_env.globals["home"] = app.config.get("HOME_URL", "https://webfluid.dev")
    app.jinja_env.globals["docs"] = app.config.get("DOCS_URL", "https://docs.webfluid.dev")
    app.jinja_env.globals["ocean"] = app.config.get("OCEAN_URL", "https://ocean.webfluid.dev")

    return app


if __name__ == "__main__":
    fluid = create_app()
    fluid.mix()