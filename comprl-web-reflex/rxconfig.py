import os
import reflex as rx


class CustomConfig(rx.Config):
    # path to comprl config file
    comprl_config_path: str = ""


# seems that in recent reflex versions, it doesn't automatically load custom config
# values from environment variables anymore, so we do it manually here
try:
    comprl_config_path = os.environ["COMPRL_CONFIG_PATH"]
except KeyError:
    msg = "Environment variable COMPRL_CONFIG_PATH is not set."
    raise RuntimeError(msg) from None

config = CustomConfig(
    app_name="comprl_web",
    telemetry_enabled=False,
    show_built_with_reflex=False,
    plugins=[rx.plugins.SitemapPlugin()],
    comprl_config_path=comprl_config_path,
)
