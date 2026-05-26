from webfluid import Fluid
import os


def create_app() -> Fluid:
    app = Fluid(__name__)

    server = os.getenv("SERVER")
    if server == "home":
        from fluid.app import home_router
        app.include_router(home_router)
    elif server == "docs":
        from fluid.app import docs_router
        app.include_router(docs_router)
        app.jinja_context["versions"] = app.config["VERSIONS"].keys()

    app.jinja_context["latest"] = app.config["LATEST_VERSION"]
    app.jinja_context["home"] = app.config.get("HOME_URL", "https://webfluid.dev")
    app.jinja_context["docs"] = app.config.get("DOCS_URL", "https://docs.webfluid.dev")
    app.jinja_context["ocean"] = app.config.get("OCEAN_URL", "https://ocean.webfluid.dev")
                
    return app


if __name__ == "__main__":
    fluid = create_app()
    fluid.mix()
