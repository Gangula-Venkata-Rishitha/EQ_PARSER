"""Query routes for retrieving parsed data."""

from fastapi import APIRouter, HTTPException
from typing import Optional
from ..storage.artifact_store import ArtifactStore
from ..models.schema import ParseResult, Summary, Equation, LogicFormula, SRSRequirement

router = APIRouter(prefix="/document", tags=["query"])
artifact_store = ArtifactStore()


@router.get("/{doc_id}/summary", response_model=Summary)
async def get_summary(doc_id: str):
    """Get summary for a document.
    
    Args:
        doc_id: Document ID
        
    Returns:
        Summary object
    """
    result = artifact_store.load(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return result.summary


@router.get("/{doc_id}/equations", response_model=list[Equation])
async def get_equations(doc_id: str):
    """Get equations for a document.
    
    Args:
        doc_id: Document ID
        
    Returns:
        List of equations
    """
    result = artifact_store.load(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return result.equations


@router.get("/{doc_id}/logic", response_model=list[LogicFormula])
async def get_logic(doc_id: str):
    """Get logic formulas for a document.
    
    Args:
        doc_id: Document ID
        
    Returns:
        List of logic formulas
    """
    result = artifact_store.load(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return result.logic_formulas


@router.get("/{doc_id}/srs", response_model=list[SRSRequirement])
async def get_srs(doc_id: str):
    """Get SRS requirements for a document.
    
    Args:
        doc_id: Document ID
        
    Returns:
        List of SRS requirements
    """
    result = artifact_store.load(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return result.srs_requirements


@router.get("/{doc_id}", response_model=ParseResult)
async def get_document(doc_id: str):
    """Get full document parse result.
    
    Args:
        doc_id: Document ID
        
    Returns:
        Full ParseResult
    """
    result = artifact_store.load(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return result
