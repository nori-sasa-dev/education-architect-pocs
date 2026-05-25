"""日本語対応の埋め込みモデルを共有シングルトンとして提供する"""
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"

_encoder: SentenceTransformer | None = None


def get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer(MODEL_NAME)
    return _encoder


def encode(text: str) -> list[float]:
    return get_encoder().encode(text).tolist()


def encode_batch(texts: list[str]) -> list[list[float]]:
    return get_encoder().encode(texts).tolist()
