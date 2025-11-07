# src/embeddings/embeddings.py

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Union, List

class EmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, text: Union[str, List[str]]) -> np.ndarray:
        if isinstance(text, str):
            emb = self.model.encode([text], normalize_embeddings=True)
            return np.array(emb[0], dtype="float32")
        else:
            emb = self.model.encode(text, normalize_embeddings=True)
            return np.array(emb, dtype="float32")
