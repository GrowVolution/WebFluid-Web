from webfluid.core.config import register_config

from fluid._my_config import MyConfig


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

    VERSIONS = {
        "1.0.0a1": {
            "stage": "alpha",
            "date": "May 22, 2026",
        },
        "1.0.0a2": {
            "stage": "alpha",
            "date": "June 13, 2026",
        }
    }
    LATEST_VERSION = "1.0.0a2"
