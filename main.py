from webfluid import Fluid


def create_app() -> Fluid:
    app = Fluid(__name__)

    if app.name == "home":
        from fluid.app import home_router
        app.include_router(home_router)
    elif app.name == "docs":
        from fluid.app import docs_router
        app.include_router(docs_router)
        app.jinja_env.globals["versions"] = app.config["VERSIONS"].keys()

    app.jinja_env.globals["latest"] = app.config["LATEST_VERSION"]
    app.jinja_env.globals["home"] = app.config.get("HOME_URL", "https://webfluid.dev")
    app.jinja_env.globals["docs"] = app.config.get("DOCS_URL", "https://docs.webfluid.dev")
    app.jinja_env.globals["ocean"] = app.config.get("OCEAN_URL", "https://ocean.webfluid.dev")
                
    return app


if __name__ == "__main__":
    fluid = create_app()
    fluid.mix()
