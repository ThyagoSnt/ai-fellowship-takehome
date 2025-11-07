# src/parsing/cache.py
from __future__ import annotations
import json
import os
import hashlib
from collections import OrderedDict
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional, Tuple
from ..pipeline.types import CacheEntry

class DocumentCache:
    """
    LRU cache keyed by (label, pdf_filename, signature).
    Also tracks the latest doc_key per (label, pdf_filename) to invalidate on file change.
    """
    def __init__(self, capacity: int = 2000) -> None:
        self._lru: "OrderedDict[str, CacheEntry]" = OrderedDict()
        self._capacity = capacity
        self._index: Dict[Tuple[Optional[str], Optional[str]], str] = {}

    # --------- signatures & keys ---------
    @staticmethod
    def _sha256_file(path: Path, max_bytes: Optional[int] = None) -> str:
        """SHA256 do arquivo inteiro (max_bytes=None) ou só dos primeiros N bytes."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            if max_bytes is None:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            else:
                h.update(f.read(max_bytes))
        return h.hexdigest()

    @staticmethod
    def compute_signature(
        pdfs_root: Path | str,
        pdf_filename: Optional[str],
        mode: str = "fast",
        hybrid_bytes: int = 2_000_000,
    ) -> str:
        if pdf_filename is None:
            return "missing"

        pdfs_root = Path(pdfs_root)
        p = pdfs_root / pdf_filename

        try:
            st = os.stat(p)
        except FileNotFoundError:
            return "missing"

        fast = f"{st.st_mtime_ns}:{st.st_size}"

        if mode == "fast":
            return fast
        elif mode == "strict":
            sha = DocumentCache._sha256_file(p)
            return f"{fast}:{sha}"
        elif mode == "hybrid":
            sha_head = DocumentCache._sha256_file(p, max_bytes=hybrid_bytes)
            return f"{fast}:{sha_head}"
        else:
            return fast

    @staticmethod
    def make_doc_key(label: Optional[str], pdf_filename: Optional[str], signature: str) -> str:
        raw = json.dumps({"label": label, "pdf_filename": pdf_filename, "sig": signature},
                         ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # --------- LRU operations ---------
    def _touch(self, doc_key: str) -> None:
        if doc_key in self._lru:
            self._lru.move_to_end(doc_key, last=True)

    def _set(self, doc_key: str, entry: CacheEntry) -> None:
        self._lru[doc_key] = entry
        self._touch(doc_key)
        while len(self._lru) > self._capacity:
            self._lru.popitem(last=False)

    def _get(self, doc_key: str) -> Optional[CacheEntry]:
        entry = self._lru.get(doc_key)
        if entry is not None:
            self._touch(doc_key)
        return entry

    # --------- public API ---------
    def upsert_latest_key(self, label: Optional[str], pdf_filename: Optional[str], new_key: str) -> None:
        base = (label, pdf_filename)
        old_key = self._index.get(base)
        if old_key is not None and old_key != new_key and old_key in self._lru:
            del self._lru[old_key]  # invalidate old version (PDF changed)
        self._index[base] = new_key

    def get(self, doc_key: str) -> Optional[CacheEntry]:
        return self._get(doc_key)

    def put(self, doc_key: str, entry: CacheEntry) -> None:
        self._set(doc_key, entry)

    def stats(self) -> Dict[str, int]:
        return {"size": len(self._lru), "capacity": self._capacity}

    def snapshot(self) -> Dict[str, Dict]:
        return {k: asdict(v) for k, v in self._lru.items()}
