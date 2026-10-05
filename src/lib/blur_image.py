import cv2

from cv2.typing import MatLike
from uniface.privacy import BlurFace
from uniface.recognition import ArcFace                
from src.lib.computer_similarity import compute_similarity
from src.lib.get_detector import get_detector
from src.lib.get_single_face_embedding import get_single_face_embedding
from src.types.blur_types import BlurMethod


def _blur_faces(
    img: MatLike,
    faces,
    blur_type: BlurMethod,
    output_path: str,
) -> None:
    blurrer = BlurFace(method=blur_type.value)

    anonymized = blurrer.anonymize(img, faces)

    success = cv2.imwrite(output_path, anonymized)

    if not success:
        raise IOError(f"Could not write image: {output_path}")


def blur_image(
    img: str,
    blur_type: BlurMethod,
    output_path: str,
) -> None:
    image = cv2.imread(img)

    if image is None:
        raise ValueError(f"Could not read image: {img}")

    detector = get_detector()
    faces = detector.detect(image)

    _blur_faces(
        image,
        faces,
        blur_type,
        output_path,
    )


def blur_image_with_filter(
    img: str,
    face_id: str,
    blur_type: BlurMethod,
    output_path: str,
) -> None:
    image = cv2.imread(img)

    if image is None:
        raise ValueError(f"Could not read image: {img}")

    detector = get_detector()
    recognizer = ArcFace()

    faces = detector.detect(image)

    target_face = get_single_face_embedding(faceId=face_id)

    if target_face is None:
        raise ValueError("Error recognizing target face")

    threshold = 0.3

    filtered_faces = [
        face
        for face in faces
        if compute_similarity(
            target_face,
            recognizer.get_normalized_embedding(
                image,
                face.landmarks,
            ),
        ) <= threshold
    ]

    _blur_faces(
        image,
        filtered_faces,
        blur_type,
        output_path,
    )