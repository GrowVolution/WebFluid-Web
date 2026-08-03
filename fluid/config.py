from webfluid.core.config import register_config

try: from fluid._my_config import MyConfig
except ImportError:
    class MyConfig: pass


@register_config(10)
class Config(MyConfig):
    APP_CONFIG = {
        "title": "WebFluid",
        "version": "1.0.0",
        "docs_url": None,
        "redoc_url": None
    }
    APP_FRONTEND = {
		'type': 'none'
	}

    HOME_LASTMOD = "2026-08-01"

    VERSIONS = {
        "1.0.0a1": {
            "stage": "alpha",
            "date": "May 22, 2026"
        },
        "1.0.0a2": {
            "stage": "alpha",
            "date": "July 06, 2026"
        },
        "1.0.0b1": {
            "stage": "beta",
            "date": "August 01, 2026"
        },
        "1.0.0b2": {
            "stage": "beta",
            "date": "August 03, 2026"
        }
    }
    LATEST_VERSION = "1.0.0b2"

    OCEAN_SITEMAP_EXTRA = {
        "/terms": "2026-07-11",
        "/licensing": "2026-07-11"
    }

    BABEL_DEFAULT_LOCALE = "en"
    BABEL_SUPPORTED_LOCALES = [BABEL_DEFAULT_LOCALE, "de"]

    PROXY_FIX = True
    PROXY_TRUSTED_HOSTS = "*"
