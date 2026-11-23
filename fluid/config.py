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
        "type": "none"
    }

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
        },
        "1.0.0b3": {
            "stage": "beta",
            "date": "August 17, 2026"
        }
    }
    LATEST_VERSION = "1.0.0b3"

    DOCS_ORDER = (
        "index", "get-started",
        "config/app-config", "config/config-class",
        "ext/base", "ext/scheduling", "ext/sqlalchemy", "ext/migrate",
        "ext/mailman", "ext/babel", "ext/security", "ext/events",
        "ext/cache", "ext/jwt",
        "surface/tooling", "surface/frontend", "surface/jinja",
        "additives/intro", "additives/base", "additives/contract",
        "utils/lifecycle", "utils/runtime", "utils/logging",
        "cli/wf", "cli/create", "cli/run", "cli/ocean",
        "ref", "ref/core", "ref/extensions",
        "ref/surface", "ref/additives", "ref/utils"
    )

    HOME_LASTMOD = "2026-10-22"
    OCEAN_INDEX_LASTMOD = "2026-08-16"
    OCEAN_SITEMAP_EXTRA = {
        "/terms": "2026-11-04",
        "/licensing": "2026-11-04"
    }

    COMPLIANCE_TERMS_TEMPLATE = "ocean/terms.html"
    COMPLIANCE_OPERATOR = {
        "name": "GrowVolution e.V.",
        "brand": "WebFluid Ocean",
        "legal_form": "eingetragener Verein",
        "address": {
            "line1": "Schöninger Straße 17",
            "postal_code": "38173",
            "city": "Sickte",
            "country": "DE"
        },
        "email": "info@growvolution.org",
        "phone": None,
        "website": "https://growvolution.org",
        "representative": None,
        "register": None,
        "vat_id": None,
        "country": "DE"
    }
    COMPLIANCE_VARIABLES = {
        "partner": "seller",
        "threshold": 3,
        "days": 30
    }
    STRIPE_TAX_CODES = {
        "ocean.package.b2c": "txcd_10202000",
        "ocean.package.b2b": "txcd_10202003"
    }

    BABEL_DEFAULT_LOCALE = "en"
    BABEL_SUPPORTED_LOCALES = [BABEL_DEFAULT_LOCALE, "de"]

    PROXY_FIX = True
    PROXY_TRUSTED_HOSTS = getattr(MyConfig, "PROXY_TRUSTED_HOSTS", "127.0.0.1,::1")
