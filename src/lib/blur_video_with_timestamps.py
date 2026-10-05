import cv2
import subprocess
import tempfile
import os

from typing import Callable

from uniface.recognition import ArcFace
from uniface.detection import RetinaFace
from uniface.privacy import BlurFace

from src.lib.blur_video import process_frame_blur, process_frame_filtered
from src.lib.computer_similarity import compute_similarity
from src.lib.get_single_face_embedding import get_single_face_embedding
from src.types.blur_types import BlurMethod


SIMILARITY_THRESHOLD = 0.5

TimestampRange = tuple[float, float]
TimestampRanges = list[TimestampRange]




def _process_video(
    video_path: str,
    output_path: str,
    process_frame: Callable,
    timestamps: TimestampRanges,
) -> None:
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(
            f"Could not open video: {video_path}"
        )

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        cap.release()
        raise ValueError("Could not determine video FPS")

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    frame_number = 0

    with tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False,
    ) as temp:
        temp_video = temp.name

    writer = None

    try:
        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        writer = cv2.VideoWriter(
            temp_video,
            fourcc,
            fps,
            (width, height),
        )

        if not writer.isOpened():
            raise ValueError(
                "Could not create temporary video"
            )

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            timestamp = frame_number / fps

            should_process = any(
                start <= timestamp <= end
                for start, end in timestamps
            )

            if should_process:
                processed_frame = process_frame(frame)
            else:
                processed_frame = frame

            writer.write(processed_frame)

            frame_number += 1

    finally:
        cap.release()

        if writer:
            writer.release()

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",

                # Processed video
                "-i",
                temp_video,

                # Original video for audio
                "-i",
                video_path,

                # Video from processed file
                "-map",
                "0:v:0",

                # Audio from original file
                "-map",
                "1:a:0?",

                # Encode video
                "-c:v",
                "libx264",

                "-preset",
                "medium",

                "-crf",
                "23",

                # Encode audio
                "-c:a",
                "aac",

                "-shortest",

                output_path,
            ],
            check=True,
        )

    finally:
        if os.path.exists(temp_video):
            os.remove(temp_video)


def blur_video_timestamps(
    video_path: str,
    output_path: str,
    blur_type: BlurMethod,
    timestamps: TimestampRanges,
) -> None:
    detector = RetinaFace()

    blurrer = BlurFace(
        method=blur_type.value
    )

    def process_frame(frame):
        return process_frame_blur(
            frame,
            detector,
            blurrer,
        )

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
    faceId: str,
    timestamps: TimestampRanges,
) -> None:
    detector = RetinaFace()
    recognizer = ArcFace()

    blurrer = BlurFace(
        method=blur_type.value
    )

    target_face = get_single_face_embedding(
        faceId=faceId,
    )

    def process_frame(frame):
        return process_frame_filtered(
            frame,
            detector,
            recognizer,
            blurrer,
            target_face,
        )

    _process_video(
        video_path=video_path,
        output_path=output_path,
        process_frame=process_frame,
        timestamps=timestamps,
    )