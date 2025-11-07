import modal
from fastapi.security import HTTPBearer
from typing import List
auth_scheme = HTTPBearer()

# Modal app and image setup
image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .pip_install(
        "fastapi[standard]==0.117.1",
        "pydantic==2.10.3",
        "pillow==11.2.1",
        "chromadb==1.1.0",
        "numpy==2.2.6",
        "PyMuPDF==1.26.3",
        "sentence-transformers==5.1.1",
        "python-dotenv==1.1.1",
        "uvicorn==0.37.0",
        "langchain-openai==0.3.35",
        "langchain==0.3.27"
    )
    .add_local_dir("./modal_endpoint_app/src", remote_path="/root/modal_endpoint_app/src")
    .add_local_dir("./modal_endpoint_app/config", remote_path="/root/modal_endpoint_app/config")
    .add_local_file("./.env", remote_path="/root/.env")
)
app = modal.App(name="enter_document_parsing_system", image=image)

from modal_endpoint_app.src.schemas.v1.schemas import ParsingRequisition

# Imports within the Modal image context
with image.imports():
    from modal_endpoint_app.src.pipeline.pipeline import Solution

# Modal function
@app.function(
    image=image,
    timeout=60 * 60 * 24,
    gpu="T4",
    scaledown_window=1200 # 30 min alive
)
def document_parsing(idx: int, label: str, extraction_schema: dict, pdf_path: str, pdf_content: str):
    solution = Solution()
    parsed = solution.process_single_sample(idx, label, extraction_schema, pdf_path, pdf_content)
    return parsed


# FastAPI endpoint
@app.function()
@modal.fastapi_endpoint(method="POST")
def document_parsing_scheduler(
    requisitions_list: List[ParsingRequisition]):
    
    results = []
    for idx, requisition in enumerate(requisitions_list):
        result = document_parsing.remote(
            idx,
            requisition.label,
            requisition.extraction_schema,
            requisition.pdf_path,
            requisition.pdf_content
        )
        results.append(result)

    return results


# Health check endpoint (no token required)
@app.function()
@modal.fastapi_endpoint(method="GET")
def health_check():
    """Simple health check to verify Modal API availability."""
    return {"status": "ok", "message": "Modal document parsing API is running"}
