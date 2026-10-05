def compute_similarity(emb1, emb2):
    from uniface import compute_similarity
    similarty = compute_similarity(emb1, emb2,normalized=True)
    return similarty