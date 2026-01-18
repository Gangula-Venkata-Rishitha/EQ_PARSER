"""Conversion routes for equation ↔ NLP."""

from fastapi import APIRouter, HTTPException
from ..models.schema import (
    ConvertEquationToNLPRequest, ConvertEquationToNLPResponse,
    ConvertNLPToEquationRequest, ConvertNLPToEquationResponse
)
from ..math.explain import equation_to_nlp
from ..math.nlp_to_eq import nlp_to_equation
from ..storage.artifact_store import ArtifactStore
from ..glossary.glossary import Glossary

router = APIRouter(prefix="/convert", tags=["convert"])
artifact_store = ArtifactStore()


@router.post("/equation-to-nlp", response_model=ConvertEquationToNLPResponse)
async def convert_equation_to_nlp(request: ConvertEquationToNLPRequest):
    """Convert equation to natural language.
    
    Args:
        request: Equation string
        
    Returns:
        NLP explanation
    """
    try:
        nlp = equation_to_nlp(request.equation)
        return ConvertEquationToNLPResponse(
            equation=request.equation,
            nlp=nlp,
            confidence=1.0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting equation: {str(e)}")


@router.post("/nlp-to-equation", response_model=ConvertNLPToEquationResponse)
async def convert_nlp_to_equation(request: ConvertNLPToEquationRequest):
    """Convert NLP to equation.
    
    Args:
        request: NLP text (optional doc_id for glossary)
        
    Returns:
        Equation candidates
    """
    try:
        # Load glossary if doc_id provided
        glossary = None
        if request.doc_id:
            result = artifact_store.load(request.doc_id)
            if result:
                # Create glossary from stored data
                glossary = Glossary()
                glossary.symbols = result.glossary
        
        # Convert NLP to equation
        candidates = nlp_to_equation(request.nlp, glossary)
        
        # Format candidates
        formatted_candidates = []
        for candidate in candidates:
            formatted_candidates.append({
                "equation": candidate.get("equation", ""),
                "explanation": candidate.get("explanation", ""),
                "confidence": candidate.get("confidence", 0.0)
            })
        
        return ConvertNLPToEquationResponse(
            nlp=request.nlp,
            candidates=formatted_candidates
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting NLP: {str(e)}")
