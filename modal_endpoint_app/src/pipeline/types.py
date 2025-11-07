# src/pipeline/types.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class CacheEntry:
    label: Optional[str]
    pdf_filename: Optional[str]
    signature: str
    fields: Dict[str, Optional[str]] = field(default_factory=dict)
    vstore_added: bool = False

from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class ResultPayload:
    label: Optional[str] = None
    pdf_filename: Optional[str] = None
    requested_fields: List[str] = None
