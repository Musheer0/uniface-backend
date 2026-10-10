import logging
import os

import modal

from src.lib.constants import (
    INPUT_IMAGES_DIR,
    INPUT_VIDEOS_DIR,
    OUTPUT_IMAGES_DIR,
    OUTPUT_VIDEOS_DIR,
    TEMP_DIR,
)

# Re-exported for backward compatibility (routers used to import these here).
__all__ = [
    "TEMP_DIR",
    "OUTPUT_VIDEOS_DIR",
    "OUTPUT_IMAGES_DIR",
    "INPUT_VIDEOS_DIR",
    "INPUT_IMAGES_DIR",
    "setup",
    "app",
    "api",
    "create_app",
]

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

logger = logging.getLogger(__name__)

MODAL_SECRET_NAME = os.getenv("MODAL_SECRET_NAME", "blur")
# Long GPU jobs (full videos) need headroom over Modal's default timeout.
MODAL_TIMEOUT_SECONDS = int(os.getenv("MODAL_TIMEOUT_SECONDS", "1800"))


def setup():
    os.makedirs(OUTPUT_VIDEOS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)
    os.makedirs(INPUT_VIDEOS_DIR, exist_ok=True)
    os.makedirs(INPUT_IMAGES_DIR, exist_ok=True)


def create_app():
    """Build the FastAPI app (importable without Modal for tests/dev)."""
    from fastapi import FastAPI

    from src.middlewares.auth_middleware import TrackingHeadersMiddleware
    from src.routers import health_routers, photo_routers, video_routers, video_timestamp_routers

    setup()

    # Optional Sentry (sentry-sdk ships in requirements; no-op unless configured).
    if os.getenv("SENTRY_DSN"):
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=os.getenv("SENTRY_DSN"),
                environment=os.getenv("SENTRY_ENV", "production"),
            )
            logger.info("Sentry initialized")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Sentry init failed: %s", exc)

    web_app = FastAPI(title="Blurfield API")

    web_app.add_middleware(TrackingHeadersMiddleware)

    web_app.include_router(health_routers.router)
    web_app.include_router(photo_routers.router)
    web_app.include_router(video_routers.router)
    web_app.include_router(video_timestamp_routers.router)
    return web_app


app = modal.App("blurfield-api")

img = (
    modal.Image.from_registry(
        "nvidia/cuda:13.3.0-cudnn-devel-ubuntu24.04",
        add_python="3.12",
    )
    .apt_install("ffmpeg")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir("src", remote_path="/root/src")
)

try:
    secrets = [modal.Secret.from_name(MODAL_SECRET_NAME)]
except Exception:  # noqa: BLE001 - resolved lazily at deploy time
    secrets = []


@app.function(image=img, secrets=secrets, timeout=MODAL_TIMEOUT_SECONDS)
@modal.asgi_app()
def api():
    return create_app()
