from pydantic import BaseModel, Field, field_validator
from pathlib import Path

class InferenceRequest(BaseModel):
    label: str
    extraction_schema: dict
    pdf_path: str

class BatchRequest(BaseModel):
    json_path: Path
    pdfs_root_path: Path = Field(default=Path("ai-fellowship-data/files"))

    @field_validator("pdfs_root_path", mode="before")
    @classmethod
    def coerce_path(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return Path("ai-fellowship-data/files")
        return v