"""Parse routes for PDF parsing."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import tempfile
import os

from ..parser import Parser
from ..storage.artifact_store import ArtifactStore
from ..models.schema import ParseResult

router = APIRouter(prefix="/parse", tags=["parse"])
parser = Parser()
artifact_store = ArtifactStore()


@router.post("", response_model=ParseResult)
async def parse_pdf(file: UploadFile = File(...)):
    """Parse uploaded PDF file.
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        ParseResult with extracted data
    """
    if not file.filename.endswith(('.pdf', '.PDF')):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Parse PDF
        result = parser.parse_pdf(tmp_path)
        
        # Save result to artifact store
        artifact_store.save(result.doc_id, result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
