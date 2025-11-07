# src/embeddings/vector_store.py

from typing import Optional, Dict, Any, Tuple, List
import json
import chromadb
import numpy as np

class VectorStore:
    def __init__(self, persist_dir: str = "./chroma_store"):
        self.client = chromadb.PersistentClient(path=persist_dir)

    def _collection_name(self, label: str) -> str:
        return f"label__{label}"

    def get_or_create_collection(self, label: str):
        name = self._collection_name(label)
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_document(
        self,
        label: str,
        doc_id: str,
        embedding: np.ndarray,
        pdf_raw_text: str,
        extracted_fields: Dict[str, Any],
        requested_fields: Optional[List[str]] = None,
    ) -> None:

        col = self.get_or_create_collection(label)

        metadata = {
            "pdf_raw_text": pdf_raw_text,
            "extracted_fields_json": json.dumps(
                extracted_fields,
                ensure_ascii=False,
            ),
            "label": label,
            "requested_fields": json.dumps(requested_fields or [], ensure_ascii=False),
        }

        col.add(
            ids=[doc_id],
            embeddings=[embedding.tolist()],
            documents=[pdf_raw_text],
            metadatas=[metadata],
        )

    def query_most_similar(
        self,
        label: str,
        embedding: np.ndarray,
        top_k: int = 1,
    ) -> Optional[Tuple[float, Dict[str, Any]]]:

        col = self.get_or_create_collection(label)

        try:
            res = col.query(
                query_embeddings=[embedding.tolist()],
                n_results=top_k,
                include=["distances", "metadatas", "documents"],
            )
        except Exception as e:
            print(f"[VSTORE::QUERY] EXCEPTION during query: {e}")
            return None

        dists_list = res.get("distances", [[]])
        metas_list = res.get("metadatas", [[]])

        if not dists_list or not metas_list:
            print("[VSTORE::QUERY] empty result (no lists)")
            return None

        if len(dists_list[0]) == 0 or len(metas_list[0]) == 0:
            print("[VSTORE::QUERY] empty result (no items in first list)")
            return None

        best_distance = dists_list[0][0]
        best_meta = metas_list[0][0]

        print(f"[VSTORE::QUERY] found candidate dist={best_distance:.4f}")
        return best_distance, best_meta
