# src/embeddings/rag.py

from __future__ import annotations
from typing import Optional, Tuple, Any
from .embeddings import EmbeddingModel
from .vector_store import VectorStore

class RAGContextBuilder:
    def __init__(self, embedder: EmbeddingModel, vstore: VectorStore) -> None:
        self.embedder = embedder
        self.vstore = vstore

    def build(self, label: str, current_pdf_text: str) -> Tuple[Optional[str], Any]:
        curr_emb = self.embedder.encode(current_pdf_text)
        best = self.vstore.query_most_similar(label=label, embedding=curr_emb, top_k=1)
        if best is None:
            return None, curr_emb
        best_distance, best_meta = best
        prev_text = best_meta.get("pdf_raw_text", "")
        prev_json_str = best_meta.get("extracted_fields_json", "{}")
        prev_requested_fields = best_meta.get("requested_fields", "[]")
        rag_context = (
            f"[SIMILARITY_DISTANCE]: {best_distance:.4f}\n\n"
            f"[LABEL]: {best_meta.get('label', '')}\n\n"
            f"[PAST_REQUESTED_FIELDS]: {prev_requested_fields}\n\n"
            f"[PAST_TEXT_SNIPPET]:\n{prev_text[:1000]}\n\n"
            f"[PAST_EXTRACTION_JSON]:\n{prev_json_str}\n"
        )
        return rag_context, curr_emb
