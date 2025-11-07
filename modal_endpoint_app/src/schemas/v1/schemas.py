from pydantic import BaseModel

class ParsingRequisition(BaseModel):
    label: str
    extraction_schema: dict
    pdf_path: str
    pdf_content: str 