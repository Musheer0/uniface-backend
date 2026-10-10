import logging
import os

from fastapi import APIRouter, Depends

from src.lib.blur_video import blur_video, blur_video_filtered
from src.lib.constants import INPUT_VIDEOS_DIR, OUTPUT_VIDEOS_DIR, base_api_path
from src.lib.download_file import download_file
from src.lib.paths import ensure_parent, safe_join
from src.lib.upload_file import upload_file
from src.middlewares.auth_middleware import InternalAuthorization
from src.routers._helpers import cleanup_paths, to_http_exception
from src.schemas.blur_video_schemas import BlurEveryoneFilteredRequest, BlurEveryoneRequest
from src.types.base_response import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=base_api_path + "/blur-video",
    dependencies=[Depends(InternalAuthorization)],
)


@router.post("/everyone")
def blur_everyone(Body: BlurEveryoneRequest) -> BaseResponse:
    input_base = os.path.join(INPUT_VIDEOS_DIR, Body.generation_id)
    output_base = os.path.join(OUTPUT_VIDEOS_DIR, Body.generation_id)
    output_path = ensure_parent(safe_join(output_base, Body.output_key))
    input_path = ensure_parent(safe_join(input_base, Body.video_key))
    try:
        local_video = download_file(file_key=Body.video_key, file_path=input_path)
        blur_video(blur_type=Body.blur_method, video_path=local_video, output_path=output_path)
        upload_file(file_path=output_path, file_key=Body.output_key)
        logger.info(
            "[generation_id=%s] video blurred: %s -> %s",
            Body.generation_id, Body.video_key, Body.output_key,
        )
        return BaseResponse(
            success=True, generation_id=Body.generation_id, user_id=Body.user_id
        )
    except Exception as exc:
        cleanup_paths(output_path)
        raise to_http_exception(exc, Body.generation_id) from exc
    finally:
        cleanup_paths(input_path)


@router.post("/everyone/filtered")
@router.post("/everyone/filerer", include_in_schema=False)  # legacy typo alias
def blur_everyone_filtered(Body: BlurEveryoneFilteredRequest) -> BaseResponse:
    input_base = os.path.join(INPUT_VIDEOS_DIR, Body.generation_id)
    output_base = os.path.join(OUTPUT_VIDEOS_DIR, Body.generation_id)
    output_path = ensure_parent(safe_join(output_base, Body.output_key))
    input_path = ensure_parent(safe_join(input_base, Body.video_key))
    face_path = ensure_parent(safe_join(input_base, Body.face_key))
    try:
        local_video = download_file(file_key=Body.video_key, file_path=input_path)
        local_face = download_file(file_key=Body.face_key, file_path=face_path)
        blur_video_filtered(
            blur_type=Body.blur_method,
            video_path=local_video,
            output_path=output_path,
            face_id=local_face,
        )
        upload_file(file_path=output_path, file_key=Body.output_key)
        logger.info(
            "[generation_id=%s] video filtered blur: %s -> %s",
            Body.generation_id, Body.video_key, Body.output_key,
        )
        return BaseResponse(
            success=True, generation_id=Body.generation_id, user_id=Body.user_id
        )
    except Exception as exc:
        cleanup_paths(output_path)
        raise to_http_exception(exc, Body.generation_id) from exc
    finally:
        cleanup_paths(input_path, face_path)
