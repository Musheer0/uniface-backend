import cv2

from cv2.typing import MatLike
from uniface.privacy import BlurFace

from src.lib.computer_similarity import compute_similarity
from src.lib.constants import SIMILARITY_THRESHOLD
from src.lib.get_detector import get_detector, get_recognizer
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
    """Blur everyone *except* the reference face.

    Faces whose embedding distance to the reference is <=
    SIMILARITY_THRESHOLD are considered different people and blurred;
    the matching face is kept clear.
    """
    image = cv2.imread(img)

    if image is None:
        raise ValueError(f"Could not read image: {img}")

    detector = get_detector()
    recognizer = get_recognizer()

    faces = detector.detect(image)

    target_face = get_single_face_embedding(face_id=face_id)

    if target_face is None:
        raise ValueError("Error recognizing target face")

    filtered_faces = [
        face
        for face in faces
        if compute_similarity(
            target_face,
            recognizer.get_normalized_embedding(
                image,
                face.landmarks,
            ),
        )
        <= SIMILARITY_THRESHOLD
    ]

    _blur_faces(
        image,
        filtered_faces,
        blur_type,
        output_path,
    )
