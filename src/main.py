import os
import modal



TEMP_DIR = "temp"

OUTPUT_VIDEOS_DIR = os.path.join(TEMP_DIR, "outputs", "videos")
OUTPUT_IMAGES_DIR = os.path.join(TEMP_DIR, "outputs", "images")

INPUT_VIDEOS_DIR = os.path.join(TEMP_DIR, "inputs", "videos")
INPUT_IMAGES_DIR = os.path.join(TEMP_DIR, "inputs", "images")


def setup():
    os.makedirs(OUTPUT_VIDEOS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)
    os.makedirs(INPUT_VIDEOS_DIR, exist_ok=True)
    os.makedirs(INPUT_IMAGES_DIR, exist_ok=True)


app = modal.App("blurfield-api")

img = (
    modal.Image.from_registry(
        "nvidia/cuda:13.3.0-cudnn-devel-ubuntu24.04",
        add_python="3.12",
    )
    .apt_install("ffmpeg")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir(
        "src",
        remote_path="/root/src",
    )
)

secrets = modal.Secret.from_name("blur")


@app.function(
    image=img,
    secrets=[secrets],
)
@modal.asgi_app()
def api():
    from fastapi import FastAPI
    from src.routers import photo_routers
    from src.routers import video_routers

    setup()

    web_app = FastAPI()

    web_app.include_router(photo_routers.router)
    web_app.include_router(video_routers.router)

    return web_app