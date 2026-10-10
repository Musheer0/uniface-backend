import logging
import os
import subprocess
import tempfile

from typing import Callable

from src.lib.blur_video import _open_capture, process_frame_blur, process_frame_filtered
from src.lib.constants import MAX_TIMESTAMP_RANGES, MAX_TIMESTAMP_SECONDS
from src.lib.ffmpeg import build_ffmpeg_command
from src.lib.get_detector import get_detector, get_recognizer
from src.lib.get_single_face_embedding import get_single_face_embedding
from src.types.blur_types import BlurMethod, TimestampRanges

logger = logging.getLogger(__name__)


def validate_timestamps(timestamps: TimestampRanges) -> TimestampRanges:
    """Validate timestamp ranges: non-empty entries, start <= end, sane caps."""
    if len(timestamps) > MAX_TIMESTAMP_RANGES:
        raise ValueError(f"Too many timestamp ranges (max {MAX_TIMESTAMP_RANGES})")
    cleaned: TimestampRanges = []
    for start, end in timestamps:
        start_f, end_f = float(start), float(end)
        if start_f < 0 or end_f < 0:
            raise ValueError("timestamp ranges must be non-negative")
        if start_f > end_f:
            raise ValueError(f"invalid timestamp range: start {start_f} > end {end_f}")
        if end_f > MAX_TIMESTAMP_SECONDS:
            raise ValueError(
                f"timestamp range end {end_f} exceeds cap of {MAX_TIMESTAMP_SECONDS}s"
            )
        cleaned.append((start_f, end_f))
    return cleaned


def _process_video(
    video_path: str,
    output_path: str,
    process_frame: Callable,
    timestamps: TimestampRanges,
) -> None:
    import cv2

    timestamps = validate_timestamps(timestamps)
    cap, fps, width, height = _open_capture(video_path)

    frame_number = 0

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp:
        temp_video = temp.name

    writer = None

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

        if not writer.isOpened():
            raise ValueError("Could not create temporary video")

        n_blurred = 0
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            timestamp = frame_number / fps

            should_process = any(start <= timestamp <= end for start, end in timestamps)

            if should_process:
                processed_frame = process_frame(frame)
                n_blurred += 1
            else:
                processed_frame = frame

            writer.write(processed_frame)

            frame_number += 1
        logger.info(
            "Timestamp blur: %d/%d frames blurred from %s",
            n_blurred,
            frame_number,
            video_path,
        )

    finally:
        cap.release()

        if writer:
            writer.release()

    try:
        subprocess.run(
            build_ffmpeg_command(temp_video, video_path, output_path),
            check=True,
        )

    finally:
        if os.path.exists(temp_video):
            os.remove(temp_video)


def blur_video_timestamps(
    video_path: str, output_path: str, blur_type: BlurMethod, timestamps: TimestampRanges
) -> None:
    from uniface.privacy import BlurFace

    detector = get_detector()
    blurrer = BlurFace(method=blur_type.value)

    def process_frame(frame):
        return process_frame_blur(frame, detector, blurrer)

    _process_video(
        video_path=video_path,
        output_path=output_path,
        process_frame=process_frame,
        timestamps=timestamps,
    )


def blur_video_filtered_timestamp(
    video_path: str,
    output_path: str,
    blur_type: BlurMethod,
    faceId: str = "",
    face_id: str = "",
    timestamps: TimestampRanges | None = None,
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

    _process_video(
        video_path=video_path,
        output_path=output_path,
        process_frame=process_frame,
        timestamps=timestamps or [],
    )
