from typing import Any


def compute_similarity(emb1: Any, emb2: Any) -> float:
    """Cosine distance between two *normalized* embeddings.

    Lower means the same person. Filtered routes blur a detected face when
    ``compute_similarity(reference, candidate) <= SIMILARITY_THRESHOLD``
    (i.e. the candidate is *different* from the reference) and keep the
    reference person clear.
    """
    from uniface import compute_similarity as _compute_similarity

    return float(_compute_similarity(emb1, emb2, normalized=True))
