"""Chatbot routes for interactive queries."""

from fastapi import APIRouter, HTTPException
import re
from ..models.schema import ChatRequest, ChatResponse
from ..storage.artifact_store import ArtifactStore
from ..math.explain import equation_to_nlp
from ..math.nlp_to_eq import nlp_to_equation

router = APIRouter(prefix="/chat", tags=["chat"])
artifact_store = ArtifactStore()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chatbot endpoint for querying parsed documents.
    
    Args:
        request: Chat request with doc_id and message
        
    Returns:
        Chat response
    """
    # Load document
    result = artifact_store.load(request.doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    message_lower = request.message.lower().strip()
    
    # Pattern matching for deterministic responses
    response = ""
    references = []
    
    # Pattern: "Explain equation eq-0003"
    explain_eq_match = re.search(r'explain\s+equation\s+(eq-\d+)', message_lower)
    if explain_eq_match:
        eq_id = explain_eq_match.group(1)
        eq = next((e for e in result.equations if e.eq_id == eq_id), None)
        if eq:
            response = f"Equation {eq_id}: {eq.explanation_nlp}"
            references.append({"type": "equation", "id": eq_id, "page": str(eq.page)})
        else:
            response = f"Equation {eq_id} not found."
        return ChatResponse(message=request.message, response=response, references=references)
    
    # Pattern: "Which equations have errors?"
    if "which equations have errors" in message_lower or "equations with errors" in message_lower:
        error_equations = [e for e in result.equations if e.errors]
        if error_equations:
            eq_ids = [e.eq_id for e in error_equations]
            response = f"Equations with errors: {', '.join(eq_ids)}"
            references = [{"type": "equation", "id": eq_id, "page": str(next(e.page for e in error_equations if e.eq_id == eq_id))} for eq_id in eq_ids]
        else:
            response = "No equations with errors found."
        return ChatResponse(message=request.message, response=response, references=references)
    
    # Pattern: "Convert ... to equation"
    convert_match = re.search(r'convert\s+(.+?)\s+to\s+equation', message_lower)
    if convert_match:
        nlp_text = convert_match.group(1)
        candidates = nlp_to_equation(nlp_text)
        if candidates:
            top_candidate = candidates[0]
            response = f"Equation: {top_candidate.get('equation', '')}. {top_candidate.get('explanation', '')}"
        else:
            response = f"Could not convert '{nlp_text}' to equation."
        return ChatResponse(message=request.message, response=response, references=references)
    
    # Pattern: "What is [symbol]?" (e.g., "What is Net Force?")
    what_is_match = re.search(r'what\s+is\s+(.+)', message_lower)
    if what_is_match:
        symbol_query = what_is_match.group(1).strip()
        # Search glossary
        matching_symbols = []
        for symbol, sym_data in result.glossary.items():
            if symbol_query.lower() in (sym_data.meaning or "").lower() or symbol_query.lower() in symbol.lower():
                matching_symbols.append((symbol, sym_data))
        
        # Also check equations
        matching_equations = [e for e in result.equations if symbol_query.lower() in e.explanation_nlp.lower()]
        
        if matching_symbols:
            symbol, sym_data = matching_symbols[0]
            response = f"Symbol '{symbol}': {sym_data.meaning or 'No meaning specified'}"
            if sym_data.unit:
                response += f" (unit: {sym_data.unit})"
            if matching_equations:
                eq_ids = [e.eq_id for e in matching_equations[:3]]
                response += f" Found in equations: {', '.join(eq_ids)}"
                references = [{"type": "equation", "id": eq_id, "page": str(next(e.page for e in matching_equations if e.eq_id == eq_id))} for eq_id in eq_ids]
        elif matching_equations:
            eq = matching_equations[0]
            response = f"Found in equation {eq.eq_id}: {eq.explanation_nlp}"
            references.append({"type": "equation", "id": eq.eq_id, "page": str(eq.page)})
        else:
            response = f"Could not find information about '{symbol_query}'."
        
        return ChatResponse(message=request.message, response=response, references=references)
    
    # Pattern: Count queries
    if "how many equations" in message_lower:
        response = f"Total equations: {result.summary.equations_total}"
        return ChatResponse(message=request.message, response=response, references=references)
    
    if "how many logic" in message_lower or "how many formulas" in message_lower:
        response = f"Total logic formulas: {result.summary.logic_total}"
        return ChatResponse(message=request.message, response=response, references=references)
    
    if "how many requirements" in message_lower or "how many srs" in message_lower:
        response = f"Total SRS requirements: {result.summary.srs_total}"
        return ChatResponse(message=request.message, response=response, references=references)
    
    # Default response
    response = "I can help you with: explaining equations, converting NLP to equations, finding errors, or querying symbols. Please try a specific question."
    return ChatResponse(message=request.message, response=response, references=references)
