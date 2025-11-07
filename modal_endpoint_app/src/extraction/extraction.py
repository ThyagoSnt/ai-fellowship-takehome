# src/extraction/extraction.py
from __future__ import annotations
from typing import Dict, List, Optional
from .llm_response import FieldExtractor

class ExtractionOrchestrator:
    def __init__(
            self,
            extractor: Optional[FieldExtractor] = None
            ) -> None:
        
        self.extractor = extractor or FieldExtractor()

    def extract(
        self,
        label: str,
        schema_keys: List[str],
        pdf_raw_text: str,
        rag_context: Optional[str],
    ) -> Dict[str, Optional[str]]:
        
        return self.extractor._extract_with_gpt(
            text=pdf_raw_text,
            schema_keys=schema_keys,
            label=label,
            rag_context=rag_context,
        )
