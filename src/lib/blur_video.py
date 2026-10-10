import logging
import os
import subprocess
import tempfile
from typing import Callable

from src.lib.computer_similarity import compute_similarity
from src.lib.constants import (
    MAX_VIDEO_PIXELS,
    MAX_VIDEO_SECONDS,
    SIMILARITY_THRESHOLD,
)
from src.lib.ffmpeg import build_ffmpeg_command
from src.lib.get_detector import get_detector, get_recognizer
from src.lib.get_single_face_embedding import get_single_face_embedding
from src.types.blur_types import BlurMethod

logger = logging.getLogger(__name__)

TimestampRange = tuple[float, float]


def build_remux_command(temp_video: str, video_path: str, output_path: str) -> list[str]:
    """Shared ffmpeg remux command (single trailing output). Testable."""
    return build_ffmpeg_command(temp_video, video_path, output_path)


def process_frame_blur(frame, detector, blurrer):
    faces = detector.detect(frame)

    return blurrer.anonymize(frame, faces)


def process_frame_filtered(frame, detector, recognizer, blurrer, target_face):
    detected_faces = detector.detect(frame)

    filtered_faces = []

    for face in detected_faces:
        embedding = recognizer.get_normalized_embedding(frame, face.landmarks)

        similarity = compute_similarity(emb1=target_face, emb2=embedding)

        if similarity <= SIMILARITY_THRESHOLD:
            filtered_faces.append(face)

    return blurrer.anonymize(frame, filtered_faces)


def _open_capture(video_path: str):
    import cv2

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        cap.release()
        raise ValueError("Could not determine video FPS")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        cap.release()
        raise ValueError("Could not determine video dimensions")
    if width * height > MAX_VIDEO_PIXELS:
        cap.release()
        raise ValueError(
            f"Video resolution {width}x{height} exceeds the "
            f"{MAX_VIDEO_PIXELS}-pixel cap"
        )
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if frame_count > 0 and frame_count / fps > MAX_VIDEO_SECONDS:
        cap.release()
        raise ValueError(
            f"Video longer than {MAX_VIDEO_SECONDS}s is not supported"
        )
    return cap, fps, width, height


def _process_video(video_path: str, output_path: str, process_frame: Callable) -> None:
    import cv2

    cap, fps, width, height = _open_capture(video_path)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp:
        temp_video = temp.name

    writer = None

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
        if not writer.isOpened():
            raise ValueError("Could not create temporary video")

        n_faces_total = 0
        n_frames = 0
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            processed_frame = process_frame(frame)
            n_frames += 1

            writer.write(processed_frame)
        logger.info("Processed %d frames from %s", n_frames, video_path)

    finally:
        cap.release()

        if writer:
            writer.release()

    try:
        subprocess.run(
            build_remux_command(temp_video, video_path, output_path),
            check=True,
        )

    finally:
        if os.path.exists(temp_video):
            os.remove(temp_video)


def blur_video(video_path: str, output_path: str, blur_type: BlurMethod) -> None:
    from uniface.detection import RetinaFace
    from uniface.privacy import BlurFace

    detector: RetinaFace = get_detector()
    blurrer = BlurFace(method=blur_type.value)

    def process_frame(frame):
        return process_frame_blur(frame, detector, blurrer)

    _process_video(video_path=video_path, output_path=output_path, process_frame=process_frame)


def blur_video_filtered(
    video_path: str, output_path: str, blur_type: BlurMethod, faceId: str = "", face_id: str = ""
) -> None:
    from uniface.privacy import BlurFace

    reference = face_id or faceId
    if not reference:
        raise ValueError("face_id is required")

    detector = get_detector()
    recognizer = get_recognizer()
    blurrer = BlurFace(method=blur_type.value)

    target_face = get_single_face_embedding(face_id=reference)

    def process_frame(frame):
        return process_frame_filtered(frame, detector, recognizer, blurrer, target_face)

    _process_video(video_path=video_path, output_path=output_path, process_frame=process_frame)
