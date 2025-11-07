# src/pipeline/pipeline.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

from modal_endpoint_app.src.pipeline.types import CacheEntry, ResultPayload
from modal_endpoint_app.src.parsing.cache import DocumentCache
from modal_endpoint_app.src.extraction.extraction import ExtractionOrchestrator
from modal_endpoint_app.src.parsing.pdf_text_parser import PDFExtractor
from modal_endpoint_app.src.embeddings.embeddings import EmbeddingModel
from modal_endpoint_app.src.embeddings.vector_store import VectorStore
from modal_endpoint_app.src.embeddings.rag import RAGContextBuilder


class Solution:
    """
    High-level orchestration for parsing PDFs, extracting fields, building RAG context,
    caching results, and recording metadata/embeddings into a vector store.

    Public API:
        - process_single_sample(...): main entry point to process one labeled PDF.
    """

    def __init__(
        self,
        persist_dir: Path = Path("./chroma_store"),
        cache_capacity: int = 2000,
    ) -> None:
        """
        Initialize core dependencies and an LRU cache keyed by document.

        Args:
            persist_dir: Filesystem directory used by the vector store to persist data.
            cache_capacity: Maximum number of document entries kept in the LRU cache.
        """
        # Core dependencies
        self.embedder = EmbeddingModel()
        self.vstore = VectorStore(persist_dir=str(persist_dir))
        self.rag = RAGContextBuilder(self.embedder, self.vstore)
        self.orchestrator = ExtractionOrchestrator()

        # LRU by document
        self.cache = DocumentCache(capacity=cache_capacity)

    # --------------- Public API ---------------

    def process_single_sample(
        self,
        idx: int,
        label: str,
        extraction_schema: dict,
        pdf_path: str,
        pdf_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a single labeled PDF:
          1) Build a stable document key and consult the cache.
          2) If all requested fields are cached, return them and ensure vector-store registration once.
          3) Otherwise, build RAG context and extract only missing fields.
          4) Merge results, persist (cache + vector store), and return a payload.

        Args:
            idx: Sample index (used for fallback doc_id).
            label: Document class/label.
            extraction_schema: Dict with the fields expected to be extracted (keys are used).
            pdf_path: Full path to the PDF file.
            pdf_content: Optional pre-parsed raw text of the PDF to skip re-reading.

        Returns:
            A dict equivalent to ResultPayload.__dict__ with fields:
              - label
              - pdf_filename
              - requested_fields (dict[str, Optional[str]])
        """
        pdf_filename, pdfs_root_path = self._split_pdf_path(pdf_path)
        signature, doc_key = self._build_doc_key(label, pdfs_root_path, pdf_filename)
        self.cache.upsert_latest_key(label, pdf_filename, doc_key)

        pdf_raw_text = self._load_pdf_text(pdf_content, pdfs_root_path, pdf_filename)

        # Cache lookup and partition into present/missing keys
        entry = self.cache.get(doc_key)
        extraction_keys = self._schema_keys(extraction_schema)
        cached_fields = dict(entry.fields) if entry else {}
        present, missing = self._partition_fields(extraction_keys, cached_fields)
        have_all = len(missing) == 0

        if have_all:
            self._log(f"[CACHE HIT-ALL] idx={idx} label={label} pdf={pdf_filename}")
            extracted_fields = {k: cached_fields.get(k) for k in extraction_keys}
            # Ensure the document is added to the vector store exactly once
            if entry and not entry.vstore_added:
                self._ensure_vstore_once(
                    entry=entry,
                    label=label,
                    pdf_filename=pdf_filename,
                    pdf_raw_text=pdf_raw_text,
                    extracted_fields=extracted_fields,
                    requested_fields=extraction_keys,
                    doc_id=self._doc_id(pdf_filename, idx),
                    doc_key=doc_key,
                )
            payload = ResultPayload(
                label=label,
                pdf_filename=pdf_filename,
                requested_fields=extracted_fields,
            )
            return payload.__dict__

        # Partial or miss → extract only missing keys
        if present:
            self._log(
                f"[CACHE HIT-PARTIAL] idx={idx} label={label} "
                f"pdf={pdf_filename} present={present} missing={missing}"
            )
        else:
            self._log(f"[CACHE MISS] idx={idx} label={label} pdf={pdf_filename}")

        # Build RAG context and encode the document once
        rag_context, curr_emb = self.rag.build(label or "", pdf_raw_text)

        # Extract missing fields only
        new_fields: Dict[str, Optional[str]] = {}
        if missing:
            new_fields = self.orchestrator.extract(
                label=label or "",
                schema_keys=missing,
                pdf_raw_text=pdf_raw_text,
                rag_context=rag_context,
            )

        # Merge new + cached
        merged_fields = {**cached_fields, **new_fields}
        extracted_for_request = {k: merged_fields.get(k) for k in extraction_keys}

        # Vector store: first time only (when we have an embedding)
        vstore_added = entry.vstore_added if entry else False
        if not vstore_added and curr_emb is not None:
            self.vstore.add_document(
                label=label,
                doc_id=self._doc_id(pdf_filename, idx),
                embedding=curr_emb,
                pdf_raw_text=pdf_raw_text,
                extracted_fields=extracted_for_request,
                requested_fields={k: extraction_schema[k] for k in extraction_keys if k in extraction_schema},
            )
            vstore_added = True

        # Update cache LRU
        new_entry = CacheEntry(
            label=label,
            pdf_filename=pdf_filename,
            signature=signature,
            fields=merged_fields,
            vstore_added=vstore_added,
        )
        self.cache.put(doc_key, new_entry)

        payload = ResultPayload(
            label=label,
            pdf_filename=pdf_filename,
            requested_fields=extracted_for_request,
        )

        self._log(json.dumps(payload.__dict__, ensure_ascii=False, indent=2))
        return payload.__dict__

    # Private helpers 
    @staticmethod
    def _split_pdf_path(pdf_path: str) -> Tuple[str, str]:
        """Return (filename, directory) from a full path."""
        pdf_filename = os.path.basename(pdf_path)
        pdfs_root_path = os.path.dirname(pdf_path)
        return pdf_filename, pdfs_root_path

    def _build_doc_key(self, label: str, root: str, filename: str) -> Tuple[str, str]:
        """Compute a stable signature and document key."""
        signature = self.cache.compute_signature(root, filename, mode="fast")
        doc_key = self.cache.make_doc_key(label, filename, signature)
        return signature, doc_key

    @staticmethod
    def _schema_keys(schema: dict) -> Iterable[str]:
        """
        Normalize the schema to an iterable of keys.
        The pipeline only needs the keys (field names).
        """
        return list(schema.keys())

    @staticmethod
    def _partition_fields(
        wanted: Iterable[str],
        cached: Dict[str, Optional[str]],
    ) -> Tuple[list[str], list[str]]:
        """Partition requested keys into present vs. missing."""
        present = [k for k in wanted if k in cached]
        missing = [k for k in wanted if k not in cached]
        return present, missing

    @staticmethod
    def _doc_id(pdf_filename: Optional[str], idx: int) -> str:
        """Build a stable doc_id for the vector store."""
        return pdf_filename if pdf_filename else f"sample_{idx}"

    @staticmethod
    def _log(msg: str) -> None:
        """Thin wrapper to centralize logging/printing."""
        print(msg)

    def _load_pdf_text(self, pdf_content: Optional[str], root: str, filename: str) -> str:
        """
        Load raw text from PDF only if not provided.
        Returns empty string on failure to keep downstream robust.
        """
        if isinstance(pdf_content, str):
            return pdf_content

        try:
            text, _ = PDFExtractor.extract_pdf_text(pdf_path=os.path.join(root, filename))
            return text if isinstance(text, str) else ""
        except Exception as exc:  # be resilient to parser failures
            self._log(f"[WARN] Failed to load PDF text for '{filename}': {exc}")
            return ""

    def _ensure_vstore_once(
        self,
        entry: CacheEntry,
        label: str,
        pdf_filename: str,
        pdf_raw_text: str,
        extracted_fields: Dict[str, Optional[str]],
        requested_fields: Iterable[str],
        doc_id: str,
        doc_key: str,
    ) -> None:
        """
        On full cache hit, ensure the document is present in the vector store exactly once.
        Embeds on-demand to avoid double work.
        """
        try:
            curr_emb = self.embedder.encode(pdf_raw_text)
            self.vstore.add_document(
                label=label,
                doc_id=doc_id,
                embedding=curr_emb,
                pdf_raw_text=pdf_raw_text,
                extracted_fields=extracted_fields,
                requested_fields={k: extracted_fields.get(k) for k in requested_fields},
            )
            entry.vstore_added = True
            self.cache.put(doc_key, entry)
        except Exception as exc:
            # If vector-store insertion fails, proceed without breaking the request.
            self._log(f"[WARN] Vector-store insertion failed for '{pdf_filename}': {exc}")
