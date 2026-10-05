import cv2
import subprocess
import tempfile
import os
from typing import Callable

from uniface.recognition import ArcFace
from uniface.detection import RetinaFace
from uniface.privacy import BlurFace

from src.lib.computer_similarity import compute_similarity
from src.lib.get_single_face_embedding import get_single_face_embedding
from src.types.blur_types import BlurMethod


SIMILARITY_THRESHOLD = 0.3

TimestampRange = tuple[float, float]


def process_frame_blur(
    frame,
    detector: RetinaFace,
    blurrer: BlurFace,
):
    faces = detector.detect(frame)

    return blurrer.anonymize(
        frame,
        faces,
    )


def process_frame_filtered(
    frame,
    detector: RetinaFace,
    recognizer: ArcFace,
    blurrer: BlurFace,
    target_face,
):
    detected_faces = detector.detect(frame)

    filtered_faces = []

    for face in detected_faces:
        embedding = recognizer.get_normalized_embedding(
            frame,
            face.landmarks,
        )

        similarity = compute_similarity(
            emb1=target_face,
            emb2=embedding,
        )

        if similarity <= SIMILARITY_THRESHOLD:
            filtered_faces.append(face)

    return blurrer.anonymize(
        frame,
        filtered_faces,
    )


def _process_video(
    video_path: str,
    output_path: str,
    process_frame: Callable,
) -> None:

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    with tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False,
    ) as temp:
        temp_video = temp.name

    writer = None

    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        writer = cv2.VideoWriter(
            temp_video,
            fourcc,
            fps,
            (width, height),
        )

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            processed_frame = process_frame(frame)

            writer.write(processed_frame)

    finally:
        cap.release()

        if writer:
            writer.release()

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", temp_video,
                "-i", video_path,

                "-map", "0:v:0",
                "-map", "1:a:0?",

                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",

                "-c:a", "aac",

                "-shortest",
                output_path,
            ],
            check=True,
        )

    finally:
        if os.path.exists(temp_video):
            os.remove(temp_video)


def blur_video(
    video_path: str,
    output_path: str,
    blur_type: BlurMethod,
) -> None:

    detector = RetinaFace()
    blurrer = BlurFace(method=blur_type.value)

    process_frame = lambda frame: process_frame_blur(
        frame,
        detector,
        blurrer,
    )

    _process_video(
        video_path=video_path,
        output_path=output_path,
        process_frame=process_frame,
    )


def blur_video_filtered(
    video_path: str,
    output_path: str,
    blur_type: BlurMethod,
    faceId: str,
) -> None:

    detector = RetinaFace()
    recognizer = ArcFace()
    blurrer = BlurFace(method=blur_type.value)

    target_face = get_single_face_embedding(
        faceId=faceId,
    )

    process_frame = lambda frame: process_frame_filtered(
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
    )