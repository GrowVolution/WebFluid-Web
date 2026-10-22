from webfluid import Fluid
from webfluid.core.ext import babel
from webfluid.core.config import DefaultConfig


def prepare_fluid() -> Fluid:
    _fluid = Fluid(__name__)
    base_url = _fluid.config["BASE_URL"]

    _fluid.add_source('<link rel="preconnect" href="https://fonts.googleapis.com">', 10)
    _fluid.add_source('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', 10)
    _fluid.add_source(
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&'
        'family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">',
        10
    )

    if _fluid.name == "home":
        base_url = _fluid.config.get("HOME_URL", "https://webfluid.dev")

        from .app import home_router, setup_home
        setup_home()
        _fluid.include_router(home_router)

        from fluid.i18n import translations
        babel.update_translations("messages", translations)

    elif _fluid.name == "docs":
        base_url = _fluid.config.get("DOCS_URL", "https://docs.webfluid.dev")

        from .app import docs_router, setup_docs
        setup_docs()
        _fluid.include_router(docs_router)
        _fluid.jinja_env.globals["versions"] = _fluid.config["VERSIONS"].keys()

    elif _fluid.name == "ocean":
        base_url = _fluid.config.get("OCEAN_URL", "https://ocean.webfluid.dev")

        from .app import ocean_router, setup_ocean
        setup_ocean()
        _fluid.include_router(ocean_router)

    _fluid.jinja_env.globals["latest"] = _fluid.config["LATEST_VERSION"]
    _fluid.jinja_env.globals["home"] = base_url
    _fluid.jinja_env.globals["docs"] = base_url
    _fluid.jinja_env.globals["ocean"] = base_url

    if base_url == DefaultConfig.BASE_URL:
        _fluid.config["BASE_URL"] = base_url

    return _fluid
